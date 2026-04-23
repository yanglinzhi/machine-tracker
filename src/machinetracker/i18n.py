import os
import locale
from typing import Optional, Dict

def get_system_lang() -> str:
    """探测系统语言，中文返回 zh，其余返回 en"""
    try:
        lang, _ = locale.getlocale()
        if not lang:
            lang = os.environ.get('LANG', '')
        if lang and lang.lower().startswith('zh'):
            return 'zh'
    except:
        pass
    return 'en'

# 翻译字典
TRANSLATIONS = {
    # CLI 基础
    "ERR_ROOT_REQUIRED": {"zh": "错误: 此操作必须以 root 权限运行（建议使用 sudo）。", "en": "Error: This operation must be run with root privileges (sudo recommended)."},
    "CLI_DESC": {"zh": "MachineTracker (mt) — 机器状态追踪与审计系统", "en": "MachineTracker (mt) — Machine status tracking and auditing system"},
    "CLI_INIT_HELP": {"zh": "初始化 MachineTracker 配置与存储 (需要 sudo)", "en": "Initialize MachineTracker config and storage (requires sudo)"},
    "CLI_CONFIG_HELP": {"zh": "查看或管理当前配置与数据路径", "en": "View or manage current config and data paths"},
    "CLI_SCAN_HELP": {"zh": "执行状态采集与差分审计 (需要 sudo)", "en": "Perform status collection and differential auditing (requires sudo)"},
    "CLI_SHOW_HELP": {"zh": "查看机器的当前状态 (最新快照)", "en": "View the current status of the machine (latest snapshot)"},
    "CLI_MACHINES_HELP": {"zh": "查看已注册的机器列表", "en": "View the list of registered machines"},
    "CLI_HISTORY_HELP": {"zh": "查看扫描历史记录", "en": "View scan history"},
    "CLI_WEB_HELP": {"zh": "Web 监控面板展示 (普通用户权限即可)", "en": "Web monitoring dashboard (standard user privileges suffice)"},
    "CLI_LOG_HELP": {"zh": "查看系统日志 (通常需要 sudo)", "en": "View system logs (usually requires sudo)"},
    "CLI_CRON_HELP": {"zh": "自动化定时扫描管理 (需要 sudo)", "en": "Automated periodic scan management (requires sudo)"},
    "CLI_LANG_HELP": {"zh": "切换系统语言 (zh/en)", "en": "Switch system language (zh/en)"},
    
    # 消息提示
    "LOG_CONFIG_EXISTS": {"zh": "配置文件已存在: {path}", "en": "Config file already exists: {path}"},
    "LOG_CONFIG_CREATED": {"zh": "已创建默认配置文件: {path}", "en": "Default config file created: {path}"},
    "CLI_EDIT_OPENING": {"zh": "正在使用 {editor} 打开配置文件...", "en": "Opening config file with {editor}..."},
    "LOG_SCAN_START": {"zh": "开始扫描: {machine}...", "en": "Starting scan: {machine}..."},
    "LOG_SCAN_NO_CHANGE": {"zh": "检测到状态无变更，跳过保存。", "en": "No changes detected, skipping save."},
    "ERR_NO_SNAPSHOT": {"zh": "没有找到快照。请先运行 'sudo mt scan'。", "en": "No snapshot found. Please run 'sudo mt scan' first."},
    "LANG_SWITCHED": {"zh": "语言已切换为: {lang}", "en": "Language switched to: {lang}"},
    "ERR_INVALID_LANG": {"zh": "错误: 不支持的语言 '{lang}'。目前仅支持 zh 或 en。", "en": "Error: Unsupported language '{lang}'. Currently only zh or en are supported."},

    # Web & Cron 服务管理
    "LOG_WEB_REGISTERED": {"zh": "Web 服务已成功注册为系统服务。", "en": "Web service successfully registered as a system service."},
    "LOG_WEB_STARTED": {"zh": "Web 服务已启动。", "en": "Web service started."},
    "LOG_WEB_STOPPED": {"zh": "Web 服务已停止。", "en": "Web service stopped."},
    "LOG_WEB_RESTARTED": {"zh": "Web 服务已重启。", "en": "Web service restarted."},
    "LOG_CRON_INSTALLED": {"zh": "定时扫描任务已安装，间隔: {interval}", "en": "Periodic scan task installed, interval: {interval}"},
    "LOG_CRON_STOPPED": {"zh": "定时扫描任务已停止。", "en": "Periodic scan task stopped."},

    # 报告与摘要
    "REP_NO_CHANGES": {"zh": "没有检测到任何变更。", "en": "No changes detected."},
    "REP_CHANGES_DETECTED": {"zh": "检测到以下变更:", "en": "The following changes were detected:"},
    "REP_INITIAL_SCAN": {"zh": "初始扫描完成。", "en": "Initial scan completed."},
    "REP_STATUS_UNCHANGED": {"zh": "状态未改变。", "en": "Status unchanged."},
    "REP_MD_TITLE": {"zh": "机器变更报告", "en": "Machine Change Report"},
    "REP_MD_COL_TYPE": {"zh": "类型", "en": "Type"},
    "REP_MD_COL_ITEM": {"zh": "项目", "en": "Item"},
    "REP_MD_COL_DETAILS": {"zh": "详情", "en": "Details"},
    "REP_MD_CHANGED": {"zh": "已变更", "en": "changed"},

    # Web 界面通用
    "WEB_DASHBOARD": {"zh": "仪表盘", "en": "Dashboard"},
    "WEB_SUBTITLE": {"zh": "机器状态监控面板", "en": "Machine Status Monitor"},
    "WEB_LATEST_SNAPSHOT": {"zh": "最新快照", "en": "Latest Snapshot"},
    "WEB_HISTORY": {"zh": "历史记录", "en": "History"},
    "WEB_DIFF": {"zh": "变更对比", "en": "Diff"},
    "WEB_MACHINE_DETAIL": {"zh": "机器详情", "en": "Machine Details"},
    "WEB_HOSTNAME": {"zh": "主机名", "en": "Hostname"},
    "WEB_TIMESTAMP": {"zh": "快照时间", "en": "Timestamp"},
    "WEB_NO_DATA": {"zh": "暂无数据", "en": "No data available"},
    "WEB_RISK_HIGH": {"zh": "高风险", "en": "High Risk"},
    "WEB_VIEW_DETAIL": {"zh": "查看详情", "en": "View Details"},
    "WEB_SWITCH_LANG": {"zh": "EN/中", "en": "中/EN"},
    "WEB_LOCAL_MACHINE_DEFAULT": {"zh": "本地机器", "en": "Local Machine"},
    "WEB_COLLECTOR_SUMMARY": {"zh": "采集器数据摘要", "en": "Collector Data Summary"},
    "WEB_STABLE_STATE": {"zh": "状态稳定，无变更记录", "en": "Status stable, no changes detected"},
    "WEB_BACK_TO_DASHBOARD": {"zh": "返回仪表盘", "en": "Back to Dashboard"},
    "WEB_BACK_TO_DETAIL": {"zh": "返回详情", "en": "Back to Details"},
    "WEB_BACK_TO_HISTORY": {"zh": "返回历史记录", "en": "Back to History"},

    # Dashboard 专用
    "WEB_DASHBOARD_DETECTED_CHANGES": {"zh": "检测到 {count} 处变更", "en": "Detected {count} changes"},
    "WEB_DASHBOARD_DETECTED_CHANGE": {"zh": "检测到 {count} 处变更", "en": "Detected {count} changes"},
    "WEB_DASHBOARD_RECENT_REPORT": {"zh": "最近变更报告", "en": "Recent Change Report"},
    "WEB_DASHBOARD_GOTO_HISTORY": {"zh": "进入历史记录详审", "en": "Go to History Detail"},

    # Machine Detail 专用
    "WEB_MACHINE_NO_SNAPSHOT": {"zh": "该机器尚无快照数据。请在终端运行 mt scan 进行首次采集。", "en": "No snapshot data for this machine. Run mt scan in terminal for first collection."},
    "WEB_MACHINE_LATEST_SUMMARY": {"zh": "最后快照摘要", "en": "Latest Snapshot Summary"},
    "WEB_MACHINE_VIEW_ALL_HISTORY": {"zh": "查看所有历史快照对比", "en": "View All History Snapshots"},
    "WEB_MACHINE_SERVICE_PANORAMA": {"zh": "服务全景溯源", "en": "Service Panorama Mapping"},
    "WEB_MACHINE_NO_SERVICE_DATA": {"zh": "暂无服务溯源数据。运行 sudo mt scan 采集服务信息。", "en": "No service data. Run sudo mt scan to collect service mapping."},
    "WEB_UNIT_PORT": {"zh": "端口", "en": "Ports"},
    "WEB_UNIT_PKG": {"zh": "软件包", "en": "Packages"},
    "WEB_UNIT_SERVICE": {"zh": "服务", "en": "Services"},
    "WEB_UNIT_FILE": {"zh": "文件", "en": "Files"},
    "WEB_UNIT_COLLECTED": {"zh": "已采集", "en": "Collected"},

    # History 专用
    "WEB_HISTORY_SUBTITLE": {"zh": "选择两个快照进行字段级变更对比（先选旧的，再选新的）", "en": "Select two snapshots to compare (Old first, then New)"},
    "WEB_HISTORY_GUIDE": {"zh": "勾选两行快照后，点击 对比所选快照 按钮查看详细变更审计报告。", "en": "Select two rows and click Compare button for detailed audit report."},
    "WEB_HISTORY_COL_FILENAME": {"zh": "文件名", "en": "Filename"},
    "WEB_HISTORY_SELECTED": {"zh": "已选择 {count} 个快照", "en": "{count} snapshots selected"},
    "WEB_HISTORY_COMPARE_BTN": {"zh": "⚡ 对比所选快照", "en": "⚡ Compare Selected Snapshots"},

    # Diff 专用
    "WEB_DIFF_AUDIT": {"zh": "变更审计", "en": "Change Audit"},
    "WEB_DIFF_AUDIT_REPORT": {"zh": "变更审计报告", "en": "Change Audit Report"},
    "WEB_DIFF_BASE": {"zh": "基准", "en": "Base"},
    "WEB_DIFF_TARGET": {"zh": "目标", "en": "Target"},
    "WEB_DIFF_NO_CHANGES": {"zh": "所选时间段内未发现任何状态变更", "en": "No changes found in the selected period"},
    "WEB_DIFF_MACHINE_STABLE": {"zh": "机器状态稳定，没有任何差异被检测到。", "en": "Machine state is stable, no differences detected."},
    "WEB_DIFF_CHANGES_COUNT": {"zh": "{count} 处变更", "en": "{count} changes"},
}

def _T(key: str, _lang: str = None, **kwargs) -> str:
    """翻译函数，使用 _lang 避免与 kwargs 中的 lang 冲突"""
    # 如果没传语言或传了 None，自动探测
    if not _lang:
        _lang = get_system_lang()
        
    text = TRANSLATIONS.get(key, {}).get(_lang, key)
    
    # 如果该语言下没这个 key，尝试回退到 zh，再不行回退到 key 本身
    if text == key and _lang != 'zh':
        text = TRANSLATIONS.get(key, {}).get('zh', key)
        
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

def get_cli_lang(app_config=None) -> str:
    """获取 CLI 应当使用的语言"""
    if app_config and hasattr(app_config, 'language'):
        return app_config.language
    return get_system_lang()

def get_web_lang(request) -> str:
    """从 Web Request (Cookie) 中获取语言，默认回退到系统设置"""
    lang = request.cookies.get("mt_lang")
    if lang in ["zh", "en"]:
        return lang
    return get_system_lang()
