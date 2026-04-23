import datetime
import socket
import pkgutil
import importlib
import inspect
from typing import Any, Dict, List, Type

from .config import AppConfig
from .collectors.base import BaseCollector
from .logger import get_logger

logger = get_logger("collector")

class CollectorManager:
    """采集器管理器，负责动态发现并按顺序调用各个采集器"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.collectors: Dict[str, BaseCollector] = {}
        self._discover_collectors()

    def _discover_collectors(self):
        """动态发现 machinetracker.collectors 路径下的所有采集器类"""
        import machinetracker.collectors as collectors_pkg
        
        for _, module_name, is_pkg in pkgutil.iter_modules(collectors_pkg.__path__):
            if is_pkg or module_name == "base":
                continue
                
            try:
                module = importlib.import_module(f"machinetracker.collectors.{module_name}")
                for _, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseCollector) and 
                        obj is not BaseCollector and 
                        not inspect.isabstract(obj)):
                        
                        # 确保通过类本身获取实例
                        try:
                            instances = obj.create_instances(self.config)
                            for inst in instances:
                                self.collectors[inst.name] = inst
                                logger.debug(f"已注册采集器实例: {inst.name}")
                        except Exception as ie:
                            logger.warning(f"实例化 {obj.__name__} 失败: {ie}")
                            
            except Exception as e:
                logger.error(f"无法加载采集器模块 {module_name}: {e}")

    # 移除之前的 _instantiate_collector 方法

    def run_all(self, machine_id: str) -> Dict[str, Any]:
        """运行所有在配置中启用的采集器"""
        enabled_names = self.config.collectors.enabled
        results = {}
        
        snapshot = {
            "machine_id": machine_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "collectors": {}
        }

        for name in enabled_names:
            if name in self.collectors:
                collector = self.collectors[name]
                if collector.is_available():
                    logger.debug(f"正在运行采集器: {name}")
                    results[name] = collector.collect()
                else:
                    logger.debug(f"跳过不可用的采集器: {name}")
            else:
                logger.warning(f"未找到已启用的采集器: {name}")

        snapshot["collectors"] = results
        return snapshot
