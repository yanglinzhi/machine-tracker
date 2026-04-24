import click
import os
import shutil
import json
import logging
import sys
from pathlib import Path
from importlib import resources

from .constants import (
    get_default_config_path, 
    get_default_data_dir, 
    APP_NAME, 
    WEB_SERVICE_NAME, 
    SCAN_SERVICE_NAME
)
from .config import load_config, save_config
from .collector import CollectorManager
from .store import SnapshotStore
from .differ import Differ
from .reporter import Reporter
from .systemd_manager import SystemdManager
from .logger import setup_logging, get_logger
from .i18n import _T, get_cli_lang

logger = get_logger("cli")

# 预提取语言环境，用于 Click 装饰器加载
CURRENT_LOCALE = "zh"
try:
    _conf = load_config(get_default_config_path())
    CURRENT_LOCALE = get_cli_lang(_conf)
except:
    pass

def get_app_lang():
    """快捷获取当前配置语言"""
    return CURRENT_LOCALE

def ensure_root():
    """检查是否具有 root 权限，若无则报错退出"""
    if os.getuid() != 0:
        click.echo(click.style(_T("ERR_ROOT_REQUIRED", CURRENT_LOCALE), fg="red", bold=True))
        sys.exit(1)

@click.group(help=_T("CLI_DESC", CURRENT_LOCALE))
@click.option('-v', '--verbose', is_flag=True, help="Show verbose logs")
def main(verbose):
    """MachineTracker (mt) — Machine status tracking and auditing system"""
    setup_logging(verbose)


@main.command(help=_T("CLI_INIT_HELP", CURRENT_LOCALE))
@click.option('--force', is_flag=True, help="Overwrite existing config")
def init(force):
    """Initialize MachineTracker config and storage (requires sudo)"""
    ensure_root()
    config_dir = get_default_config_path().parent
    data_dir = get_default_data_dir()
    
    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    config_file = get_default_config_path()
    lang = get_app_lang()
    if config_file.exists() and not force:
        logger.info(_T("LOG_CONFIG_EXISTS", lang, path=config_file))
        return

    try:
        resource_path = resources.files('machinetracker.resources').joinpath('default_config.yaml')
        with resource_path.open('rb') as src:
            with open(config_file, "wb") as dst:
                shutil.copyfileobj(src, dst)
        logger.info(_T("LOG_CONFIG_CREATED", lang, path=config_file))
    except Exception as e:
        logger.error(f"Error loading resource: {e}")
        with open(config_file, "w") as f:
            f.write("# MachineTracker Configuration\n")

@main.command(help=_T("CLI_LANG_HELP", CURRENT_LOCALE))
@click.argument('lang_code', type=click.Choice(['zh', 'en']))
def lang(lang_code):
    """Switch system language (zh/en)"""
    ensure_root()
    config_path = get_default_config_path()
    try:
        app_config = load_config(str(config_path))
        app_config.language = lang_code
        save_config(app_config, str(config_path))
        # 使用 lang_code 作为 _lang 参数，确保反馈消息本身也是目标语言
        click.echo(_T("LANG_SWITCHED", _lang=lang_code, lang=lang_code))
    except Exception as e:
        logger.error(f"Failed to switch language: {e}")

@main.group(help=_T("CLI_CONFIG_HELP", CURRENT_LOCALE))
def config():
    """View or manage current config and data paths"""
    pass

@config.command(name="show")
def config_show():
    """View current config and data paths"""
    click.echo(f"Config: {get_default_config_path()}")
    click.echo(f"Data: {get_default_data_dir()}")

@config.command(name="edit")
def config_edit():
    """Edit config with system editor (requires sudo)"""
    ensure_root()
    config_file = get_default_config_path()
    lang = get_app_lang()
    
    # 自动探测系统编辑器
    editor = os.environ.get("EDITOR") or "vim"
    if not shutil.which(editor):
        editor = "nano" if shutil.which("nano") else "vi"
    
    import subprocess
    click.echo(_T("CLI_EDIT_OPENING", lang, editor=editor))
    subprocess.run([editor, str(config_file)])

