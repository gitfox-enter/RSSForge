#!/usr/bin/env python3
"""
RSSForge Feed Health Diagnostic Tool

Purpose: Diagnose why 36 out of 48 feeds have count=0

Usage:
    python3 diagnose_feeds.py --pat YOUR_PAT [--repo owner/repo]
"""

import json
import subprocess
import sys
from pathlib import Path

class FeedDiagnostic:
    def __init__(self, pat, repo="gitfox-enter/RSSForge"):
        self.pat = pat
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.results = {
            "healthy": [],
            "zero_count": [],
            "missing_url": [],
            "parse_errors": []
        }

    def github_api(self, endpoint):
        """Call GitHub API with retry"""
        cmd = [
            "curl", "-s", "-m", "10",
            "-H", f"Authorization: token {self.pat}",
            f"{self.api_base}/{endpoint}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return None
        return None

    def github_raw(self, path):
        """Fetch raw file from GitHub"""
        cmd = [
            "curl", "-s", "-m", "10",
            "-H", f"Authorization: token {self.pat}",
            f"https://raw.githubusercontent.com/{self.repo}/main/{path}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.stdout if result.returncode == 0 else None

    def check_feeds_meta(self):
        """Check feeds_meta.json structure"""
        print("1. Checking feeds_meta.json...")

        content = self.github_raw("feeds_meta.json")
        if not content:
            print("  ❌ Failed to fetch feeds_meta.json")
            return False

        try:
            data = json.loads(content)
            print(f"  ✅ Total sites: {len(data)}")

            for site_id, info in data.items():
                count = info.get('count', 0)
                url = info.get('url', '')

                if count > 0:
                    self.results['healthy'].append({
                        'site_id': site_id,
                        'count': count,
                        'url': url,
                        'title': info.get('title', site_id)
                    })
                elif not url:
                    self.results['missing_url'].append({
                        'site_id': site_id,
                        'title': info.get('title', site_id)
                    })
                else:
                    self.results['zero_count'].append({
                        'site_id': site_id,
                        'url': url,
                        'title': info.get('title', site_id)
                    })

            print(f"  ✅ Healthy: {len(self.results['healthy'])}")
            print(f"  ⚠️  Zero count with URL: {len(self.results['zero_count'])}")
            print(f"  ❌ Missing URL: {len(self.results['missing_url'])}")

            return True
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
            self.results['parse_errors'].append(str(e))
            return False

    def check_sites_yaml(self):
        """Check sites.yaml configuration"""
        print("\n2. Checking sites.yaml...")

        content = self.github_raw("sites.yaml")
        if not content:
            print("  ❌ Failed to fetch sites.yaml")
            return False

        print(f"  ✅ File size: {len(content)} bytes")

        # Parse YAML manually (simple parsing)
        current_site = None
        sites_config = {}

        for line in content.split('\n'):
            line = line.rstrip()

            # Site header (e.g., "- site_id: xxx")
            if line.startswith('- site_id:'):
                current_site = line.split(':', 1)[1].strip().strip('"').strip("'")
                sites_config[current_site] = {}
            elif current_site and ':' in line and not line.startswith('#'):
                # Site property
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                sites_config[current_site][key] = value

        print(f"  ✅ Configured sites: {len(sites_config)}")

        # Check which zero-count sites have config
        missing_config = []
        for site in self.results['missing_url']:
            if site['site_id'] not in sites_config:
                missing_config.append(site['site_id'])

        if missing_config:
            print(f"  ⚠️  Sites missing from sites.yaml: {len(missing_config)}")
            for site_id in missing_config[:10]:
                print(f"    - {site_id}")

        return True

    def check_feeds_directory(self):
        """Check feeds/ directory"""
        print("\n3. Checking feeds/ directory...")

        files = self.github_api("contents/feeds")
        if not files:
            print("  ❌ Failed to list feeds directory")
            return False

        feed_files = [f['name'] for f in files if isinstance(files, list)]
        print(f"  ✅ Feed files: {len(feed_files)}")

        # Check if zero-count sites have feed files
        missing_feeds = []
        for site in self.results['missing_url']:
            expected_file = f"{site['site_id']}.xml"
            if expected_file not in feed_files:
                missing_feeds.append(site['site_id'])

        if missing_feeds:
            print(f"  ⚠️  Sites without feed files: {len(missing_feeds)}")
            for site_id in missing_feeds[:10]:
                print(f"    - {site_id}")

        return True

    def check_crawl_status(self):
        """Check crawl_status.json"""
        print("\n4. Checking crawl_status.json...")

        content = self.github_raw("crawl_status.json")
        if not content:
            print("  ❌ Failed to fetch crawl_status.json")
            return False

        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                print(f"  ❌ Invalid crawl_status format")
                return False
                
            print(f"  ✅ Total sites in crawl_status: {len(data)}")

            # Check last_crawl times
            sites_with_crawl = [k for k, v in data.items() if v.get('last_crawl')]
            print(f"  ✅ Sites with last_crawl: {len(sites_with_crawl)}")

            # Check which zero-count sites have crawl history
            never_crawled = []
            for site in self.results['missing_url']:
                if site['site_id'] not in data or not data[site['site_id']].get('last_crawl'):
                    never_crawled.append(site['site_id'])

            if never_crawled:
                print(f"  ⚠️  Sites never crawled: {len(never_crawled)}")
                for site_id in never_crawled[:10]:
                    print(f"    - {site_id}")

            return True
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
            return False

    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "="*60)
        print("RSSForge Feed Health Diagnostic Report")
        print("="*60)

        total = len(self.results['healthy']) + len(self.results['zero_count']) + len(self.results['missing_url'])

        print(f"\n📊 Summary:")
        print(f"  Total sites:          {total}")
        print(f"  ✅ Healthy:           {len(self.results['healthy'])} ({len(self.results['healthy'])/total*100:.1f}%)")
        print(f"  ⚠️  Zero count w/ URL: {len(self.results['zero_count'])} ({len(self.results['zero_count'])/total*100:.1f}%)")
        print(f"  ❌ Missing URL:       {len(self.results['missing_url'])} ({len(self.results['missing_url'])/total*100:.1f}%)")

        print(f"\n🔍 Root Cause Analysis:")

        if self.results['missing_url']:
            print(f"  1. feeds_meta.json 缺少 URL 字段")
            print(f"     影响: {len(self.results['missing_url'])} 个站点")
            print(f"     原因: generate_feeds_meta.py 未正确提取 URL")
            print(f"     解决: 修复 feeds_meta.json 生成逻辑")

        if self.results['zero_count']:
            print(f"  2. 有 URL 但 count=0")
            print(f"     影响: {len(self.results['zero_count'])} 个站点")
            print(f"     可能原因:")
            print(f"       - 源站已关闭或变更")
            print(f"       - 解析器失效")
            print(f"       - 网络问题")

        print(f"\n💡 Recommended Actions:")

        if self.results['missing_url']:
            print(f"  P0: 修复 feeds_meta.json 生成脚本")
            print(f"      - 检查 generate_feeds_index.py")
            print(f"      - 确保 URL 字段正确填充")

        if self.results['zero_count']:
            print(f"  P1: 逐个检查零内容站点")
            print(f"      - HTTP 状态检查")
            print(f"      - 手动访问验证")
            print(f"      - 更新或删除失效源")

        print(f"\n📝 Next Steps:")
        print(f"  1. 本地克隆仓库进行深入分析")
        print(f"  2. 检查爬虫日志")
        print(f"  3. 修复 feeds_meta.json")
        print(f"  4. HTTP 检查零内容站点")
        print(f"  5. 更新文档和 Issue Tracker")

        return self.results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 diagnose_feeds.py --pat YOUR_PAT")
        sys.exit(1)

    pat = None
    for i, arg in enumerate(sys.argv):
        if arg == "--pat" and i + 1 < len(sys.argv):
            pat = sys.argv[i + 1]

    if not pat:
        print("Error: --pat is required")
        sys.exit(1)

    diagnostic = FeedDiagnostic(pat)

    # Run all checks
    diagnostic.check_feeds_meta()
    diagnostic.check_sites_yaml()
    diagnostic.check_feeds_directory()
    diagnostic.check_crawl_status()

    # Generate report
    results = diagnostic.generate_report()

    # Save results
    with open('/tmp/feed_diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to /tmp/feed_diagnostic_results.json")


if __name__ == "__main__":
    main()
