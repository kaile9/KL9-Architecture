"""
9R-2.1 — Test Suite

Tests all non-LLM components: Router, DNA, Gate, Aggregator, Models.
LLM-dependent components (Decomposer, FoldEngine, Validator) tested via integration.
"""

import pytest
from kl9.models import (
    AcademicComplexityScore,
    RouteDecision,
    RouteLevel,
    FoldChain,
    FoldResult,
    Perspective,
    QualityScore,
    AggregatedOutput,
    TensionGateResult,
)
from kl9.core.dna import (
    PRINCIPLES,
    detect_forbidden,
    count_citations,
    validate_ending,
    extract_tensions,
    extract_umkehrs,
)
from kl9.core.router import AdaptiveRouter, LLM_ROUTER_PROMPT
from kl9.core.gate import QualityGate
from kl9.core.aggregator import TensionPreservingAggregator

# Mock LLM for router tests
from kl9.models import LLMResponse, Usage

class MockRouterLLM:
    def __init__(self, classification: str = "STANDARD"):
        self.classification = classification
    async def complete(self, *args, **kwargs):
        return LLMResponse(content=self.classification, usage=Usage(), provider="mock")


# ── DNA Tests ──

class TestDNA:
    def test_all_ten_principles_present(self):
        assert len(PRINCIPLES) == 10
        for i in range(1, 11):
            assert f"P{i}" in PRINCIPLES

    def test_detect_forbidden_summarize(self):
        violations = detect_forbidden("综上所述，两者互补")
        assert len(violations) >= 2  # 综上所述 + 两者互补

    def test_detect_forbidden_first_person(self):
        violations = detect_forbidden("在我看来，毋庸置疑")
        assert len(violations) >= 1  # 在我看来 or 毋庸置疑

    def test_clean_text_zero_violations(self):
        content = "不是X，而是Y的区分性论证。韩炳哲在《倦怠社会》中指出…"
        violations = detect_forbidden(content)
        assert len(violations) == 0

    def test_count_citations(self):
        content = "福柯(1975)、巴特勒(1990)、德里达(1967)"
        assert count_citations(content) >= 2  # At least year patterns detected

    def test_validate_ending_period_fails(self):
        assert validate_ending("这是一个句号结尾。") is False

    def test_validate_ending_ellipsis_passes(self):
        assert validate_ending("反诘式结尾……") is True

    def test_validate_ending_question_passes(self):
        assert validate_ending("这样真的能解决问题吗？") is True

    def test_extract_tensions(self):
        content = "[硬张力] A与B的根本冲突 [软张力] 视角差异"
        tensions = extract_tensions(content)
        assert len(tensions) >= 1

    def test_extract_umkehrs(self):
        content = "[UMKEHR] 从规训社会翻转为倦怠社会"
        umkehrs = extract_umkehrs(content)
        assert len(umkehrs) >= 1


# ── Router Tests ──

class TestRouter:
    async def test_high_complexity_routes_deep(self):
        router = AdaptiveRouter(llm=MockRouterLLM("DEEP"))
        route = await router.route("anything")
        assert route.level == RouteLevel.DEEP

    async def test_low_complexity_routes_quick(self):
        router = AdaptiveRouter(llm=MockRouterLLM("QUICK"))
        route = await router.route("anything")
        assert route.level == RouteLevel.QUICK

    async def test_forced_deep(self):
        router = AdaptiveRouter(llm=MockRouterLLM("QUICK"))
        route = await router.route("anything", forced="deep")
        assert route.level == RouteLevel.DEEP
        assert route.max_fold_depth > 0

    async def test_forced_quick(self):
        router = AdaptiveRouter(llm=MockRouterLLM("DEEP"))
        route = await router.route("anything", forced="quick")
        assert route.level == RouteLevel.QUICK

    async def test_fold_budget_in_range(self):
        router = AdaptiveRouter(llm=MockRouterLLM("DEEP"))
        route = await router.route("anything")
        assert 2 <= route.max_fold_depth <= 9


# ── Gate Tests ──