@main.command(help=_T("CLI_SCAN_HELP", CURRENT_LOCALE))
@click.option('--machine', default='local', help="Machine name to scan")
@click.option('--output-json', is_flag=True, help="Output in JSON format")
@click.option('--force-save', is_flag=True, help="Save snapshot even if no change")
@click.option('--no-save', is_flag=True, help="Don't save snapshot")
def scan(machine, output_json, force_save, no_save):
    """Perform status collection and differential auditing (requires sudo)"""
    ensure_root()
    try:
        app_config = load_config(str(get_default_config_path()))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    lang = get_cli_lang(app_config)
    if machine not in app_config.machines:
        logger.error(f"Machine '{machine}' not defined.")
        return

    m_conf = app_config.machines[machine]
    m_id = m_conf.id
    store = SnapshotStore(app_config)
    
    if not output_json: logger.info(_T("LOG_SCAN_START", lang, machine=machine))
    
    old_snap = store.get_latest_snapshot(m_id)
    manager = CollectorManager(app_config)
    new_snap = manager.run_all(m_id)
    
    diff = Differ(app_config).compare(old_snap, new_snap)
    
    if output_json:
        click.echo(json.dumps(new_snap, indent=2, ensure_ascii=False))
    else:
        if not old_snap: logger.info(_T("REP_INITIAL_SCAN", lang))
        elif not diff: logger.info(_T("REP_STATUS_UNCHANGED", lang))
        else: click.echo(Reporter(lang).generate_summary(diff))

    if not no_save:
        if diff or not old_snap or force_save:
            path = store.save_snapshot(m_id, new_snap)
            if not output_json: logger.info(f"Snapshot saved: {path}")
        else:
            if not output_json: logger.info(_T("LOG_SCAN_NO_CHANGE", lang))

@main.command(help=_T("CLI_SHOW_HELP", CURRENT_LOCALE))
@click.option('--machine', default='local', help="Machine name")
@click.option('--collector', help="Collector name")
def show(machine, collector):
    """View the current status of the machine (latest snapshot)"""
    config_path = get_default_config_path()
    try:
        app_config = load_config(str(config_path))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    if machine not in app_config.machines:
        logger.error(f"Machine '{machine}' not defined.")
        return

    m_id = app_config.machines[machine].id
    store = SnapshotStore(app_config)
    snapshot = store.get_latest_snapshot(m_id)
    lang = get_cli_lang(app_config)
    
    if not snapshot:
        click.echo(_T("ERR_NO_SNAPSHOT", lang))
        return
        
    if collector:
        data = snapshot.get("collectors", {}).get(collector)
        if data:
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            click.echo(f"Data for collector '{collector}' not found.")
    else:
        # 显示简要摘要
        click.echo(f"Machine: {machine} (ID: {m_id})")
        click.echo(f"Hostname: {snapshot.get('hostname')}")
        click.echo(f"Timestamp: {snapshot.get('timestamp')}")
        click.echo(f"\n{_T('WEB_COLLECTOR_SUMMARY', lang)}:")
        for name, data in snapshot.get("collectors", {}).items():
            summary = "Collected"
            if name == "network": summary = f"{len(data.get('ports', []))} ports"
            elif name == "apt": summary = f"{len(data.get('packages', {}))} pkgs"
            elif name == "service_mapper": summary = f"{len(data.get('services', []))} services"
            elif name == "config_files": summary = f"{len(data.get('files', {}))} files"
            click.echo(f"  - {name}: {summary}")

@main.command(help=_T("CLI_MACHINES_HELP", CURRENT_LOCALE))
def machines():
    """View registered machines"""
    try:
        app_config = load_config(str(get_default_config_path()))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
        
    click.echo("Registered Machines:")
    for name, m in app_config.machines.items():
        click.echo(f"- {name}: {m.name} [ID: {m.id}] (local)")

@main.command(help=_T("CLI_HISTORY_HELP", CURRENT_LOCALE))
@click.option('--machine', default='local', help="Machine name")
@click.option('--limit', default=10, help="Count to show")
def history(machine, limit):
    """View scan history"""
    app_config = load_config(str(get_default_config_path()))
    if machine not in app_config.machines:
        logger.error(f"Machine '{machine}' not defined.")
        return
    m_id = app_config.machines[machine].id
    history_list = SnapshotStore(app_config).get_history(m_id, limit)
    for h in history_list:
        click.echo(f"- {h['timestamp']} ({h['filename']})")

@main.group(invoke_without_command=True, help=_T("CLI_WEB_HELP", CURRENT_LOCALE))
@click.option('--port', default=8000)
@click.option('--host', default='127.0.0.1')
@click.pass_context
def web(ctx, port, host):
    """Web monitoring dashboard (standard user privileges suffice)"""
    if ctx.invoked_subcommand is None:
        try:
            import uvicorn
            from .web.app import app
            logger.info(f"Starting Web Monitor: http://{host}:{port}")
            uvicorn.run(app, host=host, port=port, log_level="warning")
        except ImportError:
            logger.error("Please install dependencies: pip install fastapi uvicorn jinja2")

