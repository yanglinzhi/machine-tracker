import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class MachineConfig(BaseModel):
    id: str
    name: str
    scan_interval: str = "30m"

class RiskRule(BaseModel):
    pattern: str          # 匹配的关键字（正则表达式）
    level: str = "MEDIUM" # HIGH, MEDIUM, LOW
    reason: str = ""      # 风险原因

class StorageConfig(BaseModel):
    path: str = "~/.local/share/machine-tracker"
    keep_snapshots: int = 30
    compress_old: bool = True

class CollectorsConfig(BaseModel):
    enabled: List[str]
    config_files: Dict[str, List[str]] = Field(default_factory=dict)

class OutputConfig(BaseModel):
    format: str = "markdown"
    changelog_path: str = "~/.local/share/machine-tracker/changelog.md"

from .i18n import get_system_lang

class AppConfig(BaseModel):
    machines: Dict[str, MachineConfig]
    storage: StorageConfig
    collectors: CollectorsConfig
    output: OutputConfig
    risk_rules: List[RiskRule] = Field(default_factory=list)
    language: str = Field(default_factory=get_system_lang)

def load_config(config_path: str) -> AppConfig:
    """加载并校验配置文件"""
    path = Path(os.path.expanduser(config_path))
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    return AppConfig(**config_data)

def save_config(config: AppConfig, config_path: str):
    """将配置保存回 YAML 文件"""
    path = Path(os.path.expanduser(config_path))
    with open(path, "w", encoding="utf-8") as f:
        # 使用 pydantic 的 model_dump 转换为字典，再用 safe_dump 写入
        yaml.safe_dump(config.model_dump(), f, allow_unicode=True, sort_keys=False)

def get_default_config_path() -> str:
    """获取默认配置文件路径，智能处理 sudo 环境"""
    # 1. 优先检查环境变量
    env_path = os.environ.get("MT_CONFIG")
    if env_path:
        return env_path

    # 2. 如果是 sudo 运行，尝试寻找原用户的配置
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user and sudo_user != "root":
        # 尝试构建原用户的配置路径
        user_config = Path(f"/home/{sudo_user}") / ".config" / "machine-tracker" / "config.yaml"
        if user_config.exists():
            return str(user_config)
    
    # 3. 默认当前用户路径
    return str(Path.home() / ".config" / "machine-tracker" / "config.yaml")
