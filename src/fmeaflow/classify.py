"""Classify a control as prevention （预防） or detection （探测）.

Priority: an explicit 控制类型 column value wins; otherwise keyword heuristics
over the control-method text. Returns 'prevention', 'detection' or 'unknown'.
"""
from __future__ import annotations

from .model import norm_text

PREVENTION_KEYWORDS = [
    "防错", "防呆", "预防", "联锁", "互锁", "治具", "工装", "模具", "限位",
    "自动上料", "程序控制", "参数锁定", "poka", "errorproof", "prevent",
    "interlock", "fixture",
]
DETECTION_KEYWORDS = [
    "检验", "检测", "测量", "量具", "检具", "抽检", "全检", "目视", "检查",
    "首件", "巡检", "试验", "测试", "spc", "aoi", "x光", "x-ray", "xray",
    "inspect", "measur", "gauge", "gage", "test", "audit", "check",
]


def classify_control(text: str, explicit_type: str = "") -> str:
    explicit = norm_text(explicit_type)
    if explicit:
        if "预防" in explicit or "prevent" in explicit:
            return "prevention"
        if "探测" in explicit or "检测" in explicit or "detect" in explicit:
            return "detection"
    t = norm_text(text)
    if not t:
        return "unknown"
    prev_hits = sum(1 for k in PREVENTION_KEYWORDS if k in t)
    det_hits = sum(1 for k in DETECTION_KEYWORDS if k in t)
    if prev_hits > det_hits:
        return "prevention"
    if det_hits > prev_hits:
        return "detection"
    return "unknown"


def split_controls(text: str):
    """Split a cell that lists several controls into individual control texts."""
    if text is None:
        return []
    s = str(text)
    for sep in ["；", ";", "\n", "、", "|"]:
        s = s.replace(sep, ";")
    return [part.strip() for part in s.split(";") if part.strip()]


def controls_match(a: str, b: str) -> bool:
    """Loose text match between two control descriptions (normalized)."""
    na, nb = norm_text(a), norm_text(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # containment either way (e.g. '首件检验' vs '首件检验（每班）')
    return na in nb or nb in na
