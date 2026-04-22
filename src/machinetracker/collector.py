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
        
        # 遍历 collectors 包下的所有模块
        for _, module_name, is_pkg in pkgutil.iter_modules(collectors_pkg.__path__):
            if is_pkg or module_name == "base":
                continue
                
            # 动态导入模块
            full_module_name = f"machinetracker.collectors.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                
                # 在模块中寻找 BaseCollector 的非抽象子类
                for _, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseCollector) and 
                        obj is not BaseCollector and 
                        not inspect.isabstract(obj)):
                        
                        # 实例化采集器
                        self._instantiate_collector(obj)
                        
            except Exception as e:
                logger.error(f"无法加载采集器模块 {module_name}: {e}")

    def _instantiate_collector(self, cls: Type[BaseCollector]):
        """根据类定义智能实例化采集器"""
        try:
            # 1. 处理需要特殊参数的采集器 (如 config_files)
            if cls.name == "config_files":
                watch_paths = self.config.collectors.config_files.get("watch_paths", [])
                instance = cls(watch_paths)
            
            # 2. 处理需要区分模式的采集器 (如 npm/pip)
            elif cls.name == "package_manager":
                # package_manager 比较特殊，我们需要它产生两个实例：npm 和 pip
                self.collectors["npm"] = cls(mode="npm")
                self.collectors["pip"] = cls(mode="pip")
                return
            
            else:
                # 3. 默认无参实例化
                instance = cls()
            
            self.collectors[instance.name] = instance
            logger.debug(f"已注册采集器: {instance.name}")
            
        except Exception as e:
            logger.warning(f"实例化采集器 {cls.__name__} 失败: {e}")

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
