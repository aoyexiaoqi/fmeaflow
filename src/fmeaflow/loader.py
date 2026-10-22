"""Load PFMEA / Control Plan sheets (.xlsx via openpyxl, .csv via stdlib pandas)
into normalized records that keep the exact sheet name and 1-based row number
of every record, so findings can cite precise locations.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .mapping import (CONTROL_PLAN_FIELDS, CONTROL_PLAN_REQUIRED,
                      PFMEA_FIELDS, PFMEA_REQUIRED, resolve_columns)
from .model import ControlPlanRecord, PfmeaRecord


def _read_table(path: str, sheet: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        return df, "CSV"
    if ext in (".xlsx", ".xlsm"):
        xls = pd.ExcelFile(path, engine="openpyxl")
        sheet_name = sheet or xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str, keep_default_na=False)
        return df, sheet_name
    raise ValueError("unsupported file type %r (use .xlsx or .csv)" % ext)


def _cell(row: dict, header: Optional[str]) -> str:
    if header is None:
        return ""
    v = row.get(header, "")
    if v is None:
        return ""
    return str(v).strip()


def load_pfmea(path: str, overrides: Optional[Dict[str, str]] = None,
               sheet: Optional[str] = None) -> List[PfmeaRecord]:
    df, sheet_name = _read_table(path, sheet)
    headers = [str(c) for c in df.columns]
    cols = resolve_columns(headers, PFMEA_FIELDS, overrides)
    missing = [f for f in PFMEA_REQUIRED if cols.get(f) is None]
    if missing:
        raise ValueError(
            "PFMEA sheet %s is missing required column(s): %s (headers found: %s)"
            % (path, ", ".join(missing), ", ".join(headers)))
    file_name = os.path.basename(path)
    records: List[PfmeaRecord] = []
    for idx, (_, row) in enumerate(df.iterrows()):
        row_no = idx + 2  # header is sheet row 1
        get = lambda f: _cell(row, cols.get(f))  # noqa: E731
        rec = PfmeaRecord(
            source="PFMEA", file_name=file_name, sheet=sheet_name, row=row_no,
            step_no=get("step_no"), step_name=get("step_name"),
            failure_mode=get("failure_mode"), failure_effect=get("failure_effect"),
            severity=get("severity"), failure_cause=get("failure_cause"),
            prevention_control=get("prevention_control"),
            occurrence=get("occurrence"), detection_control=get("detection_control"),
            detection=get("detection"), ap=get("ap"), special_char=get("special_char"),
        )
        # skip fully blank rows (no step and no failure mode)
        if not rec.step_no and not rec.failure_mode:
            continue
        records.append(rec)
    return records


def load_control_plan(path: str, overrides: Optional[Dict[str, str]] = None,
                      sheet: Optional[str] = None) -> List[ControlPlanRecord]:
    df, sheet_name = _read_table(path, sheet)
    headers = [str(c) for c in df.columns]
    cols = resolve_columns(headers, CONTROL_PLAN_FIELDS, overrides)
    missing = [f for f in CONTROL_PLAN_REQUIRED if cols.get(f) is None]
    if missing:
        raise ValueError(
            "Control Plan sheet %s is missing required column(s): %s (headers found: %s)"
            % (path, ", ".join(missing), ", ".join(headers)))
    file_name = os.path.basename(path)
    records: List[ControlPlanRecord] = []
    for idx, (_, row) in enumerate(df.iterrows()):
        row_no = idx + 2
        get = lambda f: _cell(row, cols.get(f))  # noqa: E731
        rec = ControlPlanRecord(
            source="Control Plan", file_name=file_name, sheet=sheet_name, row=row_no,
            step_no=get("step_no"), step_name=get("step_name"),
            characteristic=get("characteristic"), special_char=get("special_char"),
            control_method=get("control_method"), control_type=get("control_type"),
            evaluation=get("evaluation"), reaction_plan=get("reaction_plan"),
        )
        if not rec.step_no and not rec.characteristic and not rec.control_method:
            continue
        records.append(rec)
    return records
