from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import hashlib
import json

class BaseCollector(ABC):
    """采集器基类"""
    
    # 采集器的唯一标识名，由子类定义
    name: str = "base"

    @classmethod
    def create_instances(cls, config: Any) -> List['BaseCollector']:
        """
        工厂方法：根据配置创建采集器实例。
        默认返回一个无参实例，复杂采集器（如 package_manager）可返回多个实例。
        """
        return [cls()]

    @abstractmethod
    def is_available(self) -> bool:
        """检查此采集器是否可用（例如：是否安装了相关的命令行工具）"""
        pass

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """采集数据并返回结构化字典"""
        pass

    def get_hash(self, data: Dict[str, Any]) -> str:
        """计算数据的 hash 值，用于快速对比"""
        # 使用排序后的 JSON 字符串以确保一致性
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    @abstractmethod
    def diff(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        对比两份数据，返回差异列表。
        返回格式通常为：[{"type": "added/removed/changed", "item": "...", "old": "...", "new": "..."}]
        """
        pass