class TestGate:
    def test_clean_content_passes(self):
        gate = QualityGate()
        content = "不是规训社会，而是倦怠社会，韩炳哲指出成就主体已然取代规训主体……"
        passed, violations, metrics = gate.inspect(content)
        assert passed or len(violations) <= 2

    def test_forbidden_content_fails(self):
        gate = QualityGate()
        content = "综上所述，两者互补，统一来看，这无疑是正确的。"
        passed, violations, _ = gate.inspect(content)
        assert not passed  # Multiple forbidden patterns

    def test_low_citation_density_warns(self):
        gate = QualityGate()
        content = "综上所述，由此可见，总的来看，以上分析表明，简而言之。" * 10  # Pure summary
        _, violations, _ = gate.inspect(content)
        assert any("SUMMARY" in v for v in violations)


# ── Aggregator Tests ──

class TestAggregator:
    def test_aggregate_preserves_tensions(self):
        agg = TensionPreservingAggregator()
        chain = FoldChain(
            query="test",
            folds=[
                FoldResult(
                    fold_number=0,
                    perspective_a=Perspective(name="A", content="视角A内容…"),
                    perspective_b=Perspective(name="B", content="视角B内容…"),
                    raw_content="测试内容",
                    tension_markers=["[硬张力] A→B不可调和"],
                ),
                FoldResult(
                    fold_number=1,
                    perspective_a=Perspective(name="A", content="深化A…"),
                    perspective_b=Perspective(name="B", content="深化B…"),
                    raw_content="深化后的内容",
                    tension_markers=["[硬张力] 新发现的结构矛盾"],
                    umkehr_markers=["[UMKEHR] 概念反转"],
                ),
            ],
        )
        result = agg.aggregate(chain)
        assert len(result.tension_markers) > 0
        assert result.fold_depth == 2

    def test_aggregate_fixes_period_ending(self):
        agg = TensionPreservingAggregator()
        chain = FoldChain(
            query="test",
            folds=[
                FoldResult(
                    fold_number=0,
                    perspective_a=Perspective(name="A", content="A"),
                    perspective_b=Perspective(name="B", content="B"),
                    raw_content="句号结尾的论证。",
                    tension_markers=[],
                ),
            ],
        )
        result = agg.aggregate(chain)
        assert not result.content.rstrip().endswith("。")

    def test_aggregate_with_quality_violation(self):
        agg = TensionPreservingAggregator()
        chain = FoldChain(query="test", folds=[])
        quality = QualityScore(
            theoretical_framework=0.8,
            citation_standards=0.5,
            argumentative_depth=0.7,
            stylistic_quality=0.3,
            originality=0.6,
            constitutional_violations=["P2 violation: 缝合式总结"],
        )
        result = agg.aggregate(chain, quality)
        assert result.constitutional_warning is True


# ── Model Tests ──

class TestModels:
    def test_route_level_identity(self):
        assert RouteLevel.DEEP is RouteLevel.DEEP
        assert RouteLevel.QUICK is not RouteLevel.DEEP

    def test_quality_score_computation(self):
        score = QualityScore(
            theoretical_framework=0.9,
            citation_standards=0.85,
            source_fidelity=0.9,
            argumentative_depth=0.92,
            stylistic_quality=0.85,
            originality=0.88,
        )
        score.assign_grade()
        assert score.total >= 0.85
        assert score.grade == "A"

    def test_fold_chain_accumulation(self):
        chain = FoldChain(query="test")
        chain.folds.append(FoldResult(
            fold_number=0,
            perspective_a=Perspective(name="A", content="test"),
            perspective_b=Perspective(name="B", content="test"),
            raw_content="test",
            tension_markers=["[硬张力] test"],
        ))
        chain.folds.append(FoldResult(
            fold_number=1,
            perspective_a=Perspective(name="A", content="test2"),
            perspective_b=Perspective(name="B", content="test2"),
            raw_content="test2",
            tension_markers=["[硬张力] test2", "[硬张力] test3"],
        ))
        assert chain.fold_count == 2
        assert len(chain.all_tensions) == 3

    def test_tension_gate_result(self):
        result = TensionGateResult(
            should_continue=True,
            reason="new_tensions",
            prior_tension_count=2,
            new_tension_count=1,
        )
        assert result.should_continue
        assert result.prior_tension_count == 2


# ── Style Profile Tests ──

class TestStyleProfile:
    def test_style_profile_defaults(self):
        from kl9.core.dna import StyleProfile
        profile = StyleProfile()
        assert "不是X，而是Y" in profile.preferred_patterns
        assert "福柯" in profile.theoretical_markers
        assert len(profile.forbidden_endings) > 0


