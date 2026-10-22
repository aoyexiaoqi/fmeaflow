"""Normalized data model for PFMEA / Control Plan records and findings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


def norm_text(value) -> str:
    """Normalize free text for comparison: strip, drop all whitespace, lower-case."""
    if value is None:
        return ""
    s = str(value).replace("　", " ").strip()
    s = "".join(s.split())
    return s.lower()


def norm_step_no(value) -> str:
    """Normalize a process step number: '010' / '10.0' / 10 -> '10'."""
    s = norm_text(value)
    if not s:
        return ""
    # float-like strings coming from Excel, e.g. '10.0'
    if s.replace(".", "", 1).isdigit():
        try:
            f = float(s)
            if f == int(f):
                return str(int(f))
        except ValueError:
            pass
    # strip leading zeros on pure integers
    if s.isdigit():
        return str(int(s))
    return s


def step_key(step_no, step_name) -> tuple:
    return (norm_step_no(step_no), norm_text(step_name))


@dataclass
class PfmeaRecord:
    source: str          # display name of the source document, e.g. 'PFMEA'
    file_name: str
    sheet: str
    row: int             # 1-based sheet row number (header = row 1)
    step_no: str
    step_name: str
    failure_mode: str
    failure_effect: str = ""
    severity: str = ""
    failure_cause: str = ""
    prevention_control: str = ""
    occurrence: str = ""
    detection_control: str = ""
    detection: str = ""
    ap: str = ""
    special_char: str = ""

    @property
    def key(self) -> tuple:
        return step_key(self.step_no, self.step_name)

    def sod_filled(self) -> bool:
        return all(str(x).strip() for x in (self.severity, self.occurrence, self.detection))

    def severity_int(self) -> Optional[int]:
        try:
            return int(float(str(self.severity).strip()))
        except (TypeError, ValueError):
            return None


@dataclass
class ControlPlanRecord:
    source: str
    file_name: str
    sheet: str
    row: int
    step_no: str
    step_name: str
    characteristic: str = ""
    special_char: str = ""
    control_method: str = ""
    control_type: str = ""      # explicit 控制类型 column value, may be empty
    evaluation: str = ""
    reaction_plan: str = ""

    @property
    def key(self) -> tuple:
        return step_key(self.step_no, self.step_name)


@dataclass
class Finding:
    check_id: str        # e.g. 'C1'
    check_name: str      # human-readable rule name
    severity: str        # 'high' | 'medium' | 'low'
    source: str          # 'PFMEA' | 'Control Plan'
    file_name: str
    sheet: str
    row: int
    step_no: str
    step_name: str
    message: str
    suggestion: str

    def location(self) -> str:
        return "%s / %s 第 %d 行" % (self.source, self.sheet, self.row)


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class CheckResult:
    pfmea_records: List[PfmeaRecord] = field(default_factory=list)
    cp_records: List[ControlPlanRecord] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)

    def counts_by_check(self) -> dict:
        counts = {}
        for f in self.findings:
            counts[f.check_id] = counts.get(f.check_id, 0) + 1
        return counts

    def counts_by_severity(self) -> dict:
        counts = {"high": 0, "medium": 0, "low": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts
