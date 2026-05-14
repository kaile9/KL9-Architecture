# KL9-RHIZOME v1.5 迁移日志

## 迁移时间
- **日期**: 2026-05-03 02:44 UTC
- **操作**: 阶段零 — 封存旧架构
- **迁移类型**: v5.0 星型集中调度器 → KL9-RHIZOME v1.5 根茎网络协调器

## 迁移原因
1. **架构升级**: 从 7 步串行流水线 (O1-O7) + 4 级手工预算 → TensionBus 事件驱动 + fold_depth 动态调节
2. **去中心化**: orchestrator 从"唯一主入口/中心调度器"转变为"TensionBus 协调器"
3. **张力驱动**: 由张力类型自然涌现推理策略，替代手工策略选择
4. **接口兼容**: 保留对外接口语义 (process→coordinate)，内部完全重构

## 旧文件清单

| 原路径 | 归档路径 | 大小 |
|:---|:---|:---|
| `scripts/main.py` | `logs/archived_v5/main_v5_20260503_024409.py` | 17,022 bytes |
| `scripts/run.py` | `logs/archived_v5/run_v5_20260503_024409.py` | 10,963 bytes |

## 新架构文件
详见 `logs/archived_v5/DEPLOYMENT_NOTE.md`

## 回滚说明
旧文件完整保留于 `logs/archived_v5/`。如需回滚：
```bash
cp logs/archived_v5/main_v5_*.py scripts/main.py
cp logs/archived_v5/run_v5_*.py scripts/run.py
```
