import pytest
from machinetracker.differ import Differ

def test_differ_detects_added_package():
    # 模拟旧数据：没有某个包
    old_snap = {
        "collectors": {
            "apt": {
                "packages": {"nginx": "1.18.0"},
                "hash": "old_hash"
            }
        }
    }
    
    # 模拟新数据：新增了一个包
    new_snap = {
        "collectors": {
            "apt": {
                "packages": {
                    "nginx": "1.18.0",
                    "curl": "7.68.0"
                },
                "hash": "new_hash"
            }
        }
    }
    
    differ = Differ()
    results = differ.compare(old_snap, new_snap)
    
    # 验证是否检测到了 apt 维度的变更
    assert "apt" in results
    changes = results["apt"]
    
    # 验证变更类型是否为 added
    added_change = next(c for c in changes if c["type"] == "added")
    assert "curl" in added_change["item"]
    assert added_change["new"] == "7.68.0"

def test_differ_detects_changed_service():
    # 模拟旧数据：服务在 80 端口
    old_snap = {
        "collectors": {
            "service_mapper": {
                "services": [
                    {"port": 80, "process": "nginx", "deployment": {"type": "systemd"}}
                ],
                "hash": "hash1"
            }
        }
    }
    
    # 模拟新数据：80 端口的服务进程变了
    new_snap = {
        "collectors": {
            "service_mapper": {
                "services": [
                    {"port": 80, "process": "apache2", "deployment": {"type": "systemd"}}
                ],
                "hash": "hash2"
            }
        }
    }
    
    differ = Differ()
    results = differ.compare(old_snap, new_snap)
    
    assert "service_mapper" in results
    change = results["service_mapper"][0]
    assert change["type"] == "changed"
    assert change["old"]["process"] == "nginx"
    assert change["new"]["process"] == "apache2"

def test_differ_skips_when_hash_identical():
    # 模拟数据：Hash 完全一致
    data = {
        "collectors": {
            "apt": {
                "packages": {"nginx": "1.18.0"},
                "hash": "same_hash"
            }
        }
    }
    
    differ = Differ()
    results = differ.compare(data, data)
    
    # 结果应该为空，因为 hash 一致触发了快速跳过逻辑
    assert results == {}
