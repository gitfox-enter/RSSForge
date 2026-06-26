/* Frame-busting for clickjacking protection */
if(window.top!==window.self){try{window.top.location=window.location}catch(e){/* blocked by browser, keep page visible */}}

/* ================================================================
   DATA & STATE
   ================================================================ */
var allItems = [];
var sources = [];       // [{name, count, color}]
var activeSource = 'all';
var searchQuery = '';
var currentPage = 1;
var PAGE_SIZE = 40;
var currentView = 'list';
var todayOnly = false;
var sortOrder = 'newest'; // 'newest' or 'oldest'
var deferredPrompt;       // PWA install prompt event
/* Source name normalization map */
var SOURCE_MAP = {
  '线报酷 - 专注线报活动与优惠促销分享的线报网站': '线报酷',
  '好赚网 - 每日分享新鲜活动线报和优惠信息': '好赚网',
  '0818团线报资源网-京东优惠券/抽奖-为赚客服务的一手线报网站-0818线报': '0818团',
  '拔草哦 | 折扣信息分享网站_推荐海淘折扣信息_转运攻略，告诉你什么值得买': '拔草哦',
  '聚合线报 - 实时优惠线报 | 薅羊毛 | 赚客吧 | 好单精选': '聚合线报',
  '鲸线报 - 专业实时搜集与分享全网优惠线报和促销活动的平台': '鲸线报',
  '超级线报 - 实时监控 / AI驱动 / 体验超好的线报网站！': '超级线报',
  '白菜哦-高性价比网购海淘推荐': '白菜哦'
};

/* Source badge colors */
var SRC_COLORS = {
  '赚客吧':   '#e53935',
  '线报酷':   '#1e88e5',
  '好赚网':   '#8e24aa',
  '汇发部':   '#00897b',
  '聚合线报':  '#f4511e',
  '拔草哦':   '#d81b60',
  '新赚吧':   '#6d4c41',
  '0818团':   '#546e7a',
  '鲸线报':   '#039be5',
  '专业线报':  '#7cb342',
  '超级线报':  '#fb8c00',
  '线报ICU':  '#5e35b1',
  '白菜哦':   '#00acc1',
  '促销吧':   '#c0ca33',
  '好赚线报':  '#ab47bc',
  '79淘':     '#ff7043',
  '907线报':  '#26a69a',
  '天天赚':   '#ff8a65',
  '慢慢买':   '#42a5f5',
  '小众软件':  '#66bb6a',
  'IT之家':   '#ef5350',
  '开心赚':   '#ffa726',
  '羊毛党':   '#ab47bc',
  '线报迷':   '#29b6f6',
  '羊毛王':   '#ff5722',
  '资源厅':   '#5c6bc0',
  '51卡农':   '#8d6e63',
  '线报网':   '#26c6da',
  '小嘀咕':   '#ec407a',
  '豆瓣小组':  '#66bb6a',
  '好单库':   '#26a69a',
  '免费族':   '#78909c',
  '网赚':     '#7e57c2',
  '优惠线报':  '#ff7043',
  '活动5':    '#42a5f5'
};
var DEFAULT_COLOR = '#78909c';

function normalizeSource(raw) {
  if (!raw) return '未知来源';
  var mapped = SOURCE_MAP[raw];
  return mapped || raw;
}

function getSourceColor(name) {
  return SRC_COLORS[name] || DEFAULT_COLOR;
}

function getSourceChar(name) {
  if (!name) return '?';
  return name.charAt(0);
}

/* ================================================================
   TODAY FILTER & SORT CONTROLS
   ================================================================ */
function toggleTodayFilter() {
  todayOnly = !todayOnly;
  currentPage = 1;
  var btn = document.getElementById('today-toggle');
  btn.classList.toggle('active', todayOnly);
  btn.setAttribute('aria-pressed', String(todayOnly));
  renderList();
  updateStatus();
}

function toggleSortOrder() {
  sortOrder = sortOrder === 'newest' ? 'oldest' : 'newest';
  currentPage = 1;
  var btn = document.getElementById('sort-btn');
  btn.textContent = sortOrder === 'newest' ? '最新优先 ↓' : '最早优先 ↑';
  renderList();
}

/* ================================================================
   PLATFORM DETECTION
   ================================================================ */
var PLATFORM_RULES = [
  {name: '京东', kw: ['京东','jd.com','jd','京豆','京享','百亿补贴','PLUS']},
  {name: '淘宝', kw: ['淘宝','天猫','tmall','taobao','淘金币']},
  {name: '拼多多', kw: ['拼多多','pdd','拼多','拼夕夕']},
  {name: '抖音', kw: ['抖音','douyin','tiktok']},
  {name: '外卖', kw: ['外卖','美团','饿了么']},
  {name: '唯品会', kw: ['唯品会','vip.com']},
  {name: '苏宁', kw: ['苏宁','suning']}
];

