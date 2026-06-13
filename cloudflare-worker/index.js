// Cloudflare Worker: 精准定时触发器
// 解决 GitHub Actions cron 调度延迟问题（实际延迟可达数小时）
// 通过 workflow_dispatch API 精准触发工作流

const GITHUB_OWNER = 'gitfox-enter';
const GITHUB_REPO = 'site-update-monitor';
const GITHUB_API = 'https://api.github.com';

export default {
  async scheduled(event, env, ctx) {
    const now = new Date();
    const minutes = now.getUTCMinutes();

    let workflow;
    if (minutes < 15) {
      // :00 - trigger full crawl
      workflow = 'crawl.yml';
    } else if (minutes < 30) {
      // :15 - trigger fast check
      workflow = 'fast_check.yml';
    } else if (minutes < 45) {
      // :30 - trigger full crawl
      workflow = 'crawl.yml';
    } else {
      // :45 - trigger fast check
      workflow = 'fast_check.yml';
    }

    console.log(`[${now.toISOString()}] Triggering workflow: ${workflow}`);

    const result = await triggerWorkflow(env.GITHUB_TOKEN, workflow);

    if (result.ok) {
      console.log(`Successfully triggered ${workflow}`);
    } else {
      console.error(`Failed to trigger ${workflow}: ${result.status} ${result.statusText}`);
      const body = await result.text();
      console.error(body);
    }
  },

  // Optional: HTTP endpoint for manual triggering and health check
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/trigger/crawl' && request.method === 'POST') {
      const result = await triggerWorkflow(env.GITHUB_TOKEN, 'crawl.yml');
      return new Response(JSON.stringify({ workflow: 'crawl.yml', ok: result.ok, status: result.status }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (url.pathname === '/trigger/fast_check' && request.method === 'POST') {
      const result = await triggerWorkflow(env.GITHUB_TOKEN, 'fast_check.yml');
      return new Response(JSON.stringify({ workflow: 'fast_check.yml', ok: result.ok, status: result.status }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Health check
    return new Response(JSON.stringify({
      service: 'site-update-monitor-cron',
      status: 'running',
      endpoints: {
        'POST /trigger/crawl': 'Trigger full crawl',
        'POST /trigger/fast_check': 'Trigger fast check',
      },
      schedule: 'Every 15 minutes (crawl at :00/:30, fast_check at :15/:45)'
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
};

async function triggerWorkflow(token, workflowFile) {
  return fetch(
    `${GITHUB_API}/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${workflowFile}/dispatches`,
    {
      method: 'POST',
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'cloudflare-worker-cron-trigger',
      },
      body: JSON.stringify({ ref: 'main' }),
    }
  );
}
