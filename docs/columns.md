# 列模板与列名映射

FMEAFlow 读取 .xlsx（openpyxl）或 .csv 文件。两份文件按 **工序号 + 工序名称**
（归一化后：去空格、数字去前导零、英文小写）关联。

## PFMEA 规范字段

| 规范字段 | 含义 | 必需 | 常见表头（自动识别） |
|---|---|---|---|
| step_no | 工序号 | 是 | 工序号、工序编号、Step No、OP |
| step_name | 工序名称 | 否 | 工序名称、过程名称、Process Step |
| failure_mode | 失效模式 | 是 | 失效模式、潜在失效模式、Failure Mode |
| failure_effect | 失效影响 | 否 | 失效影响、失效后果、Failure Effect |
| severity | 严重度 S | 否 | 严重度、S、Severity |
| failure_cause | 失效原因 | 否 | 失效原因、潜在失效原因、Failure Cause |
| prevention_control | 现行预防控制 | 否 | 现行预防控制、预防控制、Prevention Control |
| occurrence | 频度 O | 否 | 频度、O、Occurrence |
| detection_control | 现行探测控制 | 否 | 现行探测控制、探测控制、Detection Control |
| detection | 探测度 D | 否 | 探测度、D、Detection |
| ap | 行动优先级 | 否 | AP、行动优先级、Action Priority |
| special_char | 特殊特性标记 | 否 | 特殊特性、特性分类、Classification |

可直接使用的模板见 `examples/pfmea_template.csv`。

## 控制计划规范字段

| 规范字段 | 含义 | 必需 | 常见表头（自动识别） |
|---|---|---|---|
| step_no | 工序号 | 是 | 工序号、过程编号、Step No |
| step_name | 工序名称 | 否 | 工序名称、过程名称 |
| characteristic | 特性 | 否 | 特性、产品特性、过程特性、Characteristic |
| special_char | 特殊特性标记 | 否 | 特殊特性、特性分类、Classification |
| control_method | 控制方法 | 否 | 控制方法、Control Method |
| control_type | 控制类型（预防/探测） | 否 | 控制类型、Control Type |
| evaluation | 评价/测量技术 | 否 | 评价测量技术、Evaluation Technique |
| reaction_plan | 反应计划 | 否 | 反应计划、Reaction Plan |

模板见 `examples/control_plan_template.csv`。

## 自定义列名映射

表头与内置别名对不上时，用 JSON 映射文件钉住确切表头：

```bash
fmeaflow check pfmea.xlsx cp.xlsx --out report.md --mapping mapping.json
```

格式（只需写与默认不同的字段）：

```json
{
  "pfmea":        {"severity": "严重度S", "ap": "行动优先级别"},
  "control_plan": {"control_method": "控制方法（中文）"}
}
```

完整示例见 `examples/column_mapping.example.json`。

## 匹配口径说明

- 工序关联：先按（工序号， 工序名称）精确关联；名称对不上但工序号相同时，
  仍按工序号关联，并以 C6（低）提示名称不一致。
- 控制措施匹配：文本归一化后精确相等或互相包含即视为同一措施；
  一格内多个措施可用 `；`、`;`、`、`、换行分隔。
- 预防/探测分类：控制计划有「控制类型」列时以其为准；否则用关键词
  启发式（防错/联锁/治具…→预防；检验/检测/测量/抽检…→探测）判定，
  无法判定记为 unknown，不据此报 C2b。
- 特殊特性标记识别：CC、SC、◆、▼、★、● 及「关键/重要/安全/法规/特殊」
  等字样。
