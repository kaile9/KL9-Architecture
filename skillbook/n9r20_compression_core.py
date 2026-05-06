"""
9R-2.0 RHIZOME · Compression-Core
压缩核心引擎 · 整合 orchestrator + core + fold-engine

重构说明（魔法数字消除）：
- 所有数值常量引用 core/n9r20_config.py 中的配置
- _simple_compress 保留现有行为，添加注释说明这是 fallback 实现
- 配置通过 n9r20_compression_config / n9r20_routing_config 注入
"""

import time
from typing import Optional
from dataclasses import dataclass

from core.n9r20_structures import (
    N9R20DualState, N9R20CompressedOutput, N9R20RoutingDecision,
    N9R20Perspective, N9R20Tension, N9R20PerspectiveType,
)
from core.n9r20_tension_bus import (
    n9r20_bus, N9R20CompressionTensionEvent, N9R20CompressionCompleteEvent,
)
from core.n9r20_config import (
    n9r20_compression_config as C_CFG,
    n9r20_routing_config     as R_CFG,
)
from skills.n9r20_adaptive_router import n9r20_router


class N9R20AdaptiveFourModeCodec:
    """
    自适应四模编码器

    四模通用化：
    - 建 (Construct)  : 展开语义空间
    - 破 (Deconstruct): 解构固化概念
    - 证 (Validate)   : 验证语义保留
    - 截 (Interrupt)  : 强制收敛输出

    不是佛教专用，而是通用认知工具。
    """

    def select_mode_sequence(self, query: str, difficulty: float) -> list:
        """
        根据任务难度动态选择模式序列

        阈值来自 N9R20CompressionConfig：
          difficulty < MODE_SIMPLE_DIFFICULTY_THRESHOLD → simple 序列
          difficulty < MODE_MEDIUM_DIFFICULTY_THRESHOLD → medium 序列
          otherwise                                     → hard 序列
        """
        if difficulty < C_CFG.MODE_SIMPLE_DIFFICULTY_THRESHOLD:
            return list(C_CFG.MODE_SEQUENCE_SIMPLE)
        elif difficulty < C_CFG.MODE_MEDIUM_DIFFICULTY_THRESHOLD:
            return list(C_CFG.MODE_SEQUENCE_MEDIUM)
        else:
            return list(C_CFG.MODE_SEQUENCE_HARD)


class N9R20SemanticValidator:
    """
    语义验证器

    验证压缩后的语义保留率。
    目标：保留率 > SEMANTIC_RETENTION_THRESHOLD（默认 85%）。
    """

    def validate(self, state: N9R20DualState) -> 'N9R20ValidationResult':
        """
        验证当前压缩状态的语义保留率

        估算公式：
          retention = 1 / (compression_ratio * VALIDATOR_ESTIMATION_DIVISOR)
          retention -= fold_depth * FOLD_DEPTH_PENALTY_PER_LEVEL

        参数来自 N9R20CompressionConfig。
        """
        ratio = state.compression_ratio
        safe_ratio = max(ratio, 0.01)
        estimated_retention = min(
            1.0 / (safe_ratio * C_CFG.VALIDATOR_ESTIMATION_DIVISOR), 1.0
        )

        # fold 深度惩罚
        fold_penalty = state.fold_depth * C_CFG.FOLD_DEPTH_PENALTY_PER_LEVEL
        estimated_retention = max(0.0, min(1.0, estimated_retention - fold_penalty))

        return N9R20ValidationResult(
            retention=round(estimated_retention, 2),
            ratio=ratio,
            fold_depth=state.fold_depth,
        )


@dataclass
class N9R20ValidationResult:
    """验证结果"""
    retention: float = 1.0
    ratio: float = 1.0
    fold_depth: int = 0
    passed: bool = False

    def __post_init__(self):
        self.passed = self.retention >= C_CFG.SEMANTIC_RETENTION_THRESHOLD


