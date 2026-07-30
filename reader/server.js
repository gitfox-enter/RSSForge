const http = require('http');
const fs = require('fs');
const path = require('path');
const url_mod = require('url');

const PORT = 8080;
const HOST = '0.0.0.0';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

function serveStatic(req, res, filePath) {
  if (!fs.existsSync(filePath)) { res.writeHead(404); return res.end('Not Found'); }
  const ext = path.extname(filePath);
  res.writeHead(200, {
    'Content-Type': MIME[ext] || 'application/octet-stream',
    'Cache-Control': 'no-cache'
  });
  fs.createReadStream(filePath).pipe(res);
}

// CORS Proxy handler
async function handleProxy(req, res) {
  const parsedUrl = url_mod.parse(req.url, true);
  let targetUrl = parsedUrl.query.url;
  if (!targetUrl) {
    res.writeHead(400);
    return res.end(JSON.stringify({ error: 'Missing ?url= parameter' }));
  }

  // Support encoded URLs
  try { targetUrl = decodeURIComponent(targetUrl); } catch(e) {}

  const headers = {
    'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
    'User-Agent': 'FeedForge/1.0 (RSS Reader)',
  };

  try {
    const targetParsed = new URL(targetUrl);
    const proxyRes = await new Promise((resolve, reject) => {
      const preq = https.request(targetUrl, {
        method: 'GET',
        headers: headers,
        timeout: 15000
      }, resolve);
      preq.on('error', reject);
      preq.on('timeout', () => { preq.destroy(); reject(new Error('timeout')); });
      preq.end();
    });

    const chunks = [];
    for await (const chunk of proxyRes) chunks.push(chunk);
    const body = Buffer.concat(chunks);

    res.writeHead(proxyRes.statusCode, {
      'Content-Type': proxyRes.headers['content-type'] || 'application/xml',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-cache',
    });
    res.end(body);
  } catch (e) {
    res.writeHead(502);
    res.end(JSON.stringify({ error: e.message }));
  }
}

const https = require('https');

const server = http.createServer((req, res) => {
  // CORS proxy endpoint
  if (req.url.startsWith('/proxy?') || req.url.startsWith('/proxy/')) {
    // Handle OPTIONS preflight
    if (req.method === 'OPTIONS') {
      res.writeHead(200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Max-Age': '86400',
      });
      return res.end();
    }
    return handleProxy(req, res);
  }

  // Static file serving
  let reqPath = req.url.split('?')[0];
  let filePath = path.join('.', reqPath === '/' ? 'index.html' : reqPath);
  serveStatic(req, res, filePath);
});

server.listen(PORT, HOST, () => {
  console.log(`FeedForge server running at http://${HOST}:${PORT}`);
  console.log(`CORS proxy available at http://${HOST}:${PORT}/proxy?url=<encoded_url>`);
});
