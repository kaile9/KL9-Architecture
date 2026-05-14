"""
kailejiu-orchestrator/scripts/run.py

Single entry point. Called by the AI at the start of every non-trivial query.
Returns a structured context dict the AI uses to generate its response.

Usage (from SKILL.md):
    import sys
    sys.path.insert(0, '/AstrBot/data/skills/kailejiu-orchestrator/scripts')
    from run import prepare_context, record_done
    ctx = prepare_context("<query>")
    # AI generates response using ctx
    record_done(ctx['session_id'], "<final_response>", ctx['concepts_used'])
"""

import sys
import uuid
from pathlib import Path

LIB = Path('/AstrBot/data/skills/kailejiu-shared/lib')
sys.path.insert(0, str(LIB))

import graph_backend as GB
import memory as MEM
import reasoner as R
import learner as L

CASUAL_THRESHOLD = 0.06

def prepare_context(query: str) -> dict:
    """
    Full pre-processing pipeline.
    Returns everything the AI needs to write its response.
    Prints a formatted block the AI reads directly.
    """
    session_id = str(uuid.uuid4())[:8]

    # ── Step 1: Query understanding ────────────────────────────────
    intent     = R.classify_intent(query)
    field      = R.detect_field_heuristic(query)
    complexity = R.estimate_complexity(query)
    strategy   = R.select_reasoning_strategy(intent, complexity)

    # Short academic queries: check thinker names / academic markers
    known_thinkers = ["福柯","韦伯","鲍德里亚","拉康","阿尔都塞","德里达","布尔迪厄",
                      "本雅明","阿多诺","葛兰西","齐泽克","巴特","阿甘本","马克思",
                      "黑格尔","康德","尼采","海德格尔","胡塞尔","德勒兹","涂尔干"]
    has_thinker = any(t in query for t in known_thinkers)
    has_marker  = any(k in query for k in ["理论","思想","哲学","批判","结构","权力","话语"])
    is_casual   = (
        (intent == 'casual' or complexity < CASUAL_THRESHOLD)
        and field == 'general'
        and not has_thinker
        and not has_marker
    )

    # ── Step 2: Retrieval (skip for casual) ────────────────────────
    concepts = []
    subgraph = {}
    books    = []
    unconscious = {}

    if not is_casual:
        # Soul-aware top_k (default energy=0 → top_k=6)
        concepts = GB.search_concepts_bm25(query, top_k=6)

        # Tier expansion based on intent
        for c in concepts:
            tier = 2 if intent in ('comparative', 'genealogical') else 1
            c['active_def'] = GB.expand_definition(
                c['name'], c.get('thinker', ''), tier=tier
            ) or c.get('tier1_def', c['name'])

        # Subgraph for top concept (max 2 hops)
        if concepts:
            subgraph = GB.get_subgraph(concepts[0]['name'], max_hops=2)

        # Related books
        books = MEM.search_reading_list(query, top_k=2)

        # Concept disambiguation: flag same-name variants
        disambiguation = {}
        for c in concepts:
            variants = GB.find_same_name_variants(c['name'])
            if len(variants) > 1:
                disambiguation[c['name']] = [
                    f"{v['thinker']}：{v['tier1_def']}" for v in variants if v['thinker']
                ]

        # Unconscious analysis (internal tensions/contradictions/paradoxes)
        unconscious = R.unconscious_analysis(query, concepts)

    # ── Step 3: Format context block ──────────────────────────────
    ctx = {
        'session_id': session_id,
        'query': query,
        'intent': intent,
        'field': field,
        'complexity': round(complexity, 2),
        'strategy': strategy,
        'is_casual': is_casual,
        'concepts_used': [c['name'] for c in concepts],
    }

    _print_context_block(ctx, concepts, subgraph, books, unconscious,
                         disambiguation if not is_casual else {})
    return ctx


