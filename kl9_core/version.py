"""KL9-RHIZOME 版本常量 · Version Constants

命名规则：
    9R-1.5 = 开了玖(9) + RHIZOME(R) + 大版本(1).小版本(5)
    
Marketing: 9R-1.5
Semantic:  1.5.0
"""

MAJOR = 1
MINOR = 5
PATCH = 0

MARKETING_VERSION = "9R-1.5"
SEMVER = f"{MAJOR}.{MINOR}.{PATCH}"
BUILD = f"{MAJOR}.{MINOR}"

def parse_version(v: str) -> tuple:
    """Parse '9R-1.5' or '1.5.0' to (major, minor, patch)"""
    if v.startswith("9R-"):
        parts = v.split("-")[1].split(".")
        return (int(parts[0]), int(parts[1]), 0)
    parts = v.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

def format_marketing(major: int, minor: int) -> str:
    """Format (1, 5) -> '9R-1.5'"""
    return f"9R-{major}.{minor}"
