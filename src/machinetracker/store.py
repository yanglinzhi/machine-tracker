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
                # 如果是普通用户，直接展开 ~
                path_str = os.path.expanduser(path_str)
        
        self.base_path = Path(path_str).absolute()
        os.makedirs(self.base_path, exist_ok=True)

    def _get_machine_dir(self, machine_id: str) -> Path:
        machine_dir = self.base_path / "machines" / machine_id
        os.makedirs(machine_dir / "snapshots", exist_ok=True)
        return machine_dir

    def save_snapshot(self, machine_id: str, snapshot: Dict[str, Any]) -> str:
        """保存快照"""
        machine_dir = self._get_machine_dir(machine_id)
        timestamp = snapshot["timestamp"].replace(":", "-")
        filename = f"{timestamp}.json"
        file_path = machine_dir / "snapshots" / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        # 更新 latest 软链接
        latest_link = machine_dir / "snapshots" / "latest.json"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(filename)
        
        # 清理旧快照
        self._cleanup_old_snapshots(machine_id)
        
        return str(file_path)

    def get_latest_snapshot(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """获取最新的快照"""
        machine_dir = self._get_machine_dir(machine_id)
        latest_link = machine_dir / "snapshots" / "latest.json"
        
        if not latest_link.exists():
            return None
            
        try:
            with open(latest_link, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _cleanup_old_snapshots(self, machine_id: str):
        """清理旧快照"""
        machine_dir = self._get_machine_dir(machine_id)
        snapshot_dir = machine_dir / "snapshots"
        
        snapshots = sorted([
            f for f in snapshot_dir.glob("*.json") 
            if f.name != "latest.json"
        ], key=os.path.getmtime)
        
        keep_count = self.config.storage.keep_snapshots
        if len(snapshots) > keep_count:
            for f in snapshots[:-keep_count]:
                f.unlink()
                
    def get_latest_two_snapshots(self, machine_id: str) -> List[Dict[str, Any]]:
        """获取最近的两个快照数据用于自动审计"""
        machine_dir = self._get_machine_dir(machine_id)
        snapshot_dir = machine_dir / "snapshots"
        
        snapshots = sorted([
            f for f in snapshot_dir.glob("*.json") 
            if f.name != "latest.json"
        ], key=os.path.getmtime, reverse=True)
        
        results = []
        for f in snapshots[:2]:
            try:
                with open(f, "r", encoding="utf-8") as json_file:
                    results.append(json.load(json_file))
            except Exception:
                continue
        return results

    def get_history(self, machine_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取快照历史记录摘要"""
        machine_dir = self._get_machine_dir(machine_id)
        snapshot_dir = machine_dir / "snapshots"
        
        snapshots = sorted([
            f for f in snapshot_dir.glob("*.json") 
            if f.name != "latest.json"
        ], key=os.path.getmtime, reverse=True)
        
        history = []
        for f in snapshots[:limit]:
            # 只读取基本信息以提高速度
            try:
                with open(f, "r") as json_file:
                    data = json.load(json_file)
                    history.append({
                        "timestamp": data.get("timestamp"),
                        "filename": f.name
                    })
            except Exception:
                continue
        return history
