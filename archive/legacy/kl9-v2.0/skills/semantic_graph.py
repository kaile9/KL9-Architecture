"""
KL9-RHIZOME v2.0 · Semantic-Graph
语义图谱 · 整合 graph + 术语网络 · 动态扩展

设计原则：
1. 去中心化：术语节点平等连接，无根节点
2. 动态扩展：从 query 中自动提取并连接新术语
3. 边权重衰减：随时间衰减，模拟记忆遗忘曲线
4. 概念簇检测：基于边权重的社区发现
5. 张力映射：识别语义空间中的概念张力

佛教文本只是方便构件，不是思想源流 — 本模块是通用认知架构的语义层。
"""

import time
import re
import math
import threading
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque

from core.structures import TermNode
from core.tension_bus import (
    TensionBus2, bus, TensionType,
    CompressionTensionEvent, CompressionCompleteEvent,
    ConceptClusterEvent, TensionSubscription
)


# ═══════════════════════════════════════════════════════════
# 辅助数据结构
# ═══════════════════════════════════════════════════════════

class EdgeWeightDecay:
    """
    边权重衰减器
    
    模拟认知记忆的遗忘曲线：
    - 半衰期默认 3600 秒（1 小时）
    - 每次访问增强权重（赫布学习）
    - 低于阈值的边自动剪枝
    """

    def __init__(self, half_life: float = 3600.0, prune_threshold: float = 0.05):
        self.half_life = half_life          # 半衰期（秒）
        self.prune_threshold = prune_threshold
        self._decay_constant = math.log(2) / half_life

    def decay(self, weight: float, last_updated: float, now: float) -> float:
        """指数衰减：weight * e^(-λ·Δt)"""
        dt = now - last_updated
        if dt < 0:
            return weight
        decayed = weight * math.exp(-self._decay_constant * dt)
        return max(decayed, 0.0)

    def reinforce(self, weight: float, increment: float = 0.1) -> float:
        """赫布强化：每次共现增强权重"""
        return min(weight + increment, 1.0)

    def should_prune(self, weight: float) -> bool:
        """判断边是否应被剪枝"""
        return weight < self.prune_threshold


class ConceptCluster:
    """
    概念簇 — 语义图谱中的社区

    通过边权重进行社区发现，形成动态概念簇。
    每个簇代表一个语义子空间。
    """

    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self.terms: Set[str] = set()
        self.centroid: str = ""              # 中心术语（最高度节点）
        self.intra_density: float = 0.0       # 簇内密度
        self.inter_tension: Dict[str, float] = {}  # 与其他簇的张力
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

