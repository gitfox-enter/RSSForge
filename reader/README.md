# FeedForge

A minimalist, Material Design 3 RSS reader with PWA support. Clean interface, powerful features, zero backend required.

![FeedForge](https://img.shields.io/badge/RSS-Reader-f5593d?style=for-the-badge)
![PWA](https://img.shields.io/badge/PWA-Ready-4285f4?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 🌟 Features

### 📖 Reading Experience
- **Clean, distraction-free interface** — Focus on content, not UI clutter
- **Three beautiful themes** — Light, Dark, and Sepia (not just color inversion!)
- **Adjustable interface quality** — Comfortable, Compact, or Dense layouts
- **Article view modes** — Card list, compact list, or full article view
- **Font options** — Georgia, System UI, or custom fonts for reading

### 🗂️ Organization
- **Category management** — Organize feeds into custom categories
- **Smart filtering** — Filter by category, read/unread status
- **Persistent state** — All data saved locally, survives browser refresh

### 🚀 Performance & PWA
- **Progressive Web App** — Install on any device (desktop, Android, iOS)
- **Offline support** — Basic caching via Service Worker
- **Zero backend** — Everything runs in the browser, no server required
- **Fast loading** — Single HTML file, no external dependencies

### 🔒 Privacy
- **Local storage only** — Your data stays on your device
- **No tracking** — No analytics, no telemetry
- **No account required** — Start using immediately

### 🌐 Internationalization
- **Bilingual support** — Chinese (简体中文) and English
- **Auto-detection** — Follows browser language preference

---

## 📦 Installation

### Option 1: Use Directly (Recommended)
Visit: [https://gitfox-enter.github.io/feedforge/](https://gitfox-enter.github.io/feedforge/)

### Option 2: Install as PWA
1. Open the URL above in Chrome/Edge/Safari
2. Click "Install" in the address bar (or menu → "Install App")
3. Enjoy FeedForge as a standalone app!

### Option 3: Self-Host
```bash
# Clone the repository
git clone https://github.com/gitfox-enter/feedforge.git
cd feedforge

# Option A: Simple HTTP server (Node.js)
node server.js
# Open http://localhost:8080

# Option B: Any static file server
# Just serve the folder with nginx, Apache, etc.
```

---

## 🚀 Quick Start

1. **Add your first feed**
   - Click the `+` button in the bottom-right corner
   - Enter an RSS/Atom feed URL (e.g., `https://example.com/feed.xml`)
   - Click "Add"

2. **Organize with categories**
   - Open the side menu (☰)
   - Click "Manage Categories"
   - Create categories and assign feeds

3. **Customize your experience**
   - Open Settings (gear icon)
   - Choose your theme (Light/Dark/Sepia)
   - Adjust interface quality
   - Set refresh frequency

---

## ⚙️ Configuration

### CORS Proxy (For Cross-Origin Feeds)

Due to browser security restrictions, some RSS feeds require a CORS proxy to load. FeedForge provides several solutions:

#### Solution 1: Public Proxy (Limited)
FeedForge includes a public proxy, but it may have rate limits. For personal use, we recommend:

#### Solution 2: Cloudflare Worker (Free, Recommended)
1. Go to [Cloudflare Workers](https://workers.cloudflare.com)
2. Create a new Worker
3. Paste the contents of `proxy-worker.js`
4. Deploy and copy your Worker URL
5. In FeedForge: Settings → Advanced → Custom Proxy
6. Enter: `https://your-worker.workers.dev/?url=`

#### Solution 3: RSSHub (No Proxy Needed)
Use [RSSHub](https://github.com/DIYgod/RSSHub) to generate CORS-enabled feeds:
- Many RSSHub instances already support CORS
- Self-host for full control
- No proxy configuration needed

---

## 🎨 Themes

FeedForge offers three carefully designed themes:

| Theme | Description | Best For |
|-------|-------------|----------|
| **Light** | Clean white with coral accents | Daytime reading |
| **Dark** | Pure black OLED-friendly | Night reading, battery saving |
| **Sepia** | Warm parchment tones | Extended reading sessions |

Each theme includes:
- Properly adjusted colors (not just inverted)
- Optimized contrast ratios
- Consistent design language

---

## 📱 PWA Features

FeedForge is a full Progressive Web App:

- **Installable** — Add to home screen on mobile devices
- **Standalone mode** — Run in its own window without browser UI
- **Offline support** — Basic caching for previously loaded content
- **Fast startup** — Cached assets load instantly

### Install on Mobile
- **Android**: Chrome menu → "Add to Home screen"
- **iOS**: Safari share → "Add to Home Screen"

### Install on Desktop
- **Chrome/Edge**: Click install icon in address bar

---

## 🛠️ Development

### Project Structure
```
feedforge/
├── index.html          # Main application (everything in one file)
├── manifest.json       # PWA manifest
├── sw.js              # Service Worker for offline support
├── server.js          # Local development server (Node.js)
├── proxy-worker.js    # Cloudflare Worker for CORS proxy
├── SPEC.md            # Product specification document
└── README.md          # This file
```

### Local Development
```bash
# Start local server
node server.js

# Or use any static server
python -m http.server 8080
# npx serve .
# php -S localhost:8080
```

### Building
No build process required! FeedForge is a single HTML file with embedded CSS and JavaScript. Just edit `index.html` and refresh.

---

## 🤝 Contributing

Contributions are welcome! Here's how to help:

1. **Report bugs** — Open an issue with steps to reproduce
2. **Suggest features** — Open an issue with your idea
3. **Submit pull requests** — Fork, make changes, submit PR

### Code Style
- Single HTML file architecture (CSS + JS embedded)
- Material Design 3 guidelines
- Semantic HTML
- Accessible components

---

## 📄 License

MIT License — Use freely for personal or commercial projects.

---

## 🙏 Acknowledgments

- **Material Design 3** — Design system by Google
- **RSS/Atom** — Open syndication formats
- **RSSHub** — RSS generator for various platforms
- **All Contributors** — Bug reports, suggestions, and improvements

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/gitfox-enter/feedforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gitfox-enter/feedforge/discussions)

---

## 🗺️ Roadmap

- [ ] OPML import/export
- [ ] Full-text search
- [ ] Read-it-later integration
- [ ] Keyboard shortcuts
- [ ] Feed discovery (auto-detect from URL)
- [ ] Sync across devices (optional, self-hosted)
- [ ] Article caching for full offline reading
- [ ] Custom CSS themes

---

**Made with ❤️ by [gitfox-enter](https://github.com/gitfox-enter)**
