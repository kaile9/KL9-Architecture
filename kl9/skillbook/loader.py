"""
9R-2.1 — Skillbook Loader

Unified loader that reads both v3.1 format (6-file YAML+JSON) and
v1.x format (SKILL.md markdown) into a single in-memory model.

Evolution trace:
    9R-1.0: SKILL.md (markdown, frontmatter)
    9R-1.5: SKILL.md (structured sections)
    kl9_v3.1: 6-file format (meta.yaml + lens.json + hooks.yaml + quotes.yaml + tensions.yaml + references.yaml)
    9R-2.0: N9R20SkillBookCompat (v1.x compatibility layer)
    9R-2.1: Unified loader (both formats → one memory model)

Strategy: Single-direction, lazy, no write-back.
    - Load v3.1 → parse 6 files → SkillBook dataclass
    - Load v1.x → parse SKILL.md frontmatter + body sections → same SkillBook dataclass
    - Load only when needed, never batch-convert formats
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SkillBookConcept:
    name: str
    definition: str = ""
    category: str = "core"
    related: list[str] = field(default_factory=list)
    quotes: list[dict] = field(default_factory=list)
    difficulty: float = 50.0


@dataclass
class SkillBookTension:
    name: str
    description: str = ""
    side_a: str = ""
    side_b: str = ""
    recommended_stance: str = "suspend"  # suspend | decide | delegate


@dataclass
class SkillBook:
    name: str
    domain: list[str] = field(default_factory=list)
    school: str = ""
    period: str = ""
    language: str = ""
    version: str = "1.0"
    description: str = ""
    concepts: list[SkillBookConcept] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    key_terms: dict[str, str] = field(default_factory=dict)
    hooks: list[dict] = field(default_factory=list)
    quotes: list[dict] = field(default_factory=list)
    tensions: list[SkillBookTension] = field(default_factory=list)
    references: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @property
    def concept_count(self) -> int:
        return len(self.concepts)

    @property
    def tension_count(self) -> int:
        return len(self.tensions)

    @property
    def quote_count(self) -> int:
        return len(self.quotes)


class SkillbookLoader:
    """Unified loader for kl9_v3.1 (6-file) and v1.x (SKILL.md) formats."""

    # → kl9_v3.1 format loader

    @staticmethod
    def load_v31(base_path: str | Path) -> Optional[SkillBook]:
        """Load a v3.1 6-file skillbook directory."""
        base = Path(base_path)
        if not base.is_dir():
            return None

        meta = SkillbookLoader._load_yaml(base / "meta.yaml")
        if not meta:
            return None

        lens = SkillbookLoader._load_json(base / "lens.json") or {}
        hooks = SkillbookLoader._load_yaml(base / "hooks.yaml") or []
        quotes = SkillbookLoader._load_yaml(base / "quotes.yaml") or []
        tensions_raw = SkillbookLoader._load_yaml(base / "tensions.yaml") or []
        references = SkillbookLoader._load_yaml(base / "references.yaml") or []

        concepts = []
        for c in lens.get("concepts", []):
            concepts.append(SkillBookConcept(
                name=c.get("name", ""),
                definition=c.get("definition", ""),
                category=c.get("category", "core"),
                related=c.get("related", []),
                quotes=c.get("quotes", []),
                difficulty=c.get("difficulty", 50.0),
            ))

        tensions = []
        for t in tensions_raw:
            tensions.append(SkillBookTension(
                name=t.get("name", ""),
                description=t.get("description", ""),
                side_a=t.get("side_a", ""),
                side_b=t.get("side_b", ""),
                recommended_stance=t.get("recommended_stance", "suspend"),
            ))

        return SkillBook(
            name=meta.get("name", base.name),
            domain=meta.get("domain", []),
            school=meta.get("school", ""),
            period=meta.get("period", ""),
            language=meta.get("language", ""),
            version=meta.get("version", "1.0"),
            description=meta.get("description", ""),
            concepts=concepts,
            methods=lens.get("methods", []),
            key_terms=lens.get("key_terms", {}),
            hooks=hooks if isinstance(hooks, list) else [],
            quotes=quotes if isinstance(quotes, list) else [],
            tensions=tensions,
            references=references if isinstance(references, list) else [],
            tags=meta.get("tags", []),
        )

    # → v1.x format loader

    @staticmethod
    def load_v1(skill_md_path: str | Path) -> Optional[SkillBook]:
        """Load a v1.x SKILL.md format file."""
        path = Path(skill_md_path)
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        name = path.parent.name if path.parent.name != "." else path.stem

        # Parse YAML frontmatter
        meta: dict = {}
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            try:
                meta = yaml.safe_load(fm_match.group(1)) or {}
            except yaml.YAMLError:
                pass
            content = content[fm_match.end():]

        # Extract sections from body
        sections = SkillbookLoader._parse_markdown_sections(content)

        # Build concepts from body
        concepts = []
        if "concepts" in sections:
            for line in sections["concepts"].split("\n"):
                ls = line.strip()
                if ls.startswith("- "):
                    name = ls[2:].split(":", 1)[0].strip()
                    definition = ls.split(":", 1)[-1].strip() if ":" in ls else ""
                    concepts.append(SkillBookConcept(name=name, definition=definition))

        return SkillBook(
            name=meta.get("name", name),
            domain=meta.get("domain", []),
            description=meta.get("description", ""),
            concepts=concepts,
            tags=meta.get("tags", []),
            version=meta.get("version", "1.0"),
        )

    # ── Helpers ──

    @staticmethod
    def _load_yaml(path: Path) -> Optional[dict | list]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def _load_json(path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _parse_markdown_sections(text: str) -> dict[str, str]:
        """Parse markdown into sections by ## headers."""
        sections: dict[str, str] = {}
        current_key = ""
        for line in text.split("\n"):
            if line.startswith("## "):
                current_key = line[3:].strip().lower().replace(" ", "_")
                sections[current_key] = ""
            elif current_key:
                sections[current_key] += line + "\n"
        return sections
