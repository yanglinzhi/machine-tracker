import os
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base import BaseCollector

class ConfigFilesCollector(BaseCollector):
    name = "config_files"
    """配置文件指纹采集器"""

    def __init__(self, watch_paths: List[str]):
        self.watch_paths = watch_paths

    def is_available(self) -> bool:
        return bool(self.watch_paths)

    def collect(self) -> Dict[str, Any]:
        """
        采集指定路径下所有配置文件的 SHA256 指纹
        """
        files = {}
        for watch_path in self.watch_paths:
            path = Path(os.path.expanduser(watch_path))
            if path.is_file():
                files[str(path)] = self._hash_file(path)
            elif path.is_dir():
                for root, _, filenames in os.walk(path):
                    for filename in filenames:
                        file_path = Path(root) / filename
                        # 排除常见大文件或二进制文件 (可以以后加过滤规则)
                        if file_path.stat().st_size < 1024 * 1024: # 只处理小于 1MB 的文件
                            files[str(file_path)] = self._hash_file(file_path)
            else:
                # 忽略不存在的路径
                continue
        
        return {
            "files": files,
            "hash": self.get_hash({"files": files})
        }

    def _hash_file(self, path: Path) -> Optional[str]:
        """计算文件的 SHA256 hash"""
        try:
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None

    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes = []
        old_files = old_data.get('files', {}) if old_data else {}
        new_files = new_data.get('files', {})

        for file_path, fhash in new_files.items():
            if file_path not in old_files:
                changes.append({"type": "added", "item": f"Config File {file_path}", "new": fhash})
            elif old_files[file_path] != fhash:
                changes.append({"type": "changed", "item": f"Config File {file_path}", "old": old_files[file_path], "new": fhash})

        for file_path, fhash in old_files.items():
            if file_path not in new_files:
                changes.append({"type": "removed", "item": f"Config File {file_path}", "old": fhash})

        return changes
