# MachineTracker (mt) — Industrial-Grade Machine State Tracking & Auditing System

[简体中文](README.md) | [English](README_EN.md)

> **The System Consistency Guardian for AI Agents. Record the present, track the changes, and eliminate the "black box" of AI operations.**

MachineTracker is a full-dimensional system auditing tool designed specifically for collaboration between **Human Operators and AI Agents (e.g., Gemini, Claude, GPT)**.

## 💡 Why MachineTracker?

In an era where AI assistants frequently interact with servers, **System Consistency** has become paramount.
- **Verify AI Actions**: When an AI says "Service installed," you can use `mt scan` to verify the actual changes in the system state in real-time.
- **Eliminate Hallucinations**: Provide AI with standardized, structured snapshot data (JSON), enabling it to make decisions based on "Facts" rather than "Hallucinations."
- **Consistency Auditing**: Ensure that after multiple automated operations, the system state remains as expected and prevent configuration drift.

---

## 🌟 Core Features

*   **Service Mapping**: Go beyond just ports. It identifies the process, PID, and deployment method (Docker/Systemd/Bare process) associated with each listening port.
*   **Full-Dimensional Collection**: Supports APT, NPM, and PIP packages, Systemd units, Docker containers, Cron jobs, disk mounts, and Nginx configurations.
*   **Risk Assessment**: Automatically identifies critical configuration changes (e.g., SSH, sudoers) and flags them with risk levels (🔴 HIGH RISK).
*   **Web Dashboard (GUI)**: A human-friendly web interface featuring a **Home Message Center** and modal-based auditing.
*   **Industrial Storage**: Snapshots are compressed with **Gzip** (85% reduction) and feature a **"Skip if No Change"** logic to save space.

---

## 🚀 Installation

Install via `pipx` to ensure the `mt` command is globally available:

```bash
# Run in the project root
pipx install .
```

---

## 🛠️ Common Commands

> **Note**: Most management commands require `sudo` for full system access.

### 1. Initialize & Configure
```bash
sudo mt init          # Create the default environment
sudo mt config edit   # Edit config with system editor (Vim/Nano)
mt config show        # View current paths
```

### 2. Scan & Audit
```bash
sudo mt scan          # Perform a full scan. Skips saving if no changes detected.
```

### 3. Inspect Snapshots
```bash
mt show                       # View the latest snapshot summary
mt show --collector network   # View detailed JSON for a specific collector
```

### 4. Automation & Logs
```bash
sudo mt cron install --interval 10m  # Enable 10-minute auto-scan
sudo mt cron install -f              # Force reinstall and refresh config
mt cron start                        # Start the timer
mt cron status                       # Check status
sudo mt cron uninstall               # Uninstall the timer
mt log scan                          # View background audit logs
```

### 5. Web GUI Management
```bash
sudo mt web install   # Register as a system service
sudo mt web start     # Start the dashboard (Default: port 8000)
sudo mt web uninstall # Uninstall the service
```

---

## 📂 Configuration

Located at `~/.config/machine-tracker/config.yaml`.

You can customize watch paths or risk rules:
```yaml
config_files:
  watch_paths: ["/etc/nginx/", "/etc/sudoers"]

risk_rules:
  - pattern: "shadow|passwd"
    level: "HIGH"
    reason: "Sensitive system account change detected."
```

---

## 🤖 AI Skill Integration

MachineTracker includes a `SKILL.md` guide to help you integrate it with AI Agents, ensuring a "Snapshot -> Action -> Audit" loop for every system change.

---

## License
MIT License
