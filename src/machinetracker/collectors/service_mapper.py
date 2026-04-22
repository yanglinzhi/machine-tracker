import os
from typing import Any, Dict, List, Optional
from .base import BaseCollector
from .network import NetworkCollector
from .docker import DockerCollector
from .systemd import SystemdCollector

class ServiceMapperCollector(BaseCollector):
    name = "service_mapper"
    """服务溯源采集器"""

    def __init__(self):
        self.network_collector = NetworkCollector()
        self.docker_collector = DockerCollector()
        self.systemd_collector = SystemdCollector()

    def is_available(self) -> bool:
        return self.network_collector.is_available()

    def collect(self) -> Dict[str, Any]:
        """
        进行服务溯源
        1. 扫描端口
        2. 对每个端口关联 PID
        3. 判断 PID 是 Docker, Systemd 还是普通进程
        4. 组装 ServiceProfile
        """
        # 1. 采集网络数据
        network_data = self.network_collector.collect()
        ports = network_data.get("ports", [])

        # 2. 采集 Docker 和 Systemd 数据用于关联
        docker_data = self.docker_collector.collect() if self.docker_collector.is_available() else {"containers": []}
        systemd_data = self.systemd_collector.collect() if self.systemd_collector.is_available() else {"services": []}

        services = []
        for port_info in ports:
            port = port_info['port']
            pid = port_info['pid']
            process = port_info['process']
            
            profile = {
                "port": port,
                "process": process,
                "pid": pid,
                "deployment": {"type": "unknown"}
            }

            if pid:
                # 3. 溯源
                # 检查是否为 docker-proxy (宿主机代理)
                if process == "docker-proxy":
                    container = self._find_container_by_host_port(port, docker_data)
                    if container:
                        profile["deployment"] = {
                            "type": "docker",
                            "container_name": container.get("name"),
                            "image": container.get("image"),
                            "container_id": container.get("id")[:12],
                            "is_proxy": True
                        }
                    else:
                        profile["deployment"] = {"type": "docker-proxy", "status": "orphan"}
                
                # 检查 PID 是否直接在容器内 (容器内进程)
                elif self._is_docker_pid(pid):
                    profile["deployment"] = self._trace_docker(pid, docker_data)
                
                else:
                    systemd_service = self._trace_systemd(pid, systemd_data)
                    if systemd_service:
                        profile["deployment"] = {
                            "type": "systemd",
                            "unit": systemd_service.get("Id"),
                            "exec": systemd_service.get("exec_path"),
                            "working_dir": systemd_service.get("WorkingDirectory")
                        }
                    else:
                        profile["deployment"] = self._trace_process(pid)

            services.append(profile)

        return {
            "services": services,
            "hash": self.get_hash({"services": services})
        }

    def _find_container_by_host_port(self, host_port: int, docker_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过宿主机端口寻找对应的容器"""
        for container in docker_data.get("containers", []):
            # ports 格式通常为: {"53/tcp": [{"HostIp": "0.0.0.0", "HostPort": "53"}]}
            port_bindings = container.get("ports") or {}
            for container_port, bindings in port_bindings.items():
                if bindings:
                    for binding in bindings:
                        if binding.get("HostPort") == str(host_port):
                            return container
        return None

    def _is_docker_pid(self, pid: int) -> bool:
        """检查 PID 是否在 Docker 容器中"""
        try:
            cgroup_path = f"/proc/{pid}/cgroup"
            if os.path.exists(cgroup_path):
                with open(cgroup_path, "r") as f:
                    content = f.read()
                    return "docker" in content or "kubepods" in content
            return False
        except Exception:
            return False

    def _trace_docker(self, pid: int, docker_data: Dict[str, Any]) -> Dict[str, Any]:
        """寻找对应的 Docker 容器信息"""
        # 注意：PID 关联 Docker 容器比较复杂，因为主机 PID 和容器内 PID 不同。
        # 简单方案是遍历 docker inspect 中的 State.Pid
        # 但 docker_collector 已经拿到了大部分信息。
        # 理想情况是 docker_collector 包含 State.Pid
        
        # 这里的 docker_collector 简化了输出，我们可能需要更新 docker_collector 以包含 PID。
        # 先占位。
        return {"type": "docker", "status": "tracing_not_fully_implemented"}

    def _trace_systemd(self, pid: int, systemd_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """寻找对应的 systemd 服务"""
        services = systemd_data.get("services", [])
        for s in services:
            if s.get("MainPID") == str(pid):
                return s
        return None

    def _trace_process(self, pid: int) -> Dict[str, Any]:
        """追踪普通进程信息"""
        try:
            proc_path = f"/proc/{pid}"
            if not os.path.exists(proc_path):
                return {"type": "process", "status": "terminated"}
            
            cwd = os.readlink(f"{proc_path}/cwd") if os.path.exists(f"{proc_path}/cwd") else None
            with open(f"{proc_path}/cmdline", "rb") as f:
                cmdline = f.read().replace(b'\0', b' ').decode('utf-8').strip()
            
            return {
                "type": "process",
                "cwd": cwd,
                "cmdline": cmdline
            }
        except Exception as e:
            return {"type": "process", "error": str(e)}

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_services = {s['port']: s for s in old_data.get('services', [])} if old_data else {}
        new_services = {s['port']: s for s in new_data.get('services', [])}

        for port, data in new_services.items():
            if port not in old_services:
                changes.append({"type": "added", "item": f"Service on port {port}", "new": data})
            elif old_services[port] != data:
                changes.append({"type": "changed", "item": f"Service on port {port}", "old": old_services[port], "new": data})

        for port, data in old_services.items():
            if port not in new_services:
                changes.append({"type": "removed", "item": f"Service on port {port}", "old": data})

        return changes
