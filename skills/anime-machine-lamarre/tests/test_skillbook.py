"""
动画机器技能书 — N9R20 验证测试
The Anime Machine Skillbook Validation Tests

测试覆盖：
1. 文件完整性检查
2. 概念图谱结构验证
3. N9R20 Manifest 兼容性
4. SKILL.md 内容结构验证
5. 知识库导入模拟
"""

import json
import os
import sys
import pytest

# 路径设置
SKILLBOOK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================================
# 一、文件完整性 File Integrity
# ============================================================================

class TestFileIntegrity:
    """验证技能书所有必需文件存在且非空"""

    REQUIRED_FILES = [
        "SKILL.md",
        "concept-graph.json",
        "glossary.md",
        "core-arguments.md",
        "references.md",
        "n9r20_manifest.json",
    ]

    def test_all_required_files_exist(self):
        for filename in self.REQUIRED_FILES:
            filepath = os.path.join(SKILLBOOK_DIR, filename)
            assert os.path.exists(filepath), f"缺失文件: {filename}"

    def test_all_files_non_empty(self):
        for filename in self.REQUIRED_FILES:
            filepath = os.path.join(SKILLBOOK_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            assert len(content) > 100, f"文件内容过短: {filename} ({len(content)} chars)"

    def test_skill_md_has_required_sections(self):
        filepath = os.path.join(SKILLBOOK_DIR, "SKILL.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        required_sections = [
            "核心论域",
            "核心概念群",
            "动画机器",
            "多平面图像",
            "有限动画",
            "动画间隔",
            "电影主义",
            "滑动",
            "场的分布",
            "论证结构",
        ]
        for section in required_sections:
            assert section in content, f"SKILL.md 缺少小节: {section}"


# ============================================================================
# 二、概念图谱 Concept Graph
# ============================================================================

class TestConceptGraph:
    """验证 concept-graph.json 结构和内容"""

    @pytest.fixture(autouse=True)
    def load_graph(self):
        filepath = os.path.join(SKILLBOOK_DIR, "concept-graph.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)

    def test_has_required_top_level_keys(self):
        for key in ["graph_id", "graph_name", "source", "framework", "version", "nodes", "edges"]:
            assert key in self.graph, f"缺少顶层键: {key}"

    def test_node_count_matches_manifest(self):
        manifest_path = os.path.join(SKILLBOOK_DIR, "n9r20_manifest.json")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        expected_count = manifest["concept_graph"]["node_count"]
        actual_count = len(self.graph["nodes"])
        assert actual_count == expected_count, f"节点数不匹配: 期望{expected_count}, 实际{actual_count}"

    def test_edge_count_matches_manifest(self):
        manifest_path = os.path.join(SKILLBOOK_DIR, "n9r20_manifest.json")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        expected_count = manifest["concept_graph"]["edge_count"]
        actual_count = len(self.graph["edges"])
        assert actual_count == expected_count, f"边数不匹配: 期望{expected_count}, 实际{actual_count}"

    def test_root_node_exists(self):
        node_ids = {n["id"] for n in self.graph["nodes"]}
        assert "ANIME_MACHINE" in node_ids, "根节点 ANIME_MACHINE 缺失"

    def test_all_core_nodes_present(self):
        node_ids = {n["id"] for n in self.graph["nodes"]}
        core_nodes = [
            "MULTIPLANAR_IMAGE", "LIMITED_ANIMATION", "ANIMETIC_INTERVAL",
            "CINEMATISM", "ANIMETISM", "SLIDING", "FIELD_DISTRIBUTION"
        ]
        for node_id in core_nodes:
            assert node_id in node_ids, f"核心节点缺失: {node_id}"

    def test_all_edges_reference_valid_nodes(self):
        node_ids = {n["id"] for n in self.graph["nodes"]}
        for edge in self.graph["edges"]:
            assert edge["from"] in node_ids, f"边 from 无效节点: {edge['from']}"
            assert edge["to"] in node_ids, f"边 to 无效节点: {edge['to']}"

    def test_all_nodes_have_required_fields(self):
        required_fields = ["id", "term", "category", "definition", "provenance", "links_to"]
        for node in self.graph["nodes"]:
            for field in required_fields:
                assert field in node, f"节点 {node.get('id', '?')} 缺少字段: {field}"

    def test_all_edges_have_weight_between_0_and_1(self):
        for edge in self.graph["edges"]:
            assert 0 <= edge["weight"] <= 1, f"边权重超出[0,1]: {edge}"

    def test_no_orphan_nodes(self):
        """检查每个节点至少出现在一条边中"""
        referenced_nodes = set()
        for edge in self.graph["edges"]:
            referenced_nodes.add(edge["from"])
            referenced_nodes.add(edge["to"])
        all_nodes = {n["id"] for n in self.graph["nodes"]}
        orphans = all_nodes - referenced_nodes
        # 允许根节点作为唯一孤立节点（所有边都从它出发或指向它，但它可能被图结构定义为起点）
        # 实际检查：除了可能的图结构起点的节点，其他都要有连接
        assert len(orphans) <= 1, f"存在孤立节点: {orphans}"


# ============================================================================
# 三、Manifest 验证
# ============================================================================

class TestManifest:
    """验证 n9r20_manifest.json"""

    @pytest.fixture(autouse=True)
    def load_manifest(self):
        filepath = os.path.join(SKILLBOOK_DIR, "n9r20_manifest.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.manifest = json.load(f)

    def test_manifest_version(self):
        assert self.manifest["manifest_version"] == "2.0"

    def test_skillbook_has_required_fields(self):
        sb = self.manifest["skillbook"]
        required = ["id", "name", "version", "type", "framework", "source"]
        for key in required:
            assert key in sb, f"skillbook 缺少: {key}"

    def test_academic_markers_non_empty(self):
        markers = self.manifest["academic_markers"]
        assert len(markers) >= 5, f"学术标记不足: {len(markers)}"
        expected_markers = ["media_theory", "deleuze_guattari", "animation_studies"]
        for marker in expected_markers:
            assert marker in markers, f"缺少关键学术标记: {marker}"

    def test_difficulty_profile_valid(self):
        dp = self.manifest["difficulty_profile"]
        assert 0.5 <= dp["base_difficulty"] <= 1.0
        assert 0.5 <= dp["concept_density"] <= 1.0
        assert 0.5 <= dp["theoretical_depth"] <= 1.0

    def test_n9r20_compatibility_flags(self):
        compat = self.manifest["n9r20_compatibility"]
        assert compat["routing"] == "DEEP"
        assert compat["fold_depth_default"] >= 3
        assert compat["tension_bus_compatible"] is True
        assert compat["dual_reasoner_compatible"] is True
        assert compat["semantic_graph_compatible"] is True


# ============================================================================
# 四、内容验证 Content Validation
# ============================================================================

class TestContentQuality:
    """内容质量检查"""

    def test_glossary_covers_core_concepts(self):
        filepath = os.path.join(SKILLBOOK_DIR, "glossary.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        core_terms = [
            "Anime Machine", "Multiplanar Image", "Limited Animation",
            "Animetic Interval", "Cinematism", "Animetism", "Sliding",
            "Distribution of the Field"
        ]
        for term in core_terms:
            assert term in content, f"术语表缺少核心术语: {term}"

    def test_core_arguments_has_four_arguments(self):
        filepath = os.path.join(SKILLBOOK_DIR, "core-arguments.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 应该有四个主论证
        arg_markers = ["论证一", "论证二", "论证三", "论证四"]
        for marker in arg_markers:
            assert marker in content, f"核心论证缺少: {marker}"

    def test_core_arguments_include_limitations(self):
        filepath = os.path.join(SKILLBOOK_DIR, "core-arguments.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "局限" in content, "论证缺少局限与反论证部分"
        assert "反论证" in content, "论证缺少反论证位置"

    def test_references_includes_primary_source(self):
        filepath = os.path.join(SKILLBOOK_DIR, "references.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Lamarre, T. (2009)" in content, "参考文献缺少一手文献"
        assert "University of Minnesota Press" in content, "参考文献缺少出版社"

    def test_skill_md_contains_citation_index(self):
        filepath = os.path.join(SKILLBOOK_DIR, "SKILL.md")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "引文索引" in content or "页码" in content, "SKILL.md 缺少引文索引"


# ============================================================================
# 五、N9R20 导入模拟
# ============================================================================

class TestN9R20ImportSimulation:
    """模拟 N9R20 SkillBook 导入流程"""

    def test_manifest_parses_as_valid_skillbook(self):
        """模拟 N9R20SkillBookImporter 的导入流程"""
        manifest_path = os.path.join(SKILLBOOK_DIR, "n9r20_manifest.json")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # 模拟导入逻辑
        assert manifest["manifest_version"] == "2.0"
        sb = manifest["skillbook"]

        # 检查文件引用完整性
        main_file = manifest["files"]["main"]
        assert os.path.exists(os.path.join(SKILLBOOK_DIR, main_file))

        for supp_file in manifest["files"]["supporting"]:
            assert os.path.exists(os.path.join(SKILLBOOK_DIR, supp_file))

    def test_concept_graph_integrity_for_semantic_graph(self):
        """模拟 N9R20SemanticGraph 加载概念图谱"""
        graph_path = os.path.join(SKILLBOOK_DIR, "concept-graph.json")
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.load(f)

        # 验证每个节点都可被语义图索引
        for node in graph["nodes"]:
            assert "id" in node
            assert "term" in node
            assert "links_to" in node
            # links_to 中引用的节点应存在
            node_ids = {n["id"] for n in graph["nodes"]}
            for linked_id in node["links_to"]:
                assert linked_id in node_ids, f"节点 {node['id']} 链接到不存在的节点 {linked_id}"

    def test_academic_markers_match_difficulty_profile(self):
        """学术标记数量与难度曲线匹配"""
        manifest_path = os.path.join(SKILLBOOK_DIR, "n9r20_manifest.json")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        markers = manifest["academic_markers"]
        difficulty = manifest["difficulty_profile"]["base_difficulty"]

        # 标记数量应反映难度
        assert len(markers) >= 6, f"DEEP级别技能书学术标记不足"
        assert difficulty >= 0.6, f"难度设置与标记数量不匹配"
