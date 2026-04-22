import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class NginxCollector(BaseCollector):
    name = "nginx"
    """Nginx 配置采集器"""

    def is_available(self) -> bool:
        return os.path.exists("/etc/nginx/nginx.conf")

    def collect(self) -> Dict[str, Any]:
        """
        解析 Nginx 配置文件，提取反向代理信息
        """
        vhosts = []
        nginx_dir = Path("/etc/nginx")
        
        # 搜索 sites-enabled 和 conf.d
        paths = [
            nginx_dir / "sites-enabled",
            nginx_dir / "conf.d"
        ]
        
        for path in paths:
            if path.exists() and path.is_dir():
                for f in path.glob("*"):
                    if f.is_file():
                        vhosts.extend(self._parse_config(f))
                        
        return {
            "vhosts": vhosts,
            "hash": self.get_hash({"vhosts": vhosts})
        }

    def _parse_config(self, path: Path) -> List[Dict[str, Any]]:
        """简单的 Nginx 配置文件解析"""
        results = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 匹配 server 块
            # 注意：这是一个非常简化的正则
            server_blocks = re.findall(r'server\s*\{([\s\S]*?)\}', content)
            
            for block in server_blocks:
                # 提取 server_name
                name_match = re.search(r'server_name\s+([^;]+);', block)
                server_name = name_match.group(1).strip() if name_match else "unknown"
                
                # 提取 location 中的 proxy_pass
                locations = []
                loc_matches = re.findall(r'location\s+([^{]+)\{([\s\S]*?)\}', block)
                for loc_path, loc_content in loc_matches:
                    proxy_match = re.search(r'proxy_pass\s+([^;]+);', loc_content)
                    if proxy_match:
                        locations.append({
                            "path": loc_path.strip(),
                            "proxy_pass": proxy_match.group(1).strip()
                        })
                
                if locations:
                    results.append({
                        "file": str(path),
                        "server_name": server_name,
                        "locations": locations
                    })
        except Exception:
            pass
            
        return results

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_vhosts = old_data.get('vhosts', []) if old_data else []
        new_vhosts = new_data.get('vhosts', [])

        # 为了对比，我们将 vhost 转为 map
        def get_key(v): return f"{v.get('server_name')}-{v.get('file')}"
        
        old_map = {get_key(v): v for v in old_vhosts}
        new_map = {get_key(v): v for v in new_vhosts}

        for key, data in new_map.items():
            if key not in old_map:
                changes.append({"type": "added", "item": f"Nginx VHost {data['server_name']}", "new": data})
            elif old_map[key] != data:
                changes.append({"type": "changed", "item": f"Nginx VHost {data['server_name']}", "old": old_map[key], "new": data})

        for key, data in old_map.items():
            if key not in new_map:
                changes.append({"type": "removed", "item": f"Nginx VHost {data['server_name']}", "old": data})

        return changes
