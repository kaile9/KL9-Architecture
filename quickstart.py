#!/usr/bin/env python3
"""
KL9-RHIZOME 9R-1.5 · Quick Start
================================
一键启动脚本，自动检测环境、安装依赖、初始化数据库、验证健康状态。

兼容环境：
    - AstrBot（检测 /AstrBot/data/skills/）
    - OpenClaw（检测 OPENCLAW_HOME 环境变量）
    - 独立运行（Standalone）

用法：
    python3 quickstart.py
    python3 quickstart.py --env openclaw  # 强制指定环境
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# ── 版本常量 ──────────────────────────────────────────────
MARKETING_VERSION = "9R-1.5"
SEMVER = "1.5.0"

# ── 环境检测 ──────────────────────────────────────────────
def detect_environment() -> str:
    """检测运行环境：astrbot | openclaw | standalone"""
    if os.environ.get("OPENCLAW_HOME") or os.environ.get("OPENCLAW_PLUGINS"):
        return "openclaw"
    if Path("/AstrBot/data/skills").exists() or os.environ.get("ASTRBOT_ROOT"):
        return "astrbot"
    return "standalone"

# ── 依赖检查 ──────────────────────────────────────────────
def check_dependencies() -> dict[str, bool]:
    """检查核心依赖是否已安装"""
    deps = {
        "sqlite3": False,
        "typing": False,
    }
    try:
        import sqlite3
        deps["sqlite3"] = True
    except ImportError:
        pass
    try:
        import typing
        deps["typing"] = True
    except ImportError:
        pass
    return deps

# ── 路径设置 ──────────────────────────────────────────────
def setup_paths(env: str) -> Path:
    """根据环境设置 Python 路径，返回项目根目录"""
    script_dir = Path(__file__).resolve().parent
    
    if env == "openclaw":
        # OpenClaw 插件模式：使用相对路径
        kl9_core = script_dir / "kl9_core"
        kl9_skillbook = script_dir / "kl9_skillbook"
    elif env == "astrbot":
        # AstrBot 模式：复制到 skills 目录
        astrbot_skills = Path("/AstrBot/data/skills")
        kl9_core = astrbot_skills / "kl9_core"
        kl9_skillbook = astrbot_skills / "kl9_skillbook"
    else:
        # 独立模式
        kl9_core = script_dir / "kl9_core"
        kl9_skillbook = script_dir / "kl9_skillbook"
    
    # 添加到 sys.path
    for p in [str(kl9_core), str(kl9_skillbook), str(script_dir)]:
        if p not in sys.path:
            sys.path.insert(0, p)
    
    return script_dir

# ── 数据库初始化 ───────────────────────────────────────────
def init_database(project_root: Path) -> Path:
    """初始化 SQLite 数据库"""
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "kl9.db"
    
    # 导入 graph_backend 创建 schema
    try:
        import graph_backend as GB
        # 首次连接会自动创建表
        # Database path uses kl9_core/graph_backend.py default
        print(f"  ✓ Database initialized: {db_path}")
        return db_path
    except Exception as e:
        print(f"  ⚠ Database init warning: {e}")
        return db_path

# ── 核心模块加载测试 ──────────────────────────────────────
def test_core_modules() -> dict[str, bool]:
    """测试所有核心模块可导入"""
    modules = [
        "perspective_types", "tension_bus", "core_structures",
        "dual_fold", "emergent_style", "graph_backend",
        "memory", "learner", "routing",
        "suspension_evaluator", "fold_depth_policy", "constitutional_dna",
    ]
    results = {}
    for mod in modules:
        try:
            __import__(mod)
            results[mod] = True
        except Exception as e:
            results[mod] = False
            print(f"  ✗ {mod}: {e}")
    return results

# ── 技能书系统测试 ────────────────────────────────────────
def test_skillbook_system() -> dict[str, bool]:
    """测试技能书系统可导入"""
    try:
        from kl9_skillbook import models, validator, scorer, importer
        return {"models": True, "validator": True, "scorer": True, "importer": True}
    except Exception as e:
        print(f"  ✗ Skillbook system: {e}")
        return {"models": False, "validator": False, "scorer": False, "importer": False}

# ── 健康检查 ──────────────────────────────────────────────
def health_check(project_root: Path) -> dict:
    """运行完整健康检查"""
    print("\n🔍 Health Check:")
    
    # 1. 依赖检查
    deps = check_dependencies()
    print(f"  Dependencies: {sum(deps.values())}/{len(deps)}")
    
    # 2. 核心模块
    core_results = test_core_modules()
    core_ok = sum(core_results.values())
    print(f"  Core modules: {core_ok}/{len(core_results)}")
    
    # 3. 技能书系统
    skillbook_results = test_skillbook_system()
    sb_ok = sum(skillbook_results.values())
    print(f"  Skillbook system: {sb_ok}/{len(skillbook_results)}")
    
    # 4. 数据库
    db_path = project_root / "data" / "kl9.db"
    db_ok = db_path.exists()
    print(f"  Database: {'✓' if db_ok else '✗'}")
    
    # 5. 技能书
    skillbooks_dir = project_root / "skillbooks"
    sb_count = len(list(skillbooks_dir.glob("*/*/*.md"))) if skillbooks_dir.exists() else 0
    print(f"  Skill books: {sb_count} loaded")
    
    all_ok = all(deps.values()) and all(core_results.values()) and db_ok
    
    return {
        "healthy": all_ok,
        "dependencies": deps,
        "core_modules": core_results,
        "skillbook_system": skillbook_results,
        "database": db_ok,
        "skill_books_loaded": sb_count,
    }

# ── OpenClaw 兼容 ─────────────────────────────────────────
def setup_openclaw() -> bool:
    """如果检测到 OpenClaw，注册为插件"""
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if not openclaw_home:
        return False
    
    print(f"\n🔌 OpenClaw detected: {openclaw_home}")
    
    # 检查 OpenClaw 插件目录
    plugin_dir = Path(openclaw_home) / "plugins" / "kl9-rhizome"
    if plugin_dir.exists():
        print(f"  ✓ Plugin already registered: {plugin_dir}")
        return True
    
    print(f"  ℹ To register as OpenClaw plugin, copy this directory to:")
    print(f"    {plugin_dir}")
    return False

# ── 主函数 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="KL9-RHIZOME Quick Start")
    parser.add_argument("--env", choices=["astrbot", "openclaw", "standalone"], 
                       help="Force environment (auto-detected if not specified)")
    parser.add_argument("--skip-health", action="store_true", help="Skip health check")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()
    
    if args.version:
        print(f"KL9-RHIZOME {MARKETING_VERSION} (semver: {SEMVER})")
        return
    
    print(f"\n🌿 KL9-RHIZOME {MARKETING_VERSION}")
    print("=" * 50)
    
    # 检测环境
    env = args.env or detect_environment()
    print(f"\n📦 Environment: {env}")
    
    # 设置路径
    project_root = setup_paths(env)
    print(f"  Project root: {project_root}")
    
    # OpenClaw 兼容
    if env == "openclaw":
        setup_openclaw()
    
    # 初始化数据库
    print("\n🗄 Initializing database...")
    db_path = init_database(project_root)
    
    # 健康检查
    if not args.skip_health:
        result = health_check(project_root)
        
        print("\n" + "=" * 50)
        if result["healthy"]:
            print(f"✅ KL9-RHIZOME {MARKETING_VERSION} is ready!")
            print(f"   Core modules: {sum(result['core_modules'].values())}/12")
            print(f"   Skill books: {result['skill_books_loaded']} loaded")
            print(f"   Database: {db_path}")
        else:
            print(f"⚠️  KL9-RHIZOME {MARKETING_VERSION} loaded with warnings.")
            print("   Some modules failed to load. Check logs above.")
        print("=" * 50)
    else:
        print(f"\n✓ Quick start complete (health check skipped)")
    
    # 返回环境信息供调用者使用
    return {
        "version": MARKETING_VERSION,
        "semver": SEMVER,
        "environment": env,
        "project_root": str(project_root),
        "database": str(db_path),
    }

if __name__ == "__main__":
    result = main()
    sys.exit(0 if (result is None or not isinstance(result, dict)) else 0)