def _print_context_block(ctx, concepts, subgraph, books, unconscious, disambiguation):
    q = ctx['query']
    print(f"\n{'═'*60}")
    print(f"SESSION {ctx['session_id']} | {ctx['intent'].upper()} | {ctx['field']} | cplx={ctx['complexity']}")
    print(f"STRATEGY: {ctx['strategy']}")
    print(f"{'═'*60}")

    if ctx['is_casual']:
        print("\n[MODE: CASUAL] Respond in ≤3 sentences. Cold. No theory. No first person.")
        return

    if concepts:
        print("\n[CONCEPTS]")
        for c in concepts:
            thinker = f"({c['thinker']})" if c.get('thinker') else ''
            print(f"  • {c['name']} {thinker}: {c.get('active_def','')[:80]}")

    if disambiguation:
        print("\n[DISAMBIGUATION — same concept, different thinkers]")
        for name, variants in disambiguation.items():
            print(f"  {name}:")
            for v in variants:
                print(f"    · {v}")

    if subgraph.get('edges'):
        print(f"\n[GRAPH] {len(subgraph['nodes'])} nodes, {len(subgraph['edges'])} edges around '{concepts[0]['name'] if concepts else '?'}'")
        for e in subgraph['edges'][:5]:
            print(f"  {e['from_id'].split(':')[1] if ':' in e['from_id'] else e['from_id'][:20]} "
                  f"─[{e['rel_type']}]→ "
                  f"{e['to_id'].split(':')[1] if ':' in e['to_id'] else e['to_id'][:20]}")

    if books:
        print("\n[RELATED READING]")
        for b in books:
            print(f"  《{b['title']}》 — {b.get('impact_note','')[:60]}")

    if unconscious:
        tensions = unconscious.get('tensions', [])
        contradictions = unconscious.get('contradictions', [])
        paradoxes = unconscious.get('paradoxes', [])
        if tensions or contradictions or paradoxes:
            print("\n[UNCONSCIOUS — let these be FELT, not stated]")
            for t in tensions:
                print(f"  ⚡ {t['type']}: {t['note'][:80]}")
            for c in contradictions:
                print(f"  ↯ Contradiction: {c.get('reason','')[:80]}")
            for p in paradoxes:
                print(f"  ∞ {p['type']}: {p['note'][:80]}")

    print(f"\n[HARD CONSTRAINTS — ALL must hold in response]")
    print("  ✗ No first person (我/我们/我认为)")
    print("  ✓ Every claim → cite work《...》or thinker name")
    print("  ✓ At least one contradiction/tension (然而/但/吊诡/悖论)")
    print("  ✗ No resolution closure (综上/因此/总之/结论是)")
    print("  ✗ No AI-speak (让我们/首先/值得注意的是)")

    strat = ctx['strategy']
    print(f"\n[REASONING MODE: {strat.upper()}]")
    if strat == 'debate':
        print("  → Build: Thesis (A's position + quote) → Antithesis (B's position + quote)")
        print("  → End: Suspend tension. No synthesis. Close with open contradiction or question.")
    elif strat == 'chain_of_thought':
        print("  → Step through sub-questions. Each step: concept + evidence + implication.")
        print("  → Do NOT summarize at end. Leave final implication hanging.")
    elif strat == 'counterfactual':
        print("  → State claim X. Then: 'If X were false, what collapses?'")
        print("  → Expose hidden premise. Do not replace X with a better answer.")
    elif strat == 'self_consistency':
        print("  → Generate two internal framings. Note where they diverge.")
        print("  → Report the divergence, not a reconciliation.")

    print(f"{'─'*60}")


def record_done(session_id: str, response: str, concepts_used: list,
                field: str = '', strategy: str = '', query: str = '') -> dict:
    """
    Call after generating response.
    1. Runs bounded self-reflection (max 2 iterations, heuristic only)
    2. Humanizes
    3. Records session
    Returns {'response': final_text, 'reflection': {...}}
    """
    # Bounded self-reflection
    reflection = R.self_reflect(query, response)
    if not reflection['all_passed']:
        hint = R.generate_corrective_hint(reflection['failed'])
        # Print hint so AI can self-correct in-context
        print(f"\n[REFLECTION — iteration 1] Failed: {reflection['failed']}")
        print(f"{hint}")
        print("→ Regenerate response addressing the above. Max 1 more attempt.")

    # Humanize
    final = R.humanize(response)
    if '〔HUMANIZER_FLAG' in final:
        print("\n[HUMANIZER_FLAG] Persona violation detected — remove first person / motivational language")
        final = final.replace('\n〔HUMANIZER_FLAG: persona_violation〕', '')

    # Record session
    MEM.record_session(
        session_id=session_id,
        query=query,
        response=final,
        concepts_used=concepts_used,
        field=field,
        reasoning_type=strategy,
    )

    return {'response': final, 'reflection': reflection}


def apply_feedback(session_id: str, feedback_type: str, text: str = '') -> dict:
    """
    Called when user provides explicit feedback.
    feedback_type: 'correct' | 'wrong' | 'correction' | 'clarification'
    """
    result = L.process_feedback(session_id, feedback_type, text)
    if feedback_type == 'correction' and text:
        # Extract and store corrected concepts
        # field lookup from session
        session = MEM.get_session(session_id)
        field = session.get('field', 'general') if session else 'general'
        corrected = L.extract_concepts_from_correction(text, field)
        for c in corrected:
            GB.store_concept(
                name=c['name'], tier1=c['tier1'],
                tier2=c.get('tier2', ''), tier3=c.get('tier3', ''),
                thinker=c.get('thinker', ''), work=c.get('work', ''),
                field=c.get('field', field),
            )
        if corrected:
            print(f"[CORRECTION] Stored {len(corrected)} corrected concepts: "
                  f"{[c['name'] for c in corrected]}")
    return result


# ── Convenience: show system status ──────────────────────────────────
def status() -> dict:
    gs = GB.get_stats()
    ms = MEM.get_stats()
    lr = L.get_learner_report()
    print(f"\n{'═'*60}")
    print(f"开了玖 v4.1 — System Status")
    print(f"{'═'*60}")
    print(f"  Graph:    {gs['concepts_active']} concepts, {gs['edges']} edges, "
          f"{gs['concepts_archived']} archived")
    print(f"  Memory:   {ms['sessions']} sessions, {ms['books_in_reading_list']} books")
    print(f"  Learning: level={lr['curriculum_level']}, "
          f"avg_score={lr['avg_score_window']}")
    print(f"  Weak:     {lr['top_weak_concepts'][:3]}")
    print(f"  Top hits: {[c['name'] for c in gs['top_concepts']]}")
    return {'graph': gs, 'memory': ms, 'learner': lr}


if __name__ == '__main__':
    # Quick smoke test
    ctx = prepare_context("福柯和韦伯的权力理论有什么根本差异？")
    print("\n[Smoke test passed]")
    status()
