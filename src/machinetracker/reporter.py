from typing import Any, Dict, List

class Reporter:
    """报告生成器"""

    def generate_summary(self, diff_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成文本格式的变更摘要"""
        if not diff_results:
            return "没有检测到任何变更。"

        lines = ["检测到以下变更:"]
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
            return "No changes detected."

        md = ["# Machine Change Report\n"]
        for collector_name, changes in diff_results.items():
            md.append(f"## {collector_name}\n")
            md.append("| Type | Item | Details |")
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
                        details = ", ".join(changed_keys) + " changed"
                
                md.append(f"| {ctype} | {item} | {details} |")
            md.append("")
        
        return "\n".join(md)
