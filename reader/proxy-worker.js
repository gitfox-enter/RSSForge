// Cloudflare Worker —— FeedForge 跨域代理
// 部署步骤（约 1 分钟，免费）：
//   1. 打开 https://workers.cloudflare.com ，登录后「Create Application」→「Create Worker」
//   2. 把默认代码全部删掉，粘贴本文件内容，点「Deploy」
//   3. 部署后得到地址，形如 https://feedforge-proxy.<你的子域>.workers.dev
//   4. 打开 FeedForge → 设置 → 网络 → 自定义代理，填入：
//      https://feedforge-proxy.<你的子域>.workers.dev/?url=
//   之后订阅任何 RSS 都走你自己的代理，稳定且私密。
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = url.searchParams.get('url');
    if (!target) return new Response('missing url param', { status: 400 });

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const resp = await fetch(target, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; FeedForge/1.0)',
          'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'
        },
        signal: controller.signal
      });
      clearTimeout(timer);
      const body = await resp.text();
      return new Response(body, {
        status: resp.status,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': resp.headers.get('Content-Type') || 'application/xml; charset=utf-8'
        }
      });
    } catch (e) {
      clearTimeout(timer);
      return new Response('fetch error: ' + e.message, { status: 502 });
    }
  }
}
