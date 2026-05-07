"""
KL9-RHIZOME · Skillbook Content Package

此包仅提供技能书内容的发现和加载入口。
运行时引擎请使用 core/ 目录。
"""

from pathlib import Path

__version__ = "2.0.0"

def get_prebuilt_dir() -> Path:
    """返回预置技能书目录。"""
    return Path(__file__).parent / "prebuilt"

def list_skills(language: str = "") -> list:
    """
    列出可用的技能书。
    
    Args:
        language: 语言代码（zh/en/de/fr/other），为空则列出全部
    """
    prebuilt = get_prebuilt_dir()
    if language:
        lang_dir = prebuilt / language
        if not lang_dir.exists():
            return []
        return [d.name for d in lang_dir.iterdir() if d.is_dir()]
    
    result = []
    for lang_dir in prebuilt.iterdir():
        if lang_dir.is_dir() and not lang_dir.name.startswith("."):
            for skill_dir in lang_dir.iterdir():
                if skill_dir.is_dir():
                    result.append(f"{lang_dir.name}/{skill_dir.name}")
    return result

def load_skill(language: str, skill_name: str) -> str:
    """
    加载指定技能书的 SKILL.md 内容。
    
    Args:
        language: 语言代码
        skill_name: 技能书目录名
    Returns:
        SKILL.md 文件内容
    """
    skill_path = get_prebuilt_dir() / language / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"技能书未找到: {language}/{skill_name}")
    return skill_path.read_text(encoding="utf-8")

__all__ = ["get_prebuilt_dir", "list_skills", "load_skill"]

