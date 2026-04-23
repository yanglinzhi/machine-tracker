from typing import Any, Dict, List
from .i18n import _T

class Reporter:
    """报告生成器"""

    def __init__(self, lang: str = "zh"):
        self.lang = lang

    def generate_summary(self, diff_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成文本格式的变更摘要"""
        if not diff_results:
            return _T("REP_NO_CHANGES", self.lang)

        lines = [_T("REP_CHANGES_DETECTED", self.lang)]
        for collector_name, changes in diff_results.items():
            lines.append(f"\n[{collector_name}]")
            for change in changes:
                change_type = change.get("type", "unknown").upper()
                item = change.get("item", "unnamed")
                risk = change.get("risk", "LOW")
                
                # 风险标识
                risk_prefix = ""
                if risk == "HIGH": risk_prefix = "🔴 "
                elif risk == "MEDIUM": risk_prefix = "🟡 "
                
                lines.append(f"  - {risk_prefix}{change_type}: {item}")
        
        return "\n".join(lines)

    def generate_markdown(self, diff_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成 Markdown 格式的详细报告"""
        if not diff_results:
            return _T("REP_NO_CHANGES", self.lang)

        md = [f"# {_T('REP_MD_TITLE', self.lang)}\n"]
        for collector_name, changes in diff_results.items():
            md.append(f"## {collector_name}\n")
            md.append(f"| {_T('REP_MD_COL_TYPE', self.lang)} | {_T('REP_MD_COL_ITEM', self.lang)} | {_T('REP_MD_COL_DETAILS', self.lang)} |")
            md.append("|------|------|---------|")
            for change in changes:
                ctype = change.get("type", "")
                item = change.get("item", "")
                
                # 简化详情展示
                details = ""
                if ctype == "changed":
                    # 如果是字典，找找哪里变了
                    old = change.get("old", {})
                    new = change.get("new", {})
                    if isinstance(old, dict) and isinstance(new, dict):
                        changed_keys = [k for k in new if new.get(k) != old.get(k)]
                        details = ", ".join(changed_keys) + " " + _T("REP_MD_CHANGED", self.lang)
                
                md.append(f"| {ctype} | {item} | {details} |")
            md.append("")
        
        return "\n".join(md)
