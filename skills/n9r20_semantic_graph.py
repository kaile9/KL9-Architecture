"""
9R-2.0 RHIZOME · Semantic-Graph
语义图谱 · 整合 graph + 术语网络 · 动态扩展

设计原则：
1. 去中心化：术语节点平等连接，无根节点
2. 动态扩展：从 query 中自动提取并连接新术语
3. 边权重衰减：随时间衰减，模拟记忆遗忘曲线
4. 概念簇检测：基于边权重的社区发现
5. 张力映射：识别语义空间中的概念张力

Phase 3 重构：
- 扩展 N9R20TermNode 支持上下文变体（集成 N9R20ConceptNode）
- 集成 N9R20ConceptConflictDetector
- 在 add_edge() 和 detect_clusters() 中添加冲突检测
- 移除硬编码词项模式，使用可配置的提取器（n9r20_utils）

佛教文本只是方便构件，不是思想源流 — 本模块是通用认知架构的语义层。
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
from core.n9r20_config import n9r20_semantic_graph_config
from core.n9r20_utils import extract_terms, compute_concept_density
from core.n9r20_concept_conflict import (
    N9R20ConceptConflictDetector, n9r20_conflict_detector,
)
from core.n9r20_skillbook_compat import N9R20ConceptNode, N9R20ConceptProvenance


# ═══════════════════════════════════════════════════════════
# 辅助数据结构
# ═══════════════════════════════════════════════════════════

class N9R20EdgeWeightDecay:
    """
    边权重衰减器

    模拟认知记忆的遗忘曲线：
    - 半衰期默认 3600 秒（1 小时）
    - 每次访问增强权重（赫布学习）
    - 低于阈值的边自动剪枝
    """

    def __init__(self, half_life: float = None, prune_threshold: float = None):
        cfg = n9r20_semantic_graph_config
        self.half_life = half_life if half_life is not None else cfg.EDGE_DECAY_HALFLIFE
        self.prune_threshold = prune_threshold if prune_threshold is not None else cfg.EDGE_PRUNE_THRESHOLD
        self._decay_constant = math.log(2) / self.half_life

    def decay(self, weight: float, last_updated: float, now: float) -> float:
        """指数衰减：weight * e^(-λ·Δt)"""
        dt = now - last_updated
        if dt < 0:
            return weight
        decayed = weight * math.exp(-self._decay_constant * dt)
        return max(decayed, 0.0)

    def reinforce(self, weight: float, increment: float = None) -> float:
        """赫布强化：每次共现增强权重"""
        if increment is None:
            increment = n9r20_semantic_graph_config.EDGE_REINFORCE_INCREMENT
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
        actual_sum = 0.0
        for (a, b), w in edges.items():
            if a in self.terms and b in self.terms:
                actual_sum += w
        return actual_sum / max_edges if max_edges > 0 else 0.0


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
    6. Phase 3: 概念冲突检测集成

    与 N9R20TensionBus 集成：
    - 订阅 N9R20CompressionTensionEvent：参与压缩流程，提供术语网络上下文
    - 发射 N9R20ConceptClusterEvent：当检测到显著的概念簇变化时
    """

    def __init__(self, conflict_detector: Optional[N9R20ConceptConflictDetector] = None):
        # ═══ 核心图谱结构 ═══
        self._nodes: Dict[str, N9R20TermNode] = {}
        self._edges: Dict[Tuple[str, str], float] = {}
        self._clusters: Dict[str, N9R20ConceptCluster] = {}
        self._term_to_cluster: Dict[str, str] = {}

        # Phase 3: 上下文变体存储（term → N9R20ConceptNode）
        self._context_variants: Dict[str, N9R20ConceptNode] = {}

        # ═══ 元信息 ═══
        self._decayer = N9R20EdgeWeightDecay()
        self._lock = threading.RLock()
        self._total_terms_seen: int = 0
        self._total_sessions: int = 0

        # ═══ N9R20TensionBus 集成 ═══
        self.n9r20_bus = n9r20_bus
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="semantic-graph",
            role="subscriber",
            tension_types=[N9R20TensionType.SEMANTIC.value],
            event_types=["N9R20CompressionTensionEvent", "N9R20CompressionCompleteEvent"],
            priority=2,
            callback=self._on_event,
        ))

        # Phase 3: 概念冲突检测器
        self._conflict_detector = conflict_detector or n9r20_conflict_detector
        self._detected_conflicts: List[N9R20ConceptConflict] = []

    # ═══════════════════════════════════════════════
    # 公共 API
    # ═══════════════════════════════════════════════

    def add_term(self, term: str, source_session: str = "",
                 confidence: float = None,
                 context_hint: str = "") -> N9R20TermNode:
        """
        添加或获取术语节点（去中心化 — 无层级结构）

        Phase 3: 支持上下文变体追踪。
        如果术语已存在，更新其置信度；否则创建新节点。
        """
        if confidence is None:
            confidence = n9r20_semantic_graph_config.TERM_CONFIDENCE_DEFAULT

        with self._lock:
            if term in self._nodes:
                node = self._nodes[term]
                node.confidence = min(
                    node.confidence + n9r20_semantic_graph_config.TERM_CONFIDENCE_INCREMENT,
                    1.0,
                )
                # Phase 3: 更新上下文变体
                if context_hint:
                    self._update_context_variant(term, source_session, context_hint)
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

            # Phase 3: 创建上下文变体追踪
            if context_hint or source_session:
                self._update_context_variant(term, source_session, context_hint)

            return node

    def add_edge(self, term_a: str, term_b: str, weight: float = None,
                 source_session: str = "") -> None:
        """
        添加或更新边（无向边，按字母序存储）

        赫布学习：每次共现增强权重。

        Phase 3: 添加冲突检测 — 检查新边连接的两个概念是否有视角/定义冲突。
        """
        if term_a == term_b:
            return
        if weight is None:
            weight = n9r20_semantic_graph_config.EDGE_INITIAL_WEIGHT

        key = tuple(sorted([term_a, term_b]))

        with self._lock:
            self.add_term(term_a, source_session)
            self.add_term(term_b, source_session)

            now = time.time()
            if key in self._edges:
                existing = self._edges[key]
                decayed = self._decayer.decay(
                    existing,
                    self._nodes[term_a].added_timestamp,
                    now,
                )
                self._edges[key] = self._decayer.reinforce(decayed, weight)
            else:
                self._edges[key] = weight

            self._nodes[term_a].edges[term_b] = self._edges[key]
            self._nodes[term_b].edges[term_a] = self._edges[key]
            self._nodes[term_a].added_timestamp = now
            self._nodes[term_b].added_timestamp = now

            # Phase 3: 冲突检测
            self._detect_edge_conflict(term_a, term_b, self._edges[key], source_session)

    def extract_terms_from_query(self, query: str,
                                  session_id: str = "") -> List[str]:
        """
        从 query 中提取术语（通用认知架构 — 非佛教专用）

        Phase 3: 使用 n9r20_utils.extract_terms 替代硬编码模式。
        使用通用语言学策略：
        1. 中文：2-4 字 n-gram
        2. 英文：词级提取
        3. 混合：两者结合
        """
        # Phase 3: 使用可配置的提取器
        chinese_terms, english_terms = extract_terms(
            query,
            specialized_keywords=None,  # 语义图谱不按专用关键词过滤
            term_min_len=n9r20_semantic_graph_config.term_min_len,
            term_max_len=n9r20_semantic_graph_config.term_max_len,
        )

        all_terms = chinese_terms + english_terms

        # 去重并添加到图谱
        unique_terms = list(dict.fromkeys(all_terms))
        for term in unique_terms:
            self.add_term(term, source_session=session_id)

        # 共现边
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

    def get_neighbors(self, term: str, min_weight: float = None) -> List[Tuple[str, float]]:
        """
        获取术语的邻居及权重

        返回按权重降序排列的 (term, weight) 列表。
        """
        if min_weight is None:
            min_weight = n9r20_semantic_graph_config.EDGE_NEIGHBOR_MIN_WEIGHT

        node = self._nodes.get(term)
        if node is None:
            return []

        with self._lock:
            neighbors = []
            for neighbor, weight in node.edges.items():
                key = tuple(sorted([term, neighbor]))
                now = time.time()
                decayed = self._decayer.decay(
                    weight,
                    self._nodes[neighbor].added_timestamp,
                    now,
                )
                if decayed >= min_weight:
                    neighbors.append((neighbor, round(decayed, 3)))

        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors

    def find_path(self, source: str, target: str, max_depth: int = None) -> Optional[List[str]]:
        """
        BFS 最短路径查找（去中心化 — 无权图 + 权重加权距离）

        返回从 source 到 target 的最短路径（List[term]），或 None。
        """
        if max_depth is None:
            max_depth = n9r20_semantic_graph_config.PATH_MAX_DEPTH

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

                for neighbor, weight in self.get_neighbors(current):
                    if neighbor == target:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

        return None

    def detect_clusters(self, min_cluster_size: int = None) -> List[N9R20ConceptCluster]:
        """
        社区发现：基于边权重的概念簇检测

        使用简化的标签传播算法。

        Phase 3: 添加簇间冲突检测。
        """
        if min_cluster_size is None:
            min_cluster_size = n9r20_semantic_graph_config.CLUSTER_MIN_SIZE

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
            max_iter = n9r20_semantic_graph_config.CLUSTER_MAX_ITERATIONS
            for _ in range(max_iter):
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

            # Phase 3: 簇间冲突检测
            self._detect_cluster_conflicts()

            return list(self._clusters.values())

    def compute_tension_map(self) -> Dict[str, Dict[str, float]]:
        """
        计算语义张力映射

        识别概念簇之间的张力关系。
        """
        clusters = self.detect_clusters()
        if len(clusters) < 2:
            return {}

        tension_map: Dict[str, Dict[str, float]] = {}

        for i, c1 in enumerate(clusters):
            for c2 in clusters[i + 1:]:
                tension = self._compute_inter_cluster_tension(c1, c2)
                if tension > n9r20_semantic_graph_config.CLUSTER_TENSION_THRESHOLD:
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

            isolated = [
                term for term, node in self._nodes.items()
                if not node.edges
            ]
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
                "avg_degree": sum(len(n.edges) for n in self._nodes.values()) / max(len(self._nodes), 1),
                "max_degree_node": max(
                    ((t, len(n.edges)) for t, n in self._nodes.items()),
                    key=lambda x: x[1],
                    default=("", 0)
                )[0],
                "density": (
                    2 * len(self._edges) / (len(self._nodes) * max(len(self._nodes) - 1, 1))
                    if len(self._nodes) > 1 else 0.0
                ),
                # Phase 3: 冲突统计
                "context_variants_count": len(self._context_variants),
                "detected_conflicts": len(self._detected_conflicts),
            }

    # Phase 3: 上下文变体 API

    def get_context_variant(self, term: str) -> Optional[N9R20ConceptNode]:
        """获取术语的上下文变体信息"""
        return self._context_variants.get(term)

    def get_detected_conflicts(self) -> List[N9R20ConceptConflict]:
        """获取已检测的概念冲突"""
        return list(self._detected_conflicts)

    # ═══════════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════════

    def _add_cooccurrence_edges(self, terms: List[str], session_id: str,
                                 window_size: int = None) -> None:
        """滑动窗口共现边添加"""
        if window_size is None:
            window_size = n9r20_semantic_graph_config.COOCCURRENCE_WINDOW_SIZE

        for i in range(len(terms)):
            for j in range(i + 1, min(i + window_size, len(terms))):
                distance = j - i
                initial_weight = n9r20_semantic_graph_config.EDGE_INITIAL_WEIGHT / distance
                self.add_edge(terms[i], terms[j], weight=initial_weight,
                             source_session=session_id)

    def _merge_small_clusters(self, node_cluster: Dict[str, str],
                               min_size: int) -> None:
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
                neighbors = self.get_neighbors(term)
                for neighbor, weight in neighbors:
                    nc = node_cluster.get(neighbor, "")
                    if nc != cid and nc in self._clusters:
                        if self._clusters[nc].size >= min_size:
                            if weight > best_strength:
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

    def _compute_inter_cluster_tension(self, c1: N9R20ConceptCluster,
                                        c2: N9R20ConceptCluster) -> float:
        """计算簇间张力"""
        bridge_weight = 0.0
        bridge_count = 0

        for t1 in c1.terms:
            for t2 in c2.terms:
                key = tuple(sorted([t1, t2]))
                if key in self._edges:
                    bridge_weight += self._edges[key]
                    bridge_count += 1

        if bridge_count == 0:
            return 0.7 + abs(c1.intra_density - c2.intra_density) * 0.3

        avg_bridge = bridge_weight / bridge_count
        density_diff = abs(c1.intra_density - c2.intra_density)
        tension = density_diff / (avg_bridge + 0.01)

        return min(tension, 1.0)

    # Phase 3: 上下文变体与冲突检测

    def _update_context_variant(self, term: str, source_session: str,
                                 context_hint: str) -> None:
        """更新术语的上下文变体追踪"""
        if term not in self._context_variants:
            self._context_variants[term] = N9R20ConceptNode(
                term=term,
                source_session=source_session,
            )
        variant = self._context_variants[term]
        variant.add_context_variant(source_session or "unknown", context_hint)

    def _detect_edge_conflict(self, term_a: str, term_b: str,
                               weight: float, source_session: str) -> None:
        """
        检测新边连接的两个概念之间的冲突。

        使用 N9R20ConceptConflictDetector 检查:
        - 定义冲突：两个术语的上下文变体是否分歧
        - 视角冲突：是否分属理论/实践阵营
        """
        # 构建节点字典供冲突检测器使用
        nodes_for_detection = {}
        if term_a in self._context_variants:
            nodes_for_detection[term_a] = self._context_variants[term_a]
        if term_b in self._context_variants:
            nodes_for_detection[term_b] = self._context_variants[term_b]

        if len(nodes_for_detection) >= 1:
            try:
                edge_dict = {(term_a, term_b): weight}
                conflicts = self._conflict_detector.detect_from_nodes(
                    nodes_for_detection,
                    edges=edge_dict,
                )
                for conflict in conflicts:
                    if conflict not in self._detected_conflicts:
                        self._detected_conflicts.append(conflict)
            except Exception:
                pass  # 静默处理冲突检测失败

    def _detect_cluster_conflicts(self) -> None:
        """
        在簇检测完成后，检测簇间概念冲突。

        使用 N9R20ConceptConflictDetector 分析簇间张力冲突。
        """
        clusters = list(self._clusters.values())
        if len(clusters) < 2:
            return

        try:
            conflicts = self._conflict_detector.detect_from_clusters(
                clusters,
                edges=self._edges,
            )
            for conflict in conflicts:
                if conflict not in self._detected_conflicts:
                    self._detected_conflicts.append(conflict)
        except Exception:
            pass

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
        """处理压缩张力事件"""
        query = event.query
        session_id = event.session_id

        terms = self.extract_terms_from_query(query, session_id)
        self._total_sessions += 1

        if len(terms) >= n9r20_semantic_graph_config.EVENT_TERM_COUNT_THRESHOLD:
            clusters = self.detect_clusters()
            if len(clusters) >= n9r20_semantic_graph_config.EVENT_CLUSTER_COUNT_THRESHOLD:
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
        """处理压缩完成事件"""
        if event.output:
            self.extract_terms_from_query(event.output, event.session_id)

        if self._total_sessions % n9r20_semantic_graph_config.PRUNE_PERIOD == 0:
            pruned = self.prune()
            if pruned > 0:
                self.detect_clusters()


# 全局单例
n9r20_semantic_graph = N9R20SemanticGraph()
