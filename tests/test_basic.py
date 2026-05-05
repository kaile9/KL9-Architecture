"""基础测试 / Basic tests — 任何人都能跑，不需要 mock"""

import sys
sys.path.insert(0, '../kailejiu-shared/lib')

from perspective_types import PERSPECTIVE_TYPES, TENSION_TYPES
from tension_bus import TensionBus


def test_perspectives_loaded():
    """测试视角类型已加载"""
    count = len(PERSPECTIVE_TYPES.perspective_types)
    print(f"✅ 视角类型已加载: {count} 个类别")

    # 每个类别应有两种视角
    for cat, perspectives in PERSPECTIVE_TYPES.perspective_types.items():
        assert len(perspectives) == 2, f"{cat} should have 2 perspectives"
        print(f"   ✓ {cat}: {list(perspectives.keys())}")

    assert count >= 6, "Should have at least 6 perspective categories"


def test_tension_types():
    """测试张力类型"""
    assert len(TENSION_TYPES) >= 6, "Should have at least 6 tension types"
    print(f"✅ 张力类型已定义: {len(TENSION_TYPES)} 种")

    for t_name, t_info in TENSION_TYPES.items():
        assert 'emergent_style' in t_info
        print(f"   ✓ {t_name}: style = {t_info['emergent_style']}")


def test_recommended_dualities():
    """测试推荐二重组合"""
    assert len(PERSPECTIVE_TYPES.recommended_dualities) >= 7
    print(f"✅ 推荐二重组合: {len(PERSPECTIVE_TYPES.recommended_dualities)} 组")

    for pair in PERSPECTIVE_TYPES.recommended_dualities:
        required = ['perspective_A', 'perspective_B', 'tension', 'typical_query_patterns']
        for key in required:
            assert key in pair, f"Missing {key} in duality"


def test_tension_bus():
    """测试张力总线"""
    bus = TensionBus()
    
    received = []
    def callback(event):
        received.append(event['type'])
    
    bus.subscribe("test_event", callback)
    bus.emit("test_event", {"data": "hello"})
    
    assert len(received) == 1
    assert received[0] == "test_event"
    print("✅ TensionBus: 订阅/发布正常")


if __name__ == "__main__":
    test_perspectives_loaded()
    test_tension_types()
    test_recommended_dualities()
    test_tension_bus()
    print("\n🎉 所有基础测试通过 / All basic tests passed!")
