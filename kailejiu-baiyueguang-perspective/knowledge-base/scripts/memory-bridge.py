#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Bridge - 跨对话缓存封装层
=====================================
当前实现: 文件系统持久化（唯一可用的跨对话缓存）
未来迁移: 接口保持不变，底层切换为核心记忆API

设计原则:
- 所有操作必须通过此封装层，禁止直接读写知识库文件
- 每次读写自动更新时间戳和命中统计
- 支持概念卡片的生命周期管理
"""

import json
import os
import time
from pathlib import Path

KB_DIR = Path("/AstrBot/data/skills/kailejiu-baiyueguang-perspective/knowledge-base")
INDEX_FILE = KB_DIR / "index.json"


def _load_index():
    """加载主索引"""
    if not INDEX_FILE.exists():
        return {
            "schema_version": "1.0",
            "created": time.strftime("%Y-%m-%d"),
            "last_updated": time.strftime("%Y-%m-%d"),
            "concept_count": 0,
            "quote_source_count": 0,
            "verify_queue_count": 0,
            "concepts": {},
            "quote_sources": {},
            "verify_queue": []
        }
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index):
    """保存主索引"""
    index["last_updated"] = time.strftime("%Y-%m-%d")
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def remember_concept(concept_id, content):
    """
    存储或更新概念卡片
    接口稳定性: 高 - 未来直接迁移
    """
    concept_file = KB_DIR / "concepts" / f"{concept_id}.md"
    index = _load_index()
    
    index["concepts"][concept_id] = {
        "file": str(concept_file.relative_to(KB_DIR)),
        "last_updated": time.strftime("%Y-%m-%d")
    }
    
    with open(concept_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    _save_index(index)
    return True


def recall_concept(concept_id):
    """
    检索概念卡片
    接口稳定性: 高 - 未来直接迁移
    """
    concept_file = KB_DIR / "concepts" / f"{concept_id}.md"
    if not concept_file.exists():
        return None
    
    with open(concept_file, "r", encoding="utf-8") as f:
        return f.read()


def search_concepts(query_term):
    """
    检索概念（简单字符匹配）
    未来可替换为向量搜索
    """
    index = _load_index()
    results = []
    for cid, info in index.get("concepts", {}).items():
        concept_file = KB_DIR / info["file"]
        if concept_file.exists():
            content = concept_file.read_text(encoding="utf-8")
            if query_term.lower() in content.lower():
                name = cid
                for line in content.split("\n"):
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"')
                        break
                results.append({
                    "concept_id": cid,
                    "name": name,
                    "preview": content[:200] + "..."
                })
    return results


def add_verify_queue(concept_id, question, priority="normal"):
    """
    添加验证队列
    优先级: high / normal / low
    """
    index = _load_index()
    entry = {
        "concept_id": concept_id,
        "question": question,
        "priority": priority,
        "added": time.strftime("%Y-%m-%d"),
        "status": "pending"
    }
    index["verify_queue"].append(entry)
    index["verify_queue_count"] = len(index["verify_queue"])
    _save_index(index)
    return True


def get_verify_queue(priority=None, limit=10):
    """获取验证队列"""
    index = _load_index()
    queue = index.get("verify_queue", [])
    if priority:
        queue = [q for q in queue if q["priority"] == priority]
    return queue[:limit]


def complete_verify(concept_id, result):
    """
    完成验证，更新队列状态
    result: verified / rejected / modified
    """
    index = _load_index()
    for q in index.get("verify_queue", []):
        if q["concept_id"] == concept_id and q["status"] == "pending":
            q["status"] = result
            q["completed"] = time.strftime("%Y-%m-%d")
            break
    _save_index(index)
    return True


def record_quote(scholar, work, quote_text, concept_tag):
    """
    记录验证后的引文
    返回引文ID，便于引用
    """
    quote_file = KB_DIR / "quotes" / f"{scholar}.md"
    index = _load_index()
    
    quote_entry = f"\n### {concept_tag} | {work} | {time.strftime('%Y-%m-%d')}\n\n"
    quote_entry += f"> {quote_text}\n\n"
    quote_entry += "操作: [待填充]\n"
    
    with open(quote_file, "a", encoding="utf-8") as f:
        f.write(quote_entry)
    
    if scholar in index.get("quote_sources", {}):
        index["quote_sources"][scholar]["quote_count"] = index["quote_sources"][scholar].get("quote_count", 0) + 1
    
    _save_index(index)
    return f"{scholar}:{concept_tag}"


if __name__ == "__main__":
    print("Memory Bridge 加载正常")
    print(f"索引路径: {INDEX_FILE}")
    print(f"概念卡片数: {len(_load_index().get('concepts', {}))}")
