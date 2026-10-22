import pandas as pd
import pytest

from fmeaflow.loader import load_control_plan, load_pfmea

PFMEA = {
    "工序号": [10, 20],
    "工序名称": ["上料", "压装"],
    "失效模式": ["装反", "压装力不足"],
    "严重度": [7, 9],
    "现行预防控制": ["防错定位销", "压力传感器联锁"],
    "频度": [3, 4],
    "现行探测控制": ["首件检验", "在线压力监测"],
    "探测度": [4, 3],
    "AP": ["M", "H"],
    "特殊特性": ["", "CC"],
}
CP = {
    "工序号": [10],
    "工序名称": ["上料"],
    "特性": ["工件方向"],
    "控制方法": ["首件检验"],
    "控制类型": ["探测"],
}


def test_load_csv_keeps_row_numbers(tmp_path):
    p = tmp_path / "pfmea.csv"
    pd.DataFrame(PFMEA).to_csv(p, index=False)
    recs = load_pfmea(str(p))
    assert len(recs) == 2
    assert recs[0].row == 2 and recs[1].row == 3  # header is row 1
    assert recs[1].severity == "9"
    assert recs[1].special_char == "CC"
    assert recs[0].sheet == "CSV"


def test_load_xlsx(tmp_path):
    p = tmp_path / "cp.xlsx"
    pd.DataFrame(CP).to_excel(p, index=False, engine="openpyxl")
    recs = load_control_plan(str(p))
    assert len(recs) == 1
    assert recs[0].control_method == "首件检验"
    assert recs[0].row == 2


def test_english_headers_resolved(tmp_path):
    df = pd.DataFrame({
        "Step No": [10], "Failure Mode": ["wrong orientation"],
        "Severity": [7], "Occurrence": [3], "Detection": [4], "AP": ["M"],
        "Prevention Control": ["poka-yoke pin"], "Detection Control": ["first piece inspection"],
    })
    p = tmp_path / "pfmea_en.csv"
    df.to_csv(p, index=False)
    recs = load_pfmea(str(p))
    assert recs[0].failure_mode == "wrong orientation"
    assert recs[0].severity_int() == 7


def test_mapping_override(tmp_path):
    df = pd.DataFrame({"工步": [10], "失效": ["装反"], "严重度S（自定义）": [8]})
    p = tmp_path / "pfmea_custom.csv"
    df.to_csv(p, index=False)
    recs = load_pfmea(str(p), overrides={"step_no": "工步", "failure_mode": "失效",
                                         "severity": "严重度S（自定义）"})
    assert recs[0].step_no == "10"
    assert recs[0].severity == "8"


def test_missing_required_column_raises(tmp_path):
    p = tmp_path / "bad.csv"
    pd.DataFrame({"甲": [1]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        load_pfmea(str(p))
    with pytest.raises(ValueError):
        load_control_plan(str(p))


def test_blank_rows_skipped(tmp_path):
    df = pd.DataFrame(PFMEA)
    df.loc[2] = ["", "", "", "", "", "", "", "", "", ""]
    p = tmp_path / "pfmea_blank.csv"
    df.to_csv(p, index=False)
    assert len(load_pfmea(str(p))) == 2