class N9R20DynamicFoldEngine:
    """
    动态折叠引擎

    执行单次折叠操作。
    """

    def fold_once(self, state: N9R20DualState) -> N9R20DualState:
        """
        执行一次折叠

        简化实现：基于当前状态生成压缩输出。
        实际实现应使用 LLM 进行语义压缩。
        """
        current_text = state.compressed_output or state.query
        compressed = self._simple_compress(current_text)

        state.compressed_output = compressed
        state.compression_ratio = len(state.query) / max(len(compressed), 1)
        return state

    def _simple_compress(self, text: str) -> str:
        """
        简单压缩（fallback 实现）

        注意：这是模拟实现，实际生产环境应使用 LLM 进行语义压缩。
        保留此函数作为 LLM 不可用时的降级方案。

        压缩系数 = SIMPLE_COMPRESS_RATIO（默认 0.6，即保留 60% 字符）。
        """
        target_length = int(len(text) * C_CFG.SIMPLE_COMPRESS_RATIO)
        return text[:target_length] + "..."


class N9R20CompressionCore:
    """
    压缩核心引擎

    整合 orchestrator + core + fold-engine

    职责：
    1. 接收 query → 动态 fold → 压缩输出
    2. 四模编码驱动的动态折叠
    3. 双轨验证：压缩率 + 语义保留
    """

    def __init__(self):
        self.four_mode_codec = N9R20AdaptiveFourModeCodec()
        self.fold_engine = N9R20DynamicFoldEngine()
        self.validator = N9R20SemanticValidator()
        self.n9r20_bus = n9r20_bus
        self.n9r20_router = n9r20_router

    def compress(
        self,
        query: str,
        routing: Optional[N9R20RoutingDecision] = None,
        session_id: str = "",
    ) -> N9R20CompressedOutput:
        """
        主压缩流程

        流程：
        1. 路由决策（如果没有提供）
        2. 发射 query 到 N9R20TensionBus
        3. 构建初始 N9R20DualState
        4. 四模编码 + 动态折叠
        5. 生成输出
        6. 发射完成事件
        """
        # Phase 1: 路由决策
        if routing is None:
            routing = self.n9r20_router.route(query)

        # Phase 2: 发射 query 到 N9R20TensionBus
        self.n9r20_bus.emit(N9R20CompressionTensionEvent(
            query=query,
            session_id=session_id,
            fold_depth=0,
            target_fold_depth=routing.target_fold_depth,
            target_ratio=routing.target_compression_ratio,
            urgency=routing.urgency,
        ))

        # Phase 3: 构建初始 N9R20DualState
        state = self._build_initial_state(query, routing, session_id)

        # Phase 4: 四模编码 + 动态折叠
        final_state = self._four_mode_fold(state, routing)

        # Phase 5: 生成输出
        output = self._generate_output(final_state)

        # Phase 6: 发射完成事件
        self.n9r20_bus.emit(N9R20CompressionCompleteEvent(
            state=final_state,
            output=output.output,
            compression_ratio=output.compression_ratio,
            semantic_retention=output.semantic_retention,
            session_id=session_id,
        ))

        return output

    def _build_initial_state(
        self,
        query: str,
        routing: N9R20RoutingDecision,
        session_id: str = "",
    ) -> N9R20DualState:
        """
        构建初始 N9R20DualState

        双视角（理论 / 具身）和默认辩证张力
        由 N9R20TensionConfig.DEFAULT_TENSION_TYPE 和 DEFAULT_INTENSITY 驱动。
        """
        from core.n9r20_config import n9r20_tension_config as TC
        return N9R20DualState(
            query=query,
            session_id=session_id or f"session_{int(time.time() * 1_000_000) % 1_000_000}",
            perspective_A=N9R20Perspective(
                name="theoretical",
                characteristics=["分析", "逻辑", "抽象"],
                perspective_type=N9R20PerspectiveType.THEORETICAL,
            ),
            perspective_B=N9R20Perspective(
                name="embodied",
                characteristics=["经验", "直觉", "具体"],
                perspective_type=N9R20PerspectiveType.EMBODIED,
            ),
            tension=N9R20Tension(
                perspective_A="theoretical",
                perspective_B="embodied",
                tension_type="dialectical",        # 双视角固有辩证张力，非可配置
                intensity=TC.DEFAULT_INTENSITY,
            ),
            target_fold_depth=routing.target_fold_depth,
            target_compression_ratio=routing.target_compression_ratio,
            current_mode="",
            mode_sequence=[],
            decision_ready=False,
        )

    def _four_mode_fold(
        self,
        state: N9R20DualState,
        routing: N9R20RoutingDecision,
    ) -> N9R20DualState:
        """
        四模编码驱动的动态折叠

        流程：
        1. 根据难度选择模式序列
        2. 按模式执行折叠
        3. 检查压缩目标
        4. 达到目标或最大深度后终止
        """
        current = state

        mode_sequence = self.four_mode_codec.select_mode_sequence(
            query=state.query,
            difficulty=routing.difficulty,
        )

        for mode in mode_sequence:
            current.current_mode = mode
            current.mode_sequence.append(mode)

            if mode == "construct":
                current = self._expand_semantic_space(current)

            elif mode == "deconstruct":
                current = self._deconstruct_concepts(current)

            elif mode == "validate":
                validation_result = self.validator.validate(current)
                if not validation_result.passed:
                    # 未通过验证 → 回退一层
                    current.fold_depth = max(current.fold_depth - 1, 0)
                    continue

            elif mode == "interrupt":
                current.decision_ready = True
                break

            # 执行一次折叠
            current = self.fold_engine.fold_once(current)
            current.fold_depth += 1

            # 检查是否达到压缩目标
            if self._check_compression_target(current, routing):
                current.decision_ready = True
                break

            # 达到最大 fold 深度 → 强制截断
            if current.fold_depth >= routing.target_fold_depth:
                current.current_mode = "interrupt"
                current.decision_ready = True
                break

        return current

    def _expand_semantic_space(self, state: N9R20DualState) -> N9R20DualState:
        """
        展开语义空间（建）

        在压缩前先展开语义空间，确保压缩时有足够的语义密度。
        简化实现：初始化 compressed_output = query。
        实际实现应使用 LLM 展开相关概念。
        """
        state.compressed_output = state.query
        return state

    def _deconstruct_concepts(self, state: N9R20DualState) -> N9R20DualState:
        """
        解构固化概念（破）

        打破固化概念，释放压缩空间。
        简化实现：执行一次 fold。
        实际实现应使用 LLM 解构概念。
        """
        return self.fold_engine.fold_once(state)

    def _check_compression_target(
        self,
        state: N9R20DualState,
        routing: N9R20RoutingDecision,
    ) -> bool:
        """
        检查是否同时达到：
        1. 压缩率 >= target_compression_ratio
        2. 语义保留 >= SEMANTIC_RETENTION_THRESHOLD（来自配置）
        """
        ratio_ok = state.compression_ratio >= routing.target_compression_ratio
        retention_ok = self.validator.validate(state).retention >= C_CFG.SEMANTIC_RETENTION_THRESHOLD
        return ratio_ok and retention_ok

    def _generate_output(self, state: N9R20DualState) -> N9R20CompressedOutput:
        """
        将 N9R20DualState 转换为 N9R20CompressedOutput
        """
        return N9R20CompressedOutput(
            output=state.compressed_output or state.query,
            compression_ratio=state.compression_ratio,
            semantic_retention=self.validator.validate(state).retention,
            fold_depth=state.fold_depth,
            mode_sequence=state.mode_sequence,
            decision_ready=state.decision_ready,
            session_id=state.session_id,
        )


# 全局单例
n9r20_compression_core = N9R20CompressionCore()
