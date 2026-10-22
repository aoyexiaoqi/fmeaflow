"""Report writers: Markdown and Excel issue reports.

Every report carries the disclaimer footer: this tool flags issues only; it
never assigns or approves AP ratings and never approves a PFMEA/Control Plan.
"""
from __future__ import annotations

from typing import List

from . import DISCLAIMER
from .checks import CHECK_NAMES
from .model import SEVERITY_ORDER, CheckResult, Finding

SEVERITY_LABEL = {"high": "高", "medium": "中", "low": "低"}


def _sorted(findings: List[Finding]) -> List[Finding]:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.check_id, f.row))


def render_markdown(result: CheckResult, pfmea_name: str, cp_name: str) -> str:
    sev = result.counts_by_severity()
    by_check = result.counts_by_check()
    lines = []
    lines.append("# FMEAFlow 一致性检查报告")
    lines.append("")
    lines.append("- PFMEA 文件：`%s`（%d 行数据）" % (pfmea_name, len(result.pfmea_records)))
    lines.append("- 控制计划文件：`%s`（%d 行数据）" % (cp_name, len(result.cp_records)))
    lines.append("- 问题总数：**%d**（高 %d / 中 %d / 低 %d）"
                 % (len(result.findings), sev["high"], sev["medium"], sev["low"]))
    lines.append("")
    lines.append("## 按检查项汇总")
    lines.append("")
    lines.append("| 检查项 | 说明 | 数量 |")
    lines.append("|---|---|---|")
    for cid in sorted(CHECK_NAMES):
        lines.append("| %s | %s | %d |" % (cid, CHECK_NAMES[cid], by_check.get(cid, 0)))
    lines.append("")
    for level in ("high", "medium", "low"):
        group = [f for f in _sorted(result.findings) if f.severity == level]
        if not group:
            continue
        lines.append("## 问题明细（严重度：%s）" % SEVERITY_LABEL[level])
        lines.append("")
        lines.append("| 检查项 | 位置 | 工序 | 问题 | 建议复核 |")
        lines.append("|---|---|---|---|---|")
        for f in group:
            step = ("%s %s" % (f.step_no, f.step_name)).strip()
            lines.append("| %s | %s | %s | %s | %s |"
                         % (f.check_id, f.location(), step,
                            f.message.replace("|", "/"), f.suggestion.replace("|", "/")))
        lines.append("")
    if not result.findings:
        lines.append("未发现一致性问题。（这不等于 PFMEA 或控制计划已被批准，仍须工程师评审。）")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> " + DISCLAIMER)
    lines.append("")
    return "\n".join(lines)


def write_excel(result: CheckResult, path: str, pfmea_name: str, cp_name: str) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    bold = Font(bold=True)
    sev = result.counts_by_severity()
    by_check = result.counts_by_check()
    ws["A1"] = "FMEAFlow 一致性检查报告"
    ws["A1"].font = Font(bold=True, size=14)
    rows = [
        ("PFMEA 文件", pfmea_name, "%d 行数据" % len(result.pfmea_records)),
        ("控制计划文件", cp_name, "%d 行数据" % len(result.cp_records)),
        ("问题总数", len(result.findings), "高 %d / 中 %d / 低 %d" % (sev["high"], sev["medium"], sev["low"])),
    ]
    r = 3
    for a, b, c in rows:
        ws.cell(row=r, column=1, value=a).font = bold
        ws.cell(row=r, column=2, value=b)
        ws.cell(row=r, column=3, value=c)
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="检查项").font = bold
    ws.cell(row=r, column=2, value="说明").font = bold
    ws.cell(row=r, column=3, value="数量").font = bold
    r += 1
    for cid in sorted(CHECK_NAMES):
        ws.cell(row=r, column=1, value=cid)
        ws.cell(row=r, column=2, value=CHECK_NAMES[cid])
        ws.cell(row=r, column=3, value=by_check.get(cid, 0))
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="免责声明").font = bold
    ws.cell(row=r, column=2, value=DISCLAIMER)

    ws2 = wb.create_sheet("Findings")
    headers = ["检查项", "严重度", "来源", "文件", "表", "行号", "工序号", "工序名称", "问题", "建议复核"]
    for c, h in enumerate(headers, start=1):
        ws2.cell(row=1, column=c, value=h).font = bold
    for i, f in enumerate(_sorted(result.findings), start=2):
        values = [f.check_id, SEVERITY_LABEL[f.severity], f.source, f.file_name,
                  f.sheet, f.row, f.step_no, f.step_name, f.message, f.suggestion]
        for c, v in enumerate(values, start=1):
            ws2.cell(row=i, column=c, value=v)
    wb.save(path)
