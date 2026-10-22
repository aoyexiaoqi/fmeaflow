"""Demo data: a sample PFMEA / Control Plan pair with planted inconsistencies.

Planted issues (one or more per check):
  C1  step 30 焊接 has no Control Plan rows at all
  C2a PFMEA prevention controls 防错定位销 / 压力传感器联锁 missing in the CP
  C2b 计数传感器联锁 is a prevention control in the PFMEA but classified as a
      detection control in the Control Plan
  C3  step 20 marked CC in the PFMEA but not in the CP; step 40 marked SC in
      the CP but not in the PFMEA
  C4  step 30 row has S/O/D filled but AP empty
  C5  Control Plan step 50 包装 has no PFMEA source
"""
from __future__ import annotations

import os

PFMEA_HEADERS = ["工序号", "工序名称", "失效模式", "失效影响", "严重度", "失效原因",
                 "现行预防控制", "频度", "现行探测控制", "探测度", "AP", "特殊特性"]
PFMEA_ROWS = [
    [10, "上料", "工件装反", "后续压装损坏", 7, "操作员放错方向", "防错定位销", 3, "首件检验", 4, "M", ""],
    [10, "上料", "工件数量不足", "整托缺件流出", 5, "人工计数错误", "计数传感器联锁", 2, "", "", "L", ""],
    [20, "压装", "压装力不足", "轴承松动异响", 9, "设备压力波动", "压力传感器联锁", 4, "在线压力监测", 3, "H", "CC"],
    [30, "焊接", "虚焊", "焊点脱落", 8, "焊接温度不足", "焊接参数自动锁定", 5, "X光抽检", 6, "", ""],
    [40, "检测", "漏检", "不良品流出", 6, "检验员疲劳", "", 4, "自动光学检测AOI", 3, "M", ""],
]

CP_HEADERS = ["工序号", "工序名称", "特性", "特殊特性", "控制方法", "控制类型", "评价测量技术", "反应计划"]
CP_ROWS = [
    [10, "上料", "工件方向", "", "首件检验", "探测", "目视", "隔离并全检"],
    [10, "上料", "工件数量", "", "计数传感器联锁", "探测", "计数传感器", "停机排查"],
    [20, "压装", "压装力", "", "在线压力监测", "探测", "压力传感器", "停机并隔离本批"],
    [40, "检测", "外观", "SC", "自动光学检测AOI", "探测", "AOI设备", "隔离并复检"],
    [50, "包装", "标签", "", "标签目视检查", "探测", "目视", "返工"],
]


def write_demo_files(out_dir: str):
    """Write pfmea_demo.xlsx and control_plan_demo.xlsx into out_dir."""
    import pandas as pd

    os.makedirs(out_dir, exist_ok=True)
    pfmea_path = os.path.join(out_dir, "pfmea_demo.xlsx")
    cp_path = os.path.join(out_dir, "control_plan_demo.xlsx")
    pd.DataFrame(PFMEA_ROWS, columns=PFMEA_HEADERS).to_excel(pfmea_path, index=False, engine="openpyxl")
    pd.DataFrame(CP_ROWS, columns=CP_HEADERS).to_excel(cp_path, index=False, engine="openpyxl")
    return pfmea_path, cp_path
