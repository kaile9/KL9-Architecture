"""
9R-2.0 RHIZOME · Semantic-Graph
语义图谱 · 整合 graph + 术语网络 · 动态扩展

设计原则：
1. 去中心化：术语节点平等连接，无根节点
2. 动态扩展：从 query 中自动提取并连接新术语
3. 边权重衰减：随时间衰减，模拟记忆遗忘曲线
4. 概念簇检测：基于边权重的社区发现
5. 张力映射：识别语义空间中的概念张力

重构说明（魔法数字消除）：
- 所有数值常量引用 core/n9r20_config.py 中的 N9R20SemanticGraphConfig
- N9R20ConceptConflictDetector 集成到语义图中
"""

import time
import re
import math
import threading
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque

from core.n9r20_structures import N9R20TermNode, N9R20ConceptConflict
from core.n9r20_tension_bus import (
    N9R20TensionBus, n9r20_bus, N9R20TensionType,
    N9R20CompressionTensionEvent, N9R20CompressionCompleteEvent,
    N9R20ConceptClusterEvent, N9R20TensionSubscription,
)
from core.n9r20_config import (
    n9r20_semantic_graph_config as SG_CFG,
    n9r20_tension_config        as T_CFG,
)


# ═══════════════════════════════════════════════════════════
# 辅助数据结构
# ═══════════════════════════════════════════════════════════

class N9R20EdgeWeightDecay:
    """
    边权重衰减器

    模拟认知记忆的遗忘曲线：
    - 半衰期来自 SG_CFG.EDGE_DECAY_HALFLIFE（默认 3600 秒）
    - 每次访问增强权重（赫布学习）
    - 低于 SG_CFG.EDGE_PRUNE_THRESHOLD 的边自动剪枝
    """

    def __init__(
        self,
        half_life: float = SG_CFG.EDGE_DECAY_HALFLIFE,
        prune_threshold: float = SG_CFG.EDGE_PRUNE_THRESHOLD,
    ):
        self.half_life = half_life
        self.prune_threshold = prune_threshold
        self._decay_constant = math.log(2) / half_life

    def decay(self, weight: float, last_updated: float, now: float) -> float:
        """指数衰减：weight * e^(-λ·Δt)"""
        dt = now - last_updated
        if dt < 0:
            return weight
        return max(weight * math.exp(-self._decay_constant * dt), 0.0)

    def reinforce(self, weight: float, increment: float = SG_CFG.EDGE_REINFORCE_INCREMENT) -> float:
        """赫布强化：每次共现增强权重"""
        return min(weight + increment, 1.0)

    def should_prune(self, weight: float) -> bool:
        """判断边是否应被剪枝"""
        return weight < self.prune_threshold


class N9R20ConceptCluster:
    """
    概念簇 — 语义图谱中的社区

    通过边权重进行社区发现，形成动态概念簇。
    每个簇代表一个语义子空间。
    """

    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self.terms: Set[str] = set()
        self.centroid: str = ""
        self.intra_density: float = 0.0
        self.inter_tension: Dict[str, float] = {}
        self.created_at: float = time.time()
        self.last_updated: float = time.time()

    @property
    def size(self) -> int:
        return len(self.terms)

    def compute_density(self, edges: Dict[Tuple[str, str], float]) -> float:
        """计算簇内密度：实际边权重和 / 最大可能边权重和"""
        if self.size < 2:
            return 0.0
        max_edges = self.size * (self.size - 1) / 2
        actual_sum = sum(
            w for (a, b), w in edges.items()
            if a in self.terms and b in self.terms
        )
        return actual_sum / max_edges if max_edges > 0 else 0.0


# ═══════════════════════════════════════════════════════════
# 概念冲突检测器
# ═══════════════════════════════════════════════════════════

