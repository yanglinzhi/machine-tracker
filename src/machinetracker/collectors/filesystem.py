import subprocess
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class FilesystemCollector(BaseCollector):
    name = "filesystem"
    """磁盘挂载采集器"""

    def is_available(self) -> bool:
        try:
            subprocess.run(["lsblk", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        """
        采集磁盘分区和挂载点
        命令: lsblk -J
        文件: /etc/fstab
        """
        results = {}
        
        # lsblk (JSON 格式)
        try:
            result = subprocess.run(["lsblk", "-J"], capture_output=True, text=True, check=True)
            results["lsblk"] = subprocess.json.loads(result.stdout).get("blockdevices", [])
        except Exception:
            results["lsblk"] = []
            
        # /etc/fstab
        try:
            with open("/etc/fstab", "r", encoding="utf-8") as f:
                results["fstab"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception:
            results["fstab"] = []

        return {
            "filesystem": results,
            "hash": self.get_hash({"filesystem": results})
        }

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_fs = old_data.get('filesystem', {}) if old_data else {}
        new_fs = new_data.get('filesystem', {})

        # 对比 fstab
        old_fstab = set(old_fs.get("fstab", []))
        new_fstab = set(new_fs.get("fstab", []))
        
        for line in new_fstab:
            if line not in old_fstab:
                changes.append({"type": "added", "item": "fstab entry", "new": line})
        for line in old_fstab:
            if line not in new_fstab:
                changes.append({"type": "removed", "item": "fstab entry", "old": line})

        # 对比 lsblk (这里简化了，只对比整体)
        if old_fs.get("lsblk") != new_fs.get("lsblk"):
            changes.append({"type": "changed", "item": "Disk topology (lsblk)"})

        return changes
