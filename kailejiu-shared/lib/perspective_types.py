"""
KL9-RHIZOME 视角与张力类型库。
6 大视角类别 + 6 种张力类型 + 7 组推荐二重组合 + 4 种涌现风格。
"""

PERSPECTIVE_TYPES = {
    "temporal": {
        "human": {"characteristics": ["有限性意识", "代际断裂", "哀悼与记忆"]},
        "elf": {"characteristics": ["无限时间", "永恒轮回", "意义的消解"]}
    },
    "existential": {
        "immediate": {"characteristics": ["具身体验", "在世存在", "被抛"]},
        "mediated": {"characteristics": ["符号中介", "拟像", "超真实"]}
    },
    "social": {
        "regression": {"characteristics": ["社会父亲失效", "共同体解体", "父法衰退"]},
        "growth": {"characteristics": ["新联结形式", "网络共同体", "后家庭结构"]}
    },
    "political": {
        "freedom_focused": {"characteristics": ["消极自由", "反抗权力", "去中心化"]},
        "security_focused": {"characteristics": ["生命政治", "治理术", "例外状态"]}
    },
    "economic_grotesque": {
        "economic": {"characteristics": ["效率优先", "工具理性", "计算逻辑"]},
        "grotesque": {"characteristics": ["巴塔耶式耗费", "非生产性支出", "僭越"]}
    },
    "truth_construction": {
        "truth": {"characteristics": ["可知论", "表象与本质", "启蒙理性"]},
        "slander": {"characteristics": ["话语权力", "真理体制", "知识考古学"]}
    },
    "translation": {
        "foreignizing": {"characteristics": ["保留原文句法骨架", "术语优先概念保真", "让读者走向作者", "可见的译者"]},
        "domesticating": {"characteristics": ["译入语习惯优先", "读者亲和流畅", "让作者走向读者", "透明的译者"]}
    }
}

TENSION_TYPES = {
    "eternal_vs_finite": {"perspective_source": "temporal", "emergent_style": "temporal_contrast"},
    "mediated_vs_real": {"perspective_source": "existential", "emergent_style": "analytical_juxtaposition"},
    "regression_vs_growth": {"perspective_source": "social", "emergent_style": "ironic_suspension"},
    "freedom_vs_security": {"perspective_source": "political", "emergent_style": "ironic_suspension"},
    "economic_vs_grotesque": {"perspective_source": "economic_grotesque", "emergent_style": "temporal_contrast"},
    "truth_vs_slander": {"perspective_source": "truth_construction", "emergent_style": "dialectical_negation"},
    "foreignizing_vs_domesticating": {"perspective_source": "translation", "emergent_style": "analytical_juxtaposition"},
}

RECOMMENDED_DUALITIES = [
    {"perspective_A": "temporal.human", "perspective_B": "temporal.elf",
     "tension": "eternal_vs_finite", "typical_query_patterns": ["永生", "时间", "有限", "永恒", "死亡", "衰老", "哀悼"]},
    {"perspective_A": "existential.immediate", "perspective_B": "existential.mediated",
     "tension": "mediated_vs_real", "typical_query_patterns": ["真实", "虚拟", "拟像", "模拟", "本真", "符号"]},
    {"perspective_A": "social.regression", "perspective_B": "social.growth",
     "tension": "regression_vs_growth", "typical_query_patterns": ["传统", "共同体", "家庭", "关系", "孤独", "原子化"]},
    {"perspective_A": "political.freedom_focused", "perspective_B": "political.security_focused",
     "tension": "freedom_vs_security", "typical_query_patterns": ["自由", "安全", "监控", "权力", "治理", "规训"]},
    {"perspective_A": "economic_grotesque.economic", "perspective_B": "economic_grotesque.grotesque",
     "tension": "economic_vs_grotesque", "typical_query_patterns": ["消费", "商品", "价值", "浪费", "挥霍"]},
    {"perspective_A": "truth_construction.truth", "perspective_B": "truth_construction.slander",
     "tension": "truth_vs_slander", "typical_query_patterns": ["真理", "知识", "事实", "后真相", "话语"]},
    {"perspective_A": "political.freedom_focused", "perspective_B": "social.regression",
     "tension": "freedom_vs_security", "typical_query_patterns": ["现代性", "个体化", "自律", "规范", "结构"]},
    {"perspective_A": "translation.foreignizing", "perspective_B": "translation.domesticating",
     "tension": "foreignizing_vs_domesticating", "typical_query_patterns": ["翻译", "中译", "英译", "译文", "译法", "术语翻译", "译名", "如何翻译"]},
]

