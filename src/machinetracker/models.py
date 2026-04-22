from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class CollectorResult(BaseModel):
    data: Dict[str, Any]
    hash: str

class MachineSnapshot(BaseModel):
    machine_id: str
    timestamp: str
    hostname: str
    collectors: Dict[str, Any]  # 存储各个采集器的原始输出
