import subprocess
import re
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class NetworkCollector(BaseCollector):
    """网络端口采集器 (支持 IPv4/IPv6 识别)"""
    name = "network"

    def is_available(self) -> bool:
        try:
            subprocess.run(["ss", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def collect(self) -> Dict[str, Any]:
        """
        采集正在监听的 TCP 端口 (IPv4 & IPv6)
        """
        try:
            result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, check=True)
            return self._parse_ss_output(result.stdout)
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "ports": []}

    def _parse_ss_output(self, output: str) -> Dict[str, Any]:
        ports = []
        lines = output.strip().split('\n')
        if not lines:
            return {"ports": []}

        for line in lines[1:]:
            parts = re.split(r'\s+', line.strip())
            if len(parts) < 4:
                continue
            
            # Local Address:Port
            local_addr_port = parts[3]
            
            # 识别协议并提取端口
            protocol = "ipv4"
            if local_addr_port.startswith("["): # IPv6 格式如 [::]:22
                protocol = "ipv6"
                # 寻找最后一个冒号之后的数字
                port_str = local_addr_port.split(']')[-1].lstrip(':')
            else:
                port_str = local_addr_port.split(':')[-1]

            try:
                port = int(port_str)
            except ValueError:
                continue

            # 进程溯源逻辑 (复用之前的增强解析)
            pid = None
            process_name = None
            process_info = None
            for p in parts[4:]:
                if "users:(" in p:
                    process_info = p
                    break
            
            if process_info:
                pid_match = re.search(r'pid=(\d+)', process_info)
                if pid_match: pid = int(pid_match.group(1))
                name_match = re.search(r'"([^"]+)"', process_info)
                if name_match: process_name = name_match.group(1)

            ports.append({
                "port": port,
                "address": local_addr_port,
                "protocol": protocol, # 新增协议字段
                "pid": pid,
                "process": process_name
            })

        # 排序：先按端口，再按协议
        ports.sort(key=lambda x: (x['port'], x['protocol']))
        
        return {
            "ports": ports,
            "hash": self.get_hash({"ports": ports})
        }

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        
        # 核心改进：使用 (端口, 地址) 作为唯一 Key
        def get_key(p): return f"{p['port']}-{p['address']}"
        
        old_ports = {get_key(p): p for p in old_data.get('ports', [])} if old_data else {}
        new_ports = {get_key(p): p for p in new_data.get('ports', [])}

        for key, data in new_ports.items():
            if key not in old_ports:
                changes.append({"type": "added", "item": f"Port {data['port']} ({data['protocol']}) on {data['address']}", "new": data})
            elif old_ports[key] != data:
                changes.append({"type": "changed", "item": f"Port {data['port']} ({data['protocol']})", "old": old_ports[key], "new": data})

        for key, data in old_ports.items():
            if key not in new_ports:
                changes.append({"type": "removed", "item": f"Port {data['port']} ({data['protocol']}) on {data['address']}", "old": data})

        return changes
