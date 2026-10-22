"""Column mapping: canonical field -> accepted header names (Chinese / English).

Real-world PFMEA and Control Plan sheets use many different headers. FMEAFlow
matches headers against the alias lists below (after stripping whitespace,
case-insensitive for Latin text). A user-supplied JSON mapping file can pin an
exact header for any canonical field, e.g.:

    {
      "pfmea":        {"severity": "严重度S", "ap": "行动优先级别"},
      "control_plan": {"control_method": "控制方法（中文）"}
    }
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

PFMEA_FIELDS: Dict[str, List[str]] = {
    "step_no": ["工序号", "工序编号", "工步号", "工序号/名称", "Process Step No", "Step No", "Process No", "OP No", "OP"],
    "step_name": ["工序名称", "过程名称", "工序", "过程步骤", "Process Step", "Process Name", "Step Name", "Process Step Name"],
    "failure_mode": ["失效模式", "潜在失效模式", "要求/失效模式", "Failure Mode", "Potential Failure Mode"],
    "failure_effect": ["失效影响", "失效后果", "潜在失效影响", "失效效应", "Failure Effect", "Effect", "Effects of Failure"],
    "severity": ["严重度", "严重度S", "S", "Severity", "Sev"],
    "failure_cause": ["失效原因", "失效起因", "潜在失效原因", "失效原因/起因", "Failure Cause", "Cause", "Potential Cause"],
    "prevention_control": ["现行预防控制", "预防控制", "现行过程控制-预防", "现行过程控制（预防）", "预防措施", "Prevention Control", "Current Prevention Control"],
    "occurrence": ["频度", "发生度", "频度O", "O", "Occurrence", "Occ"],
    "detection_control": ["现行探测控制", "探测控制", "现行过程控制-探测", "现行过程控制（探测）", "探测措施", "Detection Control", "Current Detection Control"],
    "detection": ["探测度", "探测度D", "D", "Detection", "Det"],
    "ap": ["AP", "行动优先级", "行动优先级别", "Action Priority"],
    "special_char": ["特殊特性", "特殊特性标记", "特性分类", "分类", "Special Characteristic", "Classification", "Class"],
}

CONTROL_PLAN_FIELDS: Dict[str, List[str]] = {
    "step_no": ["工序号", "工序编号", "工步号", "过程编号", "Process Step No", "Step No", "Process No", "OP No", "OP"],
    "step_name": ["工序名称", "过程名称", "工序", "过程/工序名称", "机器/装置/工装", "Process Step", "Process Name", "Step Name", "Process Step Name"],
    "characteristic": ["特性", "产品特性", "过程特性", "产品/过程特性", "Characteristic", "Product Characteristic", "Process Characteristic"],
    "special_char": ["特殊特性", "特殊特性标记", "特性分类", "分类", "Special Characteristic", "Classification", "Class"],
    "control_method": ["控制方法", "控制方法/措施", "Control Method", "Method of Control"],
    "control_type": ["控制类型", "控制类别", "类型", "Control Type", "Type of Control"],
    "evaluation": ["评价测量技术", "评价/测量技术", "测量技术", "Evaluation Technique", "Measurement Technique"],
    "reaction_plan": ["反应计划", "纠正措施", "Reaction Plan"],
}

# canonical fields that must be present for the check to be meaningful
PFMEA_REQUIRED = ["step_no", "failure_mode"]
CONTROL_PLAN_REQUIRED = ["step_no"]


def _norm_header(h) -> str:
    return "".join(str(h).split()).lower()


def resolve_columns(headers, field_aliases: Dict[str, List[str]],
                    overrides: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
    """Return {canonical_field: actual_header_or_None} for a sheet's headers."""
    overrides = overrides or {}
    by_norm = {}
    for h in headers:
        by_norm.setdefault(_norm_header(h), h)
    resolved: Dict[str, Optional[str]] = {}
    for field_name, aliases in field_aliases.items():
        if field_name in overrides:
            wanted = overrides[field_name]
            resolved[field_name] = wanted if wanted in headers else by_norm.get(_norm_header(wanted))
            continue
        found = None
        for alias in aliases:
            if alias in headers:
                found = alias
                break
            hit = by_norm.get(_norm_header(alias))
            if hit is not None:
                found = hit
                break
        resolved[field_name] = found
    return resolved


def load_mapping_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("mapping file must be a JSON object")
    return data
