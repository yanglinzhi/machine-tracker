import subprocess
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class AptCollector(BaseCollector):
    name = "apt"
    """APT 软件包采集器"""

    def is_available(self) -> bool:
        try:
            subprocess.run(["dpkg-query", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        """
        采集已安装的 apt 软件包
        命令: dpkg-query -W -f='${Package} ${Version}\n'
        """
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Package} ${Version}\n"],
                capture_output=True, text=True, check=True
            )
            packages = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    packages[parts[0]] = parts[1]
            
            return {
                "packages": packages,
                "hash": self.get_hash({"packages": packages})
            }
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "packages": {}}

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_pkgs = old_data.get('packages', {}) if old_data else {}
        new_pkgs = new_data.get('packages', {})

        for pkg, version in new_pkgs.items():
            if pkg not in old_pkgs:
                changes.append({"type": "added", "item": f"Package {pkg}", "new": version})
            elif old_pkgs[pkg] != version:
                changes.append({"type": "changed", "item": f"Package {pkg}", "old": old_pkgs[pkg], "new": version})

        for pkg, version in old_pkgs.items():
            if pkg not in new_pkgs:
                changes.append({"type": "removed", "item": f"Package {pkg}", "old": version})

        return changes