function detectPlatform(item) {
  var text = (item.text || '') + ' ' + (item.url || '');
  for (var i = 0; i < PLATFORM_RULES.length; i++) {
    var r = PLATFORM_RULES[i];
    for (var j = 0; j < r.kw.length; j++) {
      if (text.indexOf(r.kw[j]) !== -1) return r.name;
    }
  }
  return null;
}

/* ================================================================
   GIST DATA LOADER
   Loads data from GitHub Gist (CDN-cached) with local fallback.
   Reduces Git repo size by keeping items.json out of version control.
   ================================================================ */
var _gistRef = null;  // Cached items_ref.json data

function _fetchData(filename) {
  // Strategy: try Gist (via items_ref.json) first, then local fallback
  var refPromise = _gistRef
    ? Promise.resolve(_gistRef)
    : fetch('items_ref.json?t=' + Date.now())
      .then(function(r) {
        if (!r.ok) return null;
        return r.json();
      })
      .catch(function() { return null; });

  function _tryFallback(ref, key) {
    // Try fallback from ref or local file
    var fallbackUrl = (ref && ref.fallback && ref.fallback[key])
      ? ref.fallback[key] + '?t=' + Date.now()
      : filename + '?t=' + Date.now();
    return fetch(fallbackUrl, {priority: 'high'})
      .then(function(r) {
        if (!r.ok) throw new Error('Fallback fetch failed: ' + r.status);
        return r.json();
      });
  }

  return refPromise.then(function(ref) {
    if (ref) _gistRef = ref;
    var key = filename.replace('.json', '');

    // Try Gist URL first if available
    if (ref && ref.files && ref.files[key]) {
      var url = ref.files[key] + '?t=' + Date.now();
      return fetch(url, {priority: 'high'}).then(function(r) {
        if (!r.ok) throw new Error('Gist fetch failed: ' + r.status);
        return r.json();
      }).then(function(data) {
        // If Gist returned empty items, try local fallback
        if (data && data.items && data.items.length === 0 && ref.fallback && ref.fallback[key]) {
          return _tryFallback(ref, key);
        }
        return data;
      }).catch(function(err) {
        // Gist fetch failed — try fallback
        console.warn('Gist load failed, trying fallback:', err.message);
        return _tryFallback(ref, key);
      });
    }

    // If ref has local/fallback paths, use them
    if (ref && ref.fallback && ref.fallback[key]) {
      return fetch(ref.fallback[key] + '?t=' + Date.now(), {priority: 'high'})
        .then(function(r) {
          if (!r.ok) throw new Error('Local fetch failed: ' + r.status);
          return r.json();
        });
    }

    // Final fallback: try local file directly
    return fetch(filename + '?t=' + Date.now(), {priority: 'high'})
      .then(function(r) {
        if (!r.ok) throw new Error('Local fetch failed: ' + r.status);
        return r.json();
      });
  });
}

/* ================================================================
   PRICE HIGHLIGHTING
   ================================================================ */
var PRICE_RE = /((?:到手|约|仅需|券后|实付|折合|折后|大概)?[¥￥]?\d+(?:\.\d+)?(?:元|块|亓|￥)?)/g;
function highlightPrice(text) {
  return text.replace(PRICE_RE, '<span class="price-hl">$1</span>');
}

/* ================================================================
   TIME FORMATTING
   ================================================================ */
function formatTime(t) {
  if (!t) return '';
  return t.replace(/^\d{4}-/, '').replace(/:\d{2}$/, '');
}

/* ================================================================
   TITLE CLEANUP - strip leading date/time prefixes
   ================================================================ */
function cleanTitle(text) {
  if (!text) return '';
  // Strip leading "MM-DD HH:MM" pattern (e.g., "06-07 20:08伊利...")
  text = text.replace(/^\d{2}[-/]\d{2}\s+\d{2}:\d{2}\s*/, '');
  // Also strip "MM-DD" at start if followed by Chinese text
  text = text.replace(/^\d{2}[-/]\d{2}\s+/, '');
  return text.trim();
}

/* ================================================================
   DATA LOADING
   ================================================================ */
