# KL9-RHIZOME 技能书库

两种格式并存的技能书仓库：

| 格式 | 用途 | 目录结构 |
|------|------|---------|
| `.skillbook.json` | 可导入的标准化技能书（含 manifest + 概念图谱） | `de/` `en/` `fr/` `zh/` `other/` |
| `SKILL.md` | 参考技能书（kailejiu-research 直接征用，含论证结构 + 引文） | `{语言}/{书名}/SKILL.md` |

---

## 目录结构

```
skillbooks/
├── de/                          ← 德语原著
│   └── Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md
├── en/                          ← 英语原著
├── fr/                          ← 法语原著
├── zh/                          ← 中文原著
│   └── Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md
├── other/                       ← 其他语言
├── README.md
└── SKILLBOOK_STANDARD.md        ← 技能书格式规范 v1.1
```

---

## 使用

### 导入 .skillbook.json

```python
from kl9_skillbook.bridge import import_skillbook_to_graph
result = import_skillbook_to_graph("skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md")
```

### 征用 SKILL.md（kailejiu-research）

在 `dialogical_activation` 中通过技能名引用：
```
@skillbook:Brodbeck-Phaenomenologie_des_Geldes-2023 → 加载 skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md
@skillbook:Asvaghosa-Dasheng-Qixin-Lun-554 → 加载 skillbooks/zh/Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md
```

---

## 评分体系 v1.1

### 难度分 (0-100)
LLM 评估四项取均值：风格密度、信息密度、观点创新、引用密度

### 质量分 (0-100)
基于制作记录：rounds×20(≤60) + verify(0/10/20) + counter×5(≤20)

### 模型能力上限 (动态)
HLE×0.5 + Arena Overall×0.25 + Arena Creative Writing×0.25

### 语言补偿
中文模型读中文书 +3%，英文模型读中文书 −3%（同层不反超）

详见 [SKILLBOOK_STANDARD.md](SKILLBOOK_STANDARD.md)

---

## 现有藏书

| 格式 | 文件 | 语言 | 作者 | 著作 | 年份 |
|------|------|:--:|------|------|:--:|
| SKILL.md | `de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md` | DE | Brodbeck | Phänomenologie des Geldes | 2023 |
| SKILL.md | `zh/Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md` | ZH | ~Aśvaghoṣa | 大乘起信論 | ~554 |