EMERGENT_STYLE_MAP = {
    "analytical_juxtaposition": {"syntax": "冷静并置", "tone": "冷冽", "closure": "悬置反问"},
    "temporal_contrast": {"syntax": "时间跨度跳跃", "tone": "哀而不伤", "closure": "无终点的开端"},
    "ironic_suspension": {"syntax": "反诘嵌套", "tone": "讽刺疏离", "closure": "悖论裸露"},
    "dialectical_negation": {"syntax": "否定之否定", "tone": "锐利批判", "closure": "拒绝任何肯定命题"},
}

FAMILY_SIGNALS = {
    "temporal": {"keywords": ["时间", "永恒", "有限", "死亡", "衰老", "记忆", "哀悼", "世代", "历史", "轮回"],
                 "weight": 1.0, "subtypes": {
        "human": ["有限", "死亡", "衰老", "记忆", "哀悼", "世代"],
        "elf": ["永恒", "轮回", "无限", "不朽", "长存"]
    }},
    "existential": {"keywords": ["存在", "真实", "虚拟", "拟像", "本真", "符号", "意义", "荒谬"],
                    "weight": 1.0, "subtypes": {
        "immediate": ["本真", "具身", "在世", "被抛", "体验"],
        "mediated": ["拟像", "符号", "媒介", "超真实", "再现"]
    }},
    "social": {"keywords": ["社会", "共同体", "传统", "家庭", "关系", "孤独", "原子化", "联结"],
               "weight": 0.9, "subtypes": {
        "regression": ["解体", "衰退", "原子化", "孤独", "父法", "失效"],
        "growth": ["新联结", "网络", "后家庭", "重构", "共同体"]
    }},
    "political": {"keywords": ["权力", "自由", "安全", "治理", "规训", "监控", "反抗", "国家"],
                  "weight": 1.0, "subtypes": {
        "freedom_focused": ["自由", "反抗", "去中心", "解放", "自治"],
        "security_focused": ["安全", "监控", "规训", "治理", "例外"]
    }},
    "epistemological": {"keywords": ["知识", "真理", "认知", "理性", "科学", "范式", "分类"],
                        "weight": 0.8, "subtypes": {
        "rational": ["理性", "科学", "逻辑", "证明"],
        "genealogical": ["谱系", "考古", "断裂", "知识型"]
    }},
    "aesthetic": {"keywords": ["美", "艺术", "感性", "崇高", "表征", "想象力"],
                  "weight": 0.7, "subtypes": {
        "beauty": ["美", "和谐", "形式"],
        "sublime": ["崇高", "不可呈现", "震撼"]
    }},
}

FAMILY_TENSION_MAP = {
    ("temporal", "existential"): "eternal_vs_finite",
    ("existential", "temporal"): "eternal_vs_finite",
    ("existential", "political"): "mediated_vs_real",
    ("political", "existential"): "mediated_vs_real",
    ("social", "political"): "regression_vs_growth",
    ("political", "social"): "regression_vs_growth",
    ("political", "economic_grotesque"): "freedom_vs_security",
    ("economic_grotesque", "political"): "freedom_vs_security",
    ("economic_grotesque", "aesthetic"): "economic_vs_grotesque",
    ("aesthetic", "economic_grotesque"): "economic_vs_grotesque",
    ("truth_construction", "political"): "truth_vs_slander",
    ("political", "truth_construction"): "truth_vs_slander",
}
