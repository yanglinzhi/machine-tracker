# MachineTracker (mt) — 工业级机器状态追踪与审计系统

## 一句话解释

MachineTracker 是一个为人类和 AI 共同设计的“服务器状态摄影机”，它能以工业级标准捕获、追踪并审计服务器的所有细微变更。

**它不仅记录发生了什么，更通过“服务溯源”告诉你每一个变更背后的故事。**

---

## 为什么需要这个？

在现代 DevOps 环境中，由于人和 AI 助手（如 Gemini、Claude）都在频繁操作服务器，状态的透明度变得至关重要。

- **情景 A**：AI 助手昨天更新了某个 Python 包或 Docker 镜像，导致今天凌晨的定时任务挂了，而你完全不知道改动了哪里。
- **情景 B**：服务器上突然多出一个 8080 端口，你想知道它是哪个进程跑的、是 Docker 还是 Systemd 启动的、配置文件在哪个路径。

**MachineTracker 让机器状态变得可审计、可回溯。** 它是连接人类运维人员与 AI 助手的关键“真相来源（Source of Truth）”。

---

## 项目亮点 (Core Features)

1.  **全维度快照**：覆盖端口、进程、APT/NPM/PIP 包、Docker 容器、Systemd 服务、Nginx 配置、Cron 任务、文件指纹。
2.  **服务全景溯源 (Service Mapping)**：核心能力。能从监听端口一路反查到 PID、启动命令、部署方式（Docker/Systemd）及其对应的配置文件。
3.  **人类友好审计 (Web GUI)**：基于 FastAPI 的内置监控面板，支持图形化查看快照摘要、历史时间轴和字段级颜色高亮对比。
4.  **全自动后台运行**：深度集成 Systemd Timer，支持每 10 分钟自动扫描，状态无变更自动跳过，节省存储空间。
5.  **工业级包管理**：支持 `pipx` 一键全局安装，命令与配置、数据完全解耦，支持智能处理 `sudo` 环境变量。
6.  **专业日志审计**：与 `Journald` 无缝集成，支持 `mt log` 统一审计系统执行记录。

---

## 项目目录结构

```
machine-tracker/
│
├── pyproject.toml              ← 开源元数据、依赖管理及包资源定义
├── LICENSE                     ← MIT 开源许可证
├── README.md                   ← 面向用户的说明文档
│
├── src/machinetracker/         ← 核心源码包
│   ├── __init__.py
│   ├── __main__.py             ← 程序入口
│   ├── cli.py                  ← 极简 CLI 层，仅负责参数解析
│   ├── constants.py            ← 全局常量与智能路径发现逻辑（深度解耦）
│   ├── systemd_manager.py      ← 业务逻辑层，负责 Systemd 服务与定时器安装
│   ├── logger.py               ← 标准化日志系统（支持 --verbose）
│   ├── config.py               ← Pydantic 配置校验逻辑
│   ├── collector.py            ← 采集器指挥中心
│   ├── collectors/             ← 插件化采集器目录
│   │   ├── base.py             ← 采集器标准接口（Schema）
│   │   ├── service_mapper.py   ← 【核心】全链路溯源逻辑
│   │   └── ... (apt, docker, systemd, nginx, etc.)
│   ├── differ.py               ← 智能差分引擎（支持 Hash 快速对比）
│   ├── reporter.py             ← 变更摘要生成器
│   ├── store.py                ← 智能存储管理（处理 ~ 路径与无变更跳过）
│   ├── models.py               ← 数据模型定义
│   └── web/                    ← 监控面板 (GUI)
│       ├── app.py              ← FastAPI 后端
│       └── templates/          ← Jinja2 模板（支持响应式布局）
│
├── tests/                      ← 自动化测试框架 (pytest)
│   └── test_differ.py          ← 核心差分逻辑测试
└── data/
    └── default_config.yaml     ← 配置模板
```

---

## 快速上手命令

```bash
# 1. 扫描与审计
sudo mt scan            # 特权扫描（捕获完整进程名与容器关联）
mt history              # 查看历史快照时间轴
mt show --collector network  # 查看当前网络详情

# 2. Web 监控面板
sudo mt web install     # 安装后台 Web 服务
mt web start            # 启动面板 (http://localhost:8000)
mt log web -f           # 实时审计 Web 访问日志

# 3. 自动化配置
sudo mt cron install --interval 10m  # 每 10 分钟自动快照一次
mt log scan             # 审计后台自动扫描记录
```

---

## 项目现状与标准化进度 (Current Status & Roadmap)

目前项目已完成 **"开源级架构重构"**，符合工业级 CLI 工具标准。

### ✅ 已完成 (Finished)
1.  **架构解耦**：引入 `constants.py` 和 `systemd_manager.py`，彻底分离 CLI 层、业务逻辑层和配置层。
2.  **Web 监控面板 (GUI)**：支持快照摘要、历史审计、以及人类可读的字段级高亮对比。
3.  **自动化运维**：实现 `mt web` 和 `mt cron` 的服务化管理。
4.  **专业日志系统**：标准 `logging` 模块 + `Journald` 联动。
5.  **资源管理**：包内资源动态提取，确保分发稳定性。
6.  **智能存储**：无变更不保存，路径自动识别 `sudo` 原用户。
7.  **质量保证**：`pytest` 基础用例已覆盖核心 `Differ`。

### 🚀 待办事项 (Next Steps)
1.  **采集器动态插件化 (Dynamic Discovery)**：消除 `collector.py` 中的手动 import，支持热插拔。
2.  **风险评估引擎 (Risk Assessment)**：在报告中标记 🔴 HIGH RISK 变更。
3.  **多机远程采集 (Remote Scan)**：正式激活 `ssh` 远程快照能力。
4.  **UI 响应式增强**：优化移动端显示及长内容排版。

---

## 给 AI 用的 Skill（薄胶水层）

MachineTracker 的核心价值之一是让 AI 能够“自省”其对机器的影响。对应的 Hermes Skill 逻辑：
1. **感知现状**：AI 在执行关键操作（如安装软件）前后，应调用 `mt scan`。
2. **分析变更**：AI 通过解析 `mt scan --output-json` 的 `diff` 结果，确认操作是否符合预期。
3. **长期记忆**：AI 将扫描摘要写入 memory，确保跨会话的状态连贯性。
