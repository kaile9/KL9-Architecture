"""N9R20Framework version constants."""

MARKETING_VERSION = "9R-2.0"
SEMVER = "2.0.0"
CODENAME = "RHIZOME"

# N9R20 = N9R20Framework
# 9 = 开了玖
# R = RHIZOME
# 2.0 = major.minor

def parse_version(v: str) -> tuple:
    """Parse marketing version string to semver components."""
    if v.startswith("9R-"):
        parts = v.replace("9R-", "").split(".")
        return tuple(int(p) for p in parts)
    return (0, 0, 0)

__all__ = ["MARKETING_VERSION", "SEMVER", "CODENAME", "parse_version"]
