import pkgutil
import importlib
import inspect
from typing import Any, Dict, List, Optional, Type

from .config import AppConfig
from .collectors.base import BaseCollector

class Differ:
    """快照对比引擎，支持动态发现采集器的差异对比算法"""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config
        self.collectors: Dict[str, BaseCollector] = {}
        self._discover_collectors()

    def _discover_collectors(self):
        """动态发现所有的采集器实例"""
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
                        
                        # 使用工厂方法实例化，保持与 CollectorManager 一致
                        instances = obj.create_instances(self.config)
                        for inst in instances:
                            self.collectors[inst.name] = inst
            except Exception:
                pass

    def compare(self, old_snapshot: Optional[Dict[str, Any]], new_snapshot: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """对比两份全量快照，返回差异结果"""
        diff_results = {}
        
        old_collectors = old_snapshot.get("collectors", {}) if old_snapshot else {}
        new_collectors = new_snapshot.get("collectors", {})
        
        for name, new_data in new_collectors.items():
            if name in self.collectors:
                old_data = old_collectors.get(name)
                
                # 快速 Hash 对比
                if old_data and old_data.get("hash") == new_data.get("hash"):
                    continue
                
                # 深度 Diff 对比
                collector = self.collectors[name]
                changes = collector.diff(old_data, new_data)
                
                if changes:
                    # 对每一条变更进行风险评估
                    for change in changes:
                        self._evaluate_risk(change, name)
                    diff_results[name] = changes
                
        return diff_results

    def _evaluate_risk(self, change: Dict[str, Any], collector_name: str):
        """根据配置的规则评估变更风险"""
        change["risk"] = "LOW" # 默认低风险
        change["risk_reason"] = ""

        if not self.config or not self.config.risk_rules:
            return

        import re
        # 将变更内容转为字符串以便匹配
        change_str = f"{collector_name} {change.get('item', '')} {str(change.get('new', ''))} {str(change.get('old', ''))}"
        
        for rule in self.config.risk_rules:
            try:
                if re.search(rule.pattern, change_str, re.IGNORECASE):
                    # 如果匹配到更高等级的风险，则覆盖
                    risk_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
                    current_level = risk_levels.get(change["risk"], 0)
                    new_level = risk_levels.get(rule.level.upper(), 0)
                    
                    if new_level > current_level:
                        change["risk"] = rule.level.upper()
                        change["risk_reason"] = rule.reason
            except Exception:
                continue
