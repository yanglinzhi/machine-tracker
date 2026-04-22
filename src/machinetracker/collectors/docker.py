import subprocess
import json
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class DockerCollector(BaseCollector):
    name = "docker"
    """Docker 容器采集器"""

    def is_available(self) -> bool:
        for cmd in ["/usr/bin/docker", "docker", "/usr/local/bin/docker"]:
            try:
                # 修正：docker ps 没有 --version 参数，应该是 docker --version
                res = subprocess.run([cmd, "--version"], capture_output=True, text=True)
                if res.returncode == 0:
                    self.docker_cmd = cmd
                    return True
            except Exception:
                continue
        return False


    def collect(self) -> Dict[str, Any]:
        """
        采集所有 Docker 容器的信息
        """
        if not hasattr(self, 'docker_cmd'):
            if not self.is_available():
                return {"error": "docker command not found", "containers": []}

        try:
            # 获取所有容器的列表 (使用之前确定的有效命令路径)
            result = subprocess.run(
                [self.docker_cmd, "ps", "-a", "--format", "{{json .}}"], 
                capture_output=True, text=True, check=True
            )
            containers = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    container_summary = json.loads(line)
                    # 关键修复：这里的 ID 字段在 --format {{json .}} 中是大写的 'ID' 还是小写的 'id'？
                    # 不同的 docker 版本表现不一，我们做兼容处理
                    cid = container_summary.get('ID') or container_summary.get('id')
                    if not cid: continue

                    detail = self._inspect_container(cid)
                    if detail:
                        containers.append(detail)
                    else:
                        # 降级处理
                        containers.append({
                            "id": cid,
                            "name": container_summary.get("Names"),
                            "image": container_summary.get("Image"),
                            "status": container_summary.get("Status")
                        })
                except json.JSONDecodeError:
                    continue
            
            return {
                "containers": containers,
                "hash": self.get_hash({"containers": containers})
            }
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "containers": []}

    def _inspect_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """获取容器的详细信息"""
        try:
            result = subprocess.run(
                [self.docker_cmd, "inspect", container_id],
                capture_output=True, text=True, check=True
            )
            inspect_data = json.loads(result.stdout)
            if not inspect_data:
                return None
            
            data = inspect_data[0]
            
            # 提取感兴趣的字段
            simplified = {
                "id": data.get("Id"),
                "name": data.get("Name", "").lstrip("/"),
                "image": data.get("Config", {}).get("Image"),
                "status": data.get("State", {}).get("Status"),
                "created": data.get("Created"),
                "env": [e.split('=')[0] for e in data.get("Config", {}).get("Env", [])],
                # 关键修复：NetworkSettings 结构解析
                "ports": data.get("NetworkSettings", {}).get("Ports") or data.get("HostConfig", {}).get("PortBindings"),
                "mounts": [
                    {
                        "source": m.get("Source"),
                        "destination": m.get("Destination"),
                        "mode": m.get("Mode")
                    } for m in data.get("Mounts", [])
                ],
                "labels": data.get("Config", {}).get("Labels", {}),
                "networks": data.get("NetworkSettings", {}).get("Networks", {})
            }
            
            # 特殊处理：有些版本端口在 NetworkSettings.Ports 下
            if not simplified["ports"]:
                simplified["ports"] = data.get("NetworkSettings", {}).get("Ports")

            if "com.docker.compose.project" in simplified["labels"]:
                simplified["deployment"] = "docker-compose"
                simplified["compose_project"] = simplified["labels"].get("com.docker.compose.project")
                simplified["compose_service"] = simplified["labels"].get("com.docker.compose.service")
                simplified["compose_working_dir"] = simplified["labels"].get("com.docker.compose.project.working_dir")
            
            return simplified
        except Exception:
            return None

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_containers = {c['id']: c for c in old_data.get('containers', [])} if old_data else {}
        new_containers = {c['id']: c for c in new_data.get('containers', [])}

        for cid, data in new_containers.items():
            if cid not in old_containers:
                changes.append({"type": "added", "item": f"Container {data['name']}", "new": data})
            elif old_containers[cid] != data:
                changes.append({"type": "changed", "item": f"Container {data['name']}", "old": old_containers[cid], "new": data})

        for cid, data in old_containers.items():
            if cid not in new_containers:
                changes.append({"type": "removed", "item": f"Container {data['name']}", "old": data})

        return changes
