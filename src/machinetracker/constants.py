import os
from pathlib import Path

# 项目名称标识
APP_NAME = "machine-tracker"

# 默认目录定义
DEFAULT_CONFIG_DIR_NAME = f".config/{APP_NAME}"
DEFAULT_DATA_DIR_NAME = f".local/share/{APP_NAME}"

# 系统服务定义
WEB_SERVICE_NAME = "mt-web"
SCAN_SERVICE_NAME = "mt-scan"

# 环境变量名
ENV_CONFIG_PATH = "MT_CONFIG"

def get_home_dir():
    """智能获取家目录，处理 sudo 环境"""
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user and sudo_user != "root":
        return Path(f"/home/{sudo_user}")
    return Path.home()

def get_default_config_path():
    return get_home_dir() / DEFAULT_CONFIG_DIR_NAME / "config.yaml"

def get_default_data_dir():
    return get_home_dir() / DEFAULT_DATA_DIR_NAME
