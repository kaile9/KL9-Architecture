"""Manifest validation for skillbook import protocol v1.0."""
import time
from .models import SkillBookManifest

KNOWN_LLM = {
    "claude","claude-3","claude-3.5","gpt-4","gpt-4o","gpt-4-turbo",
    "gemini","gemini-pro","llama","llama-3","mistral","qwen","deepseek",
    "anthropic","openai","google",
}

def validate_manifest(manifest_json: dict, current_version: str = "1.0"
                      ) -> tuple[bool, "SkillBookManifest | None", list[str]]:
    """Validate skillbook manifest. Returns (ok, manifest, warnings)."""
    w: list[str] = []
    v = manifest_json.get("version")
    if not v or v != current_version:
        return False, None, [f"FATAL: version missing/mismatch (got {v!r}, want {current_version!r})"]
    qt = manifest_json.get("quality_tier")
    if qt is None:
        return False, None, ["FATAL: quality_tier missing"]
    if not isinstance(qt, int) or qt < 1 or qt > 5:
        return False, None, [f"FATAL: quality_tier must be int 1-5, got {qt!r}"]
    llm = manifest_json.get("llm_source", "unknown")
    if llm.lower() not in KNOWN_LLM:
        w.append(f"WARNING: unknown llm_source '{llm}'")
    ts = manifest_json.get("created_timestamp")
    if ts is None:
        ts = int(time.time())
        w.append("WARNING: created_timestamp missing, using import time")
    known = {"skill_book_id","version","quality_tier","llm_source",
             "kl9_version","created_timestamp","book_title","concept_count","extra"}
    unk = set(manifest_json) - known
    if unk:
        w.append(f"WARNING: unknown manifest fields: {sorted(unk)}")
    cc = manifest_json.get("concept_count", 0)
    m = SkillBookManifest(
        skill_book_id=manifest_json.get("skill_book_id",""),
        version=v, quality_tier=qt, llm_source=llm,
        kl9_version=manifest_json.get("kl9_version",""),
        created_timestamp=ts,
        book_title=manifest_json.get("book_title",""),
        concept_count=cc,
        extra=manifest_json.get("extra",{}),
    )
    return True, m, w