function loadData() {
  // Try to restore from cache first (back-navigation)
  var savedScrollY = restoreScrollState();
  var usedCache = false;

  if (savedScrollY !== false && tryRestoreFromCache()) {
    // Back-navigation: use cached data, skip fetch
    usedCache = true;
    buildSidebar();
    buildMobileDropdown();
    renderAll();
    updateStatus();

    // Scroll to saved position after DOM is ready
    var scrollTarget = savedScrollY;
    var attempts = 0;
    function tryScroll() {
      attempts++;
      window.scrollTo(0, scrollTarget);
      // Verify scroll actually worked (DOM might not be tall enough yet)
      if (window.scrollY < scrollTarget - 50 && attempts < 10) {
        requestAnimationFrame(tryScroll);
      } else {
        // Successfully restored
        try { sessionStorage.removeItem(SCROLL_KEY); sessionStorage.removeItem(DATA_KEY); } catch(e) {}
      }
    }
    requestAnimationFrame(tryScroll);

    // Refresh data in background (silently, no re-render unless new items found)
    _fetchData('items_latest.json').then(function(data) {
      if (!data || !data.items) return;
      var newItems = data.items.map(function(it) {
        return { url: it.url || '', text: (it.text || '').trim(), source: normalizeSource(it.source), rawSource: it.source || '', time: it.time || '', category: it.category || null, platform: detectPlatform(it) };
      });
      if (newItems.length > allItems.length) {
        allItems = newItems;
        var srcMap = {};
        allItems.forEach(function(it) { srcMap[it.source] = (srcMap[it.source] || 0) + 1; });
        sources = Object.keys(srcMap).map(function(name) { return { name: name, count: srcMap[name], color: getSourceColor(name) }; }).sort(function(a, b) { return b.count - a.count; });
        buildSidebar();
        buildMobileDropdown();
        renderList();
        updateStatus();
      }
    }).catch(function() {});

    return;
  }

  // Normal load: fresh fetch
  document.getElementById('item-list').innerHTML = '<div class="loading">加载中</div>';

  _fetchData('items_latest.json')
    .then(function(data) {
      var rawItems = data.items || [];
      /* Capture last update time */
      var lastUpdate = data.updated_at || data.last_updated || '';
      if (!lastUpdate && rawItems.length > 0) {
        /* Fallback: use the most recent item time */
        var latest = '';
        for (var i = 0; i < Math.min(rawItems.length, 50); i++) {
          if (rawItems[i].time && rawItems[i].time > latest) latest = rawItems[i].time;
        }
        lastUpdate = latest;
      }
      if (lastUpdate) {
        var el = document.getElementById('last-update');
        if (el) el.textContent = '更新于 ' + lastUpdate.replace(' ', ' ').slice(5, 16);
      }
      /* Normalize sources & detect platform */
      allItems = rawItems.map(function(it) {
        return {
          url: it.url || '',
          text: (it.text || '').trim(),
          source: normalizeSource(it.source),
          rawSource: it.source || '',
          time: it.time || '',
          category: it.category || null,
          platform: detectPlatform(it)
        };
      });

      /* Build source stats */
      var srcMap = {};
      allItems.forEach(function(it) {
        srcMap[it.source] = (srcMap[it.source] || 0) + 1;
      });
      sources = Object.keys(srcMap).map(function(name) {
        return { name: name, count: srcMap[name], color: getSourceColor(name) };
      }).sort(function(a, b) { return b.count - a.count; });

      buildSidebar();
      buildMobileDropdown();

      // Load full items.json in background for complete archive
      _fetchData('items.json').then(function(fullData) {
        var fullItems = fullData.items || [];
        if (fullItems.length > allItems.length) {
          allItems = fullItems.map(function(it) {
            return { url: it.url || '', text: (it.text || '').trim(), source: normalizeSource(it.source), rawSource: it.source || '', time: it.time || '', category: it.category || null, platform: detectPlatform(it) };
          });
          // Rebuild sidebar with full source list
          var srcMap2 = {};
          allItems.forEach(function(it) { srcMap2[it.source] = (srcMap2[it.source] || 0) + 1; });
          sources = Object.keys(srcMap2).map(function(name) { return { name: name, count: srcMap2[name], color: getSourceColor(name) }; }).sort(function(a, b) { return b.count - a.count; });
          buildSidebar();
          buildMobileDropdown();
          renderList();
          updateStatus();
          // Sync localStorage count with full dataset (no badge flash)
          try { localStorage.setItem('xb_last_count', String(allItems.length)); } catch(e) {}
        }
      }).catch(function() { /* full load failed, latest is enough */ });

      renderAll();
      updateStatus();
    })
    .catch(function(err) {
      var el = document.getElementById('item-list');
      el.innerHTML = '<div class="list-empty">加载失败，请刷新重试<br><small></small></div>';
      el.querySelector('small').textContent = err.message || '未知错误';
    });

/* ================================================================
   SIDEBAR
   ================================================================ */
function buildSidebar() {
  var container = document.getElementById('sidebar-cats');
  var html = '<button class="cat-item' + (activeSource === 'all' ? ' active' : '') + '" data-src="all" onclick="selectSource(\'all\')" aria-label="筛选来源: 全部线报" aria-pressed="' + (activeSource === 'all') + '">' +
    '<span class="cat-name">全部线报</span>' +
    '<span class="cat-count">' + allItems.length + '</span></button>';

  sources.forEach(function(s) {
    var isActive = activeSource === s.name;
    html += '<button class="cat-item' + (isActive ? ' active' : '') + '" data-src="' + escAttr(s.name) + '" onclick="selectSource(\'' + escAttr(s.name) + '\')" aria-label="筛选来源: ' + escAttr(s.name) + '" aria-pressed="' + isActive + '">' +
      '<span class="cat-name">' + esc(s.name) + '</span>' +
      '<span class="cat-count">' + s.count + '</span></button>';
  });

  container.innerHTML = html;
}

function buildMobileDropdown() {
  var container = document.getElementById('cat-dropdown');
  var html = '<button class="cat-item' + (activeSource === 'all' ? ' active' : '') + '" onclick="selectSource(\'all\');closeCatDropdown()" role="option" aria-selected="' + (activeSource === 'all') + '">' +
    '<span class="cat-name">全部线报</span>' +
    '<span class="cat-count">' + allItems.length + '</span></button>';

  sources.forEach(function(s) {
    var isActive = activeSource === s.name;
    html += '<button class="cat-item' + (isActive ? ' active' : '') + '" onclick="selectSource(\'' + escAttr(s.name) + '\');closeCatDropdown()" role="option" aria-selected="' + isActive + '">' +
      '<span class="cat-name">' + esc(s.name) + '</span>' +
      '<span class="cat-count">' + s.count + '</span></button>';
  });

  container.innerHTML = html;
}

function selectSource(name) {
  activeSource = name;
  currentPage = 1;
  buildSidebar();
  buildMobileDropdown();
  renderList();
  updateStatus();
  /* Update toggle bar text */
  var toggleText = document.getElementById('cat-toggle-text');
  toggleText.textContent = name === 'all' ? '全部线报' : name;
  /* Scroll to top of list */
  window.scrollTo({top: 0, behavior: 'smooth'});
}

/* ================================================================
   FILTERING
   ================================================================ */
function isNoiseItem(item) {
  if (!item || !item.url) return false;
  var url = item.url;
  /* Navigation / non-content page patterns */
  if (/\bforum\.php\?/i.test(url) && !/mod=redirect/i.test(url)) return true;
  if (/xianbao-my\.html/i.test(url)) return true;
  if (/xianbao-day\.html/i.test(url)) return true;
  if (/member\.php\?mod=logging/i.test(url)) return true;
  if (/beian\.miit\.gov\.cn/i.test(url)) return true;
  if (/beian\.mps\.gov\.cn/i.test(url)) return true;
  /* ICP/micp registration text patterns */
  if (item.text && /(?:[京津沪渝冀晋辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新]ICP|[京津沪渝冀晋辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云藏陕甘青宁新]公网安备)/.test(item.text)) return true;
  return false;
}

function getFiltered() {
  var filtered = allItems;

  /* Noise filter */
  filtered = filtered.filter(function(it) { return !isNoiseItem(it); });

  /* Source filter */
  if (activeSource !== 'all') {
    filtered = filtered.filter(function(it) { return it.source === activeSource; });
  }

  /* Today filter */
  if (todayOnly) {
    var now = new Date();
    var y = now.getFullYear();
    var m = String(now.getMonth() + 1).padStart(2, '0');
    var d = String(now.getDate()).padStart(2, '0');
    var todayStr = y + '-' + m + '-' + d;
    filtered = filtered.filter(function(it) {
      return it.time && it.time.substring(0, 10) === todayStr;
    });
  }

  /* Search filter */
  if (searchQuery) {
    var q = searchQuery.toLowerCase();
    filtered = filtered.filter(function(it) {
      return it.text.toLowerCase().indexOf(q) !== -1 ||
             it.source.toLowerCase().indexOf(q) !== -1 ||
             (it.platform && it.platform.toLowerCase().indexOf(q) !== -1);
    });
  }

  /* Sort by time */
  filtered.sort(function(a, b) {
    if (sortOrder === 'newest') {
      return (b.time || '').localeCompare(a.time || '');
    } else {
      return (a.time || '').localeCompare(b.time || '');
    }
  });

  return filtered;
}

/* ================================================================
   RENDERING
   ================================================================ */
function renderAll() {
  renderList();
}

function renderList() {
  var filtered = getFiltered();
  var total = filtered.length;
  var totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (currentPage > totalPages) currentPage = totalPages;

  var start = (currentPage - 1) * PAGE_SIZE;
  var pageItems = filtered.slice(start, start + PAGE_SIZE);

  var container = document.getElementById('item-list');

  if (total === 0) {
    var hint = searchQuery
      ? '换个关键词试试，或清空搜索查看全部线报'
      : (activeSource !== 'all' ? '该来源暂无线报，试试其他来源' : '暂无线报数据');
    container.innerHTML =
      '<div class="list-empty">' +
        '<span class="empty-icon">📭</span>' +
        '<div>暂无相关线报</div>' +
        '<div class="empty-hint">' + esc(hint) + '</div>' +
        (searchQuery || activeSource !== 'all'
          ? '<button class="empty-action" onclick="resetFilters()">查看全部线报</button>'
          : '') +
      '</div>';
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  var html = '';
  pageItems.forEach(function(it) {
    var char = getSourceChar(it.source);
    var color = getSourceColor(it.source);
    var title = highlightPrice(esc(cleanTitle(it.text)));
    var time = formatTime(it.time);
    var platformHtml = it.platform ? '<span class="platform-tag">' + esc(it.platform) + '</span>' : '';

    html += '<article class="item" role="listitem">' +
      '<a href="redirect.html?url=' + encodeURIComponent(it.url) + '&title=' + encodeURIComponent(cleanTitle(it.text)) + '" target="_blank" rel="noopener noreferrer" aria-label="' + escAttr(cleanTitle(it.text)) + ' - 来源: ' + escAttr(it.source) + ' (安全跳转)">' +
        '<span class="src-badge" style="background:' + color + '" aria-hidden="true">' + esc(char) + '</span>' +
        '<div class="item-body">' +
          '<div class="item-title">' + title + '</div>' +
          '<div class="item-meta">' +
            '<span>' +
              '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' +
              '<time>' + esc(time) + '</time>' +
            '</span>' +
            platformHtml +
          '</div>' +
        '</div>' +
      '</a>' +
    '</article>';
  });

  try {
    container.innerHTML = html;
  } catch(e) {
    console.error('renderList error:', e);
    container.innerHTML = '<div class="list-empty">数据渲染出错，请刷新页面重试</div>';
    return;
  }
  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  var container = document.getElementById('pagination');
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  var prevClass = currentPage <= 1 ? 'page-btn disabled' : 'page-btn';
  var nextClass = currentPage >= totalPages ? 'page-btn disabled' : 'page-btn';

  var selectHtml = '<select id="page-select" onchange="goToPage(this.value)">';
  for (var i = 1; i <= totalPages; i++) {
    selectHtml += '<option value="' + i + '"' + (i === currentPage ? ' selected' : '') + '>第 ' + i + ' 页</option>';
  }
  selectHtml += '</select>';

  container.innerHTML =
    '<button class="' + prevClass + '" onclick="goToPage(' + (currentPage - 1) + ')">上一页</button>' +
    selectHtml +
    '<button class="' + nextClass + '" onclick="goToPage(' + (currentPage + 1) + ')">下一页</button>';
}

function goToPage(p) {
  p = parseInt(p);
  var filtered = getFiltered();
  var totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  if (p < 1 || p > totalPages) return;
  currentPage = p;
  renderList();
  updateStatus();
  window.scrollTo({top: 0, behavior: 'smooth'});
}

/* ================================================================
   VIEW SWITCHING
   ================================================================ */
function switchView(view) {
  currentView = view;

  /* Update menu */
  document.querySelectorAll('#menu button').forEach(function(el) {
    el.classList.toggle('active', el.getAttribute('data-view') === view);
  });

  /* Show/hide sections */
  document.getElementById('list-view').style.display = view === 'list' ? '' : 'none';
}

/* ================================================================
   SEARCH
   ================================================================ */
function handleSearch(e) {
  e.preventDefault();
  searchQuery = document.getElementById('search-input').value.trim();
  currentPage = 1;
  renderList();
  updateStatus();
}

function resetFilters() {
  searchQuery = '';
  activeSource = 'all';
  todayOnly = false;
  sortOrder = 'newest';
  currentPage = 1;
  document.getElementById('search-input').value = '';
  var todayBtn = document.getElementById('today-toggle');
  todayBtn.classList.remove('active');
  todayBtn.setAttribute('aria-pressed', 'false');
  document.getElementById('sort-btn').textContent = '最新优先 ↓';
  buildSidebar();
  buildMobileDropdown();
  renderAll();
  updateStatus();
  document.getElementById('cat-toggle-text').textContent = '全部线报';
}

/* ================================================================
   STATUS
   ================================================================ */
function updateStatus() {
  var filtered = getFiltered();
  var el = document.getElementById('status-text');
  el.removeAttribute('aria-busy');
  var parts = [];

  if (activeSource !== 'all') {
    parts.push('来源: <span class="highlight">' + esc(activeSource) + '</span>');
  }
  if (searchQuery) {
    parts.push('搜索: <span class="highlight">"' + esc(searchQuery) + '"</span>');
  }
  if (todayOnly) {
    parts.push('<span class="highlight">只看今天</span>');
  }

  var totalCount = allItems.length;
  var filteredCount = filtered.length;
  var countText = '共 ' + filteredCount + ' 条线报';
  if (filteredCount !== totalCount) {
    countText = '显示 <span class="ct-hl">' + filteredCount + '</span> / ' + totalCount + ' 条';
  }
  parts.push(countText);

  el.innerHTML = parts.join(' · ');

  /* Also update the toolbar item count */
  var countEl = document.getElementById('item-count');
  if (countEl) {
    if (filteredCount !== totalCount) {
      countEl.innerHTML = '显示 <span class="ct-hl">' + filteredCount + '</span> / ' + totalCount + ' 条';
    } else {
      countEl.innerHTML = '共 ' + totalCount + ' 条';
    }
  }
}

/* ================================================================
   MOBILE CATEGORY DROPDOWN
   ================================================================ */
var catDropdownOpen = false;
function toggleCatDropdown() {
  catDropdownOpen = !catDropdownOpen;
  var dd = document.getElementById('cat-dropdown');
  var bar = document.getElementById('cat-toggle-bar');
  dd.classList.toggle('open', catDropdownOpen);
  bar.classList.toggle('open', catDropdownOpen);
  bar.setAttribute('aria-expanded', catDropdownOpen);
}
function closeCatDropdown() {
  catDropdownOpen = false;
  document.getElementById('cat-dropdown').classList.remove('open');
  document.getElementById('cat-toggle-bar').classList.remove('open');
  document.getElementById('cat-toggle-bar').setAttribute('aria-expanded', 'false');
}

/* ================================================================
   BACK TO TOP
   ================================================================ */
window.addEventListener('scroll', function() {
  document.getElementById('back-top').classList.toggle('show', window.scrollY > 300);
});

/* ================================================================
   UTILITIES
   ================================================================ */
function esc(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function escAttr(s) {
  if (!s) return '';
  return s.replace(/\\/g, '\\\\').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ================================================================
   KEYBOARD SHORTCUTS
   ================================================================ */
document.addEventListener('keydown', function(e) {
  var tag = (e.target.tagName || '').toLowerCase();
  var isInput = tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable;

  /* Esc: close dropdown, blur search, clear search */
  if (e.key === 'Escape') {
    if (catDropdownOpen) closeCatDropdown();
    if (isInput) { e.target.blur(); }
    if (searchQuery) {
      document.getElementById('search-input').value = '';
      searchQuery = '';
      currentPage = 1;
      renderAll();
      updateStatus();
    }
    return;
  }

  /* / : focus search (when not already in an input) */
  if (e.key === '/' && !isInput && !e.ctrlKey && !e.metaKey && !e.altKey) {
    e.preventDefault();
    document.getElementById('search-input').focus();
    return;
  }
});

/* Show keyboard hints on desktop after load */
if (window.innerWidth > 960) {
  setTimeout(function() {
    var hint = document.getElementById('kbd-hint');
    hint.classList.add('show');
    setTimeout(function() { hint.classList.remove('show'); }, 5000);
  }, 2000);
}

/* ================================================================
   REDUCED MOTION
   ================================================================ */
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  document.documentElement.style.scrollBehavior = 'auto';
  var style = document.createElement('style');
  style.textContent = '*,*::before,*::after{animation-duration:0.01ms!important;transition-duration:0.01ms!important}';
  document.head.appendChild(style);
}

/* ================================================================
   PWA INSTALL PROMPT (handled below after loadData)
   ================================================================ */
/* deferredPrompt is set via the beforeinstallprompt listener below */
/* Hide install button if app is already installed (standalone mode) */
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
  var ib = document.getElementById('install-btn');
  if (ib) ib.style.display = 'none';
}
function installApp() {
  if (!deferredPrompt) {
    showToast('💡 您的浏览器不支持安装，请使用 Chrome/Edge 打开本站');
    return;
  }
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then(function(result) {
    if (result.outcome === 'accepted') {
      var btn = document.getElementById('install-btn');
      if (btn) { btn.classList.remove('visible'); btn.style.display = 'none'; }
    }
    deferredPrompt = null;
  });
}

/* ================================================================
   TOUCH GESTURES (swipe to switch views)
   ================================================================ */
/* ================================================================
   SERVICE WORKER
   ================================================================ */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(function(){});
}

/* ================================================================
   SCROLL POSITION & STATE RESTORE (back-navigation fix)
   ================================================================ */
var SCROLL_KEY = 'xb_scroll_state';
var DATA_KEY = 'xb_cached_data';
var _restorePending = false;

function saveScrollState() {
  try {
    sessionStorage.setItem(SCROLL_KEY, JSON.stringify({
      scrollY: window.scrollY,
      activeSource: activeSource,
      searchQuery: searchQuery,
      currentPage: currentPage,
      todayOnly: todayOnly,
      sortOrder: sortOrder,
      timestamp: Date.now()
    }));
    // Also cache current data so we can render without fetching
    if (allItems.length > 0) {
      sessionStorage.setItem(DATA_KEY, JSON.stringify({
        items: allItems,
        sources: sources,
        timestamp: Date.now()
      }));
    }
  } catch(e) {}
}

function restoreScrollState() {
  try {
    var raw = sessionStorage.getItem(SCROLL_KEY);
    if (!raw) return false;
    var state = JSON.parse(raw);
    // Only restore if within 30 minutes
    if (Date.now() - state.timestamp > 30 * 60 * 1000) {
      sessionStorage.removeItem(SCROLL_KEY);
      sessionStorage.removeItem(DATA_KEY);
      return false;
    }
    // Restore filters
    if (state.activeSource && state.activeSource !== 'all') {
      activeSource = state.activeSource;
    }
    if (state.searchQuery) {
      searchQuery = state.searchQuery;
      document.getElementById('search-input').value = searchQuery;
    }
    if (state.currentPage) currentPage = state.currentPage;
    if (state.todayOnly) {
      todayOnly = true;
      var todayBtn = document.getElementById('today-toggle');
      if (todayBtn) { todayBtn.classList.add('active'); todayBtn.setAttribute('aria-pressed', 'true'); }
    }
    if (state.sortOrder && state.sortOrder !== 'newest') {
      sortOrder = state.sortOrder;
      var sortBtn = document.getElementById('sort-btn');
      if (sortBtn) sortBtn.textContent = '最早优先 ↑';
    }
    // Update category toggle text
    var toggleText = document.getElementById('cat-toggle-text');
    if (toggleText) toggleText.textContent = activeSource === 'all' ? '全部线报' : activeSource;
    _restorePending = true;
    return state.scrollY || 0;
  } catch(e) {
    return false;
  }
}

function tryRestoreFromCache() {
  try {
    var raw = sessionStorage.getItem(DATA_KEY);
    if (!raw) return false;
    var cached = JSON.parse(raw);
    if (Date.now() - cached.timestamp > 30 * 60 * 1000) {
      sessionStorage.removeItem(DATA_KEY);
      return false;
    }
    if (cached.items && cached.items.length > 0) {
      allItems = cached.items;
      sources = cached.sources || [];
      return true;
    }
  } catch(e) {}
  return false;
}

/* Save state before navigating away (clicking a link) */
window.addEventListener('beforeunload', saveScrollState);
/* Also save on link clicks specifically */
document.addEventListener('click', function(e) {
  var link = e.target.closest('a');
  if (link && link.href && !link.href.startsWith('javascript:')) {
    saveScrollState();
  }
});

/* Handle bfcache restore (browser back-forward cache) */
window.addEventListener('pageshow', function(e) {
  if (e.persisted) {
    // Page restored from bfcache - scroll position is usually preserved,
    // but we still restore state if needed
    var savedState = null;
    try {
      var raw = sessionStorage.getItem(SCROLL_KEY);
      if (raw) savedState = JSON.parse(raw);
    } catch(ex) {}
    if (savedState && Date.now() - savedState.timestamp < 30 * 60 * 1000) {
      // bfcache usually preserves scroll, but just in case
      if (window.scrollY === 0 && savedState.scrollY > 0) {
        window.scrollTo(0, savedState.scrollY);
      }
      try { sessionStorage.removeItem(SCROLL_KEY); } catch(ex) {}
    }
  }
});

/* ================================================================
   INIT
   ================================================================ */

  // === Copy Site Link ===
  function copySiteLink() {
    var url = window.location.href.split('?')[0].split('#')[0];
    var text = '线报聚合 - 全网羊毛线报实时聚合 ' + url;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function() {
        showToast('📎 链接已复制！快去分享给朋友吧~');
      }).catch(function() {
        fallbackCopy(text);
      });
    } else {
      fallbackCopy(text);
    }
  }
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); showToast('📎 链接已复制！'); } catch(e) { showToast('复制失败，请手动复制链接'); }
    document.body.removeChild(ta);
  }

  // === Bookmark Tip ===
  function showBookmarkTip() {
    var isMac = /Mac|iPhone|iPad/.test(navigator.userAgent);
    var shortcut = isMac ? '⌘ Command + D' : 'Ctrl + D';
    showToast('⭐ 请按 ' + shortcut + ' 将「线报聚合」加入浏览器书签，方便随时查看线报！');
  }

  // === Toast ===
  var toastTimer = null;
  function showToast(msg) {
    var t = document.getElementById('bookmark-toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function() { t.classList.remove('show'); }, 4000);
  }

  // === Ctrl+D / Cmd+D Bookmark Shortcut ===
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
      e.preventDefault();
      showBookmarkTip();
    }
  }, true); // useCapture=true to intercept before browser

  // === PWA Install Banner ===
  var pwaBannerDismissed = false;
  try { pwaBannerDismissed = localStorage.getItem('pwa_banner_dismissed') === 'true'; } catch(e) {}

  function showPwaBanner() {
    if (pwaBannerDismissed || window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) return;
    var banner = document.getElementById('pwa-banner');
    if (banner) banner.classList.add('show');
  }
  function closePwaBanner() {
    var banner = document.getElementById('pwa-banner');
    if (banner) banner.classList.remove('show');
    pwaBannerDismissed = true;
    try { localStorage.setItem('pwa_banner_dismissed', 'true'); } catch(e) {}
  }

  // Show PWA banner after 5 seconds if prompt is available
  setTimeout(function() {
    if (deferredPrompt) showPwaBanner();
  }, 5000);

  // Also show banner on first beforeinstallprompt
  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    var btn = document.getElementById('install-btn');
    if (btn) btn.classList.add('visible');
    showPwaBanner();
  });

  // Hide PWA banner + install btn when installed
  window.addEventListener('appinstalled', function() {
    closePwaBanner();
    var ib = document.getElementById('install-btn');
    if (ib) { ib.classList.remove('visible'); ib.style.display = 'none'; }
    showToast('✅ 线报聚合已安装成功！');
  });

  // === Dynamic Title for SEO ===
  function updateDocumentTitle() {
    var base = '线报聚合 - 实时监控全网羊毛线报';
    var parts = [];
    if (activeSource !== 'all') parts.push(activeSource);
    if (searchQuery) parts.push('搜索: ' + searchQuery);
    if (todayOnly) parts.push('今日线报');
    if (parts.length > 0) {
      document.title = parts.join(' · ') + ' - ' + base;
    } else {
      document.title = base;
    }
  }
  setInterval(updateDocumentTitle, 2000); // lightweight periodic update

  // === Promo banner: show only on first 3 visits, then hide ===
  try {
    var visitCount = parseInt(localStorage.getItem('xb_visits') || '0') + 1;
    localStorage.setItem('xb_visits', String(visitCount));
    if (visitCount > 3) {
      var promo = document.getElementById('promo-banner');
      if (promo) promo.style.display = 'none';
    }
  } catch(e) {}

  // === Expose functions called from HTML onclick to global scope ===
  window.copySiteLink = copySiteLink;
  window.showBookmarkTip = showBookmarkTip;
  window.closePwaBanner = closePwaBanner;
  window.goToPage = goToPage;
  window.resetFilters = resetFilters;
  window.switchView = switchView;
  window.installApp = installApp;
  window.selectSource = selectSource;
  window.toggleCatDropdown = toggleCatDropdown;
  window.closeCatDropdown = closeCatDropdown;
  window.handleSearch = handleSearch;
  window.renderList = renderList;
  window.updateStatus = updateStatus;
  window.toggleTodayFilter = toggleTodayFilter;
  window.toggleSortOrder = toggleSortOrder;

} // end of loadData

  // === Initialize data loading (must be after all function definitions) ===
  loadData();

