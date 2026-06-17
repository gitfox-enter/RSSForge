# Deploy to GitHub

## Deployment Steps

### 1. Fork the Repository

Visit [RSSForge GitHub](https://github.com/gitfox-enter/RSSForge) and click **Fork** in the top-right corner.

### 2. Rename the Repository (Optional)

If you'd like to give the repository a different name:
1. Go to **Settings** in your repository
2. Change **Repository name** to `RSSForge` or any name you prefer
3. Your GitHub Pages URL will update accordingly: `https://your-username.github.io/new-name/`

### 3. Configure sites.yaml

Refer to the [sites.yaml configuration guide](/en/config/sites) to add the websites you want to subscribe to.

### 4. Enable GitHub Pages

1. Go to **Settings → Pages**
2. Under **Build and deployment**, set Source to **GitHub Actions**
3. Wait for Actions to run automatically (if it doesn't trigger on its own, you can run it manually once)

### 5. Verify the Deployment

Open `https://your-username.github.io/RSSForge/` and confirm the homepage loads correctly.

## Custom Domain (Optional)

If you have your own domain, you can bind it to GitHub Pages:

1. Enter your domain in **Settings → Pages → Custom domain**
2. Add a CNAME record in your domain's DNS pointing to `your-username.github.io`
3. Wait for DNS propagation (usually a few minutes, up to 24 hours)

> Note: After setting up a custom domain, the `base` configuration needs to be adjusted accordingly. Refer to the VitePress documentation for details.

## Manually Trigger an Update

Sometimes you may want to refresh your feeds immediately. You can trigger a manual run from the GitHub Actions page:

1. Go to the **Actions** tab in your repository
2. Find the **Site update monitor** workflow
3. Click **Run workflow** → **Run workflow**

## Troubleshooting

### Getting a 404 on GitHub Pages?

Check whether all Actions have completed successfully (green checkmark). If Actions failed, Pages will show a 404.

### Configuration changes not taking effect?

Verify that your `sites.yaml` format is correct. YAML is indentation-sensitive — use spaces, not tabs.

### Crawl failures?

This is usually caused by the target website blocking crawlers. You can mark the site in `blacklist.json`, or try enabling `fast_check` mode.
