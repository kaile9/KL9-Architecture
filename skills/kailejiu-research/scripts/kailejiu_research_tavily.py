#!/usr/bin/env python3
"""
kailejiu-research-tavily: 精确文献检索模块
为 KL9-RHIZOME 提供外部文献溯源能力

设计原则：
- 只检索、不评价
- 返回原始文本片段 + 精确来源
- 不编造页码，只报数据源实际提供的
"""

import os
import json
import urllib.request
import ssl
from typing import List, Dict, Optional

ORIGINAL_LANGUAGE_MAP = {
    # 法语
    "福柯": "fr", "Foucault": "fr", "德里达": "fr", "Derrida": "fr",
    "德勒兹": "fr", "Deleuze": "fr", "鲍德里亚": "fr", "Baudrillard": "fr",
    "萨特": "fr", "Sartre": "fr", "加缪": "fr", "Camus": "fr",
    # 德语
    "海德格尔": "de", "Heidegger": "de", "康德": "de", "Kant": "de",
    "黑格尔": "de", "Hegel": "de", "马克思": "de", "Marx": "de",
    "尼采": "de", "Nietzsche": "de", "维特根斯坦": "de", "Wittgenstein": "de",
    "阿多诺": "de", "Adorno": "de", "霍克海默": "de", "Horkheimer": "de",
    "哈贝马斯": "de", "Habermas": "de", "本雅明": "de", "Benjamin": "de",
    # 意大利语
    "阿甘本": "it", "Agamben": "it", "埃柯": "it", "Eco": "it",
    # 拉丁语
    "奥古斯丁": "la", "Augustine": "la", "阿奎那": "la", "Aquinas": "la",
    # 英语（但需注意英美学者的著作可能先用英语写）
    "罗尔斯": "en", "Rawls": "en", "齐泽克": "sl", "Zizek": "sl",
    # 中文
    "梁漱溟": "zh", "牟宗三": "zh", "费孝通": "zh",
}

TAVILY_API = "https://api.tavily.com/search"
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def search(query: str, max_results: int = 5, search_depth: str = "advanced",
           include_domains: Optional[List[str]] = None,
           exclude_domains: Optional[List[str]] = None,
           days: Optional[int] = None) -> Dict:
    """调用 Tavily 搜索 API，返回清洁文本结果。"""
    if not TAVILY_KEY:
        return {"error": "TAVILY_API_KEY not set"}
    
    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": False,
        "include_raw_content": True,
    }
    if include_domains: payload["include_domains"] = include_domains
    if exclude_domains: payload["exclude_domains"] = exclude_domains
    if days: payload["days"] = days
    
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(TAVILY_API, data=body,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=CTX)
        data = json.loads(resp.read().decode("utf-8"))
        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "raw_content": r.get("raw_content", ""),
            })
        return {"query": query, "results": results,
                "images": data.get("images", []),
                "response_time": data.get("response_time", 0), "status": "ok"}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}


def _infer_language_from_graph(author: str, title: str) -> Optional[str]:
    """预留接口：从 kailejiu-graph 查询作品元数据
    当前返回 None，后续接入 graph 数据库后实现
    """
    return None


def _infer_language_heuristic(author: str) -> Optional[str]:
    """基于作者国籍/传统的启发式语言推断
    用于 ORIGINAL_LANGUAGE_MAP 未覆盖的作者
    """
    # 东亚学者默认中文
    if any(char in author for char in "中日韩越"):
        return "zh"
    # 俄语系（托尔斯泰、陀思妥耶夫斯基等）
    if any(name in author for name in ["陀", "托尔斯", "陀思", "契诃", "普希"]):
        return "ru"
    # 默认无法推断
    return None


def search_book(author: str, title: str, chapter: Optional[str] = None,
                year: Optional[str] = None, language: Optional[str] = None,
                max_results: int = 5) -> Dict:
    """书籍专用搜索，自动构建最优查询 + 学术域名过滤。"""
    if language is None:
        # 优先从 ORIGINAL_LANGUAGE_MAP 查找
        language = ORIGINAL_LANGUAGE_MAP.get(author)
        if not language:
            # Fallback: 尝试从 kailejiu-graph 查询（预留接口）
            language = _infer_language_from_graph(author, title)
        if not language:
            # 最终 fallback: 基于作者国籍的启发式规则
            language = _infer_language_heuristic(author)
        if not language:
            language = "zh"  # 最后默认

    parts = [author, title]
    if chapter: parts.append(chapter)
    if year: parts.append(year)
    lang_hint = {
        "fr": "法语原版 original French edition",
        "zh": "中译本 中文翻译",
        "en": "English original edition",
        "de": "德语原版 original German Ausgabe",
        "it": "意大利语原版 edizione originale italiana",
        "la": "拉丁语原版 editio latina originalis",
        "gr": "希腊语原版 ελληνική πρωτότυπη έκδοση",
        "sl": "斯洛文尼亚语版 izvirno slovensko izdajo",
        "ar": "阿拉伯语原版 النسخة العربية الأصلية",
        "ru": "俄语原版 русское оригинальное издание",
    }.get(language, "")
    if lang_hint: parts.append(lang_hint)
    query = " ".join(parts)
    
    academic_domains = [
        "persee.fr", "cairn.info", "jstor.org",
        "gallimard.fr", "presses-universitaires.fr",
        "books.openedition.org", "archive.org", "gallica.bnf.fr",
    ]
    return search(query=query, max_results=max_results,
                  search_depth="advanced", include_domains=academic_domains)


def extract_quote(search_result: Dict, keyword: str,
                  context_chars: int = 300) -> Optional[Dict]:
    """从 Tavily 返回的 raw_content 中提取包含关键词的段落。"""
    for r in search_result.get("results", []):
        text = r.get("raw_content", "") or r.get("content", "")
        if not text: continue
        idx = text.lower().find(keyword.lower())
        if idx == -1: continue
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(keyword) + context_chars)
        return {
            "quote": text[idx:idx + len(keyword)],
            "context": text[start:end],
            "before": text[start:idx],
            "after": text[idx + len(keyword):end],
            "source_url": r.get("url", ""),
            "source_title": r.get("title", ""),
        }
    return None


def format_for_kl9(result: Dict) -> str:
    """将 Tavily 搜索结果格式化为 KL9 可注入的上下文。"""
    lines = [f"## 文献检索结果：{result.get('query', '')}", ""]
    for i, r in enumerate(result.get("results", []), 1):
        lines.append(f"### 来源 {i}")
        lines.append(f"- **标题**：{r['title']}")
        lines.append(f"- **URL**：{r['url']}")
        lines.append(f"- **相关性**：{r['score']:.2f}")
        lines.append("")
        text = r.get("raw_content", "") or r.get("content", "")
        if text:
            excerpt = text[:1500] + "..." if len(text) > 1500 else text
            lines.append("**文本片段**：")
            lines.append(excerpt)
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python kailejiu_research_tavily.py <query>")
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    result = search(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