/* ================================================================
   VIRTUAL SCROLL — 只渲染可视区域内的 DOM 节点，大幅提升性能
   ================================================================ */
var _ITEM_HEIGHT = 60;   // 每条线报大约高度 (px)
var _BUFFER = 10;        // 上下缓冲区条目数
var _vScrollActive = false;

function renderListVirtual() {
  var container = document.getElementById('item-list');
  if (!container) return;
  var items = filteredItems || allItems;
  var total = items.length;

  if (total < 100) {
    // 小数据集直接渲染，不需要虚拟滚动
    renderList();
    return;
  }

  if (!_vScrollActive) {
    container.style.height = (total * _ITEM_HEIGHT) + 'px';
    container.style.position = 'relative';
    container.style.overflow = 'hidden';
    _vScrollActive = true;
  }

  var scrollTop = container.parentElement ? container.parentElement.scrollTop : 0;
  var viewHeight = window.innerHeight || 600;
  var startIdx = Math.max(0, Math.floor(scrollTop / _ITEM_HEIGHT) - _BUFFER);
  var endIdx = Math.min(total, Math.ceil((scrollTop + viewHeight) / _ITEM_HEIGHT) + _BUFFER);

  var html = '';
  for (var i = startIdx; i < endIdx; i++) {
    var it = items[i];
    var top = i * _ITEM_HEIGHT;
    var cls = 'item' + (it.platform ? ' platform-' + it.platform : '');
    var srcBadge = it.source ? '<span class="src-badge" style="background:' + (getSourceColor(it.source) || '#999') + '">' + escHtml(it.source) + '</span>' : '';
    var multiSrc = (it.sources && it.sources.length > 1) ? '<span class="src-badge multi" title="' + escHtml(it.sources.join(', ')) + '">' + it.sources.length + '源</span>' : '';
    var timeStr = it.time ? '<span class="item-time">' + escHtml(it.time.slice(5, 16)) + '</span>' : '';
    html += '<div class="' + cls + '" style="position:absolute;top:' + top + 'px;left:0;right:0;height:' + _ITEM_HEIGHT + 'px">';
    html += '<a href="' + escHtml(it.url) + '" target="_blank" rel="noopener">';
    html += srcBadge + multiSrc + escHtml(it.text);
    html += timeStr + '</a></div>';
  }
  container.innerHTML = html;
}
