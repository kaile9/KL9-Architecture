"""KL9-RHIZOME 9R-1.5 · 健康检查框架 · Health Check Framework

提供运行时健康状态检查、性能基准测试和模块完整性验证。

用法：
    from kl9_core.health import HealthCheck
    hc = HealthCheck()
    report = hc.full_check()
    print(report)
"""

import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 版本常量
MARKETING_VERSION = "9R-1.5"
SEMVER = "1.5.0"

class HealthCheck:
    """KL9-RHIZOME 健康检查器"""
    
    # 核心模块清单
    CORE_MODULES = [
        "perspective_types", "tension_bus", "core_structures",
        "dual_fold", "emergent_style", "graph_backend",
        "memory", "learner", "routing",
        "suspension_evaluator", "fold_depth_policy", "constitutional_dna",
    ]
    
    # 技能书系统模块
    SKILLBOOK_MODULES = [
        "kl9_skillbook.models",
        "kl9_skillbook.validator",
        "kl9_skillbook.scorer",
        "kl9_skillbook.importer",
        "kl9_skillbook.bridge",
        "kl9_skillbook.matcher",
        "kl9_skillbook.merger",
        "kl9_skillbook.tension",
    ]
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.results: Dict = {}
        self.errors: List[str] = []
    
    def check_modules(self) -> Dict[str, bool]:
        """检查所有核心模块可导入"""
        results = {}
        for mod in self.CORE_MODULES:
            try:
                start = time.time()
                __import__(mod)
                elapsed = (time.time() - start) * 1000
                results[mod] = {"ok": True, "load_time_ms": round(elapsed, 2)}
            except Exception as e:
                results[mod] = {"ok": False, "error": str(e)}
                self.errors.append(f"Module {mod}: {e}")
        return results
    
    def check_skillbook_system(self) -> Dict[str, bool]:
        """检查技能书系统可导入"""
        results = {}
        for mod in self.SKILLBOOK_MODULES:
            try:
                start = time.time()
                __import__(mod)
                elapsed = (time.time() - start) * 1000
                results[mod] = {"ok": True, "load_time_ms": round(elapsed, 2)}
            except Exception as e:
                results[mod] = {"ok": False, "error": str(e)}
                self.errors.append(f"Skillbook {mod}: {e}")
        return results
    
    def check_database(self) -> Dict:
        """检查数据库连接和表结构"""
        try:
            import graph_backend as GB
            conn = GB._get_conn()
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ["nodes", "edges", "sessions", "genealogy"]
            missing = [t for t in expected_tables if t not in tables]
            
            return {
                "ok": len(missing) == 0,
                "tables": tables,
                "missing": missing,
                "path": GB.DB_PATH,
            }
        except Exception as e:
            self.errors.append(f"Database: {e}")
            return {"ok": False, "error": str(e)}
    
    def check_skillbooks(self) -> Dict:
        """检查技能书文件完整性"""
        skillbooks_dir = self.project_root / "skillbooks"
        if not skillbooks_dir.exists():
            return {"ok": False, "error": "skillbooks/ directory not found"}
        
        books = []
        for lang_dir in skillbooks_dir.iterdir():
            if lang_dir.is_dir() and not lang_dir.name.startswith("."):
                for book_dir in lang_dir.iterdir():
                    if book_dir.is_dir():
                        skill_md = book_dir / "SKILL.md"
                        if skill_md.exists():
                            books.append(f"{lang_dir.name}/{book_dir.name}")
        
        return {
            "ok": len(books) > 0,
            "count": len(books),
            "books": books,
        }
    
    def benchmark(self) -> Dict[str, float]:
        """运行性能基准测试"""
        benchmarks = {}
        
        # 模块加载时间
        start = time.time()
        for mod in self.CORE_MODULES:
            __import__(mod)
        benchmarks["module_load_total_ms"] = round((time.time() - start) * 1000, 2)
        
        # 数据库查询（如果可用）
        try:
            import graph_backend as GB
            conn = GB._get_conn()
            cursor = conn.cursor()
            
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM nodes")
            benchmarks["db_count_ms"] = round((time.time() - start) * 1000, 2)
            
            start = time.time()
            cursor.execute("SELECT * FROM nodes LIMIT 10")
            benchmarks["db_query_ms"] = round((time.time() - start) * 1000, 2)
        except Exception:
            benchmarks["db_count_ms"] = -1
            benchmarks["db_query_ms"] = -1
        
        return benchmarks
    
    def full_check(self) -> Dict:
        """运行完整健康检查"""
        self.results = {
            "version": MARKETING_VERSION,
            "semver": SEMVER,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modules": self.check_modules(),
            "skillbook_system": self.check_skillbook_system(),
            "database": self.check_database(),
            "skillbooks": self.check_skillbooks(),
            "benchmark": self.benchmark(),
            "errors": self.errors,
            "healthy": len(self.errors) == 0,
        }
        return self.results
    
    def report(self) -> str:
        """生成人类可读的健康报告"""
        if not self.results:
            self.full_check()
        
        r = self.results
        lines = [
            f"KL9-RHIZOME {r['version']} Health Report",
            "=" * 50,
            f"Timestamp: {r['timestamp']}",
            "",
            "Core Modules:",
        ]
        
        for mod, status in r["modules"].items():
            ok = "✓" if status["ok"] else "✗"
            lines.append(f"  {ok} {mod}")
        
        lines.extend([
            "",
            "Skillbook System:",
        ])
        
        for mod, status in r["skillbook_system"].items():
            ok = "✓" if status["ok"] else "✗"
            lines.append(f"  {ok} {mod}")
        
        lines.extend([
            "",
            f"Database: {'✓' if r['database']['ok'] else '✗'}",
            f"Skill Books: {r['skillbooks']['count']} loaded",
            "",
            "Benchmarks:",
        ])
        
        for name, value in r["benchmark"].items():
            lines.append(f"  {name}: {value}ms")
        
        if r["errors"]:
            lines.extend(["", "Errors:"])
            for err in r["errors"]:
                lines.append(f"  ! {err}")
        
        lines.extend([
            "",
            "=" * 50,
            f"Status: {'HEALTHY' if r['healthy'] else 'DEGRADED'}",
        ])
        
        return "\n".join(lines)


# 命令行入口
def main():
    """命令行运行健康检查"""
    import argparse
    parser = argparse.ArgumentParser(description="KL9-RHIZOME Health Check")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmarks")
    args = parser.parse_args()
    
    hc = HealthCheck()
    results = hc.full_check()
    
    if args.json:
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(hc.report())
    
    sys.exit(0 if results["healthy"] else 1)

if __name__ == "__main__":
    main()
