#!/usr/bin/env python3
"""
Export KL9-RHIZOME SQLite graph to skillbook JSON (v1.1).

Usage:
    python scripts/export_skillbook.py "书名" "作者" "年份" "语言" [options]

Options:
    --llm LLM               LLM 源名称 (default: deepseek-v4-pro)
    --rounds N              完成的学习轮数 (default: 1)
    --verify METHOD         验证方法: none|spot-check|full-reread|external (default: none)
    --hours H               投入小时数 (default: 0.0)
    --counter "视角1,视角2"  反视角列表，逗号分隔

Examples:
    python scripts/export_skillbook.py "Phänomenologie des Geldes" "K.-H. Brodbeck" 2023 de \
        --llm "deepseek-v4-pro" --rounds 2 --verify "spot-check" --hours 20.0 \
        --counter "马克思货币理论,Simmel货币哲学"

    python scripts/export_skillbook.py "资本论" "Karl Marx" 1867 de \
        --llm "deepseek-v4-pro" --rounds 3 --verify "full-reread" --hours 50.0
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kl9_skillbook.bridge import export_graph_to_skillbook
from kl9_skillbook.models import ProductionRecord


def parse_args(argv: list[str]) -> dict:
    """解析命令行参数."""
    if len(argv) < 4:
        print(__doc__)
        sys.exit(1)

    result = {
        "book_title": argv[0],
        "author": argv[1],
        "year": argv[2],
        "language": argv[3],
        "llm": "deepseek-v4-pro",
        "rounds": 1,
        "verify": "none",
        "hours": 0.0,
        "counter": [],
    }

    remaining = argv[4:]
    i = 0
    while i < len(remaining):
        arg = remaining[i]
        if arg == "--llm" and i + 1 < len(remaining):
            result["llm"] = remaining[i + 1]
            i += 2
        elif arg == "--rounds" and i + 1 < len(remaining):
            result["rounds"] = int(remaining[i + 1])
            i += 2
        elif arg == "--verify" and i + 1 < len(remaining):
            result["verify"] = remaining[i + 1]
            i += 2
        elif arg == "--hours" and i + 1 < len(remaining):
            result["hours"] = float(remaining[i + 1])
            i += 2
        elif arg == "--counter" and i + 1 < len(remaining):
            result["counter"] = [c.strip() for c in remaining[i + 1].split(",") if c.strip()]
            i += 2
        else:
            print(f"Unknown argument: {arg}")
            i += 1

    return result


def main():
    args = parse_args(sys.argv[1:])

    book_title = args["book_title"]
    author = args["author"]
    year = args["year"]
    language = args["language"]
    llm_source = args["llm"]

    # 生成安全的文件名
    safe_title = book_title.lower().replace(" ", "_").replace("/", "_")[:60]
    output_path = f"skillbooks/{language}/{safe_title}.skillbook.json"

    manifest = {
        "skill_book_id": f"kl9_export_{safe_title}",
        "version": "1.1",
        "quality_tier": 4,  # 导出时由系统自动计算 quality_score
        "llm_source": llm_source,
        "kl9_version": "1.5.0",
        "created_timestamp": int(time.time()),
        "book_title": f"{book_title} — {author} ({year})",
        "extra": {
            "original_author": author,
            "original_year": int(year),
            "language": language,
        },
    }

    # 构建制作记录
    prod_record = ProductionRecord(
        rounds_completed=args["rounds"],
        verification_method=args["verify"],
        counter_perspectives=args["counter"],
        total_hours=args["hours"],
    )

    print(f"📦 导出技能书 (v1.1): {book_title}")
    print(f"   作者: {author} ({year})")
    print(f"   语言: {language}")
    print(f"   LLM 源: {llm_source}")
    print(f"   学习轮数: {args['rounds']}")
    print(f"   验证方法: {args['verify']}")
    print(f"   投入时间: {args['hours']}h")
    if args["counter"]:
        print(f"   反视角: {', '.join(args['counter'])}")

    try:
        result_path = export_graph_to_skillbook(
            output_path=output_path,
            manifest=manifest,
            production_record=prod_record,
        )
        print(f"✅ 导出成功: {result_path}")

        # 显示统计
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        m = data.get("manifest", {})
        concept_count = len(data.get("concepts", {}))
        print(f"   概念数量: {concept_count}")
        print(f"   难度评分: {m.get('difficulty', 'N/A')}")
        print(f"   质量评分: {m.get('quality_score', 'N/A')}")
        print(f"   信任度: {m.get('_trust', 'N/A')} ({m.get('_trust_level', 'N/A')})")

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
