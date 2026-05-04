# KL9-RHIZOME 技能书标准 · Skill Book Standard v1.0

## 核心原则 · Core Principle

**技能书不是摘要。技能书是精读后的认知残留。**

技能书只能由深入阅读原著后产生——不来自二手文献，不来自 AI 摘要，不来自学术速读。每一份技能书都是一次真实的认知折叠记录，其权威性仅来源于"确实读完了整本书"这个事实。

## 目录结构 · Directory Structure

```
skillbooks/
└── {skillbook_name}/
    ├── manifest.json         # 必需：元数据（见下方规范）
    ├── SKILL.md              # 必需：人类可读描述
    ├── memory/
    │   ├── fold_nodes.json   # 必需：DualState 图节点
    │   └── fold_edges.json   # 必需：折叠关系边
    ├── graph/
    │   ├── concepts.json     # 必需：概念图谱节点
    │   └── edges.json        # 必需：谱系边 + 张力场边
    └── learner/
        ├── state.json        # 必需：难度谱系 + 后续查询
        └── tensions.json     # 可选：结构化张力留白
```

## manifest.json 规范 · Manifest Specification

```jsonc
{
  // === 必填字段 ===
  
  "skillbook_name":       "书名_作者_snake_case",       // 唯一标识
  "version":              "1.0.0",                       // 语义化版本
  "kl9_rhizome_version":  ">=1.5",                       // 兼容的最低 KL9 版本
  "architecture_version": "v1.5",                        // 生成时的架构版本号
  "llm_name":             "deepseek-v4-pro",             // 学习使用的 LLM 名称
  
  "source_text": {
    "title":    "原始书名",                               // 完整书名
    "author":   "作者名",                                // 
    "year":     2023,                                    // 出版年份
    "pages":    110,                                     // 页数（用于验证深度）
    "language": "German"                                // 原文语言
  },
  
  "author": {
    "creator":      "GitHub用户名",                      // 创建者
    "learning_date": "2026-05-05"                        // YYYY-MM-DD
  },
  
  // === 质量自述（必填） ===
  
  "quality_notes": "详细描述阅读方式、使用了几轮迭代、交叉验证方式等",

  // === 技术字段 ===
  
  "description": "一句话 + 一段话描述内容",
  "dependencies": [],                                   // 依赖的其他技能书
  "rounds_completed": 2,                               // 完成的学习轮数
  "tension_gradient_peak": "最核心张力的名称 (强度)",      // 方便导入时评估是否有价值
  "estimated_cycles_to_stability": 3                   // 预计还需几轮至稳定
}
```

### 字段校验规则

| 字段 | 规则 | 严重度 |
|------|------|--------|
| `kl9_rhizome_version` | 必须匹配当前 KL9 版本 | ❌ 阻断 |
| `architecture_version` | 必须 ≤ 当前架构版本（不可用未来版本） | ❌ 阻断 |
| `llm_name` | 必须非空（用于追溯认知偏差） | ⚠️ 警告 |
| `source_text.pages` | 必须 ≥ 50（排除短文/论文） | ⚠️ 警告 |
| `source_text.language` | 必须注明原文语言（区分原文/译本阅读） | ⚠️ 警告 |
| `quality_notes` | 必须非空（否则视为自动生成） | ❌ 阻断 |
| `rounds_completed` | 必须 ≥ 1（至少完成首轮学习） | ❌ 阻断 |

## 上传前检查清单 · Pre-Upload Checklist

- [ ] **原著通读完成**——逐页，非跳读，非摘要
- [ ] **至少完成 1 轮完整学习**——从逐章折叠到张力梯度重构
- [ ] **每个 DualState 可追溯到原文**——具体页码或段落
- [ ] **manifest.json 所有必填字段完整**
- [ ] **quality_notes 如实描述阅读方式**——是否使用了辅助工具、AI翻译等
- [ ] **无误导性简化**——概念定义不能扭曲原著核心论点
- [ ] **已在本地 KL9 实例上验证导入**——确保不破坏现有图谱

## 质量分级 · Quality Tiers

导入时会根据 manifest 信息自动评估质量等级，但不拒绝导入：

| 等级 | 条件 | 默认信任权重 |
|------|------|:---:|
| **S** | 原文精读 + ≥3 轮学习 + 交叉验证 | 1.0 |
| **A** | 原文精读 + ≥2 轮学习 | 0.8 |
| **B** | 原文精读 + 1 轮学习 | 0.6 |
| **C** | 译本阅读 或 疑似自动生成 | 0.3 |
| **D** | 字段缺失 或 源文本不明 | 0.1 |

## 禁止项 · Prohibitions

- ❌ 基于 AI 摘要/二手文献产生的技能书
- ❌ 伪造 quality_notes
- ❌ 包含未注明出处的外部内容
- ❌ 使用未来版本的 architecture_version
- ❌ 将多本书合并为一个技能书（一书一谱）

---

*"一场真实的阅读。一次真实的折叠。其他都是噪音。"*
