import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from .constants import WEB_SERVICE_NAME, SCAN_SERVICE_NAME, get_default_config_path

class SystemdManager:
    """负责所有 Systemd 服务单元的安装与管理"""

    def __init__(self, user: str):
        self.user = user
        self.config_path = get_default_config_path()

    def _run_cmd(self, cmd: list, use_sudo: bool = True):
        full_cmd = ["sudo"] + cmd if use_sudo and os.getuid() != 0 else cmd
        return subprocess.run(full_cmd, check=True, capture_output=True, text=True)

    def install_web_service(self):
        """安装 Web GUI 服务"""
        mt_path = shutil.which("mt")
        content = f"""[Unit]
Description=MachineTracker Web GUI
After=network.target

[Service]
Type=simple
User={self.user}
ExecStart={mt_path} web --port 8000 --host 0.0.0.0
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment=MT_CONFIG={self.config_path}
Environment=SUDO_USER={self.user}

[Install]
WantedBy=multi-user.target
"""
        self._write_and_reload(WEB_SERVICE_NAME, content)

    def install_scan_timer(self, interval: str = "10m"):
        """安装定时扫描服务与定时器"""
        mt_path = shutil.which("mt")
        
        service_content = f"""[Unit]
Description=MachineTracker Periodic Scan
After=network.target

[Service]
Type=oneshot
User=root
RemainAfterExit=yes
ExecStart={mt_path} scan
Environment=MT_CONFIG={self.config_path}
Environment=SUDO_USER={self.user}
"""
        
        timer_content = f"""[Unit]
Description=Run MachineTracker scan every {interval}

[Timer]
OnBootSec=1min
OnUnitActiveSec={interval}
Unit={SCAN_SERVICE_NAME}.service

[Install]
WantedBy=timers.target
"""
        self._write_and_reload(SCAN_SERVICE_NAME, service_content, is_timer=True, timer_content=timer_content)

    def _write_and_reload(self, name: str, content: str, is_timer: bool = False, timer_content: Optional[str] = None):
        svc_path = Path(f"/etc/systemd/system/{name}.service")
        
        # 写入 Service 文件
        temp_file = Path(f"/tmp/{name}.service")
        with open(temp_file, "w") as f: f.write(content)
        self._run_cmd(["cp", str(temp_file), str(svc_path)])
        
        if is_timer and timer_content:
            timer_path = Path(f"/etc/systemd/system/{name}.timer")
            temp_timer = Path(f"/tmp/{name}.timer")
            with open(temp_timer, "w") as f: f.write(timer_content)
            self._run_cmd(["cp", str(temp_timer), str(timer_path)])
            self._run_cmd(["systemctl", "enable", "--now", f"{name}.timer"])

        self._run_cmd(["systemctl", "daemon-reload"])
        if not is_timer:
            self._run_cmd(["systemctl", "enable", name])

    def manage_service(self, action: str, name: str):
        """执行 start/stop/restart 等操作"""
        self._run_cmd(["systemctl", action, name])
