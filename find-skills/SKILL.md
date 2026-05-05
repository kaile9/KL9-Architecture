---
name: find-skills
description: 帮助用户发现并安装 agent skills。当用户问"如何做X"、"找一个X的skill"、"是否有skill可以..."或表达延展能力兴趣时触发。目前已适配为本地 skill 生态。
---

# Find Skills

> 原版来自 Vercel Labs 开源 agent skills 生态，已适配为本地目录式 skill 系统。

## 何时使用此 Skill

当用户：
- 问 "如何做 X"，其中 X 可能已有现成 skill
- 说 "找一个 X 的 skill" 或 "是否有 skill 能做 X"
- 问 "你能做 X 吗"，其中 X 是某个专业能力
- 表达延展能力的兴趣
- 想搜索工具、模板或工作流
- 提到需要某个领域的帮助（设计、测试、部署等）

## 本地 Skill 生态说明

当前系统采用目录式 skill 管理，路径：`/AstrBot/data/skills/<skill-name>/SKILL.md`

**关键差异**：
- 本地环境不支持 `npx skills` CLI 命令
- 无法直接从 skills.sh 或 GitHub 自动安装
- 但可以手动下载、clone 或创建 skill 到该目录

**本地安装方式**：
```bash
# 方式1: 直接 clone 整个仓库
cd /AstrBot/data/skills
git clone <repo-url> <skill-name>

# 方式2: 手动创建目录
mkdir -p /AstrBot/data/skills/<skill-name>
# 然后编写 SKILL.md
```

## 帮助用户寻找 Skills

### Step 1: 理解需求

当用户询问时，确定：
1. 领域（如 React、测试、设计、部署）
2. 具体任务（如写测试、创建动画、审查 PR）
3. 是否是常见任务，存在对应 skill 的可能性

### Step 2: 检查已安装的 Skills

先查看本地已安装的 skills：
```bash
ls /AstrBot/data/skills/
```

当前已安装 skills 示例：
- `darwin-skill` — Skill 质量优化
- `file-text-extractor` — 文件文本提取
- `kailejiu-baiyueguang-perspective` — AI 认知框架
- `nuwa-skill` — 自动生成人物 Skill

### Step 3: 搜索外部 Skills

若本地没有匹配的 skill，可以：
1. 访问 https://skills.sh/ 或 https://github.com/vercel-labs/skills 搜索
2. 使用 GitHub 搜索: `site:github.com "SKILL.md" <关键词>`
3. 直接询问用户是否有具体的 GitHub 仓库链接

### Step 4: 验证质量

**推荐前必须验证**：
1. **来源声誉** — 官方源（`vercel-labs`、`anthropics`、`microsoft`）更可信
2. **GitHub stars** — 仓库 <100 stars 需谨慎对待
3. **更新时间** — 最近是否有维护

### Step 5: 展示并安装

当找到合适的 skill 时，展示给用户：
1. Skill 名称和功能说明
2. 来源和声誉
3. 安装步骤（手动 clone 或复制）
4. 学习更多链接

**如果用户确认安装，帮其执行：**
```bash
cd /AstrBot/data/skills
git clone https://github.com/<owner>/<repo>.git <skill-name>
# 或手动下载 SKILL.md 到新建目录
```

## 常见 Skill 类别

| 类别 | 示例查询 |
|------|--------|
| Web 开发 | react, nextjs, typescript, css, tailwind |
| 测试 | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| 文档 | docs, readme, changelog, api-docs |
| 代码质量 | review, lint, refactor, best-practices |
| 设计 | ui, ux, design-system, accessibility |
| 效率 | workflow, automation, git |

## 未找到时的处理

若未找到相关 skill：
1. 告知用户未找到现成 skill
2. 提供直接帮助（用通用能力解决）
3. 建议用户可以自己创建 skill

**创建新 Skill 的方法**：
```bash
mkdir -p /AstrBot/data/skills/<my-skill>
# 编写 SKILL.md，参考其他 skill 的格式
```

或使用 `nuwa-skill`（若已安装）自动生成人物/角色 skill。

## 版本

v1.0.0 — 适配本地目录式 skill 生态