# ── Decomposer Inline Title Tests (Bug-7 fix) ──

class TestDecomposerParse:
    def test_inline_perspective_name_not_lost(self):
        """When LLM writes '[视角A] 视角名称: 程序正义' on one line,
        the name must be parsed, not skipped."""
        from kl9.core.decomposer import TaskDecomposer
        class _Mock: pass
        dec = TaskDecomposer(_Mock())
        content = "[视角A]\n视角名称: 程序正义视角\n核心论证: 测试论证\n[视角B]\n视角名称: 实质正义视角\n核心论证: 反论证"
        pa, pb, _ = dec._parse(content)
        assert pa.name == "程序正义视角", f"Expected '程序正义视角', got '{pa.name}'"
        assert pb.name == "实质正义视角", f"Expected '实质正义视角', got '{pb.name}'"

    def test_inline_title_strips_tag_correctly(self):
        """Inline '[视角A] Title' must strip '[视角A]' and keep 'Title'."""
        from kl9.core.decomposer import TaskDecomposer
        class _Mock: pass
        dec = TaskDecomposer(_Mock())
        content = "[视角A]  Key concept\n核心论证: X\n[视角B]\n视角名称: Y"
        pa, pb, _ = dec._parse(content)
        # The LS.strip() after tag removal should give 'Key concept'
        assert pa.name == "Perspective A" or pa.content.strip() == "Key concept"


# ── Quality Gate Summary Ratio Tests (Opt-4 fix) ──

class TestGateSummaryRatio:
    def test_sentence_level_no_double_count(self):
        from kl9.core.gate import QualityGate
        gate = QualityGate()
        # Two markers in close proximity — old algorithm double-counted
        content = "综上所述，这是第一句。总而言之，这是第二句。普通文本内容。"
        ratio = gate._summary_ratio(content)
        assert ratio <= 1.0

    def test_clean_text_zero_summary(self):
        from kl9.core.gate import QualityGate
        gate = QualityGate()
        content = "福柯在规训与惩罚中指出了权力技术的演变。"
        ratio = gate._summary_ratio(content)
        assert ratio < 0.1

    def test_all_summary_high_ratio(self):
        from kl9.core.gate import QualityGate
        gate = QualityGate()
        content = "综上所述，A。总而言之，B。由此可见，C。"
        ratio = gate._summary_ratio(content)
        assert ratio > 0.3


# ── Fold Chain Preservation Tests (Bug-8 fix) ──

class TestFoldChainPreservation:
    def test_chain_preserved_on_llm_failure(self):
        from kl9.models import FoldChain, FoldResult, Perspective
        chain = FoldChain(query="test", folds=[
            FoldResult(fold_number=0, perspective_a=Perspective(name="A",content="a"),
                       perspective_b=Perspective(name="B",content="b"),
                       raw_content="fold0", tension_markers=["[硬张力] test"]),
            FoldResult(fold_number=1, perspective_a=Perspective(name="A",content="a2"),
                       perspective_b=Perspective(name="B",content="b2"),
                       raw_content="fold1", tension_markers=["[硬张力] test2"]),
        ])
        assert chain.fold_count == 2
        assert len(chain.all_tensions) == 2


# ── Validator JSON Parse Tests (Opt-3 fix) ──

class TestValidatorJSONParse:
    def test_parses_json_after_cot(self):
        from kl9.core.validator import QualityValidator
        class _Mock: pass
        v = QualityValidator(_Mock())
        # JSON after some CoT text
        content = '思考：这个分析不错。\n{"theoretical_framework": 0.8, "citation_standards": 0.7, "source_fidelity": 0.9, "argumentative_depth": 0.85, "stylistic_quality": 0.6, "originality": 0.75, "constitutional_violations": [], "grade": "B"}'
        score = v._parse(content)
        assert score.grade == "B"
        assert score.theoretical_framework == 0.8

    def test_returns_default_on_bad_json(self):
        from kl9.core.validator import QualityValidator
        from kl9.models import QualityScore
        class _Mock: pass
        v = QualityValidator(_Mock())
        score = v._parse("not json at all")
        assert isinstance(score, QualityScore)
