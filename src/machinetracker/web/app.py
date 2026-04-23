import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional

from machinetracker.config import load_config
from machinetracker.store import SnapshotStore
from machinetracker.differ import Differ
from machinetracker.constants import get_default_config_path
from machinetracker.i18n import _T, get_web_lang

app = FastAPI(title="MachineTracker GUI")

# 设置模板和静态文件路径
current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# 注入翻译函数到模板
@app.middleware("http")
async def add_lang_to_request(request: Request, call_next):
    # 将 _T 注入到 request 对象，以便在视图中使用
    lang = get_web_lang(request)
    request.state.lang = lang
    response = await call_next(request)
    return response

# 模板全局变量
templates.env.globals["_T"] = _T

@app.get("/set_lang/{lang}")
async def set_lang(lang: str, request: Request):
    from fastapi.responses import RedirectResponse
    response = RedirectResponse(url=request.headers.get("referer", "/"))
    if lang in ["zh", "en"]:
        response.set_cookie(key="mt_lang", value=lang, max_age=31536000)
    return response

def get_store():
    config_path = get_default_config_path()
    config = load_config(str(config_path))
    return SnapshotStore(config), config

@app.get("/")
async def dashboard(request: Request):
    store, config = get_store()
    machines_data = []
    differ = Differ(config)
    
    for m_key, m_config in config.machines.items():
        # 获取最近两个快照进行自动对比
        snaps = store.get_latest_two_snapshots(m_config.id)
        latest_change = None
        has_high_risk = False
        
        if len(snaps) >= 2:
            # snaps[0] 是最新的, snaps[1] 是次新的
            diff = differ.compare(snaps[1], snaps[0])
            if diff:
                # 统计变更数量和最高风险等级
                count = sum(len(changes) for changes in diff.values())
                for changes in diff.values():
                    if any(c.get("risk") == "HIGH" for c in changes):
                        has_high_risk = True
                        break
                
                latest_change = {
                    "count": count,
                    "timestamp": snaps[0].get("timestamp"),
                    "diff": diff  # 将 diff 传给前端用于弹窗
                }

        latest = snaps[0] if snaps else None
        # 如果机器名是默认的“本地机器”，则根据当前 Web 语言进行翻译
        m_display_name = m_config.name
        if m_display_name in ["本地机器", "local-machine"]:
            m_display_name = _T("WEB_LOCAL_MACHINE_DEFAULT", request.state.lang)

        machines_data.append({
            "key": m_key,
            "name": m_display_name,
            "id": m_config.id,
            "latest_timestamp": latest.get("timestamp") if latest else None,
            "hostname": latest.get("hostname") if latest else "Unknown",
            "latest_change": latest_change,
            "has_high_risk": has_high_risk
        })
    
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"machines": machines_data, "lang": request.state.lang}
    )

@app.get("/machine/{machine_key}")
async def machine_detail(request: Request, machine_key: str):
    store, config = get_store()
    if machine_key not in config.machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    m_config = config.machines[machine_key]
    m_display_name = m_config.name
    if m_display_name in ["本地机器", "local-machine"]:
        m_display_name = _T("WEB_LOCAL_MACHINE_DEFAULT", request.state.lang)
    
    snapshot = store.get_latest_snapshot(m_config.id)
    
    if not snapshot:
        return templates.TemplateResponse(
            request=request, name="machine.html", context={"machine": m_config, "machine_name": m_display_name, "machine_key": machine_key, "snapshot": None, "lang": request.state.lang}
        )
    
    return templates.TemplateResponse(
        request=request, name="machine.html", context={"machine": m_config, "machine_name": m_display_name, "machine_key": machine_key, "snapshot": snapshot, "lang": request.state.lang}
    )

@app.get("/machine/{machine_key}/history")
async def history(request: Request, machine_key: str):
    store, config = get_store()
    if machine_key not in config.machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    m_config = config.machines[machine_key]
    m_display_name = m_config.name
    if m_display_name in ["本地机器", "local-machine"]:
        m_display_name = _T("WEB_LOCAL_MACHINE_DEFAULT", request.state.lang)

    history_list = store.get_history(m_config.id, limit=50)
    
    return templates.TemplateResponse(
        request=request, name="history.html", context={"machine": m_config, "machine_name": m_display_name, "machine_key": machine_key, "history": history_list, "lang": request.state.lang}
    )

@app.get("/machine/{machine_key}/diff/{t1}/{t2}")
async def diff_view(request: Request, machine_key: str, t1: str, t2: str):
    store, config = get_store()
    if machine_key not in config.machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    m_config = config.machines[machine_key]
    m_display_name = m_config.name
    if m_display_name in ["本地机器", "local-machine"]:
        m_display_name = _T("WEB_LOCAL_MACHINE_DEFAULT", request.state.lang)
    
    def load_snap(filename):
        # 统一使用 store 的方法定位机器目录
        machine_dir = store._get_machine_dir(m_config.id)
        path = machine_dir / "snapshots" / filename
        return store._load_json_gz(path)

    snap1 = load_snap(t1)
    snap2 = load_snap(t2)
    
    if not snap1 or not snap2:
        raise HTTPException(status_code=404, detail=f"Snapshots not found: {t1} or {t2}")
        
    differ = Differ(config)
    diff_results = differ.compare(snap1, snap2)
    
    return templates.TemplateResponse(
        request=request, name="diff.html", context={
            "machine": m_config,
            "machine_name": m_display_name,
            "machine_key": machine_key,
            "diff": diff_results,
            "t1": t1,
            "t2": t2,
            "lang": request.state.lang
        }
    )
