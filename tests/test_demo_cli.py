from fmeaflow import DISCLAIMER
from fmeaflow.checks import run_checks
from fmeaflow.cli import main
from fmeaflow.demo import write_demo_files
from fmeaflow.loader import load_control_plan, load_pfmea

EXPECTED_COUNTS = {"C1": 1, "C2a": 2, "C2b": 1, "C3": 2, "C4": 1, "C5": 1}


def test_demo_planted_issues_all_detected(tmp_path):
    pfmea_path, cp_path = write_demo_files(str(tmp_path))
    result = run_checks(load_pfmea(pfmea_path), load_control_plan(cp_path))
    counts = result.counts_by_check()
    for cid, n in EXPECTED_COUNTS.items():
        assert counts.get(cid) == n, (cid, counts)
    # every finding cites an exact row number
    assert all(f.row >= 2 for f in result.findings)


def test_cli_demo(tmp_path, capsys):
    rc = main(["--demo", "--demo-dir", str(tmp_path / "demo")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "全部 5 类预置问题" in out
    assert DISCLAIMER.split("。")[0] in out  # disclaimer printed on CLI
    assert (tmp_path / "demo" / "report.md").exists()
    assert (tmp_path / "demo" / "report.xlsx").exists()


def test_cli_check_demo_files_returns_2_and_writes_reports(tmp_path):
    pfmea_path, cp_path = write_demo_files(str(tmp_path))
    md = tmp_path / "r.md"
    rc = main(["check", pfmea_path, cp_path, "--out", str(md),
               "--out-xlsx", str(tmp_path / "r.xlsx")])
    assert rc == 2  # findings present
    text = md.read_text(encoding="utf-8")
    assert "FMEAFlow 一致性检查报告" in text
    assert "不评定、不批准 AP" in text  # disclaimer footer in report
    assert (tmp_path / "r.xlsx").exists()


def test_cli_check_missing_file_returns_1(tmp_path):
    rc = main(["check", str(tmp_path / "nope.xlsx"), str(tmp_path / "nope2.xlsx")])
    assert rc == 1
