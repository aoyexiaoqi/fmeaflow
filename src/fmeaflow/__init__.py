"""FMEAFlow — PFMEA 与控制计划一致性关联检查工具。

FMEAFlow links a PFMEA with its Control Plan and flags omissions and
inconsistencies between them. It only *flags* issues for a human engineer
to review: it never assigns or approves AP ratings and never approves a
PFMEA or a Control Plan.
"""

__version__ = "0.1.0"

DISCLAIMER_ZH = (
    "本工具仅自动标记 PFMEA 与控制计划之间的一致性问题，供工程师复核参考；"
    "不评定、不批准 AP（行动优先级），不批准 PFMEA 或控制计划。"
    "所有风险评定与文件批准必须由具备资质的工程师人工完成。"
)
DISCLAIMER_EN = (
    "This tool only flags consistency issues between a PFMEA and a Control Plan "
    "for engineer review. It never assigns or approves AP ratings and never "
    "approves a PFMEA or Control Plan. All risk ratings and document approvals "
    "must be made by a qualified engineer."
)
DISCLAIMER = DISCLAIMER_ZH + " " + DISCLAIMER_EN
