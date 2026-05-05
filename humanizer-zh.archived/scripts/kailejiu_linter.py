#!/usr/bin/env python3
"""
kailejiu_linter.py —— 开了玖文本抛光器配套检测脚本。

用途：对文本进行后置扫描，检测 AI 生成痕迹、保护区侵蚀、强化区可优化点，
      输出极简检测报告。

用法：
    python kailejiu_linter.py --text "待检测的文本内容"
    python kailejiu_linter.py --file input.txt
    echo "文本" | python kailejiu_linter.py --stdin

输出：结构化检测报告（markdown），含行号定位、问题引用、简易评分。
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    category: str        # 大类：清除区 / 保护区 / 强化区
    subcategory: str     # 子类：连接词入侵 / 人称呼告 / ...
    severity: str        # 严重 / 一般 / 提示
    line: int            # 行号（1-based）
    snippet: str         # 引用片段（截断至 80 字符）
    detail: str = ""     # 补充说明


@dataclass
class Report:
    findings: List[Finding] = field(default_factory=list)
    score: int = 50
    score_detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 清除区模式定义
# ---------------------------------------------------------------------------

# 模式 A：人称与呼告入侵
PATTERN_A_PERSON = [
    (r'我们希望', '人称呼告', '严重'),
    (r'我认为', '人称呼告', '严重'),
    (r'在我看来', '人称呼告', '严重'),
    (r'我们要', '人称呼告', '严重'),
    (r'我们可以(看到|认为|理解)', '人称呼告', '严重'),
    (r'让我们', '人称呼告', '严重'),
    (r'你可以看到', '人称呼告', '严重'),
    (r'你或许会', '人称呼告', '严重'),
    (r'值得注意的是', '呼告入侵', '严重'),
    (r'需要指出的是', '呼告入侵', '一般'),
    (r'应该看到', '呼告入侵', '一般'),
    (r'我建议', '人称呼告', '严重'),
    (r'我们不妨', '人称呼告', '严重'),
    (r'我们来', '人称呼告', '严重'),
    (r'读者可以', '读者呼告', '一般'),
    (r'读者不妨', '读者呼告', '一般'),
]

# 模式 B：连接词与过渡句入侵
PATTERN_B_CONNECTOR = [
    (r'此外，|此外,', '连接词', '一般'),
    (r'而且，|而且,', '连接词', '一般'),
    (r'与此同时，|与此同时,', '连接词', '一般'),
    (r'更重要的是，|更重要的是,', '连接词', '严重'),
    (r'无独有偶', '连接词', '严重'),
    (r'不可否认的是', '连接词', '严重'),
    (r'从另一个角度(来看|看)', '连接词', '一般'),
    (r'基于此', '连接词', '一般'),
    (r'归根结底', '连接词', '一般'),
    (r'说到底', '连接词', '一般'),
    (r'首先.*其次.*最后', '三段式连接', '严重'),
    (r'一方面.*另一方面', '二段式连接', '一般'),
    (r'综上所述', '总结闭环', '严重'),
    (r'总而言之', '总结闭环', '严重'),
    (r'通过以上分析', '总结闭环', '严重'),
    (r'以上分析表明', '总结闭环', '严重'),
    (r'不难发现', '总结过渡', '一般'),
    (r'由此可见', '总结过渡', '一般'),
]

# 模式 C2：否定式排比
PATTERN_C2_NEGATIVE_PARALLEL = [
    (r'不仅仅是.{1,30}，?而是', '否定式排比', '一般'),
    (r'不是.{1,30}，?而是', '否定式排比', '一般'),
    (r'不只.{1,30}，?更是', '否定式排比', '一般'),
]

# 模式 C3：破折号堆叠（同一句中 ≥3 个 ——）
# 此模式用函数检测，不在此处列正则

# 模式 D：模糊归因
PATTERN_D_ATTRIBUTION = [
    (r'专家认为', '模糊归因', '一般'),
    (r'行业报告显示', '模糊归因', '严重'),
    (r'观察者指出', '模糊归因', '一般'),
    (r'一些批评者认为', '模糊归因', '一般'),
    (r'多位学者指出', '模糊归因', '一般'),
    (r'相关研究(表明|显示)', '模糊归因', '一般'),
    (r'多数分析认为', '模糊归因', '一般'),
    (r'有评论认为', '模糊归因', '一般'),
    (r'据报道', '模糊归因', '一般'),
    (r'有数据显示', '模糊归因', '一般'),
    (r'众所周知', '模糊归因', '一般'),
    (r'普遍认为', '模糊归因', '一般'),
]

# 模式 E1：积极结论
PATTERN_E1_POSITIVE = [
    (r'充满希望', '积极结论', '一般'),
    (r'激动人心的时代', '积极结论', '严重'),
    (r'代表了正确方向', '积极结论', '严重'),
    (r'美好的未来', '积极结论', '一般'),
    (r'深刻的情感共鸣', '积极结论', '一般'),
    (r'思想启迪', '积极结论', '一般'),
    (r'值得期待', '积极结论', '一般'),
    (r'具有重要意义', '积极结论', '一般'),
    (r'为我们提供了宝贵的', '积极结论', '一般'),
    (r'深刻揭示', '积极结论', '一般'),
    (r'闪耀着.*光芒', '积极结论', '严重'),
    (r'无疑将', '积极结论', '一般'),
]

# 模式 E2：知识截止日期免责
PATTERN_E2_DISCLAIMER = [
    (r'截至我的知识(更新|截止)', '知识免责', '严重'),
    (r'基于(我的|可用)信息', '知识免责', '严重'),
    (r'在我(所掌握|所能获取)的(资料|信息|数据)', '知识免责', '严重'),
    (r'根据.*训练数据', '知识免责', '严重'),
    (r'我的知识库', '知识免责', '严重'),
]

# 模式 E3：谄媚语气
PATTERN_E3_FLATTERY = [
    (r'好问题[!！]', '谄媚语气', '严重'),
    (r'您说得完全正确', '谄媚语气', '严重'),
    (r'这是一个深刻的洞察', '谄媚语气', '严重'),
    (r'非常精彩的(提问|问题|观点)', '谄媚语气', '严重'),
    (r'我很高兴您', '谄媚语气', '严重'),
    (r'感谢您的(提问|问题)', '谄媚语气', '一般'),
    (r'很有趣的(问题|角度|观点)', '谄媚语气', '一般'),
    (r'您的洞察力', '谄媚语气', '严重'),
]

# 模式 E4：填充短语
PATTERN_E4_FILLER = [
    (r'为了实现这一目标', '填充短语', '一般'),
    (r'在这个时间点', '填充短语', '一般'),
    (r'值得注意的是数据显示', '填充短语', '一般'),
    (r'系统具有处理的能力', '填充短语', '一般'),
    (r'可以潜在地可能被认为', '填充短语', '严重'),
    (r'具有.*的能力', '填充短语', '一般'),
    (r'在.*的背景下', '填充短语', '一般'),
    (r'在某种程度上', '填充短语', '一般'),
    (r'在很大程度(上|地)', '填充短语', '一般'),
    (r'作为一个整体', '填充短语', '一般'),
    (r'总的来说', '填充短语', '一般'),
    (r'需要强调的是', '填充短语', '一般'),
    (r'必须承认', '填充短语', '一般'),
]

# 模式 F：格式入侵
PATTERN_F_FORMAT = [
    (r'[\U0001F300-\U0001F9FF]', '表情符号', '严重'),   # emoji range
    (r'[\u2600-\u27BF]', '表情符号', '严重'),            # misc symbols
    (r'[""]', '英文弯引号', '一般'),                      # curly quotes
    (r'\*\*[^*]{1,60}\*\*', '粗体使用', '一般'),         # bold text (to be counted)
]

# ---------------------------------------------------------------------------
# 保护区检测定义
# ---------------------------------------------------------------------------

PERSON_PRONOUNS = r'(?<![「『])[我我]们?|你[们们]?|咱[们们]?(?![」』])'
# 简化：检测行首/非引文内的人称代词（引文内保留）
# 实际实现中逐行扫描，若行中无「」则全部检测

SUMMARY_CLOSURE = [
    (r'综上所述', '总结闭环侵犯悬置结尾'),
    (r'总而言之', '总结闭环侵犯悬置结尾'),
    (r'通过以上分析', '总结闭环侵犯悬置结尾'),
    (r'至此，?[我我们]们?可以得出结论', '总结闭环侵犯悬置结尾'),
    (r'因此，?这部作品', '因果闭环侵犯悬置结尾'),
]

# ---------------------------------------------------------------------------
# 强化区检测定义
# ---------------------------------------------------------------------------

QUOTATION_PATTERN = r'[「『][^」』]+[」』]'
QUESTION_ENDING = re.compile(r'[？?]\s*$')
PARADOX_INDICATORS = [r'悖论', r'矛盾的是', r'未完成', r'悬置', r'仍是问题']


# ---------------------------------------------------------------------------
# 核心检测逻辑
# ---------------------------------------------------------------------------

def scan_line(line: str, line_no: int, patterns: list, category: str) -> List[Finding]:
    """对单行文本执行一组正则匹配，返回 Findings 列表。"""
    results = []
    for pat, subcat, sev in patterns:
        for m in re.finditer(pat, line):
            start = max(m.start() - 10, 0)
            end = min(m.end() + 10, len(line))
            snippet = line[start:end].strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + '...'
            results.append(Finding(
                category=category,
                subcategory=subcat,
                severity=sev,
                line=line_no,
                snippet=snippet,
            ))
    return results


def detect_dash_abuse(lines: List[str]) -> List[Finding]:
    """检测破折号堆叠：同一句中 ≥3 个 '——'。"""
    results = []
    for i, line in enumerate(lines, 1):
        # 按句号/问号/感叹号分句
        sentences = re.split(r'[。！？!?]', line)
        for sent in sentences:
            count = sent.count('——')
            if count >= 3:
                snippet = sent.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + '...'
                results.append(Finding(
                    category='清除区',
                    subcategory='破折号堆叠',
                    severity='一般',
                    line=i,
                    snippet=snippet,
                    detail=f'单句内出现 {count} 个破折号',
                ))
    return results


def detect_triple_list(lines: List[str]) -> List[Finding]:
    """检测三段式法则：连续三个分号/顿号/逗号分隔的并列项，或三连项目符号。"""
    results = []
    # 三连顿号分隔
    triple_dun = re.compile(r'([^、]+)、([^、]+)、([^、]+)')
    # 连续三行以 - 或 · 或 1. 开头的列表项
    for i in range(len(lines) - 2):
        l1, l2, l3 = lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()
        if all(re.match(r'^[-·•]', l) for l in [l1, l2, l3]):
            results.append(Finding(
                category='清除区',
                subcategory='三段式列表',
                severity='一般',
                line=i + 1,
                snippet=f'{l1[:30]} | {l2[:30]} | {l3[:30]}',
                detail='连续三行项目符号列表',
            ))
    # 文本内的三连项（如"记忆、时间与道德"）
    # triple_dun 匹配在 scan_line 中已通过模式 B 部分覆盖，但可细化
    for i, line in enumerate(lines, 1):
        for m in triple_dun.finditer(line):
            snippet = m.group(0)[:80]
            results.append(Finding(
                category='清除区',
                subcategory='三段式列举',
                severity='一般',
                line=i,
                snippet=snippet,
            ))
    return results


def detect_bold_abuse(lines: List[str]) -> List[Finding]:
    """检测粗体堆叠：同一段落（非空行分隔）内 ≥2 处 **...**。"""
    results = []
    paragraph = []
    para_start_line = 0
    for i, line in enumerate(lines, 1):
        if line.strip() == '':
            if paragraph:
                bold_count = sum(len(re.findall(r'\*\*[^*]+\*\*', l)) for l in paragraph)
                if bold_count >= 2:
                    results.append(Finding(
                        category='清除区',
                        subcategory='粗体堆叠',
                        severity='一般',
                        line=para_start_line,
                        snippet=f'段落内 {bold_count} 处粗体使用',
                    ))
                paragraph = []
            continue
        if not paragraph:
            para_start_line = i
        paragraph.append(line)
    # 处理最后一段
    if paragraph:
        bold_count = sum(len(re.findall(r'\*\*[^*]+\*\*', l)) for l in paragraph)
        if bold_count >= 2:
            results.append(Finding(
                category='清除区',
                subcategory='粗体堆叠',
                severity='一般',
                line=para_start_line,
                snippet=f'段落内 {bold_count} 处粗体使用',
            ))
    return results


def check_protection_zone(lines: List[str]) -> List[Finding]:
    """保护区检查：人称代词侵犯、总结式闭环侵犯悬置结尾。"""
    results = []

    # 检查是否在非引文语境下出现人称代词
    for i, line in enumerate(lines, 1):
        # 提取引文外的部分：去除「」内的内容
        stripped = re.sub(r'[「『][^」』]*[」』]', '', line)
        # 检查人称代词
        pronoun_matches = re.findall(r'(我们?|你们?|咱[们们]?)', stripped)
        for pm in pronoun_matches:
            if pm:  # 排除空匹配
                results.append(Finding(
                    category='保护区',
                    subcategory='人称代词侵犯',
                    severity='严重',
                    line=i,
                    snippet=line.strip()[:80],
                    detail=f'非引文语境中出现「{pm}」',
                ))
                break  # 每行只报一次

    # 检查结尾是否出现总结式闭环
    if lines:
        # 检查最后 3 行
        last_few = lines[-3:] if len(lines) >= 3 else lines
        for pat, subcat in SUMMARY_CLOSURE:
            for j, line in enumerate(last_few):
                if re.search(pat, line):
                    results.append(Finding(
                        category='保护区',
                        subcategory=subcat,
                        severity='严重',
                        line=len(lines) - len(last_few) + j + 1,
                        snippet=line.strip()[:80],
                    ))
    return results


def check_reinforcement_zone(lines: List[str]) -> List[Finding]:
    """强化区提示：引文后是否有操作、结尾是否悬置。"""
    results = []

    # 检查直接引文（带「」或『』）
    for i, line in enumerate(lines, 1):
        has_quote = bool(re.search(QUOTATION_PATTERN, line))
        if has_quote:
            # 检查引文后是否有操作：不是"这说明了""这意味着"等平淡概括
            if re.search(r'(这说明|这意味着|这揭示|这反映|这表明)', line):
                results.append(Finding(
                    category='强化区',
                    subcategory='引文操作不足',
                    severity='提示',
                    line=i,
                    snippet=line.strip()[:80],
                    detail='引文后仅做平淡概括，建议改为反转/扩展/强制嫁接',
                ))
            else:
                results.append(Finding(
                    category='强化区',
                    subcategory='引文存在',
                    severity='提示',
                    line=i,
                    snippet=line.strip()[:80],
                    detail='请确认引文后是否已执行操作（反转/扩展/嫁接）',
                ))

    # 检查结尾是否悬置
    if lines:
        last_meaningful = ''
        for line in reversed(lines):
            stripped = line.strip()
            if stripped:
                last_meaningful = stripped
                break

        if last_meaningful:
            is_question = bool(QUESTION_ENDING.search(last_meaningful))
            has_paradox = any(re.search(p, last_meaningful) for p in PARADOX_INDICATORS)
            if not is_question and not has_paradox:
                results.append(Finding(
                    category='强化区',
                    subcategory='结尾未悬置',
                    severity='提示',
                    line=len(lines),
                    snippet=last_meaningful[:80],
                    detail='结尾未以问号或悖论收尾，建议改为开放问题、悖论或反问',
                ))
            elif is_question:
                results.append(Finding(
                    category='强化区',
                    subcategory='结尾悬置（已满足）',
                    severity='提示',
                    line=len(lines),
                    snippet=last_meaningful[:80],
                    detail='结尾以问号收尾，符合悬置要求',
                ))

    return results


# ---------------------------------------------------------------------------
# 评分逻辑
# ---------------------------------------------------------------------------

def calculate_score(findings: List[Finding]) -> Tuple[int, dict]:
    """简易评分：从 50 分起扣。"""
    base = 50
    detail = {'严重扣分': 0, '一般扣分': 0, '提示': 0}

    for f in findings:
        if f.category == '保护区' and f.severity == '严重':
            base -= 5
            detail['严重扣分'] += 5
        elif f.category == '清除区' and f.severity == '严重':
            base -= 3
            detail['严重扣分'] += 3
        elif f.category == '清除区' and f.severity == '一般':
            base -= 1
            detail['一般扣分'] += 1
        elif f.category == '强化区' and f.severity == '提示':
            detail['提示'] += 1
            # 提示不扣分

    return max(base, 0), detail


# ---------------------------------------------------------------------------
# 全量扫描
# ---------------------------------------------------------------------------

def lint_text(text: str) -> Report:
    """对完整文本执行全量扫描，返回 Report。"""
    lines = text.split('\n')
    report = Report()

    # ---- 清除区扫描 ----
    all_clear_patterns = []
    for entry in PATTERN_A_PERSON:
        all_clear_patterns.append(entry)
    for entry in PATTERN_B_CONNECTOR:
        all_clear_patterns.append(entry)
    for entry in PATTERN_C2_NEGATIVE_PARALLEL:
        all_clear_patterns.append(entry)
    for entry in PATTERN_D_ATTRIBUTION:
        all_clear_patterns.append(entry)
    for entry in PATTERN_E1_POSITIVE:
        all_clear_patterns.append(entry)
    for entry in PATTERN_E2_DISCLAIMER:
        all_clear_patterns.append(entry)
    for entry in PATTERN_E3_FLATTERY:
        all_clear_patterns.append(entry)
    for entry in PATTERN_E4_FILLER:
        all_clear_patterns.append(entry)
    for entry in PATTERN_F_FORMAT:
        all_clear_patterns.append(entry)

    for i, line in enumerate(lines, 1):
        report.findings.extend(scan_line(line, i, all_clear_patterns, '清除区'))

    # 破折号堆叠
    report.findings.extend(detect_dash_abuse(lines))

    # 三段式列表
    report.findings.extend(detect_triple_list(lines))

    # 粗体堆叠
    report.findings.extend(detect_bold_abuse(lines))

    # ---- 保护区扫描 ----
    report.findings.extend(check_protection_zone(lines))

    # ---- 强化区扫描 ----
    report.findings.extend(check_reinforcement_zone(lines))

    # ---- 评分 ----
    report.score, report.score_detail = calculate_score(report.findings)

    return report


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def format_report(report: Report) -> str:
    """将 Report 格式化为冷感检测报告。"""
    lines_out = []
    lines_out.append('=' * 48)
    lines_out.append('  开了玖文本抛光器 · 检测报告')
    lines_out.append('=' * 48)
    lines_out.append('')

    # 评分
    grade = (
        '锋利' if report.score >= 45 else
        '可用' if report.score >= 35 else
        '需重铸'
    )
    lines_out.append(f'估分：{report.score}/50  ({grade})')
    if report.score_detail.get('严重扣分'):
        lines_out.append(f'  严重项扣分：-{report.score_detail["严重扣分"]}')
    if report.score_detail.get('一般扣分'):
        lines_out.append(f'  一般项扣分：-{report.score_detail["一般扣分"]}')
    if report.score_detail.get('提示'):
        lines_out.append(f'  强化提示（不扣分）：{report.score_detail["提示"]} 条')
    lines_out.append('')

    # 分组输出
    categories_order = ['保护区', '清除区', '强化区']
    for cat in categories_order:
        cat_findings = [f for f in report.findings if f.category == cat]
        if not cat_findings:
            lines_out.append(f'## {cat}')
            lines_out.append('  (未检出)')
            lines_out.append('')
            continue

        lines_out.append(f'## {cat}  [{len(cat_findings)} 条]')
        # 按子类聚合
        by_subcat: dict = {}
        for f in cat_findings:
            key = (f.subcategory, f.severity)
            by_subcat.setdefault(key, []).append(f)

        for (subcat, sev), items in by_subcat.items():
            sev_mark = '!!' if sev == '严重' else ('!' if sev == '一般' else '?')
            lines_out.append(f'  {sev_mark} {subcat} ×{len(items)}')
            for item in items[:5]:  # 每子类最多展示 5 条
                lines_out.append(f'    L{item.line:03d} | {item.snippet}')
                if item.detail:
                    lines_out.append(f'          > {item.detail}')
            if len(items) > 5:
                lines_out.append(f'    ... 另有 {len(items) - 5} 条，略')
        lines_out.append('')

    if report.score < 35:
        lines_out.append('---')
        lines_out.append('建议：分数过低，请返回 kailejiu 预思考层重新生成，而非仅靠抛光。')
        lines_out.append('')

    lines_out.append('=' * 48)
    return '\n'.join(lines_out)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='开了玖文本抛光器配套检测脚本 —— 检测 AI 生成痕迹与风格侵蚀',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  python kailejiu_linter.py --text "值得注意的是，这部作品……"
  python kailejiu_linter.py --file input.txt
  cat essay.txt | python kailejiu_linter.py --stdin
        ''',
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--text', '-t', type=str, help='直接传入待检测文本')
    group.add_argument('--file', '-f', type=str, help='从文件读取待检测文本')
    group.add_argument('--stdin', '-s', action='store_true', help='从标准输入读取')

    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f'错误：文件不存在 —— {args.file}', file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f'错误：读取文件失败 —— {e}', file=sys.stderr)
            sys.exit(1)
    elif args.stdin:
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    if not text.strip():
        print('错误：输入文本为空', file=sys.stderr)
        sys.exit(1)

    report = lint_text(text)
    print(format_report(report))


if __name__ == '__main__':
    main()