class SemanticGraph:
    """
    语义图谱 · 动态术语网络

    核心功能：
    1. 术语提取与节点管理（去中心化）
    2. 边权重动态更新（赫布学习 + 衰减）
    3. 概念簇检测（基于边权重的社区发现）
    4. 张力映射（识别概念间的语义张力）
    5. 动态扩展（从 query 中学习新术语）

    与 TensionBus 集成：
    - 订阅 CompressionTensionEvent：参与压缩流程，提供术语网络上下文
    - 发射 ConceptClusterEvent：当检测到显著的概念簇变化时
    """

    def __init__(self):
        # ═══ 核心图谱结构 ═══
        self._nodes: Dict[str, TermNode] = {}          # term → TermNode
        self._edges: Dict[Tuple[str, str], float] = {}  # (term_a, term_b) → weight (按字母序排列)
        self._clusters: Dict[str, ConceptCluster] = {}  # cluster_id → ConceptCluster
        self._term_to_cluster: Dict[str, str] = {}      # term → cluster_id

        # ═══ 元信息 ═══
        self._decayer = EdgeWeightDecay()
        self._lock = threading.RLock()
        self._total_terms_seen: int = 0
        self._total_sessions: int = 0

        # ═══ TensionBus 集成 ═══
        self.bus = bus
        self.bus.subscribe(TensionSubscription(
            skill_name="semantic-graph",
            role="subscriber",
            tension_types=[TensionType.SEMANTIC.value],
            event_types=["CompressionTensionEvent", "CompressionCompleteEvent"],
            priority=2,
            callback=self._on_event
        ))

    # ═══════════════════════════════════════════════
    # 公共 API
    # ═══════════════════════════════════════════════

    def add_term(self, term: str, source_session: str = "", confidence: float = 0.7) -> TermNode:
        """
        添加或获取术语节点（去中心化 — 无层级结构）

        如果术语已存在，更新其置信度；否则创建新节点。
        """
        with self._lock:
            if term in self._nodes:
                node = self._nodes[term]
                # 赫布强化：已存在术语的置信度提升
                node.confidence = min(node.confidence + 0.05, 1.0)
                return node

            node = TermNode(
                term=term,
                edges={},
                source_session=source_session,
                confidence=confidence,
                added_timestamp=time.time()
            )
            self._nodes[term] = node
            self._total_terms_seen += 1
            return node

    def add_edge(self, term_a: str, term_b: str, weight: float = 0.3,
                 source_session: str = "") -> None:
        """
        添加或更新边（无向边，按字母序存储）

        赫布学习：每次共现增强权重。
        """
        if term_a == term_b:
            return
        # 按字母序排列以确保无向边的一致性
        key = tuple(sorted([term_a, term_b]))

        with self._lock:
            # 确保两端节点存在
            self.add_term(term_a, source_session)
            self.add_term(term_b, source_session)

            now = time.time()
            if key in self._edges:
                existing = self._edges[key]
                # 先衰减再增强（赫布学习）
                decayed = self._decayer.decay(existing, self._nodes[term_a].added_timestamp, now)
                self._edges[key] = self._decayer.reinforce(decayed, weight)
            else:
                self._edges[key] = weight

            # 更新节点内部边引用
            self._nodes[term_a].edges[term_b] = self._edges[key]
            self._nodes[term_b].edges[term_a] = self._edges[key]
            self._nodes[term_a].added_timestamp = now
            self._nodes[term_b].added_timestamp = now

    def extract_terms_from_query(self, query: str, 
                                  session_id: str = "") -> List[str]:
        """
        从 query 中提取术语（通用认知架构 — 非佛教专用）

        使用通用语言学策略：
        1. 中文：2-4 字 n-gram
        2. 英文：词级提取
        3. 混合：两者结合
        """
        terms: List[str] = []

        # 中文术语提取（2-4 字 n-gram）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
        terms.extend(chinese_chars)

        # 英文术语提取（词级，过滤短词和常见停用词）
        english_words = re.findall(r'[a-zA-Z]{3,}', query)
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'what', 'how'}
        terms.extend([w.lower() for w in english_words if w.lower() not in stop_words])

        # 混合术语（中英混合如"KL9-系统"）
        mixed = re.findall(r'[\u4e00-\u9fffa-zA-Z0-9\-_]{3,}', query)
        terms.extend([t for t in mixed if t not in terms])

        # 去重并添加到图谱
        unique_terms = list(dict.fromkeys(terms))  # 保持顺序去重
        for term in unique_terms:
            self.add_term(term, source_session=session_id)

        # 共现边：在滑动窗口中连接术语
        self._add_cooccurrence_edges(unique_terms, session_id)

        return unique_terms

    def query_term(self, term: str) -> Optional[TermNode]:
        """查询术语节点"""
        return self._nodes.get(term)

    @property
    def learned_nodes(self) -> Dict[str, TermNode]:
        """学习到的节点（兼容访问）"""
        return dict(self._nodes)

    @property
    def core_network(self) -> 'SemanticGraph':
        """核心网络（兼容访问）"""
        return self

    @property
    def nodes(self) -> Dict[str, TermNode]:
        """节点属性（兼容访问）"""
        return dict(self._nodes)

    def get_neighbors(self, term: str, min_weight: float = 0.1) -> List[Tuple[str, float]]:
        """
        获取术语的邻居及权重

        返回按权重降序排列的 (term, weight) 列表。
        """
        node = self._nodes.get(term)
        if node is None:
            return []

        with self._lock:
            neighbors = []
            for neighbor, weight in node.edges.items():
                # 应用衰减
                key = tuple(sorted([term, neighbor]))
                now = time.time()
                decayed = self._decayer.decay(
                    weight,
                    self._nodes[neighbor].added_timestamp,
                    now
                )
                if decayed >= min_weight:
                    neighbors.append((neighbor, round(decayed, 3)))

        # 按权重降序排列
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors

    def find_path(self, source: str, target: str, max_depth: int = 4) -> Optional[List[str]]:
        """
        BFS 最短路径查找（去中心化 — 无权图 + 权重加权距离）

        返回从 source 到 target 的最短路径（List[term]），或 None。
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

                for neighbor, weight in self.get_neighbors(current):
                    if neighbor == target:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

        return None

    def detect_clusters(self, min_cluster_size: int = 3) -> List[ConceptCluster]:
        """
        社区发现：基于边权重的概念簇检测

        使用简化的标签传播算法：
        1. 每个节点初始化为自己的簇
        2. 迭代：节点加入其最强邻居的簇
        3. 收敛后合并小簇
        """
        with self._lock:
            if len(self._nodes) < min_cluster_size:
                return list(self._clusters.values())

            # Phase 1: 初始化 — 每个节点一个簇
            node_cluster: Dict[str, str] = {}
            for term in self._nodes:
                cid = f"cluster_{term}"
                node_cluster[term] = cid
                if cid not in self._clusters:
                    self._clusters[cid] = ConceptCluster(cluster_id=cid)
                self._clusters[cid].terms.add(term)

            # Phase 2: 标签传播（迭代 max_iter 次）
            max_iter = 10
            for _ in range(max_iter):
                changed = False
                for term in self._nodes:
                    neighbors = self.get_neighbors(term)
                    if not neighbors:
                        continue

                    # 找到最强邻居所属的簇
                    cluster_votes: Dict[str, float] = defaultdict(float)
                    for neighbor, weight in neighbors:
                        nc = node_cluster.get(neighbor, "")
                        if nc:
                            cluster_votes[nc] += weight

                    if cluster_votes:
                        best_cluster = max(cluster_votes, key=cluster_votes.get)
                        if node_cluster[term] != best_cluster:
                            # 移动节点
                            old_cid = node_cluster[term]
                            if old_cid in self._clusters:
                                self._clusters[old_cid].terms.discard(term)
                            node_cluster[term] = best_cluster
                            if best_cluster in self._clusters:
                                self._clusters[best_cluster].terms.add(term)
                            changed = True

                if not changed:
                    break

            # Phase 3: 合并小簇到最近的大簇
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

            # 更新 term → cluster 映射
            self._term_to_cluster = node_cluster

            return list(self._clusters.values())

    def compute_tension_map(self) -> Dict[str, Dict[str, float]]:
        """
        计算语义张力映射

        识别概念簇之间的张力关系：
        - 高密度簇 vs 低密度簇 → 结构张力
        - 远距离簇 → 距离张力
        """
        clusters = self.detect_clusters()
        if len(clusters) < 2:
            return {}

        tension_map: Dict[str, Dict[str, float]] = {}

        for i, c1 in enumerate(clusters):
            for c2 in clusters[i + 1:]:
                tension = self._compute_inter_cluster_tension(c1, c2)
                if tension > 0.1:
                    tension_map.setdefault(c1.cluster_id, {})[c2.cluster_id] = round(tension, 3)
                    tension_map.setdefault(c2.cluster_id, {})[c1.cluster_id] = round(tension, 3)

                    # 记录在簇中
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

            # 剪枝边
            to_remove: List[Tuple[str, str]] = []
            for key, weight in self._edges.items():
                # 应用衰减后判断
                avg_timestamp = max(
                    self._nodes.get(key[0], TermNode(term="")).added_timestamp,
                    self._nodes.get(key[1], TermNode(term="")).added_timestamp
                )
                decayed = self._decayer.decay(weight, avg_timestamp, now)
                if self._decayer.should_prune(decayed):
                    to_remove.append(key)

            for key in to_remove:
                del self._edges[key]
                # 同步更新节点内部边引用
                a, b = key
                if a in self._nodes and b in self._nodes[a].edges:
                    del self._nodes[a].edges[b]
                if b in self._nodes and a in self._nodes[b].edges:
                    del self._nodes[b].edges[a]
                pruned_edges += 1

            # 剪枝孤立节点（无边的节点）
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
                )
            }

    # ═══════════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════════

    def _add_cooccurrence_edges(self, terms: List[str], session_id: str,
                                 window_size: int = 3) -> None:
        """
        滑动窗口共现边添加

        在窗口内的术语之间建立边，窗口大小控制局部语义范围。
        """
        for i in range(len(terms)):
            for j in range(i + 1, min(i + window_size, len(terms))):
                # 距离越近，初始权重越高
                distance = j - i
                initial_weight = 0.3 / distance
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

            # 找到最近的大簇
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

    def _update_centroid(self, cluster: ConceptCluster) -> None:
        """更新簇的质心（最高度节点）"""
        max_degree = -1
        centroid = ""
        for term in cluster.terms:
            node = self._nodes.get(term)
            if node and len(node.edges) > max_degree:
                max_degree = len(node.edges)
                centroid = term
        cluster.centroid = centroid

    def _compute_inter_cluster_tension(self, c1: ConceptCluster,
                                        c2: ConceptCluster) -> float:
        """
        计算簇间张力

        基于：
        1. 簇间桥接边的权重和
        2. 簇密度差异
        3. 距离因子
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
            # 无直接连接 → 高张力（语义距离远）
            return 0.7 + abs(c1.intra_density - c2.intra_density) * 0.3

        # 有连接时：张力 = 密度差异 / 桥接强度
        avg_bridge = bridge_weight / bridge_count
        density_diff = abs(c1.intra_density - c2.intra_density)
        tension = density_diff / (avg_bridge + 0.01)

        return min(tension, 1.0)

    # ═══════════════════════════════════════════════
    # TensionBus 事件处理
    # ═══════════════════════════════════════════════

    def _on_event(self, event: Any) -> None:
        """统一事件处理入口"""
        if isinstance(event, CompressionTensionEvent):
            self._handle_compression_tension(event)
        elif isinstance(event, CompressionCompleteEvent):
            self._handle_compression_complete(event)

    def _handle_compression_tension(self, event: CompressionTensionEvent) -> None:
        """
        处理压缩张力事件

        职责：从 query 中提取术语，为压缩提供语义上下文。
        """
        query = event.query
        session_id = event.session_id

        # 提取术语并添加到图谱
        terms = self.extract_terms_from_query(query, session_id)
        self._total_sessions += 1

        # 如果检测到显著的概念簇变化，发射事件
        if len(terms) >= 5:
            # 检测簇
            clusters = self.detect_clusters()
            if len(clusters) >= 2:
                tension_map = self.compute_tension_map()
                self.bus.emit(ConceptClusterEvent(
                    session_id=session_id,
                    concepts=[
                        {
                            "cluster_id": c.cluster_id,
                            "terms": list(c.terms),
                            "centroid": c.centroid,
                            "size": c.size,
                            "density": round(c.intra_density, 3)
                        }
                        for c in clusters
                    ],
                    tension_map=tension_map
                ))

    def _handle_compression_complete(self, event: CompressionCompleteEvent) -> None:
        """
        处理压缩完成事件

        职责：从压缩输出中学习，更新术语网络。
        """
        if event.output:
            # 从压缩输出中提取术语，加强相关边
            self.extract_terms_from_query(event.output, event.session_id)

        # 定期剪枝（每 10 个会话）
        if self._total_sessions % 10 == 0:
            pruned = self.prune()
            if pruned > 0:
                # 重新检测簇
                self.detect_clusters()


# 全局单例
semantic_graph = SemanticGraph()