class N9R20ConceptConflictDetector:
    """
    概念冲突检测器

    当同一术语在不同上下文中具有不同含义时检测冲突。

    方法：
    - detect_conflict(term, context_A, context_B)  → Optional[N9R20ConceptConflict]
    - detect_all_conflicts()                        → List[N9R20ConceptConflict]
    - generate_conflict_report()                    → str（自然语言报告）
    """

    # 冲突类型标识
    CONFLICT_TYPE_DEFINITION  = "definition"   # 定义差异
    CONFLICT_TYPE_PERSPECTIVE = "perspective"  # 视角差异
    CONFLICT_TYPE_TENSION     = "tension"      # 语义张力差异

    # 严重程度阈值
    SEVERITY_THRESHOLD = 0.3  # 低于此值不报告

    def __init__(self, graph: 'N9R20SemanticGraph' = None):
        self._graph = graph or n9r20_semantic_graph

    def detect_conflict(
        self,
        term: str,
        context_A: str,
        context_B: str,
    ) -> Optional[N9R20ConceptConflict]:
        """
        检测同一术语在两个上下文之间是否存在冲突

        策略：
        1. 获取术语节点
        2. 比较两个上下文的变体定义
        3. 计算语义差异度 → severity

        返回 N9R20ConceptConflict，或 None（无冲突/无数据）。
        """
        node = self._graph.query_term(term)
        if node is None:
            return None

        variant_a = node.get_variant(context_A)
        variant_b = node.get_variant(context_B)

        # 至少需要一个变体存在
        if variant_a is None and variant_b is None:
            return None

        # 如果只有一个变体，生成一个默认空变体用于对比
        variant_a = variant_a or {}
        variant_b = variant_b or {}

        # 计算严重程度
        severity, conflict_type = self._compute_severity(
            term, variant_a, variant_b, context_A, context_B
        )

        if severity < self.SEVERITY_THRESHOLD:
            return None

        return N9R20ConceptConflict(
            term=term,
            variant_A=variant_a,
            variant_B=variant_b,
            conflict_type=conflict_type,
            severity=round(severity, 2),
            context_A=context_A,
            context_B=context_B,
        )

    def detect_all_conflicts(self) -> List[N9R20ConceptConflict]:
        """
        遍历所有具有多个上下文变体的术语，检测所有冲突

        返回按 severity 降序排列的冲突列表。
        """
        conflicts: List[N9R20ConceptConflict] = []

        for term, node in self._graph.nodes.items():
            contexts = list(node.context_variants.keys())
            if len(contexts) < 2:
                continue

            # 两两比较
            for i in range(len(contexts)):
                for j in range(i + 1, len(contexts)):
                    conflict = self.detect_conflict(term, contexts[i], contexts[j])
                    if conflict is not None:
                        conflicts.append(conflict)

        # 按严重程度降序排序
        conflicts.sort(key=lambda c: c.severity, reverse=True)
        return conflicts

    def generate_conflict_report(self) -> str:
        """
        生成自然语言冲突报告

        格式：
          = 概念冲突报告 =
          检测到 N 个概念冲突（共 M 个术语节点）
          1. [严重] 术语"xxx"：...
          2. [中等] 术语"yyy"：...
          ...
          未检测到冲突。（无冲突时）
        """
        conflicts = self.detect_all_conflicts()
        total_nodes = len(self._graph.nodes)

        lines = ["= 概念冲突报告 =", f"节点总数：{total_nodes}"]

        if not conflicts:
            lines.append("未检测到概念冲突。")
            return "\n".join(lines)

        lines.append(f"检测到 {len(conflicts)} 个概念冲突：\n")

        for i, c in enumerate(conflicts, 1):
            severity_label = (
                "严重" if c.severity >= 0.7 else
                "中等" if c.severity >= 0.4 else
                "轻微"
            )
            lines.append(f"{i}. [{severity_label}] 术语「{c.term}」（{c.conflict_type} 冲突，严重程度 {c.severity:.0%}）")
            def_a = str(c.variant_A.get("definition", "（未定义）"))[:100]
            def_b = str(c.variant_B.get("definition", "（未定义）"))[:100]
            lines.append(f"   · 上下文 {c.context_A!r}：{def_a}")
            lines.append(f"   · 上下文 {c.context_B!r}：{def_b}")
            lines.append(f"   → {c.to_natural_description()}")

        return "\n".join(lines)

    # ── 内部方法 ──────────────────────────────────────────

    def _compute_severity(
        self,
        term: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        context_a: str,
        context_b: str,
    ) -> Tuple[float, str]:
        """
        计算冲突严重程度与类型

        策略：
        1. 定义文本相似度（字符集 Jaccard 距离）
        2. 置信度差异
        3. 综合加权
        """
        severity = 0.5  # 默认中等
        conflict_type = self.CONFLICT_TYPE_DEFINITION

        def_a = str(variant_a.get("definition", ""))
        def_b = str(variant_b.get("definition", ""))

        if def_a and def_b:
            # Jaccard 字符集相似度
            chars_a, chars_b = set(def_a), set(def_b)
            union = chars_a | chars_b
            intersection = chars_a & chars_b
            similarity = len(intersection) / len(union) if union else 1.0
            severity = 1.0 - similarity
            conflict_type = self.CONFLICT_TYPE_DEFINITION

        elif def_a or def_b:
            # 只有一方有定义 → 高差异
            severity = 0.8
            conflict_type = self.CONFLICT_TYPE_PERSPECTIVE

        # 置信度差异加成
        conf_a = float(variant_a.get("confidence", 0.7))
        conf_b = float(variant_b.get("confidence", 0.7))
        conf_diff = abs(conf_a - conf_b)
        severity = min(severity + conf_diff * 0.2, 1.0)

        # 上下文名称暗示张力（如 "佛教" vs "物理"）
        if context_a != context_b:
            conflict_type = self.CONFLICT_TYPE_TENSION if severity > 0.5 else conflict_type

        return round(severity, 2), conflict_type


