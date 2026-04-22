import subprocess
import re
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class NetworkCollector(BaseCollector):
    name = "network"
    """网络端口采集器"""

    def is_available(self) -> bool:
        try:
            subprocess.run(["ss", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        """
        采集正在监听的 TCP 端口
        命令: ss -tlnp
        """
        try:
            # -t: tcp, -l: listening, -n: numeric, -p: process
            result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, check=True)
            return self._parse_ss_output(result.stdout)
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "ports": []}

    def _parse_ss_output(self, output: str) -> Dict[str, Any]:
        ports = []
        lines = output.strip().split('\n')
        if not lines:
            return {"ports": []}

        # 跳过表头
        for line in lines[1:]:
            parts = re.split(r'\s+', line.strip())
            if len(parts) < 6:
                continue
            
            # Local Address:Port
            local_addr_port = parts[3]
            if ':' not in local_addr_port:
                continue
                
            port_str = local_addr_port.split(':')[-1]
            try:
                port = int(port_str)
            except ValueError:
                continue

            # Process info: users:(("node",pid=45231,fd=11))
            pid = None
            process_name = None
            
            # 搜索包含 "users:(" 的部分，而不是固定索引
            process_info = None
            for p in parts[4:]:
                if "users:(" in p:
                    process_info = p
                    break
            
            if process_info:
                # 提取第一个匹配的 pid
                pid_match = re.search(r'pid=(\d+)', process_info)
                if pid_match:
                    pid = int(pid_match.group(1))
                
                # 提取进程名 (双引号内的内容)
                name_match = re.search(r'"([^"]+)"', process_info)
                if name_match:
                    process_name = name_match.group(1)

            ports.append({
                "port": port,
                "address": local_addr_port,
                "pid": pid,
                "process": process_name
            })

        # 按端口排序
        ports.sort(key=lambda x: x['port'])
        
        return {
            "ports": ports,
            "hash": self.get_hash({"ports": ports})
        }

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_ports = {p['port']: p for p in old_data.get('ports', [])} if old_data else {}
        new_ports = {p['port']: p for p in new_data.get('ports', [])}

        for port, data in new_ports.items():
            if port not in old_ports:
                changes.append({"type": "added", "item": f"Port {port}", "new": data})
            elif old_ports[port] != data:
                changes.append({"type": "changed", "item": f"Port {port}", "old": old_ports[port], "new": data})

        for port, data in old_ports.items():
            if port not in new_ports:
                changes.append({"type": "removed", "item": f"Port {port}", "old": data})

        return changes
