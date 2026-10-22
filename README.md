# FMEAFlow

**PFMEA 与控制计划智能关联检查工具** — 把一份 PFMEA 和它的控制计划按工序关联起来，
自动找出两份文件之间的遗漏与不一致：失效模式没有对应控制、预防/探测措施对不上、
特殊特性标记不一致、S/O/D 填了但 AP 空着、控制计划里有 PFMEA 中不存在的工序……
每个问题都标注**来源文件 + 工作表 + 确切行号**，输出 Markdown / Excel 报告供工程师复核。

纯规则引擎、确定性结果、可离线运行，不依赖任何在线服务或 AI 模型。

> ⚠️ **硬性边界**：本工具仅标记一致性问题、给出复核建议；**不评定、不批准 AP
> （行动优先级），不批准 PFMEA 或控制计划**。所有风险评定与文件批准必须由
> 具备资质的工程师人工完成。

## 检查项

| 编号 | 检查内容 |
|---|---|
| C1 | PFMEA 失效模式在控制计划中无对应控制（整工序未覆盖） |
| C2a | PFMEA 的预防/探测控制未出现在控制计划中 |
| C2b | 同一控制在两份文件中预防/探测分类不一致 |
| C3 | 特殊特性（CC/SC 等）标记在两份文件中不一致 |
| C4 | S/O/D 已填写但 AP 为空（只提示补评定，工具不代评） |
| C5 | 控制计划的行在 PFMEA 中无来源工序 |
| C6 | 同一工序号在两份文件中工序名称不一致（提示） |

详细口径见 [docs/checks.md](docs/checks.md)，列模板与列名映射见
[docs/columns.md](docs/columns.md)。

## 安装

```bash
pip install .          # 或 pip install -e .[dev] 做开发
```

需要 Python ≥ 3.9，依赖 pandas 与 openpyxl，可离线安装。

## 使用

```bash
# 基本检查（.md 出 Markdown 报告，.xlsx 出 Excel 报告）
fmeaflow check pfmea.xlsx cp.xlsx --out report.md
fmeaflow check pfmea.csv  cp.csv  --out report.xlsx --out-xlsx extra.xlsx

# 表头与内置别名对不上时，用 JSON 映射钉住列名
fmeaflow check pfmea.xlsx cp.xlsx --out report.md --mapping mapping.json

# 演示：生成一份埋了 5 类问题的示例 PFMEA/控制计划并运行检查
fmeaflow --demo
```

退出码：`0` 无问题，`2` 有问题，`1` 输入/使用错误。

输入为 .xlsx 或 .csv，两份文件按**工序号 + 工序名称**（归一化）关联；
列模板见 `examples/`（`pfmea_template.csv`、`control_plan_template.csv`、
`column_mapping.example.json`）。

## 示例输出（演示数据）

```
FMEAFlow 一致性检查完成
  PFMEA：pfmea_demo.xlsx（5 行）
  控制计划：control_plan_demo.xlsx（5 行）
  问题总数：8（高 2 / 中 5 / 低 1）
    C1 PFMEA 失效模式在控制计划中无对应控制：1
    C2a PFMEA 控制措施未出现在控制计划：2
    C2b 预防/探测分类在两份文件中不一致：1
    C3 特殊特性标记在两份文件中不一致：2
    C4 S/O/D 已填写但 AP 为空：1
    C5 控制计划行在 PFMEA 中无来源：1
```

## 项目结构

```
src/fmeaflow/   核心代码（loader / mapping / classify / checks / report / cli / demo）
tests/          pytest 测试
examples/       PFMEA / 控制计划列模板与列名映射示例
docs/           列模板、检查项与局限说明
```

## 开发

```bash
pip install -e .[dev]
pytest --cov=fmeaflow
```

## License

MIT

---

## English

**FMEAFlow** links a PFMEA with its Control Plan by process step and flags
omissions and inconsistencies between the two documents: failure modes with no
control coverage, prevention/detection controls missing or classified
differently, special-characteristic markings that disagree, rows with S/O/D
filled but AP left empty, and Control Plan rows with no PFMEA source. Every
finding cites the exact source sheet and row number, and reports are written
as Markdown or Excel.

It is a deterministic, offline rule engine — no AI, no network calls.

> ⚠️ **Hard rule**: FMEAFlow only *flags* issues and suggests what a human
> engineer should review. It **never assigns or approves AP ratings** and
> **never approves a PFMEA or a Control Plan**. All risk ratings and document
> approvals must be made by a qualified engineer.

```bash
pip install .
fmeaflow check pfmea.xlsx cp.xlsx --out report.md
fmeaflow --demo   # sample PFMEA/Control Plan pair with planted issues
```

Exit codes: `0` no findings, `2` findings present, `1` input error.
See `docs/columns.md` for the column templates and the column-mapping config.

MIT License.
