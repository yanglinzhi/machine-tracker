# MachineTracker (mt) — 机器状态追踪系统

> **给你的服务器拍“X光片”。记录现在，追踪变化。**

MachineTracker 是一个轻量级、全维度的服务器状态记录与对比工具。它能精准捕获机器在某一时刻的所有状态（服务、端口、包、配置），并在下次扫描时告诉你“什么被改动了”。

---

## 🌟 核心能力

*   **服务全景溯源 (Service Mapper)**：不只是看端口，还能告诉你该端口对应的进程、PID 以及它是如何部署的（Docker/Systemd/普通进程）。
*   **全维度采集**：支持 APT、NPM、PIP 软件包，Systemd 服务，Docker 容器，Cron 任务，磁盘挂载及 Nginx 配置。
*   **状态差分 (Snapshot Diff)**：自动对比两次快照，直观展示 **ADDED (新增)**、**REMOVED (删除)** 和 **CHANGED (变更)**。
*   **Web 监控面板 (GUI)**：提供人类友好的网页端，图形化审计机器状态和变更历史。
*   **配置监控**：通过 SHA256 指纹追踪关键配置文件（如 `/etc/nginx/`）的微小改动。

---

## 🚀 安装

推荐使用 `pipx` 安装，这样 `mt` 命令将直接注册到您的全局系统路径：

```bash
# 在项目根目录下运行
pipx install .
```

---

## 🛠️ 常用命令

### 1. 初始化
创建默认配置和数据目录：
```bash
mt init
```

### 2. 扫描并记录
扫描当前机器并生成快照。如果有变化，会立即打印变更摘要：
```bash
mt scan
```

### 3. 查看当前状态
以人类友好的方式查看最新快照的摘要：
```bash
mt show
```
查看特定采集器的详细 JSON 数据（如端口映射）：
```bash
mt show --collector service_mapper
```

### 4. 启动 Web 监控面板
在浏览器中直观审计所有信息：
```bash
mt web
```
启动后访问：`http://127.0.0.1:8000`

### 5. 查看历史
查看快照扫描记录：
```bash
mt history
```

---

## 📂 配置文件说明

配置文件位于 `~/.config/machine-tracker/config.yaml`。

您可以自定义监控哪些文件：
```yaml
collectors:
  config_files:
    watch_paths:
      - "/etc/nginx/"
      - "/etc/fstab"
      - "~/.bashrc"
```

---

## 💡 为什么需要 MachineTracker？

在运维和开发过程中，最头疼的问题往往是：
1.  “这个端口是谁占用的？怎么跑起来的？”
2.  “我昨晚手动装了个包，现在不记得名字了。”
3.  “AI 助手帮我改了配置，但我不知道它到底改了哪几行。”

`mt` 让机器状态变得**可审计、可回溯、透明化**。无论你是手动操作还是 AI 辅助，所有的变化都难逃法网。

---

## 许可证
MIT License
