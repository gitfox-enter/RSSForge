#!/usr/bin/env python3
"""
RSSForge Auto-Fix Tool

Purpose: Automatically fix feeds_meta.json and other data issues
Run: Weekly or on-demand
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class RSSForgeAutoFix:
    def __init__(self, pat, repo="gitfox-enter/RSSForge", workspace="/tmp/rssforge-autofix"):
        self.pat = pat
        self.repo = repo
        self.workspace = Path(workspace)
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.fixes_applied = []

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def github_api(self, endpoint, method="GET", data=None):
        """GitHub API call"""
        cmd = [
            "curl", "-s", "-X", method,
            "-H", f"Authorization: token {self.pat}",
            "-H", "Accept: application/vnd.github.v3+json"
        ]

        if data:
            import json as json_module
            cmd.extend(["-d", json_module.dumps(data)])

        cmd.append(f"{self.api_base}/{endpoint}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return None
        return None

    def github_raw(self, path):
        """Fetch raw file from GitHub"""
        cmd = [
            "curl", "-s", "-m", "15",
            "-H", f"Authorization: token {self.pat}",
            f"https://raw.githubusercontent.com/{self.repo}/main/{path}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return result.stdout if result.returncode == 0 else None

    def fix_feeds_meta(self):
        """Fix feeds_meta.json missing URL field"""
        self.log("Fixing feeds_meta.json...")

        # Fetch current feeds_meta.json
        content = self.github_raw("feeds_meta.json")
        if not content:
            self.log("Failed to fetch feeds_meta.json", "ERROR")
            return False

        try:
            feeds_meta = json.loads(content)
        except json.JSONDecodeError as e:
            self.log(f"JSON parse error: {e}", "ERROR")
            return False

        # Fetch sites.yaml to get URLs
        sites_yaml = self.github_raw("sites.yaml")
        if not sites_yaml:
            self.log("Failed to fetch sites.yaml", "ERROR")
            return False

        # Parse sites.yaml (simple parser)
        sites_config = {}
        current_site = None

        for line in sites_yaml.split('\n'):
            line = line.rstrip()
            if line.startswith('- site_id:'):
                current_site = line.split(':', 1)[1].strip().strip('"').strip("'")
                sites_config[current_site] = {}
            elif current_site and ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                sites_config[current_site][key] = value

        # Fix missing URLs
        fixed_count = 0
        for site_id, meta in feeds_meta.items():
            if not meta.get('url') and site_id in sites_config:
                if 'url' in sites_config[site_id]:
                    feeds_meta[site_id]['url'] = sites_config[site_id]['url']
                    fixed_count += 1
                    self.log(f"Fixed URL for {site_id}: {sites_config[site_id]['url']}")

        if fixed_count == 0:
            self.log("No fixes needed", "INFO")
            return True

        # Commit fix
        self.log(f"Fixed {fixed_count} sites, committing...")

        # Get current SHA
        file_info = self.github_api("contents/feeds_meta.json")
        if not file_info or 'sha' not in file_info:
            self.log("Failed to get feeds_meta.json SHA", "ERROR")
            return False

        # Upload fixed file
        import base64
        content_bytes = json.dumps(feeds_meta, indent=2, ensure_ascii=False).encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')

        result = self.github_api("contents/feeds_meta.json", method="PUT", data={
            "message": f"fix: auto-populate {fixed_count} missing URLs in feeds_meta.json",
            "content": content_b64,
            "sha": file_info['sha'],
            "branch": "main"
        })

        if result and 'content' in result:
            self.log(f"✅ Committed fix for {fixed_count} sites", "INFO")
            self.fixes_applied.append({
                "type": "feeds_meta_url_fix",
                "count": fixed_count,
                "commit": result['content']['sha']
            })
            return True
        else:
            self.log("Failed to commit fix", "ERROR")
            return False

    def check_feed_links(self):
        """Check if RSS feed links are accessible"""
        self.log("Checking feed link accessibility...")

        # Get feeds directory
        feeds = self.github_api("contents/feeds")
        if not feeds:
            self.log("Failed to list feeds directory", "ERROR")
            return False

        feed_files = [f['name'] for f in feeds if isinstance(feeds, list)]

        # Check GitHub Pages URL
        pages_url = f"https://{self.repo.split('/')[0]}.github.io/{self.repo.split('/')[1]}/feeds/"

        self.log(f"Found {len(feed_files)} feed files")
        self.log(f"GitHub Pages URL: {pages_url}")

        # Test a sample feed
        if feed_files:
            sample_feed = feed_files[0]
            feed_url = f"{pages_url}{sample_feed}"

            cmd = ["curl", "-s", "-I", "-m", "10", feed_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and "200 OK" in result.stdout:
                self.log(f"✅ Sample feed accessible: {feed_url}")
            else:
                self.log(f"❌ Sample feed not accessible: {feed_url}", "WARN")

        return True

    def check_official_links(self):
        """Check if official source sites are accessible"""
        self.log("Checking official source site accessibility...")

        # Get sites.yaml
        sites_yaml = self.github_raw("sites.yaml")
        if not sites_yaml:
            self.log("Failed to fetch sites.yaml", "ERROR")
            return False

        # Parse and check URLs
        sites_to_check = []
        current_site = None

        for line in sites_yaml.split('\n'):
            line = line.rstrip()
            if line.startswith('- site_id:'):
                current_site = line.split(':', 1)[1].strip().strip('"').strip("'")
            elif current_site and 'url:' in line:
                url = line.split(':', 1)[1].strip().strip('"').strip("'")
                if url.startswith('http'):
                    sites_to_check.append({'site_id': current_site, 'url': url})

        self.log(f"Checking {len(sites_to_check)} official sites...")

        # Check each site (limit to 10 for performance)
        checked = 0
        accessible = 0
        failed = []

        for site in sites_to_check[:10]:
            cmd = ["curl", "-s", "-I", "-m", "10", site['url']]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            checked += 1
            if result.returncode == 0 and ("200 OK" in result.stdout or "301" in result.stdout or "302" in result.stdout):
                accessible += 1
                self.log(f"  ✅ {site['site_id']}")
            else:
                failed.append(site['site_id'])
                self.log(f"  ❌ {site['site_id']}: {site['url']}", "WARN")

        self.log(f"Result: {accessible}/{checked} sites accessible")
        if failed:
            self.log(f"Failed sites: {', '.join(failed)}", "WARN")

        return True

    def generate_report(self):
        """Generate fix report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": self.fixes_applied,
            "summary": {
                "total_fixes": len(self.fixes_applied),
                "feeds_meta_fixed": sum(f['count'] for f in self.fixes_applied if f['type'] == 'feeds_meta_url_fix')
            }
        }

        report_path = self.workspace / "auto-fix-report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.log(f"Report saved to {report_path}")
        return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 auto_fix.py --pat YOUR_PAT")
        sys.exit(1)

    pat = None
    for i, arg in enumerate(sys.argv):
        if arg == "--pat" and i + 1 < len(sys.argv):
            pat = sys.argv[i + 1]

    if not pat:
        print("Error: --pat is required")
        sys.exit(1)

    print("="*60)
    print("RSSForge Auto-Fix Tool")
    print("="*60)

    autofix = RSSForgeAutoFix(pat)

    # Run fixes
    autofix.fix_feeds_meta()
    autofix.check_feed_links()
    autofix.check_official_links()

    # Generate report
    report = autofix.generate_report()

    print("\n" + "="*60)
    print("Auto-Fix Summary")
    print("="*60)
    print(f"Total fixes applied: {report['summary']['total_fixes']}")
    print(f"Feeds meta fixed: {report['summary']['feeds_meta_fixed']}")

    if report['summary']['total_fixes'] > 0:
        print("\n✅ Auto-fix completed successfully")
    else:
        print("\n✅ No fixes needed - all healthy")


if __name__ == "__main__":
    main()
