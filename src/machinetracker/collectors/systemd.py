import subprocess
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class SystemdCollector(BaseCollector):
    name = "systemd"
    """Systemd 服务采集器"""

    def is_available(self) -> bool:
        try:
            subprocess.run(["systemctl", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        """
        采集所有 systemd 服务的信息
        命令: systemctl list-units --type=service --all --no-pager --output=json
        或者解析 systemctl list-unit-files
        """
        try:
            # 获取所有服务的运行状态
            # 注意: --output=json 需要较新版本的 systemd，
            # 为了兼容性，我们可以解析 --no-legend 的输出
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--all", "--no-legend", "--no-pager"],
                capture_output=True, text=True, check=True
            )
            
            services = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                
                unit = parts[0]
                load = parts[1]
                active = parts[2]
                sub = parts[3]
                description = " ".join(parts[4:]) if len(parts) > 4 else ""
                
                # 进一步获取每个服务的详细信息
                detail = self._show_service(unit)
                if detail:
                    services.append(detail)
                else:
                    services.append({
                        "unit": unit,
                        "load": load,
                        "active": active,
                        "sub": sub,
                        "description": description
                    })

            return {
                "services": services,
                "hash": self.get_hash({"services": services})
            }
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "services": []}

    def _show_service(self, unit: str) -> Optional[Dict[str, Any]]:
        """使用 systemctl show 获取服务的详细信息"""
        try:
            # 获取感兴趣的属性
            properties = [
                "Id", "LoadState", "ActiveState", "SubState", "UnitFileState",
                "Description", "ExecStart", "WorkingDirectory", "MainPID", "Environment"
            ]
            result = subprocess.run(
                ["systemctl", "show", unit, "--property=" + ",".join(properties)],
                capture_output=True, text=True, check=True
            )
            
            data = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key] = value
            
            # 简化 ExecStart
            if "ExecStart" in data:
                # 格式通常是 { path=/usr/sbin/nginx ; argv[]=/usr/sbin/nginx -g daemon on; master_pid=0 ; exit_status=0 }
                # 这里简单处理
                exec_start = data["ExecStart"]
                if "path=" in exec_start:
                    path_match = exec_start.split("path=")[1].split(" ;")[0]
                    data["exec_path"] = path_match
            
            # 处理环境变量 (只记录 Key)
            if "Environment" in data:
                envs = data["Environment"].split()
                data["env_keys"] = [e.split('=')[0] for e in envs]
                del data["Environment"]

            return data
        except subprocess.CalledProcessError:
            return None

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_services = {s['Id']: s for s in old_data.get('services', []) if 'Id' in s} if old_data else {}
        new_services = {s['Id']: s for s in new_data.get('services', []) if 'Id' in s}

        for sid, data in new_services.items():
            if sid not in old_services:
                changes.append({"type": "added", "item": f"Service {sid}", "new": data})
            elif old_services[sid] != data:
                changes.append({"type": "changed", "item": f"Service {sid}", "old": old_services[sid], "new": data})

        for sid, data in old_services.items():
            if sid not in new_services:
                changes.append({"type": "removed", "item": f"Service {sid}", "old": data})

        return changes
