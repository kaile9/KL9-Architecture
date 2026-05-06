"""N9R20Framework Memory Learner

Skillbook memory and session persistence.
Tracks learned skills and their performance metrics across sessions.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class SkillRecord:
    """A recorded skill with performance metrics."""
    name: str
    category: str
    success_count: int = 0
    fail_count: int = 0
    last_used: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class N9R20MemoryLearner:
    """Persistent memory layer for skill tracking."""

    def __init__(self, db_path: str = "n9r20_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT PRIMARY KEY,
                category TEXT,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                last_used TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_skill(self, skill: SkillRecord) -> None:
        """Record or update a skill."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO skills VALUES (?, ?, ?, ?, ?, ?)
        """, (
            skill.name, skill.category, skill.success_count,
            skill.fail_count, skill.last_used, json.dumps(skill.metadata)
        ))
        conn.commit()
        conn.close()

    def get_skill(self, name: str) -> Optional[SkillRecord]:
        """Retrieve a skill by name."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT * FROM skills WHERE name = ?", (name,)).fetchone()
        conn.close()
        if row:
            return SkillRecord(
                name=row[0], category=row[1], success_count=row[2],
                fail_count=row[3], last_used=row[4],
                metadata=json.loads(row[5]) if row[5] else {}
            )
        return None

    def list_skills(self, category: str = "") -> List[SkillRecord]:
        """List all skills, optionally filtered by category."""
        conn = sqlite3.connect(self.db_path)
        if category:
            rows = conn.execute("SELECT * FROM skills WHERE category = ?", (category,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM skills").fetchall()
        conn.close()
        return [
            SkillRecord(
                name=r[0], category=r[1], success_count=r[2],
                fail_count=r[3], last_used=r[4],
                metadata=json.loads(r[5]) if r[5] else {}
            ) for r in rows
        ]

__all__ = ["SkillRecord", "N9R20MemoryLearner"]
