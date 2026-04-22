import click
import os
import shutil
import json
import logging
from pathlib import Path
from importlib import resources

from .constants import (
    get_default_config_path, 
    get_default_data_dir, 
    APP_NAME, 
    WEB_SERVICE_NAME, 
    SCAN_SERVICE_NAME
)
from .config import load_config
from .collector import CollectorManager
from .store import SnapshotStore
from .differ import Differ
from .reporter import Reporter
from .systemd_manager import SystemdManager
from .logger import setup_logging, get_logger

logger = get_logger("cli")

@click.group()
@click.option('-v', '--verbose', is_flag=True, help="显示详细调试日志")
def main(verbose):
    """MachineTracker (mt) — 机器状态追踪与审计系统"""
    setup_logging(verbose)

@main.command()
@click.option('--force', is_flag=True, help="是否覆盖已有的配置文件")
def init(force):
    """初始化 MachineTracker 配置与存储"""
    config_dir = get_default_config_path().parent
    data_dir = get_default_data_dir()
    
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    config_file = get_default_config_path()
    if config_file.exists() and not force:
        logger.info(f"配置文件已存在: {config_file}")
        return

    # 安全地从包内资源读取默认配置
    try:
        # Python 3.9+ 推荐方式
        resource_path = resources.files('machinetracker.resources').joinpath('default_config.yaml')
        with resource_path.open('rb') as src:
            with open(config_file, "wb") as dst:
                shutil.copyfileobj(src, dst)
        logger.info(f"已创建默认配置文件: {config_file}")
    except Exception as e:
        logger.error(f"无法加载包内资源: {e}")
        with open(config_file, "w") as f:
            f.write("# MachineTracker Configuration\n")
        logger.warning(f"已回退并创建空白配置文件: {config_file}")

@main.command()
def config():
    """查看当前配置与数据路径"""
    click.echo(f"配置文件: {get_default_config_path()}")
    click.echo(f"数据存储: {get_default_data_dir()}")

@main.command()
@click.option('--machine', default='local', help="指定要扫描的机器名")
@click.option('--output-json', is_flag=True, help="以 JSON 格式输出")
@click.option('--force-save', is_flag=True, help="即使没有变更也保存快照")
@click.option('--no-save', is_flag=True, help="不保存快照")
def scan(machine, output_json, force_save, no_save):
    """执行扫描并对比状态"""
    try:
        app_config = load_config(str(get_default_config_path()))
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return

    if machine not in app_config.machines:
        logger.error(f"机器 '{machine}' 未定义。")
        return

    m_id = app_config.machines[machine].id
    manager = CollectorManager(app_config)
    store = SnapshotStore(app_config)
    
    if not output_json: logger.info(f"开始扫描: {machine}...")
    
    old_snap = store.get_latest_snapshot(m_id)
    new_snap = manager.run_all(m_id)
    
    diff = Differ(app_config).compare(old_snap, new_snap)
    
    if output_json:
        click.echo(json.dumps(new_snap, indent=2, ensure_ascii=False))
    else:
        if not old_snap: logger.info("初始扫描完成。")
        elif not diff: logger.info("状态未改变。")
        else: click.echo(Reporter().generate_summary(diff))

    # 智能保存逻辑：有变更才存，或者强制保存
    if not no_save:
        if diff or not old_snap or force_save:
            path = store.save_snapshot(m_id, new_snap)
            if not output_json: logger.info(f"快照已保存: {path}")
        else:
            if not output_json: logger.info("检测到状态无变更，跳过保存。")

@main.command()
@click.option('--machine', default='local', help="机器名")
@click.option('--limit', default=10, help="显示数量")
def history(machine, limit):
    """查看扫描历史记录"""
    app_config = load_config(str(get_default_config_path()))
    m_id = app_config.machines[machine].id
    history_list = SnapshotStore(app_config).get_history(m_id, limit)
    for h in history_list:
        click.echo(f"- {h['timestamp']} ({h['filename']})")

@main.group(invoke_without_command=True)
@click.option('--port', default=8000)
@click.option('--host', default='127.0.0.1')
@click.pass_context
def web(ctx, port, host):
    """Web 监控面板管理"""
    if ctx.invoked_subcommand is None:
        try:
            import uvicorn
            from .web.app import app
            logger.info(f"正在启动 Web 监控面板: http://{host}:{port}")
            uvicorn.run(app, host=host, port=port, log_level="warning")
        except ImportError:
            logger.error("请安装依赖: pip install fastapi uvicorn jinja2")

@web.command()
def install():
    """安装 Systemd 服务 (需要 sudo)"""
    import getpass
    user = os.environ.get("SUDO_USER", getpass.getuser())
    SystemdManager(user).install_web_service()
    logger.info("Web 服务已成功注册为系统服务。")

@web.command()
def start():
    """启动 Web 服务"""
    SystemdManager("").manage_service("start", WEB_SERVICE_NAME)
    logger.info("Web 服务已启动指令已发出。")

@web.command()
def stop():
    """停止 Web 服务"""
    SystemdManager("").manage_service("stop", WEB_SERVICE_NAME)
    logger.info("Web 服务已停止。")

@web.command()
def restart():
    """重启 Web 服务"""
    SystemdManager("").manage_service("restart", WEB_SERVICE_NAME)
    logger.info("Web 服务已重启。")

@main.group()
def log():
    """查看系统日志"""
    pass

@log.command(name="web")
@click.option('-f', '--follow', is_flag=True)
@click.option('-n', '--lines', default=50)
def log_web(follow, lines):
    """Web 服务日志"""
    cmd = ["journalctl", "-u", WEB_SERVICE_NAME, f"-n{lines}"]
    if follow: cmd.append("-f")
    import subprocess
    subprocess.run(cmd)

@log.command(name="scan")
@click.option('-f', '--follow', is_flag=True)
@click.option('-n', '--lines', default=50)
def log_scan(follow, lines):
    """定时扫描日志"""
    cmd = ["journalctl", "-u", SCAN_SERVICE_NAME, f"-n{lines}"]
    if follow: cmd.append("-f")
    import subprocess
    subprocess.run(cmd)

@main.group()
def cron():
    """自动化定时扫描管理"""
    pass

@cron.command(name="install")
@click.option('--interval', default="10m")
def cron_install(interval):
    """安装定时器 (需要 sudo)"""
    import getpass
    user = os.environ.get("SUDO_USER", getpass.getuser())
    SystemdManager(user).install_scan_timer(interval)
    logger.info(f"定时扫描任务已安装，间隔: {interval}")

@cron.command()
def stop():
    """停用定时扫描"""
    SystemdManager("").manage_service("stop", f"{SCAN_SERVICE_NAME}.timer")
    logger.info("定时扫描任务已停止。")

if __name__ == "__main__":
    main()
