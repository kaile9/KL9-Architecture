"""
9R-2.0 RHIZOME · Compression-Core
压缩核心引擎 · 整合 orchestrator + core + fold-engine

Phase 3 重构：
- 移除硬编码 thinker 关键词
- 替换 _simple_compress() 为 N9R20LLMCompressor
- 集成 N9R20ProductionLogger 进行完整会话记录
- 从 n9r20_config 导入常量替代魔法数字
"""

import time
from typing import Optional
from dataclasses import dataclass

from core.n9r20_structures import (
    N9R20DualState, N9R20CompressedOutput, N9R20RoutingDecision,
    N9R20Perspective, N9R20Tension, N9R20PerspectiveType,
)
from core.n9r20_tension_bus import (
    N9R20TensionBus, n9r20_bus,
    N9R20CompressionTensionEvent, N9R20CompressionCompleteEvent,
)
from core.n9r20_config import n9r20_compression_config
from core.n9r20_llm_compressor import N9R20LLMCompressor, n9r20_llm_compressor
from core.n9r20_production_logger import N9R20ProductionLogger, n9r20_production_logger
from skills.n9r20_adaptive_router import n9r20_router


class N9R20AdaptiveFourModeCodec:
    """
    自适应四模编码器

    四模通用化：
    - 建 (Construct): 展开语义空间
    - 破 (Deconstruct): 解构固化概念
    - 证 (Validate): 验证语义保留
    - 截 (Interrupt): 强制收敛输出

    不是佛教专用，而是通用认知工具
    """

    def __init__(self):
        self._config = n9r20_compression_config

    def select_mode_sequence(self, query: str, difficulty: float) -> list:
        """
        根据任务难度动态选择模式序列

        简单任务（difficulty < simple_threshold）: construct → interrupt
        中等任务（simple_threshold-<medium_threshold）: construct → deconstruct → interrupt
        困难任务（>= medium_threshold）: construct → deconstruct → validate → interrupt
        """
        if difficulty < self._config.MODE_SIMPLE_DIFFICULTY_THRESHOLD:
            return list(self._config.MODE_SEQUENCE_SIMPLE)
        elif difficulty < self._config.MODE_MEDIUM_DIFFICULTY_THRESHOLD:
            return list(self._config.MODE_SEQUENCE_MEDIUM)
        else:
            return list(self._config.MODE_SEQUENCE_HARD)


class N9R20SemanticValidator:
    """
    语义验证器

    验证压缩后的语义保留率
    目标：保留率 > 85%
    """

    def __init__(self):
        self._config = n9r20_compression_config

    def validate(self, state: N9R20DualState) -> 'N9R20ValidationResult':
        """
        验证当前压缩状态的语义保留率

        简化实现：基于压缩比和 fold 深度估算
        实际实现应使用 LLM 评估语义相似度
        """
        ratio = state.compression_ratio

        # 使用配置常量替代魔法数字
        safe_ratio = max(ratio, 0.01)
        estimated_retention = min(
            1.0 / (safe_ratio * self._config.VALIDATOR_ESTIMATION_DIVISOR),
            1.0
        )

        # fold 深度惩罚
        fold_penalty = state.fold_depth * self._config.FOLD_DEPTH_PENALTY_PER_LEVEL
        estimated_retention -= fold_penalty

        estimated_retention = max(0.0, min(1.0, estimated_retention))

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
        self.passed = self.retention >= n9r20_compression_config.SEMANTIC_RETENTION_THRESHOLD


class N9R20DynamicFoldEngine:
    """
    动态折叠引擎

    执行单次折叠操作。
    Phase 3: 使用 N9R20LLMCompressor 替代 _simple_compress()。
    """

    def __init__(self, llm_compressor: Optional[N9R20LLMCompressor] = None):
        """
        参数：
            llm_compressor: LLM 压缩器实例，None 时使用全局单例
        """
        self._config = n9r20_compression_config
        self._llm_compressor = llm_compressor or n9r20_llm_compressor

    def fold_once(self, state: N9R20DualState) -> N9R20DualState:
        """
        执行一次折叠

        使用 N9R20LLMCompressor 进行语义压缩（LLM 优先，回退规则式）。
        """
        current_text = state.compressed_output or state.query

        # Phase 3: 使用 N9R20LLMCompressor 替代 _simple_compress
        result = self._llm_compressor.compress(
            text=current_text,
            target_ratio=state.target_compression_ratio,
        )

        compressed = result.compressed_text

        # 更新状态
        state.compressed_output = compressed
        state.compression_ratio = len(state.query) / max(len(compressed), 1)

        return state

    def _simple_compress(self, text: str) -> str:
        """
        简单压缩（向后兼容 — 委托给 N9R20LLMCompressor 的规则式回退）

        保留此方法以维持向后兼容的 API 签名。
        """
        result = self._llm_compressor.compress(text=text, target_ratio=2.5)
        return result.compressed_text


