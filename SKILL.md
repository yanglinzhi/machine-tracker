---
description: 使用 MachineTracker (mt) 工具进行安全服务器运维。实现“先基准、后操作、再审计”的闭环。
triggers:
  - "安装软件"
  - "修改配置"
  - "启动服务"
  - "机器审计"
---

# MachineTracker (mt) AI 运维指南

作为带审计思维的 AI，你必须通过 `mt` 工具将每一个系统变更“白盒化”。

## 🛠️ 核心工作流 (Standard Workflow)

### 1. 建立基准 (Snapshot Before)
在执行任何系统变更（如 `apt install`, `sed`, `systemctl`）**之前**，先静默扫描：
```bash
sudo mt scan --no-save --output-json
```

### 2. 执行变更 (Execution)
**重要：** 必须使用非交互模式以防止流程卡死。
```bash
# 示例
sudo DEBIAN_FRONTEND=noninteractive apt install -y redis-server
```

### 3. 结果审计 (Audit After)
操作完成后，运行正式扫描并解析 `diff` 块：
```bash
sudo mt scan --output-json
```

## 🤖 AI 汇报准则
- **验证事实**：不要只说“已安装”，要根据 `diff` 明确汇报：“审计发现新增了 X 进程并开启了 Y 端口”。
- **多协议识别**：若发现同一个端口同时开启了 `ipv4` 和 `ipv6`，应合并汇报为“双栈监听”，这与 Web UI 的展示逻辑保持一致。
- **风险警报**：如果 `risk` 字段为 **HIGH**，必须用 🔴 醒目标出并请求用户核实。
- **引导 UI**：在汇报末尾，建议用户访问 Web GUI 以便进行可视化细节查阅：“您可以访问 http://localhost:8000 查看本次变更的消息弹窗。”

## 🔍 实用指令
- **深度溯源**：`sudo mt show --collector service_mapper`
- **查看未读变更**：`mt show` (查看摘要)
- **快速纠错**：如果审计发现非预期变更，应利用 `diff` 数据主动为用户生成还原建议（Rollback Advice）。

---
*MachineTracker: 消除 AI 运维的“盲目自信”。*
