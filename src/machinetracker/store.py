import os
import json
import gzip
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from .config import AppConfig

class SnapshotStore:
    """快照存储管理器"""

    def __init__(self, config: AppConfig):
        self.config = config
        path_str = config.storage.path
        
        # 智能处理 ~ 路径
        if path_str.startswith("~"):
            sudo_user = os.environ.get("SUDO_USER")
            if sudo_user and sudo_user != "root":
                path_str = path_str.replace("~", f"/home/{sudo_user}", 1)
            else:
                path_str = os.path.expanduser(path_str)
        
        self.base_path = Path(path_str).absolute()
        os.makedirs(self.base_path, exist_ok=True)

    def _get_machine_dir(self, machine_id: str) -> Path:
        machine_dir = self.base_path / "machines" / machine_id
        os.makedirs(machine_dir / "snapshots", exist_ok=True)
        return machine_dir

    def save_snapshot(self, machine_id: str, snapshot: Dict[str, Any]) -> str:
        """保存快照 (使用 Gzip 压缩)"""
        machine_dir = self._get_machine_dir(machine_id)
        timestamp = snapshot["timestamp"].replace(":", "-")
        # 改用 .json.gz 扩展名
        filename = f"{timestamp}.json.gz"
        file_path = machine_dir / "snapshots" / filename
        
        # 使用 gzip 写入
        json_data = json.dumps(snapshot, indent=2, ensure_ascii=False).encode('utf-8')
        with gzip.open(file_path, "wb") as f:
            f.write(json_data)
        
        # 更新 latest 软链接
        latest_link = machine_dir / "snapshots" / "latest.json.gz"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(filename)
        
        self._cleanup_old_snapshots(machine_id)
        return str(file_path)

    def _load_json_gz(self, path: Path) -> Optional[Dict[str, Any]]:
        """通用的加载 gzip json 方法"""
        if not path.exists(): return None
        try:
            with gzip.open(path, "rb") as f:
                return json.loads(f.read().decode('utf-8'))
        except Exception:
            # 兼容老版本的非压缩 JSON
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

    def get_latest_snapshot(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """获取最新的快照"""
        machine_dir = self._get_machine_dir(machine_id)
        latest_link = machine_dir / "snapshots" / "latest.json.gz"
        return self._load_json_gz(latest_link)

    def _cleanup_old_snapshots(self, machine_id: str):
        """清理旧快照"""
        machine_dir = self._get_machine_dir(machine_id)
        snapshot_dir = machine_dir / "snapshots"
        
        snapshots = sorted([
            f for f in snapshot_dir.glob("*.json.gz") 
            if f.name != "latest.json.gz"
        ], key=os.path.getmtime)
        
        keep_count = self.config.storage.keep_snapshots
        if len(snapshots) > keep_count:
            for f in snapshots[:-keep_count]:
                f.unlink()
                
    def get_latest_two_snapshots(self, machine_id: str) -> List[Dict[str, Any]]:
        """获取最近的两个快照数据"""
        machine_dir = self._get_machine_dir(machine_id)
        snapshot_dir = machine_dir / "snapshots"
        
        snapshots = sorted([
            f for f in snapshot_dir.glob("*.json.gz") 
            if f.name != "latest.json.gz"
        ], key=os.path.getmtime, reverse=True)
        
        results = []
        for f in snapshots[:2]:
            data = self._load_json_gz(f)
            if data: results.append(data)
        return results

    def get_history(self, machine_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取快照历史记录摘要"""
        machine_dir = self._get_machine_dir(machine_id)
        snapshot_dir = machine_dir / "snapshots"
        
        snapshots = sorted([
            f for f in snapshot_dir.glob("*.json.gz") 
            if f.name != "latest.json.gz"
        ], key=os.path.getmtime, reverse=True)
        
        history = []
        for f in snapshots[:limit]:
            data = self._load_json_gz(f)
            if data:
                history.append({
                    "timestamp": data.get("timestamp"),
                    "filename": f.name
                })
        return history
