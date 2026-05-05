#!/usr/bin/env python3
"""KL9-RHIZOME 最短可用示例 / Minimal working example"""

# 确保 kl9_core 在 Python 路径中
import sys
sys.path.insert(0, '../kl9_core')

from perspective_types import PERSPECTIVE_TYPES, TENSION_TYPES

def demo():
    print("=" * 60)
    print("KL9-RHIZOME · 双视角张力演示")
    print("Dual Perspective Tension Demo")
    print("=" * 60)

    # 列出所有可用的二重组合
    print("\n📋 可用视角对 / Available Dualities:\n")
    for i, pair in enumerate(PERSPECTIVE_TYPES.recommended_dualities):
        print(f"  {i+1}. {pair['perspective_A']:35s} ↔  {pair['perspective_B']}")
        print(f"     张力类型: {pair['tension']}")
        print(f"     触发关键词: {', '.join(pair['typical_query_patterns'][:4])}")
        print()

    # 选择一个张力类型，查看其特征
    print("\n📖 张力类型详解 / Tension Type Details:\n")
    for t_name, t_info in TENSION_TYPES.items():
        style = t_info['emergent_style']
        style_info = PERSPECTIVE_TYPES.emergent_style_map.get(style, {})
        print(f"  {t_name:25s} → 风格: {style:25s} 句法: {style_info.get('syntax', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ 系统就绪 / System Ready")
    print("=" * 60)

if __name__ == "__main__":
    demo()
