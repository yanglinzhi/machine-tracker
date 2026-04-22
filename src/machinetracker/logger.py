import logging
import sys

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    
    # 简单的格式，适合 CLI 和 Systemd
    formatter = logging.Formatter(
        '[%(levelname)s] %(message)s' if not verbose else 
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("machinetracker")
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    # 禁用第三方库的冗余日志
    logging.getLogger("uvicorn").setLevel(logging.WARNING)

def get_logger(name: str):
    return logging.getLogger(f"machinetracker.{name}")
