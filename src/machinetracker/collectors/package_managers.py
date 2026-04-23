import subprocess
import json
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class PackageManagersCollector(BaseCollector):
    name = "package_manager"
    """NPM 和 PIP 软件包采集器"""

    @classmethod
    def create_instances(cls, config: Any) -> List[BaseCollector]:
        return [cls(mode="npm"), cls(mode="pip")]

    def __init__(self, mode: str):
        self.mode = mode # 'npm' or 'pip'
        self.name = mode # 覆盖类属性，确保实例有独立的名字

    def is_available(self) -> bool:
        if self.mode == 'npm':
            return self._has_npm()
        if self.mode == 'pip':
            return self._has_pip()
        return False

    def _has_npm(self) -> bool:
        try:
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _has_pip(self) -> bool:
        try:
            subprocess.run(["pip", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        results = {}
        
        if self.mode == 'npm' and self._has_npm():
            results["npm_global"] = self._collect_npm_global()
        
        if self.mode == 'pip' and self._has_pip():
            results["pip"] = self._collect_pip()
            
        return {
            "packages": results,
            "hash": self.get_hash({"packages": results})
        }

    def _collect_npm_global(self) -> Dict[str, str]:
        """采集全局安装的 npm 包"""
        try:
            result = subprocess.run(
                ["npm", "ls", "-g", "--depth=0", "--json"],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            dependencies = data.get("dependencies", {})
            return {name: info.get("version") for name, info in dependencies.items()}
        except Exception:
            return {}

    def _collect_pip(self) -> Dict[str, str]:
        """采集已安装的 pip 包"""
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            return {item["name"]: item["version"] for item in data}
        except Exception:
            return {}

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_pkgs = old_data.get('packages', {}) if old_data else {}
        new_pkgs = new_data.get('packages', {})

        managers = []
        if self.mode == 'npm': managers = ["npm_global"]
        if self.mode == 'pip': managers = ["pip"]

        for manager in managers:
            old_m = old_pkgs.get(manager, {})
            new_m = new_pkgs.get(manager, {})
            
            for pkg, version in new_m.items():
                if pkg not in old_m:
                    changes.append({"type": "added", "item": f"[{manager}] {pkg}", "new": version})
                elif old_m[pkg] != version:
                    changes.append({"type": "changed", "item": f"[{manager}] {pkg}", "old": old_m[pkg], "new": version})

            for pkg, version in old_m.items():
                if pkg not in new_m:
                    changes.append({"type": "removed", "item": f"[{manager}] {pkg}", "old": version})

        return changes
