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

app = FastAPI(title="MachineTracker GUI")

# 设置模板和静态文件路径
current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))

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
        machines_data.append({
            "key": m_key,
            "name": m_config.name,
            "id": m_config.id,
            "latest_timestamp": latest.get("timestamp") if latest else None,
            "hostname": latest.get("hostname") if latest else "Unknown",
            "latest_change": latest_change,
            "has_high_risk": has_high_risk
        })
    
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"machines": machines_data}
    )

@app.get("/machine/{machine_key}")
async def machine_detail(request: Request, machine_key: str):
    store, config = get_store()
    if machine_key not in config.machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    m_config = config.machines[machine_key]
    snapshot = store.get_latest_snapshot(m_config.id)
    
    if not snapshot:
        return templates.TemplateResponse(
            request=request, name="machine.html", context={"machine": m_config, "machine_key": machine_key, "snapshot": None}
        )
    
    return templates.TemplateResponse(
        request=request, name="machine.html", context={"machine": m_config, "machine_key": machine_key, "snapshot": snapshot}
    )

@app.get("/machine/{machine_key}/history")
async def history(request: Request, machine_key: str):
    store, config = get_store()
    if machine_key not in config.machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    m_config = config.machines[machine_key]
    history_list = store.get_history(m_config.id, limit=50)
    
    return templates.TemplateResponse(
        request=request, name="history.html", context={"machine": m_config, "machine_key": machine_key, "history": history_list}
    )

@app.get("/machine/{machine_key}/diff/{t1}/{t2}")
async def diff_view(request: Request, machine_key: str, t1: str, t2: str):
    store, config = get_store()
    if machine_key not in config.machines:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    m_config = config.machines[machine_key]
    
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
            "machine_key": machine_key,
            "diff": diff_results,
            "t1": t1,
            "t2": t2
        }
    )
