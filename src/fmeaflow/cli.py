"""Command line interface.

Usage:
  fmeaflow check pfmea.xlsx cp.xlsx --out report.md
  fmeaflow check pfmea.csv  cp.csv  --out report.xlsx --mapping mapping.json
  fmeaflow --demo            # generate a sample pair with planted issues and check it

Exit codes: 0 = no findings, 2 = findings present, 1 = input/usage error.
"""
from __future__ import annotations

import argparse
import os
import sys

from . import DISCLAIMER, __version__
from .checks import CHECK_NAMES, run_checks
from .loader import load_control_plan, load_pfmea
from .mapping import load_mapping_file
from .report import render_markdown, write_excel


def _print_summary(result, pfmea_name, cp_name, out_paths) -> None:
    sev = result.counts_by_severity()
    by_check = result.counts_by_check()
    print("FMEAFlow 一致性检查完成")
    print("  PFMEA：%s（%d 行）" % (pfmea_name, len(result.pfmea_records)))
    print("  控制计划：%s（%d 行）" % (cp_name, len(result.cp_records)))
    print("  问题总数：%d（高 %d / 中 %d / 低 %d）"
          % (len(result.findings), sev["high"], sev["medium"], sev["low"]))
    for cid in sorted(CHECK_NAMES):
        if by_check.get(cid):
            print("    %s %s：%d" % (cid, CHECK_NAMES[cid], by_check[cid]))
    for p in out_paths:
        print("  报告已写入：%s" % p)
    print("")
    print(DISCLAIMER)


def _write_reports(result, pfmea_path, cp_path, out, out_xlsx):
    written = []
    if out:
        if out.lower().endswith((".xlsx", ".xlsm")):
            write_excel(result, out, pfmea_path, cp_path)
        else:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(render_markdown(result, pfmea_path, cp_path))
        written.append(out)
    if out_xlsx:
        write_excel(result, out_xlsx, pfmea_path, cp_path)
        written.append(out_xlsx)
    return written


def _do_check(pfmea_path, cp_path, mapping_path=None, out=None, out_xlsx=None,
              pfmea_sheet=None, cp_sheet=None) -> int:
    mapping = load_mapping_file(mapping_path) if mapping_path else {}
    pfmea = load_pfmea(pfmea_path, overrides=mapping.get("pfmea"), sheet=pfmea_sheet)
    cp = load_control_plan(cp_path, overrides=mapping.get("control_plan"), sheet=cp_sheet)
    result = run_checks(pfmea, cp)
    written = _write_reports(result, pfmea_path, cp_path, out, out_xlsx)
    _print_summary(result, pfmea_path, cp_path, written)
    return 2 if result.findings else 0


def _do_demo(demo_dir: str) -> int:
    from .demo import write_demo_files

    pfmea_path, cp_path = write_demo_files(demo_dir)
    print("演示文件已生成：%s, %s" % (pfmea_path, cp_path))
    result = run_checks(load_pfmea(pfmea_path), load_control_plan(cp_path))
    md_out = os.path.join(demo_dir, "report.md")
    xlsx_out = os.path.join(demo_dir, "report.xlsx")
    written = _write_reports(result, pfmea_path, cp_path, md_out, xlsx_out)
    _print_summary(result, pfmea_path, cp_path, written)
    expected = {"C1", "C2a", "C2b", "C3", "C4", "C5"}
    found = set(result.counts_by_check())
    missing = expected - found
    if missing:
        print("警告：以下预置问题未被检出：%s" % ", ".join(sorted(missing)))
        return 2
    print("演示验证：全部 5 类预置问题（C1/C2a/C2b/C3/C4/C5）均已检出。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fmeaflow",
        description="PFMEA 与控制计划一致性关联检查（仅标记问题，不评定/不批准 AP）")
    parser.add_argument("--version", action="version", version="fmeaflow %s" % __version__)
    parser.add_argument("--demo", action="store_true",
                        help="生成带预置问题的示例 PFMEA/控制计划并运行检查")
    parser.add_argument("--demo-dir", default="fmeaflow_demo",
                        help="--demo 的输出目录（默认 fmeaflow_demo）")
    sub = parser.add_subparsers(dest="command")
    p_check = sub.add_parser("check", help="检查一对 PFMEA 与控制计划文件")
    p_check.add_argument("pfmea", help="PFMEA 文件（.xlsx 或 .csv）")
    p_check.add_argument("control_plan", help="控制计划文件（.xlsx 或 .csv）")
    p_check.add_argument("--out", default="fmeaflow_report.md",
                         help="报告路径：.md 写 Markdown，.xlsx 写 Excel（默认 fmeaflow_report.md）")
    p_check.add_argument("--out-xlsx", default=None,
                         help="额外再写一份 Excel 报告到该路径")
    p_check.add_argument("--mapping", default=None,
                         help="列名映射 JSON 文件（见 docs/columns.md）")
    p_check.add_argument("--pfmea-sheet", default=None, help="PFMEA 工作表名（默认第一个）")
    p_check.add_argument("--cp-sheet", default=None, help="控制计划工作表名（默认第一个）")
    sub.add_parser("demo", help="同 --demo")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.demo or args.command == "demo":
            return _do_demo(args.demo_dir)
        if args.command == "check":
            return _do_check(args.pfmea, args.control_plan, mapping_path=args.mapping,
                             out=args.out, out_xlsx=args.out_xlsx,
                             pfmea_sheet=args.pfmea_sheet, cp_sheet=args.cp_sheet)
        parser.print_help()
        return 1
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
