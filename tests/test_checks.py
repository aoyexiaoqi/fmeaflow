from fmeaflow.checks import run_checks
from fmeaflow.model import ControlPlanRecord, PfmeaRecord


def pf(row=2, step_no="10", step_name="上料", fm="装反", s="7", prev="防错定位销",
       o="3", det="首件检验", d="4", ap="M", sc=""):
    return PfmeaRecord(source="PFMEA", file_name="p.xlsx", sheet="S1", row=row,
                       step_no=step_no, step_name=step_name, failure_mode=fm,
                       severity=s, prevention_control=prev, occurrence=o,
                       detection_control=det, detection=d, ap=ap, special_char=sc)


def cp(row=2, step_no="10", step_name="上料", char="方向", sc="",
       method="首件检验", ctype="探测"):
    return ControlPlanRecord(source="Control Plan", file_name="c.xlsx", sheet="S1",
                             row=row, step_no=step_no, step_name=step_name,
                             characteristic=char, special_char=sc,
                             control_method=method, control_type=ctype)


def ids(result):
    return [f.check_id for f in result.findings]


def test_clean_pair_no_findings():
    pfmea = [pf(prev="防错定位销", det="首件检验")]
    plan = [cp(method="防错定位销", ctype="预防"), cp(row=3, method="首件检验", ctype="探测")]
    assert run_checks(pfmea, plan).findings == []


def test_c1_no_cp_coverage():
    result = run_checks([pf(step_no="30", step_name="焊接")], [])
    assert ids(result) == ["C1"]
    f = result.findings[0]
    assert f.row == 2 and f.source == "PFMEA"


def test_c1_and_c5_together_when_steps_disjoint():
    result = run_checks([pf(step_no="30", step_name="焊接")], [cp()])
    assert sorted(ids(result)) == ["C1", "C5"]


def test_c2a_missing_prevention_control():
    result = run_checks([pf()], [cp(method="首件检验", ctype="探测")])
    assert "C2a" in ids(result)
    msgs = [f.message for f in result.findings if f.check_id == "C2a"]
    assert any("防错定位销" in m for m in msgs)


def test_c2b_classification_mismatch():
    result = run_checks([pf(prev="计数传感器联锁", det="")],
                        [cp(method="计数传感器联锁", ctype="探测")])
    assert ids(result) == ["C2b"]


def test_c2_skipped_when_step_uncovered():
    # whole step uncovered -> only C1 + C4-type checks, no C2 noise
    result = run_checks([pf(step_no="99", step_name="其他")], [])
    assert "C2a" not in ids(result) and "C1" in ids(result)


def test_c3_pfmea_sc_not_in_cp():
    result = run_checks([pf(sc="CC")],
                        [cp(method="防错定位销", ctype="预防"), cp(row=3)])
    assert "C3" in ids(result)


def test_c3_cp_sc_not_in_pfmea():
    result = run_checks([pf()], [cp(sc="SC", method="防错定位销", ctype="预防"),
                                 cp(row=3)])
    assert "C3" in ids(result)


def test_c4_sod_filled_ap_empty():
    result = run_checks([pf(ap="")],
                        [cp(method="防错定位销", ctype="预防"), cp(row=3)])
    assert ids(result) == ["C4"]


def test_c4_not_triggered_when_sod_incomplete():
    result = run_checks([pf(ap="", d="")],
                        [cp(method="防错定位销", ctype="预防"), cp(row=3)])
    assert result.findings == []


def test_c5_cp_without_pfmea():
    result = run_checks([pf()], [cp(), cp(row=3, step_no="50", step_name="包装",
                                          method="标签目视检查")])
    c5 = [f for f in result.findings if f.check_id == "C5"]
    assert len(c5) == 1 and c5[0].step_no == "50"


def test_c6_step_name_mismatch_and_still_linked():
    result = run_checks([pf(step_name="上料")],
                        [cp(step_name="上料工序", method="防错定位销", ctype="预防"),
                         cp(row=3, step_name="上料工序")])
    assert "C6" in ids(result)
    assert "C1" not in ids(result)  # linked by step number despite name drift


def test_high_severity_escalation():
    result = run_checks([pf(s="9", step_no="30", step_name="焊接", ap="H")], [])
    assert result.findings[0].severity == "high"
