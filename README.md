# MachineTracker (mt) — 工业级机器状态追踪与审计系统

> **面向 AI Agent 的系统一致性守护者。记录现状，追踪变化，消除 AI 运维的“黑盒”。**

MachineTracker 是一个专门为**人类运维人员与 AI Agent (如 Gemini, Claude, GPT)** 协同工作设计的全维度系统审计工具。

### 为什么选择 MachineTracker？
在 AI 助手频繁操作服务器的今天，**系统一致性 (System Consistency)** 变得至关重要。
- **验证 AI 操作**：AI 告诉你“已装好服务”，你可以通过 `mt scan` 实时验证系统状态的真实变化。
- **消除幻觉**：为 AI 提供标准化的结构化快照数据（JSON），让 AI 基于“事实”而非“幻觉”进行下一步决策。
- **一致性审计**：确保多次自动化操作后，系统状态依然符合预期，防止配置漂移。

---


## 🌟 核心能力

*   **服务全景溯源 (Service Mapping)**：不只是看端口，还能告诉你该端口对应的进程、PID 以及它是如何部署的（Docker/Systemd/普通进程）。
*   **全维度采集**：支持 APT、NPM、PIP 软件包，Systemd 服务，Docker 容器，Cron 任务，磁盘挂载及 Nginx 配置。
*   **风险评估**：自动识别关键配置（如 SSH、sudoers）变更并标记风险等级（🔴 HIGH RISK）。
*   **Web 监控面板**：提供人类友好的网页端，支持**首页变更消息提醒**和弹窗审计，告别繁琐的 JSON 对比。
*   **工业级存储**：快照采用 **Gzip 压缩**（体积缩小 85%），且支持**“无变更不保存”**逻辑，极大节省磁盘空间。

---

## 🚀 安装

推荐使用 `pipx` 安装，确保 `mt` 命令全局可用：

```bash
# 在项目根目录下运行
pipx install .
```

---

## 🛠️ 常用命令

> **注意**：涉及系统采集和配置的操作必须使用 `sudo` 运行。

### 1. 初始化与配置
```bash
sudo mt init          # 创建默认环境
sudo mt config edit   # 一键使用系统编辑器（Vim/Nano）修改配置
mt config show        # 查看当前路径
```

### 2. 扫描并审计
```bash
sudo mt scan          # 执行全量扫描。若无变更，系统将自动跳过保存。
```

### 3. 查看快照
```bash
mt show                       # 查看最新扫描摘要
mt show --collector network   # 查看特定维度的详细 JSON 数据
```

### 4. 自动化与日志
```bash
sudo mt cron install --interval 10m  # 每10分钟后台自动扫描
mt log scan                          # 查看后台审计日志
```

### 5. Web GUI 管理
```bash
sudo mt web install   # 注册后台服务
sudo mt web start     # 启动监控面板 (默认端口 8000)
```

---

## 📂 配置文件

配置文件位于 `~/.config/machine-tracker/config.yaml`。

您可以自定义监控哪些路径或设置风险规则：
```yaml
config_files:
  watch_paths: ["/etc/nginx/", "/etc/sudoers"]

risk_rules:
  - pattern: "shadow|passwd"
    level: "HIGH"
    reason: "发现系统账号敏感变更"
```

---

## 许可证
MIT License
