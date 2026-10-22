"""Rule engine: link PFMEA and Control Plan records by process step and flag
omissions / inconsistencies. Deterministic rules only — no AI, and the tool
never assigns or approves AP ratings.

Checks:
  C1  PFMEA failure mode with no Control Plan coverage for its process step
  C2a PFMEA prevention/detection control missing from the Control Plan
  C2b control present in both, but prevention/detection classification differs
  C3  special characteristic marking inconsistent between the two documents
  C4  PFMEA row with S/O/D filled in but AP empty
  C5  Control Plan row whose process step has no PFMEA source
  C6  (note) same step number, different step name in the two documents
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .classify import classify_control, controls_match, split_controls
from .model import (CheckResult, ControlPlanRecord, Finding, PfmeaRecord,
                    norm_step_no, norm_text)

CHECK_NAMES = {
    "C1": "PFMEA 失效模式在控制计划中无对应控制",
    "C2a": "PFMEA 控制措施未出现在控制计划",
    "C2b": "预防/探测分类在两份文件中不一致",
    "C3": "特殊特性标记在两份文件中不一致",
    "C4": "S/O/D 已填写但 AP 为空",
    "C5": "控制计划行在 PFMEA 中无来源",
    "C6": "同一工序号在两份文件中工序名称不一致",
}

SC_MARKERS = ["cc", "sc", "◆", "▼", "★", "●", "关键", "重要", "安全", "法规", "特殊"]


def has_sc_marking(value: str) -> bool:
    t = norm_text(value)
    if not t:
        return False
    return any(m in t for m in SC_MARKERS)


def _group_by(records, attr):
    out: Dict[str, list] = {}
    for r in records:
        out.setdefault(attr(r), []).append(r)
    return out


def _suggestion(check_id: str) -> str:
    return {
        "C1": "请工程师确认该工序是否漏编控制计划，或工序号/工序名称在两份文件中是否写法不一致。",
        "C2a": "请工程师确认该控制措施应纳入控制计划，或在 PFMEA 中修正措施描述使其与控制计划一致。",
        "C2b": "请工程师核对该措施的性质：预防控制应降低发生度，探测控制应降低探测度，两份文件须一致。",
        "C3": "特殊特性必须在 PFMEA 与控制计划中一致标识并传递到作业文件，请工程师核对标记。",
        "C4": "AP 必须由工程师按 AIAG-VDA AP 表评定（本工具不评定 AP），请补齐评定结果。",
        "C5": "请工程师确认该控制计划行对应的 PFMEA 工序是否存在，或是否引用了已删除的工序。",
        "C6": "请工程师统一两份文件中的工序名称，避免后续关联失效。",
    }[check_id]


def _finding(check_id, severity, rec, message) -> Finding:
    return Finding(
        check_id=check_id, check_name=CHECK_NAMES[check_id], severity=severity,
        source=rec.source, file_name=rec.file_name, sheet=rec.sheet, row=rec.row,
        step_no=rec.step_no, step_name=rec.step_name, message=message,
        suggestion=_suggestion(check_id),
    )


def run_checks(pfmea: List[PfmeaRecord], cp: List[ControlPlanRecord]) -> CheckResult:
    result = CheckResult(pfmea_records=pfmea, cp_records=cp)
    findings: List[Finding] = []

    cp_by_key = _group_by(cp, lambda r: r.key)
    pf_by_key = _group_by(pfmea, lambda r: r.key)
    cp_by_no = _group_by(cp, lambda r: norm_step_no(r.step_no))
    pf_by_no = _group_by(pfmea, lambda r: norm_step_no(r.step_no))

    def linked_cp(rec: PfmeaRecord) -> List[ControlPlanRecord]:
        if rec.key in cp_by_key:
            return cp_by_key[rec.key]
        return cp_by_no.get(norm_step_no(rec.step_no), [])

    def linked_pf(rec: ControlPlanRecord) -> List[PfmeaRecord]:
        if rec.key in pf_by_key:
            return pf_by_key[rec.key]
        return pf_by_no.get(norm_step_no(rec.step_no), [])

    # ---- C6: step name mismatch on the same step number -------------------
    seen_pairs = set()
    for no, pf_recs in pf_by_no.items():
        if not no:
            continue
        for crec in cp_by_no.get(no, []):
            for prec in pf_recs:
                if norm_text(prec.step_name) != norm_text(crec.step_name):
                    pair = (no, norm_text(prec.step_name), norm_text(crec.step_name))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        findings.append(_finding(
                            "C6", "low", prec,
                            "工序号 %s 在 PFMEA 中为「%s」，在控制计划中为「%s」。"
                            % (prec.step_no, prec.step_name, crec.step_name)))

    # ---- C1 + C2: PFMEA side ----------------------------------------------
    for rec in pfmea:
        s = rec.severity_int()
        linked = linked_cp(rec)
        if not linked:
            sev = "high" if (s is not None and s >= 9) else "medium"
            findings.append(_finding(
                "C1", sev, rec,
                "失效模式「%s」（工序 %s %s）在控制计划中没有对应工序的任何控制行。"
                % (rec.failure_mode, rec.step_no, rec.step_name)))
            continue  # whole step uncovered: C1 only, C2 would be redundant

        cp_controls: List[Tuple[str, str, ControlPlanRecord]] = []
        for crec in linked:
            for text in split_controls(crec.control_method):
                cp_controls.append((text, classify_control(text, crec.control_type), crec))

        for kind, cell in (("prevention", rec.prevention_control),
                           ("detection", rec.detection_control)):
            for text in split_controls(cell):
                matches = [c for c in cp_controls if controls_match(text, c[0])]
                if not matches:
                    sev = "medium"
                    if kind == "detection" and s is not None and s >= 9:
                        sev = "high"
                    label = "预防控制" if kind == "prevention" else "探测控制"
                    findings.append(_finding(
                        "C2a", sev, rec,
                        "%s「%s」（工序 %s %s，失效模式「%s」）未出现在控制计划对应工序的控制方法中。"
                        % (label, text, rec.step_no, rec.step_name, rec.failure_mode)))
                else:
                    for _t, cls, _crec in matches:
                        if cls not in ("unknown", kind):
                            label_pf = "预防" if kind == "prevention" else "探测"
                            label_cp = "预防" if cls == "prevention" else "探测"
                            findings.append(_finding(
                                "C2b", "medium", rec,
                                "控制「%s」在 PFMEA 中列为%s控制，但在控制计划中被分类为%s控制（工序 %s %s）。"
                                % (text, label_pf, label_cp, rec.step_no, rec.step_name)))
                            break

    # ---- C3: special characteristics ---------------------------------------
    pf_sc_by_no: Dict[str, PfmeaRecord] = {}
    for rec in pfmea:
        if has_sc_marking(rec.special_char):
            pf_sc_by_no.setdefault(norm_step_no(rec.step_no), rec)
    cp_sc_by_no: Dict[str, ControlPlanRecord] = {}
    for rec in cp:
        if has_sc_marking(rec.special_char):
            cp_sc_by_no.setdefault(norm_step_no(rec.step_no), rec)

    for no, rec in pf_sc_by_no.items():
        if no not in cp_sc_by_no and no in cp_by_no:
            findings.append(_finding(
                "C3", "high", rec,
                "工序 %s %s 在 PFMEA 中标记了特殊特性「%s」，但控制计划对应工序未标记特殊特性。"
                % (rec.step_no, rec.step_name, rec.special_char)))
    for no, rec in cp_sc_by_no.items():
        if no not in pf_sc_by_no and no in pf_by_no:
            findings.append(_finding(
                "C3", "high", rec,
                "工序 %s %s 在控制计划中标记了特殊特性「%s」，但 PFMEA 对应工序未标记特殊特性。"
                % (rec.step_no, rec.step_name, rec.special_char)))

    # ---- C4: S/O/D filled but AP empty --------------------------------------
    for rec in pfmea:
        if rec.sod_filled() and not str(rec.ap).strip():
            s = rec.severity_int()
            sev = "high" if (s is not None and s >= 9) else "medium"
            findings.append(_finding(
                "C4", sev, rec,
                "失效模式「%s」（工序 %s %s）S=%s、O=%s、D=%s 已填写，但 AP 为空。"
                % (rec.failure_mode, rec.step_no, rec.step_name,
                   rec.severity, rec.occurrence, rec.detection)))

    # ---- C5: Control Plan rows with no PFMEA source -------------------------
    for rec in cp:
        if not linked_pf(rec):
            findings.append(_finding(
                "C5", "low", rec,
                "控制计划行（工序 %s %s，特性「%s」）在 PFMEA 中找不到对应工序。"
                % (rec.step_no, rec.step_name, rec.characteristic)))

    result.findings = findings
    return result
