#!/usr/bin/env python3
"""
KL9-RHIZOME v1.5 协调器测试入口。
用于快速验证 coordinate() 函数。
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from koordinator import coordinate, status


def test_query(query: str, label: str = ""):
    """测试单条 query。"""
    print(f"\n{'─'*50}")
    print(f"【{label}】{query}")
    print(f"{'─'*50}")
    
    result = coordinate(query)
    
    print(f"  模式:     {result.get('mode', '?')}")
    print(f"  张力类型: {result.get('tension_type', 'N/A')}")
    print(f"  折叠深度: {result.get('fold_depth', 0)}")
    print(f"  悬置质量: {result.get('suspension_quality', 'N/A')}")
    print(f"  会话ID:   {result.get('session_id')}")
    print(f"  响应:     {result.get('response', '')[:200]}")


if __name__ == '__main__':
    print("=" * 50)
    print("KL9-RHIZOME v1.5 协调器测试")
    print("=" * 50)
    
    # 系统状态
    try:
        s = status()
        print(f"\n系统状态:")
        print(f"  图谱: {s.get('graph', {}).get('nodes', '?')} 节点")
        print(f"  记忆: {s.get('memory', {}).get('sessions', '?')} 会话")
    except Exception as e:
        print(f"  状态异常: {e}")
    
    # 测试用例
    tests = [
        ("你好", "短问短答"),
        ("现在几点", "工具性查询"),
        ("存在先于本质吗？", "哲学判断句"),
        ("福柯和韦伯的权力理论有什么根本差异？", "二重性对比"),
        ("资本的异化与人的自由之间是否存在不可调和的结构性张力？", "深层学术"),
    ]
    
    if len(sys.argv) > 1:
        # 单条 query 模式
        test_query(sys.argv[1], "自定义")
    else:
        # 批量测试
        for q, label in tests:
            test_query(q, label)
    
    print(f"\n{'=' * 50}")
    print("测试完成")
    print("=" * 50)
