import subprocess
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class CronCollector(BaseCollector):
    name = "cron"
    """定时任务采集器"""

    def is_available(self) -> bool:
        try:
            subprocess.run(["crontab", "-l"], capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        """
        采集定时任务
        1. 用户 crontab
        2. /etc/cron.d/
        """
        jobs = {}
        
        # 用户 crontab
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                jobs["user"] = result.stdout.strip()
            else:
                jobs["user"] = ""
        except Exception:
            jobs["user"] = ""
            
        # /etc/cron.d/
        cron_d_path = Path("/etc/cron.d")
        if cron_d_path.exists() and cron_d_path.is_dir():
            for f in cron_d_path.glob("*"):
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        jobs[f"etc_{f.name}"] = file.read().strip()
                except Exception:
                    continue

        return {
            "jobs": jobs,
            "hash": self.get_hash({"jobs": jobs})
        }

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_jobs = old_data.get('jobs', {}) if old_data else {}
        new_jobs = new_data.get('jobs', {})

        for source, content in new_jobs.items():
            if source not in old_jobs:
                changes.append({"type": "added", "item": f"Cron Job {source}", "new": content})
            elif old_jobs[source] != content:
                changes.append({"type": "changed", "item": f"Cron Job {source}", "old": old_jobs[source], "new": content})

        for source, content in old_jobs.items():
            if source not in new_jobs:
                changes.append({"type": "removed", "item": f"Cron Job {source}", "old": content})

        return changes