@web.command(name="install")
@click.option('-f', '--force', is_flag=True, help="Force reinstall")
def web_install(force):
    """Install Systemd service (requires sudo)"""
    ensure_root()
    import getpass
    user = os.environ.get("SUDO_USER", getpass.getuser())
    SystemdManager(user).install_web_service(force=force)
    lang = get_app_lang()
    logger.info(_T("LOG_WEB_REGISTERED", lang))

@web.command()
def uninstall():
    """Uninstall Web service (requires sudo)"""
    ensure_root()
    SystemdManager("").uninstall_web_service()
    lang = get_app_lang()
    logger.info(_T("LOG_WEB_UNINSTALLED", lang))

@web.command()
def start():
    """Start Web service (requires sudo)"""
    ensure_root()
    SystemdManager("").manage_service("start", WEB_SERVICE_NAME)
    lang = get_app_lang()
    logger.info(_T("LOG_WEB_STARTED", lang))

@web.command()
def stop():
    """Stop Web service (requires sudo)"""
    ensure_root()
    SystemdManager("").manage_service("stop", WEB_SERVICE_NAME)
    lang = get_app_lang()
    logger.info(_T("LOG_WEB_STOPPED", lang))

@web.command()
def restart():
    """Restart Web service (requires sudo)"""
    ensure_root()
    SystemdManager("").manage_service("restart", WEB_SERVICE_NAME)
    lang = get_app_lang()
    logger.info(_T("LOG_WEB_RESTARTED", lang))

@web.command()
def status():
    """Check Web service status"""
    import subprocess
    subprocess.run(["systemctl", "status", WEB_SERVICE_NAME])

@main.group(help=_T("CLI_LOG_HELP", CURRENT_LOCALE))
def log():
    """View system logs (usually requires sudo)"""
    ensure_root()
    pass

@log.command(name="web")
@click.option('-f', '--follow', is_flag=True)
@click.option('-n', '--lines', default=50)
def log_web(follow, lines):
    """Web service logs"""
    cmd = ["journalctl", "-u", WEB_SERVICE_NAME, f"-n{lines}"]
    if follow: cmd.append("-f")
    import subprocess
    subprocess.run(cmd)

@log.command(name="scan")
@click.option('-f', '--follow', is_flag=True)
@click.option('-n', '--lines', default=50)
def log_scan(follow, lines):
    """Scan timer logs"""
    cmd = ["journalctl", "-u", SCAN_SERVICE_NAME, f"-n{lines}"]
    if follow: cmd.append("-f")
    import subprocess
    subprocess.run(cmd)

@main.group(help=_T("CLI_CRON_HELP", CURRENT_LOCALE))
def cron():
    """Automated periodic scan management (requires sudo)"""
    ensure_root()
    pass

@cron.command(name="install")
@click.option('--interval', default="10m")
@click.option('-f', '--force', is_flag=True, help="Force reinstall")
def cron_install(interval, force):
    """Install timer"""
    import getpass
    user = os.environ.get("SUDO_USER", getpass.getuser())
    SystemdManager(user).install_scan_timer(interval, force=force)
    lang = get_app_lang()
    logger.info(_T("LOG_CRON_INSTALLED", lang, interval=interval))

@cron.command()
def uninstall():
    """Uninstall periodic scan (requires sudo)"""
    ensure_root()
    SystemdManager("").uninstall_scan_timer()
    lang = get_app_lang()
    logger.info(_T("LOG_CRON_UNINSTALLED", lang))

@cron.command()
def start():
    """Start periodic scan"""
    SystemdManager("").manage_service("start", f"{SCAN_SERVICE_NAME}.timer")
    lang = get_app_lang()
    logger.info(_T("LOG_CRON_STARTED", lang))

@cron.command()
def stop():
    """Stop periodic scan"""
    SystemdManager("").manage_service("stop", f"{SCAN_SERVICE_NAME}.timer")
    lang = get_app_lang()
    logger.info(_T("LOG_CRON_STOPPED", lang))

@cron.command()
def restart():
    """Restart periodic scan"""
    SystemdManager("").manage_service("restart", f"{SCAN_SERVICE_NAME}.timer")
    lang = get_app_lang()
    logger.info(_T("LOG_CRON_RESTARTED", lang))

@cron.command()
def status():
    """Check periodic scan status"""
    import subprocess
    subprocess.run(["systemctl", "status", f"{SCAN_SERVICE_NAME}.timer"])

if __name__ == "__main__":
    main()