class N9R20CompressionCore:
    """
    压缩核心引擎

    整合 orchestrator + core + fold-engine

    职责：
    1. 接收 query → 动态 fold → 压缩输出
    2. 四模编码驱动的动态折叠
    3. 双轨验证：压缩率 + 语义保留
    4. Phase 3: 集成 N9R20ProductionLogger 进行完整会话记录
    """

    def __init__(self, production_logger: Optional[N9R20ProductionLogger] = None):
        self.four_mode_codec = N9R20AdaptiveFourModeCodec()
        self.fold_engine = N9R20DynamicFoldEngine()
        self.validator = N9R20SemanticValidator()
        self.n9r20_bus = n9r20_bus
        self.n9r20_router = n9r20_router
        self._config = n9r20_compression_config
        # Phase 3: 生产日志记录器
        self._production_logger = production_logger or n9r20_production_logger

    def compress(self, query: str,
                 routing: Optional[N9R20RoutingDecision] = None,
                 session_id: str = "") -> N9R20CompressedOutput:
        """
        主压缩流程

        流程：
        1. 路由决策（如果没有提供）
        2. 发射 query 到 N9R20TensionBus
        3. 收集技能响应
        4. 构建初始 N9R20DualState
        5. 四模编码 + 动态折叠
        6. 生成输出
        7. 发射完成事件
        8. Phase 3: 记录到 N9R20ProductionLogger
        """
        # Phase 1: 路由决策
        if routing is None:
            routing = self.n9r20_router.route(query)

        # Phase 3: 开始生产会话
        prod_session = self._production_logger.start(
            query=query,
            session_id=session_id,
            path=routing.path,
            target_fold_depth=routing.target_fold_depth,
            target_compression_ratio=routing.target_compression_ratio,
            difficulty=routing.difficulty,
            urgency=routing.urgency,
        )

        # Phase 2: 发射 query 到 N9R20TensionBus
        self.n9r20_bus.emit(N9R20CompressionTensionEvent(
            query=query,
            session_id=session_id,
            fold_depth=0,
            target_fold_depth=routing.target_fold_depth,
            target_ratio=routing.target_compression_ratio,
            urgency=routing.urgency,
        ))

        # Phase 3: 收集技能响应（简化：直接构建 N9R20DualState）
        state = self._build_initial_state(query, routing, session_id)

        # Phase 4: 四模编码 + 动态折叠
        final_state = self._four_mode_fold(state, routing, session_id)

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

        # Phase 3: 结束生产会话并记录
        self._production_logger.end(
            session_id=prod_session.session_id,
            output=output,
            success=output.semantic_retention >= self._config.SEMANTIC_RETENTION_THRESHOLD,
        )

        return output

    def _build_initial_state(self, query: str,
                            routing: N9R20RoutingDecision,
                            session_id: str = "") -> N9R20DualState:
        """
        构建初始 N9R20DualState
        """
        return N9R20DualState(
            query=query,
            session_id=session_id or f"session_{int(time.time() * 1000000) % 1000000}",
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
                tension_type="dialectical",
                intensity=0.5,
            ),
            target_fold_depth=routing.target_fold_depth,
            target_compression_ratio=routing.target_compression_ratio,
            current_mode="",
            mode_sequence=[],
            decision_ready=False,
        )

    def _four_mode_fold(self, state: N9R20DualState,
                       routing: N9R20RoutingDecision,
                       session_id: str = "") -> N9R20DualState:
        """
        四模编码驱动的动态折叠
        """
        current = state

        mode_sequence = self.four_mode_codec.select_mode_sequence(
            query=state.query,
            difficulty=routing.difficulty,
        )

        for mode in mode_sequence:
            current.current_mode = mode
            current.mode_sequence.append(mode)

            # Phase 3: 记录每次迭代到 production_logger
            iter_start = time.time()

            if mode == "construct":
                current = self._expand_semantic_space(current)

            elif mode == "deconstruct":
                current = self._deconstruct_concepts(current)

            elif mode == "validate":
                validation_result = self.validator.validate(current)
                if not validation_result.passed:
                    current.fold_depth = max(current.fold_depth - 1, 0)
                    continue

            elif mode == "interrupt":
                current.decision_ready = True
                break

            # 执行一次折叠
            current = self.fold_engine.fold_once(current)
            current.fold_depth += 1

            # Phase 3: 记录迭代
            self._production_logger.log(
                session_id=session_id or current.session_id,
                mode=mode,
                fold_depth=current.fold_depth,
                compression_ratio=current.compression_ratio,
                semantic_retention=self.validator.validate(current).retention,
                output_preview=(current.compressed_output or "")[:80],
                duration_ms=(time.time() - iter_start) * 1000,
            )

            # 检查是否达到目标
            if self._check_compression_target(current, routing):
                current.decision_ready = True
                break

            # 检查是否达到最大 fold 深度
            if current.fold_depth >= routing.target_fold_depth:
                current.current_mode = "interrupt"
                current.decision_ready = True
                break

        return current

    def _expand_semantic_space(self, state: N9R20DualState) -> N9R20DualState:
        """展开语义空间（建）"""
        state.compressed_output = state.query
        return state

    def _deconstruct_concepts(self, state: N9R20DualState) -> N9R20DualState:
        """解构固化概念（破）"""
        return self.fold_engine.fold_once(state)

    def _check_compression_target(self, state: N9R20DualState,
                                  routing: N9R20RoutingDecision) -> bool:
        """
        检查是否达到压缩目标

        硬性要求：
        1. 压缩率达标
        2. 语义保留达标
        """
        ratio_ok = state.compression_ratio >= routing.target_compression_ratio

        validation = self.validator.validate(state)
        retention_ok = validation.retention >= self._config.SEMANTIC_RETENTION_THRESHOLD

        return ratio_ok and retention_ok

    def _generate_output(self, state: N9R20DualState) -> N9R20CompressedOutput:
        """生成最终输出"""
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
