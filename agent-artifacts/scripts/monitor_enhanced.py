#!/usr/bin/env python3
"""
RSSForge Enhanced Monitor with Link Checking
Run: Every 6 hours (aligned with Actions + 5 min)
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class RSSForgeMonitor:
    def __init__(self, pat, repo="gitfox-enter/RSSForge"):
        self.pat = pat
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.log_messages = []
        self.alerts = []

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        print(formatted)
        self.log_messages.append({"time": timestamp, "level": level, "message": message})

    def github_api(self, endpoint):
        """Call GitHub API"""
        cmd = [
            "curl", "-s", "-m", "15",
            "-H", f"Authorization: token {self.pat}",
            f"{self.api_base}/{endpoint}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
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

    def check_actions(self):
        """Check GitHub Actions status"""
        self.log("📊 Checking GitHub Actions...")

        data = self.github_api("actions/runs?per_page=5")
        if not data or 'workflow_runs' not in data:
            self.log("Failed to fetch Actions data", "ERROR")
            return

        runs = data['workflow_runs'][:5]
        success = sum(1 for r in runs if r.get('conclusion') == 'success')
        failed = sum(1 for r in runs if r.get('conclusion') == 'failure')

        self.log(f"Recent runs: {len(runs)}")
        self.log(f"✅ Success: {success}")
        if failed > 0:
            self.log(f"❌ Failed: {failed}", "WARN")
            self.alerts.append(f"[Actions:{failed} failed]")

    def check_feeds_meta(self):
        """Check feeds_meta.json freshness"""
        self.log("📅 Checking feeds_meta.json...")

        content = self.github_raw("feeds_meta.json")
        if not content:
            self.log("Failed to fetch feeds_meta.json", "ERROR")
            self.alerts.append("[Feeds:fetch failed]")
            return

        try:
            data = json.loads(content)
            total = len(data)
            healthy = sum(1 for v in data.values() if v.get('count', 0) > 0)
            zero_count = total - healthy

            self.log(f"Total sites: {total}")
            self.log(f"✅ Healthy: {healthy} ({healthy*100//total if total > 0 else 0}%)")
            self.log(f"❌ Zero-count: {zero_count} ({zero_count*100//total if total > 0 else 0}%)")

            if zero_count > 30:
                self.alerts.append(f"[Feeds:{zero_count} zero-count]")
        except json.JSONDecodeError:
            self.log("Failed to parse feeds_meta.json", "ERROR")
            self.alerts.append("[Feeds:parse error]")

    def check_feed_links(self):
        """Check RSS feed links accessibility"""
        self.log("🔗 Checking RSS feed links...")

        pages_url = f"https://{self.repo.split('/')[0]}.github.io/{self.repo.split('/')[1]}/feeds/"

        # Test GitHub Pages
        cmd = ["curl", "-s", "-I", "-m", "10", pages_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if "200 OK" in result.stdout:
            self.log(f"✅ GitHub Pages accessible: {pages_url}")

            # Test sample feed
            sample_url = f"{pages_url}线报酷.xml"
            cmd = ["curl", "-s", "-I", "-m", "10", sample_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if "200 OK" in result.stdout:
                self.log(f"✅ Sample feed OK: {sample_url}")
            else:
                self.log(f"❌ Sample feed failed: {sample_url}", "WARN")
                self.alerts.append("[Feed Links:sample failed]")
        else:
            self.log(f"❌ GitHub Pages not accessible", "ERROR")
            self.alerts.append("[Feed Links:pages down]")

    def check_source_sites(self):
        """Check official source sites accessibility"""
        self.log("🌐 Checking official source sites...")

        # Known sites to check
        sites_to_check = [
            ("线报酷", "https://www.xianbao.co"),
            ("汇发部", "https://www.huifabu.com"),
            ("线报ICU", "https://www.xianbao.icu"),
        ]

        accessible = 0
        failed = []

        for name, url in sites_to_check:
            cmd = ["curl", "-s", "-I", "-m", "10", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if "200" in result.stdout or "301" in result.stdout or "302" in result.stdout:
                self.log(f"✅ {name}")
                accessible += 1
            else:
                self.log(f"❌ {name}: {url}", "WARN")
                failed.append(name)

        total = len(sites_to_check)
        self.log(f"Result: {accessible}/{total} accessible")

        if failed:
            self.alerts.append(f"[Sources:{len(failed)} down]")

    def generate_summary(self):
        """Generate summary report"""
        print("\n" + "="*60)
        print("📊 RSSForge Monitor Summary")
        print("="*60)

        for msg in self.log_messages[-10:]:  # Last 10 messages
            print(f"  {msg['message']}")

        print("\n" + "="*60)

        if self.alerts:
            print(f"⚠️  Alerts: {' '.join(self.alerts)}")
            return 1
        else:
            print("✅ All systems healthy")
            return 0

    def save_log(self, log_dir):
        """Save log to file"""
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        log_file = log_path / f"monitor_{timestamp}.log"

        with open(log_file, 'w') as f:
            f.write(f"RSSForge Monitor Log - {datetime.now().isoformat()}\n")
            f.write("="*60 + "\n\n")

            for msg in self.log_messages:
                f.write(f"[{msg['level']}] {msg['message']}\n")

            f.write("\n" + "="*60 + "\n")
            if self.alerts:
                f.write(f"Alerts: {' '.join(self.alerts)}\n")
            else:
                f.write("Status: All systems healthy\n")

        self.log(f"Log saved to {log_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 monitor_enhanced.py --pat YOUR_PAT")
        sys.exit(1)

    pat = None
    log_dir = "/tmp/rssforge-logs"

    for i, arg in enumerate(sys.argv):
        if arg == "--pat" and i + 1 < len(sys.argv):
            pat = sys.argv[i + 1]
        elif arg == "--log-dir" and i + 1 < len(sys.argv):
            log_dir = sys.argv[i + 1]

    if not pat:
        print("Error: --pat is required")
        sys.exit(1)

    print("="*60)
    print("RSSForge Enhanced Monitor")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    monitor = RSSForgeMonitor(pat)

    # Run all checks
    monitor.check_actions()
    monitor.check_feeds_meta()
    monitor.check_feed_links()
    monitor.check_source_sites()

    # Generate summary
    exit_code = monitor.generate_summary()

    # Save log
    monitor.save_log(log_dir)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
