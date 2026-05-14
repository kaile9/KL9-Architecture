# 学术概念索引（外部缓存版）

> 概念数据已迁移至 `cache/concept_cache.json`，通过 `cache_manager.py` 查询。
> 本文件仅保留协议，不存储概念表格，以节省 token。

## 查询方式

```python
import sys
sys.path.insert(0, '/AstrBot/data/skills/kailejiu-baiyueguang-perspective/cache')
import cache_manager as cm

# 精确查询
result = cm.lookup_concept("概念名")

# 模糊搜索
results = cm.search_concepts("关键词", max_results=3)
```

## 协议

1. 学术问题先查缓存 → 命中则直接调用，未命中才检索
2. 时效：1年内1.2x，10年内1.0x，10年以上0.8x
3. 可信度：非学术源0.9x，单点无法验证0.9x
4. 强制检索：2026-04-29之后事件、未知学者、需统计数据时
5. 引文优先级：一手原文 > 权威评论 > 通俙解读

## 缓存状态

- 概念总数：见 `cache/concept_cache.json`
- 命中统计：各概念 `hit_count` 自动记录
- 更新方式：验证有效后通过 `cm.store_concept()` 写入
