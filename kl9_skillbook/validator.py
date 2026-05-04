"""Manifest validation for skillbook import protocol v1.1."""
import time
from .models import SkillBookManifest, ProductionRecord, DifficultyBreakdown

KNOWN_LLM = {
    "claude","claude-3","claude-3.5","gpt-4","gpt-4o","gpt-4-turbo",
    "gemini","gemini-pro","llama","llama-3","mistral","qwen","deepseek",
    "anthropic","openai","google",
}


def validate_manifest(manifest_json: dict, current_version: str = "1.1"
                      ) -> tuple[bool, "SkillBookManifest | None", list[str]]:
    """Validate skillbook manifest. Returns (ok, manifest, warnings).

    v1.1 adds: difficulty (FATAL if missing), quality_score (FATAL if missing),
    production_record (WARNING if missing), backward compat for quality_tier.
    """
    w: list[str] = []

    v = manifest_json.get("version")
    # Accept both "1.0" and "1.1" — backward compatible
    if not v or v not in ("1.0", "1.1"):
        return False, None, [f"FATAL: version missing/mismatch (got {v!r}, want '1.0' or '1.1')"]

    is_v11 = (v == "1.1")

    # ── v1.1 必填字段 ──
    if is_v11:
        difficulty = manifest_json.get("difficulty")
        if difficulty is None:
            return False, None, ["FATAL: difficulty missing (required in v1.1)"]
        if not isinstance(difficulty, (int, float)) or difficulty < 0 or difficulty > 100:
            return False, None, [f"FATAL: difficulty must be 0-100, got {difficulty!r}"]

        quality_score = manifest_json.get("quality_score")
        if quality_score is None:
            return False, None, ["FATAL: quality_score missing (required in v1.1)"]
        if not isinstance(quality_score, (int, float)) or quality_score < 0 or quality_score > 100:
            return False, None, [f"FATAL: quality_score must be 0-100, got {quality_score!r}"]

        # production_record: WARNING if missing
        pr = manifest_json.get("production_record")
        if pr is None:
            w.append("WARNING: production_record missing")
        else:
            rc = pr.get("rounds_completed")
            if rc is None or not isinstance(rc, (int, float)) or rc < 1:
                w.append("WARNING: production_record.rounds_completed < 1 or missing")

    # ── quality_tier (v1.0 backward compat) ──
    qt = manifest_json.get("quality_tier")
    if qt is None and not is_v11:
        return False, None, ["FATAL: quality_tier missing"]
    elif qt is not None:
        if not isinstance(qt, int) or qt < 1 or qt > 5:
            return False, None, [f"FATAL: quality_tier must be int 1-5, got {qt!r}"]
    # If v1.1 and no quality_tier, derive it from quality_score
    if qt is None and is_v11:
        qt = round(quality_score / 20)
        qt = max(1, min(5, qt))

    # ── llm_source ──
    llm = manifest_json.get("llm_source", "unknown")
    if llm.lower() not in KNOWN_LLM:
        w.append(f"WARNING: unknown llm_source '{llm}'")

    # ── timestamp ──
    ts = manifest_json.get("created_timestamp")
    if ts is None:
        ts = int(time.time())
        w.append("WARNING: created_timestamp missing, using import time")

    # ── unknown fields ──
    known = {"skill_book_id","version","quality_tier","llm_source",
             "kl9_version","created_timestamp","book_title","concept_count","extra",
             "difficulty","quality_score","production_record","difficulty_breakdown"}
    unk = set(manifest_json) - known
    if unk:
        w.append(f"WARNING: unknown manifest fields: {sorted(unk)}")

    cc = manifest_json.get("concept_count", 0)

    # ── Build ProductionRecord ──
    prod_rec = None
    pr = manifest_json.get("production_record")
    if pr and isinstance(pr, dict):
        prod_rec = ProductionRecord(
            rounds_completed=pr.get("rounds_completed", 1),
            verification_method=pr.get("verification_method", "none"),
            counter_perspectives=pr.get("counter_perspectives", []),
            total_hours=pr.get("total_hours", 0.0),
        )

    # ── Build DifficultyBreakdown ──
    diff_break = None
    db = manifest_json.get("difficulty_breakdown")
    if db and isinstance(db, dict):
        diff_break = DifficultyBreakdown(
            style_density=db.get("style_density", 0),
            info_density=db.get("info_density", 0),
            viewpoint_novelty=db.get("viewpoint_novelty", 0),
            citation_density=db.get("citation_density", 0),
            overall=db.get("overall", 0),
        )

    m = SkillBookManifest(
        skill_book_id=manifest_json.get("skill_book_id",""),
        version=v,
        quality_tier=qt,
        llm_source=llm,
        kl9_version=manifest_json.get("kl9_version",""),
        created_timestamp=ts,
        book_title=manifest_json.get("book_title",""),
        concept_count=cc,
        extra=manifest_json.get("extra",{}),
        difficulty=difficulty if is_v11 else 0.0,
        quality_score=quality_score if is_v11 else float(qt * 20),
        production_record=prod_rec,
        difficulty_breakdown=diff_break,
    )
    return True, m, w