# ═══════════════════════════════════════════════════════════
# 语义图谱核心
# ═══════════════════════════════════════════════════════════

class N9R20SemanticGraph:
    """
    语义图谱 · 动态术语网络

    核心功能：
    1. 术语提取与节点管理（去中心化）
    2. 边权重动态更新（赫布学习 + 衰减）
    3. 概念簇检测（基于边权重的社区发现）
    4. 张力映射（识别概念间的语义张力）
    5. 动态扩展（从 query 中学习新术语）
    6. 概念冲突检测（N9R20ConceptConflictDetector）

    与 N9R20TensionBus 集成：
    - 订阅 N9R20CompressionTensionEvent：参与压缩流程，提供术语网络上下文
    - 发射 N9R20ConceptClusterEvent：当检测到显著的概念簇变化时
    """

    def __init__(self):
        # ═══ 核心图谱结构 ═══
        self._nodes: Dict[str, N9R20TermNode] = {}
        self._edges: Dict[Tuple[str, str], float] = {}
        self._clusters: Dict[str, N9R20ConceptCluster] = {}
        self._term_to_cluster: Dict[str, str] = {}

        # ═══ 元信息 ═══
        self._decayer = N9R20EdgeWeightDecay()
        self._lock = threading.RLock()
        self._total_terms_seen: int = 0
        self._total_sessions: int = 0

        # ═══ 概念冲突检测器（延迟初始化避免循环引用） ═══
        self._conflict_detector: Optional[N9R20ConceptConflictDetector] = None

        # ═══ N9R20TensionBus 集成 ═══
        self.n9r20_bus = n9r20_bus
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="semantic-graph",
            role="subscriber",
            tension_types=[N9R20TensionType.SEMANTIC],
            event_types=["N9R20CompressionTensionEvent", "N9R20CompressionCompleteEvent"],
            priority=2,
            callback=self._on_event,
        ))

    @property
    def conflict_detector(self) -> N9R20ConceptConflictDetector:
        """延迟初始化概念冲突检测器"""
        if self._conflict_detector is None:
            self._conflict_detector = N9R20ConceptConflictDetector(self)
        return self._conflict_detector

    # ═══════════════════════════════════════════════
    # 公共 API
    # ═══════════════════════════════════════════════

    def add_term(
        self,
        term: str,
        source_session: str = "",
        confidence: float = SG_CFG.TERM_CONFIDENCE_DEFAULT,
    ) -> N9R20TermNode:
        """
        添加或获取术语节点（去中心化 — 无层级结构）

        赫布强化：已存在术语的置信度提升 TERM_CONFIDENCE_INCREMENT。
        """
        with self._lock:
            if term in self._nodes:
                node = self._nodes[term]
                node.confidence = min(
                    node.confidence + SG_CFG.TERM_CONFIDENCE_INCREMENT, 1.0
                )
                return node

            node = N9R20TermNode(
                term=term,
                edges={},
                source_session=source_session,
                confidence=confidence,
                added_timestamp=time.time(),
            )
            self._nodes[term] = node
            self._total_terms_seen += 1
            return node

    def add_term_with_context(
        self,
        term: str,
        context: str,
        definition: str,
        confidence: float = SG_CFG.TERM_CONFIDENCE_DEFAULT,
        source_session: str = "",
    ) -> N9R20TermNode:
        """
        添加术语节点，并注册一个上下文变体

        当同一术语在不同上下文中出现时（如"空"在物理学与佛学中），
        自动检测冲突并广播到 TensionBus。
        """
        node = self.add_term(term, source_session, confidence)
        existing_contexts = list(node.context_variants.keys())

        # 注册新变体
        node.add_variant(context, definition, confidence)

        # 与已有变体比较，触发冲突检测
        for old_ctx in existing_contexts:
            conflict = self.conflict_detector.detect_conflict(term, old_ctx, context)
            if conflict is not None:
                # 将冲突信息发射到 TensionBus（使用语义张力事件携带）
                self.n9r20_bus.emit(N9R20CompressionTensionEvent(
                    query=f"[CONFLICT] {term}: {old_ctx} ↔ {context}",
                    session_id=source_session,
                    fold_depth=0,
                    target_fold_depth=0,
                    target_ratio=0.0,
                    urgency=conflict.severity,
                ))

        return node

    def add_edge(
        self,
        term_a: str,
        term_b: str,
        weight: float = SG_CFG.EDGE_INITIAL_WEIGHT,
        source_session: str = "",
    ) -> None:
        """
        添加或更新边（无向边，按字母序存储）

        赫布学习：每次共现增强权重。
        """
        if term_a == term_b:
            return
        key = tuple(sorted([term_a, term_b]))

        with self._lock:
            self.add_term(term_a, source_session)
            self.add_term(term_b, source_session)

            now = time.time()
            if key in self._edges:
                existing = self._edges[key]
                decayed = self._decayer.decay(
                    existing, self._nodes[term_a].added_timestamp, now
                )
                self._edges[key] = self._decayer.reinforce(decayed, weight)
            else:
                self._edges[key] = weight

            self._nodes[term_a].edges[term_b] = self._edges[key]
            self._nodes[term_b].edges[term_a] = self._edges[key]
            self._nodes[term_a].added_timestamp = now
            self._nodes[term_b].added_timestamp = now

    def extract_terms_from_query(
        self,
        query: str,
        session_id: str = "",
    ) -> List[str]:
        """
        从 query 中提取术语（通用认知架构 — 非佛教专用）

        策略：
        1. 中文：2-4 字 n-gram
        2. 英文：词级提取，过滤停用词
        3. 混合：中英混合词组
        """
        terms: List[str] = []

        chinese_chars = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
        terms.extend(chinese_chars)

        english_words = re.findall(r'[a-zA-Z]{3,}', query)
        stop_words = set(T_CFG.ENGLISH_STOP_WORDS)
        terms.extend([w.lower() for w in english_words if w.lower() not in stop_words])

        mixed = re.findall(r'[\u4e00-\u9fffa-zA-Z0-9\-_]{3,}', query)
        terms.extend([t for t in mixed if t not in terms])

        unique_terms = list(dict.fromkeys(terms))
        for term in unique_terms:
            self.add_term(term, source_session=session_id)

        self._add_cooccurrence_edges(unique_terms, session_id)

        return unique_terms

    def query_term(self, term: str) -> Optional[N9R20TermNode]:
        """查询术语节点"""
        return self._nodes.get(term)

    @property
    def learned_nodes(self) -> Dict[str, N9R20TermNode]:
        """学习到的节点（兼容访问）"""
        return dict(self._nodes)

    @property
    def core_network(self) -> 'N9R20SemanticGraph':
        """核心网络（兼容访问）"""
        return self

    @property
    def nodes(self) -> Dict[str, N9R20TermNode]:
        """节点属性（兼容访问）"""
        return dict(self._nodes)

    def get_neighbors(
        self,
        term: str,
        min_weight: float = SG_CFG.EDGE_NEIGHBOR_MIN_WEIGHT,
    ) -> List[Tuple[str, float]]:
        """
        获取术语的邻居及权重

        返回按权重降序排列的 (term, weight) 列表。
        低于 min_weight 的邻居被过滤。
        """
        node = self._nodes.get(term)
        if node is None:
            return []

        with self._lock:
            neighbors = []
            now = time.time()
            for neighbor, weight in node.edges.items():
                decayed = self._decayer.decay(
                    weight,
                    self._nodes[neighbor].added_timestamp,
                    now,
                )
                if decayed >= min_weight:
                    neighbors.append((neighbor, round(decayed, 3)))

        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors

    def find_path(
        self,
        source: str,
        target: str,
        max_depth: int = SG_CFG.PATH_MAX_DEPTH,
    ) -> Optional[List[str]]:
        """
        BFS 最短路径查找

        返回从 source 到 target 的最短路径，或 None。
        最大搜索深度 = PATH_MAX_DEPTH（默认 4）。
        """
        if source not in self._nodes or target not in self._nodes:
            return None
        if source == target:
            return [source]

        visited: Set[str] = {source}
        queue: deque = deque([(source, [source])])

        with self._lock:
            while queue:
                current, path = queue.popleft()
                if len(path) > max_depth:
                    continue
                for neighbor, _ in self.get_neighbors(current):
                    if neighbor == target:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

        return None

    def detect_clusters(
        self,
        min_cluster_size: int = SG_CFG.CLUSTER_MIN_SIZE,
    ) -> List[N9R20ConceptCluster]:
        """
        社区发现：基于边权重的概念簇检测

        使用标签传播算法（迭代 CLUSTER_MAX_ITERATIONS 次）：
        1. 每个节点初始化为自己的簇
        2. 迭代：节点加入其最强邻居的簇
        3. 收敛后合并小簇
        """
        with self._lock:
            if len(self._nodes) < min_cluster_size:
                return list(self._clusters.values())

            # Phase 1: 初始化
            node_cluster: Dict[str, str] = {}
            for term in self._nodes:
                cid = f"cluster_{term}"
                node_cluster[term] = cid
                if cid not in self._clusters:
                    self._clusters[cid] = N9R20ConceptCluster(cluster_id=cid)
                self._clusters[cid].terms.add(term)

            # Phase 2: 标签传播
            for _ in range(SG_CFG.CLUSTER_MAX_ITERATIONS):
                changed = False
                for term in self._nodes:
                    neighbors = self.get_neighbors(term)
                    if not neighbors:
                        continue

                    cluster_votes: Dict[str, float] = defaultdict(float)
                    for neighbor, weight in neighbors:
                        nc = node_cluster.get(neighbor, "")
                        if nc:
                            cluster_votes[nc] += weight

                    if cluster_votes:
                        best_cluster = max(cluster_votes, key=cluster_votes.get)
                        if node_cluster[term] != best_cluster:
                            old_cid = node_cluster[term]
                            if old_cid in self._clusters:
                                self._clusters[old_cid].terms.discard(term)
                            node_cluster[term] = best_cluster
                            if best_cluster in self._clusters:
                                self._clusters[best_cluster].terms.add(term)
                            changed = True

                if not changed:
                    break

            # Phase 3: 合并小簇
            self._merge_small_clusters(node_cluster, min_cluster_size)

            # Phase 4: 更新簇元信息
            for cid, cluster in self._clusters.items():
                cluster.compute_density(self._edges)
                cluster.last_updated = time.time()
                self._update_centroid(cluster)

            # 清理空簇
            self._clusters = {
                cid: c for cid, c in self._clusters.items() if c.size >= 1
            }
            self._term_to_cluster = node_cluster

            return list(self._clusters.values())

    def compute_tension_map(self) -> Dict[str, Dict[str, float]]:
        """
        计算语义张力映射

        识别概念簇之间的张力关系：
        - 张力阈值 = CLUSTER_TENSION_THRESHOLD（默认 0.1）
        """
        clusters = self.detect_clusters()
        if len(clusters) < 2:
            return {}

        tension_map: Dict[str, Dict[str, float]] = {}

        for i, c1 in enumerate(clusters):
            for c2 in clusters[i + 1:]:
                tension = self._compute_inter_cluster_tension(c1, c2)
                if tension > SG_CFG.CLUSTER_TENSION_THRESHOLD:
                    tension_map.setdefault(c1.cluster_id, {})[c2.cluster_id] = round(tension, 3)
                    tension_map.setdefault(c2.cluster_id, {})[c1.cluster_id] = round(tension, 3)
                    c1.inter_tension[c2.cluster_id] = round(tension, 3)
                    c2.inter_tension[c1.cluster_id] = round(tension, 3)

        return tension_map

    def prune(self) -> int:
        """
        剪枝：移除低于阈值的边和孤立节点

        返回被剪枝的边数。
        """
        with self._lock:
            pruned_edges = 0
            now = time.time()

            to_remove: List[Tuple[str, str]] = []
            for key, weight in self._edges.items():
                avg_timestamp = max(
                    self._nodes.get(key[0], N9R20TermNode(term="")).added_timestamp,
                    self._nodes.get(key[1], N9R20TermNode(term="")).added_timestamp,
                )
                decayed = self._decayer.decay(weight, avg_timestamp, now)
                if self._decayer.should_prune(decayed):
                    to_remove.append(key)

            for key in to_remove:
                del self._edges[key]
                a, b = key
                if a in self._nodes and b in self._nodes[a].edges:
                    del self._nodes[a].edges[b]
                if b in self._nodes and a in self._nodes[b].edges:
                    del self._nodes[b].edges[a]
                pruned_edges += 1

            # 剪枝孤立节点
            isolated = [t for t, n in self._nodes.items() if not n.edges]
            for term in isolated:
                del self._nodes[term]

            return pruned_edges

    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        with self._lock:
            return {
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "total_clusters": len(self._clusters),
                "total_terms_seen": self._total_terms_seen,
                "total_sessions": self._total_sessions,
                "avg_degree": (
                    sum(len(n.edges) for n in self._nodes.values())
                    / max(len(self._nodes), 1)
                ),
                "max_degree_node": max(
                    ((t, len(n.edges)) for t, n in self._nodes.items()),
                    key=lambda x: x[1],
                    default=("", 0),
                )[0],
                "density": (
                    2 * len(self._edges)
                    / (len(self._nodes) * max(len(self._nodes) - 1, 1))
                    if len(self._nodes) > 1
                    else 0.0
                ),
            }

    # ═══════════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════════

    def _add_cooccurrence_edges(
        self,
        terms: List[str],
        session_id: str,
        window_size: int = SG_CFG.COOCCURRENCE_WINDOW_SIZE,
    ) -> None:
        """
        滑动窗口共现边添加

        距离越近，初始权重越高（EDGE_INITIAL_WEIGHT / distance）。
        """
        for i in range(len(terms)):
            for j in range(i + 1, min(i + window_size, len(terms))):
                distance = j - i
                initial_weight = SG_CFG.EDGE_INITIAL_WEIGHT / distance
                self.add_edge(terms[i], terms[j], weight=initial_weight,
                              source_session=session_id)

    def _merge_small_clusters(
        self,
        node_cluster: Dict[str, str],
        min_size: int,
    ) -> None:
        """合并过小的簇到最近的大簇"""
        small_clusters = [
            (cid, c) for cid, c in self._clusters.items()
            if c.size < min_size
        ]

        for cid, cluster in small_clusters:
            if cluster.size == 0:
                continue
            best_target = None
            best_strength = 0.0
            for term in cluster.terms:
                for neighbor, weight in self.get_neighbors(term):
                    nc = node_cluster.get(neighbor, "")
                    if nc != cid and nc in self._clusters:
                        if self._clusters[nc].size >= min_size and weight > best_strength:
                            best_strength = weight
                            best_target = nc

            if best_target:
                for term in cluster.terms:
                    node_cluster[term] = best_target
                    self._clusters[best_target].terms.add(term)
                self._clusters[cid].terms.clear()

    def _update_centroid(self, cluster: N9R20ConceptCluster) -> None:
        """更新簇的质心（最高度节点）"""
        max_degree = -1
        centroid = ""
        for term in cluster.terms:
            node = self._nodes.get(term)
            if node and len(node.edges) > max_degree:
                max_degree = len(node.edges)
                centroid = term
        cluster.centroid = centroid

    def _compute_inter_cluster_tension(
        self,
        c1: N9R20ConceptCluster,
        c2: N9R20ConceptCluster,
    ) -> float:
        """
        计算簇间张力

        - 无桥接边 → 高张力（CLUSTER_ISOLATED_TENSION + 密度差异 * 0.3）
        - 有桥接边 → 密度差异 / 平均桥接强度
        """
        bridge_weight = 0.0
        bridge_count = 0

        for t1 in c1.terms:
            for t2 in c2.terms:
                key = tuple(sorted([t1, t2]))
                if key in self._edges:
                    bridge_weight += self._edges[key]
                    bridge_count += 1

        if bridge_count == 0:
            return SG_CFG.CLUSTER_ISOLATED_TENSION + abs(
                c1.intra_density - c2.intra_density
            ) * 0.3

        avg_bridge = bridge_weight / bridge_count
        density_diff = abs(c1.intra_density - c2.intra_density)
        tension = density_diff / (avg_bridge + 0.01)

        return min(tension, 1.0)

    # ═══════════════════════════════════════════════
    # N9R20TensionBus 事件处理
    # ═══════════════════════════════════════════════

    def _on_event(self, event: Any) -> None:
        """统一事件处理入口"""
        if isinstance(event, N9R20CompressionTensionEvent):
            self._handle_compression_tension(event)
        elif isinstance(event, N9R20CompressionCompleteEvent):
            self._handle_compression_complete(event)

    def _handle_compression_tension(self, event: N9R20CompressionTensionEvent) -> None:
        """
        处理压缩张力事件

        职责：从 query 中提取术语，为压缩提供语义上下文。
        当术语数量 >= EVENT_TERM_COUNT_THRESHOLD 且簇数量 >= EVENT_CLUSTER_COUNT_THRESHOLD 时
        发射 ConceptClusterEvent。
        """
        query = event.query
        session_id = event.session_id

        terms = self.extract_terms_from_query(query, session_id)
        self._total_sessions += 1

        if len(terms) >= SG_CFG.EVENT_TERM_COUNT_THRESHOLD:
            clusters = self.detect_clusters()
            if len(clusters) >= SG_CFG.EVENT_CLUSTER_COUNT_THRESHOLD:
                tension_map = self.compute_tension_map()
                self.n9r20_bus.emit(N9R20ConceptClusterEvent(
                    session_id=session_id,
                    concepts=[
                        {
                            "cluster_id": c.cluster_id,
                            "terms": list(c.terms),
                            "centroid": c.centroid,
                            "size": c.size,
                            "density": round(c.intra_density, 3),
                        }
                        for c in clusters
                    ],
                    tension_map=tension_map,
                ))

    def _handle_compression_complete(self, event: N9R20CompressionCompleteEvent) -> None:
        """
        处理压缩完成事件

        职责：从压缩输出中学习，更新术语网络。
        每 PRUNE_PERIOD 个会话执行一次剪枝。
        """
        if event.output:
            self.extract_terms_from_query(event.output, event.session_id)

        if self._total_sessions % SG_CFG.PRUNE_PERIOD == 0:
            pruned = self.prune()
            if pruned > 0:
                self.detect_clusters()


# 全局单例
n9r20_semantic_graph = N9R20SemanticGraph()
n9r20_conflict_detector = N9R20ConceptConflictDetector(n9r20_semantic_graph)
