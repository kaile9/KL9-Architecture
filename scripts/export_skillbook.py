#!/usr/bin/env python3
"""
Export KL9-RHIZOME SQLite graph to skillbook JSON.

Usage:
    python scripts/export_skillbook.py "书名" "作者/LLM源" [quality_tier=4]

Examples:
    python scripts/export_skillbook.py "Phänomenologie des Geldes" "K.-H. Brodbeck" 4
    python scripts/export_skillbook.py "资本论" "deepseek-v4-pro" 5
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kl9_skillbook.bridge import export_graph_to_skillbook


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    book_title = sys.argv[1]
    llm_source = sys.argv[2]
    quality_tier = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    # 生成安全的文件名
    safe_title = book_title.lower().replace(" ", "_").replace("/", "_")[:60]
    output_path = f"skillbooks/{safe_title}.skillbook.json"

    manifest = {
        "skill_book_id": f"kl9_export_{safe_title}",
        "version": "1.0",
        "quality_tier": quality_tier,
        "llm_source": llm_source,
        "kl9_version": "1.5.0",
        "created_timestamp": int(time.time()),
        "book_title": book_title,
    }

    print(f"📦 导出技能书: {book_title}")
    print(f"   质量等级: {quality_tier}")
    print(f"   LLM 源: {llm_source}")

    try:
        result_path = export_graph_to_skillbook(
            output_path=output_path,
            manifest=manifest,
        )
        print(f"✅ 导出成功: {result_path}")

        # 显示统计
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        concept_count = len(data.get("concepts", {}))
        print(f"   概念数量: {concept_count}")

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
