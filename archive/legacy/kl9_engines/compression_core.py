"""
KL9-RHIZOME v2.0 · Compression-Core
压缩核心引擎 · 整合 orchestrator + core + fold-engine
"""

import time
from typing import Optional
from dataclasses import dataclass

from core.structures import DualState, CompressedOutput, RoutingDecision, Perspective, Tension, PerspectiveType
from core.tension_bus import TensionBus2, bus, CompressionTensionEvent, CompressionCompleteEvent
from skills.adaptive_router import router


class AdaptiveFourModeCodec:
    """
    自适应四模编码器
    
    四模通用化：
    - 建 (Construct): 展开语义空间
    - 破 (Deconstruct): 解构固化概念
    - 证 (Validate): 验证语义保留
    - 截 (Interrupt): 强制收敛输出
    
    不是佛教专用，而是通用认知工具
    """
    
    def select_mode_sequence(self, query: str, difficulty: float) -> list:
        """
        根据任务难度动态选择模式序列
        
        简单任务（difficulty < 0.3）: construct → interrupt
        中等任务（0.3-0.7）: construct → deconstruct → interrupt
        困难任务（> 0.7）: construct → deconstruct → validate → interrupt
        """
        if difficulty < 0.3:
            return ["construct", "interrupt"]
        elif difficulty < 0.7:
            return ["construct", "deconstruct", "interrupt"]
        else:
            return ["construct", "deconstruct", "validate", "interrupt"]


class SemanticValidator:
    """
    语义验证器
    
    验证压缩后的语义保留率
    目标：保留率 > 85%
    """
    
    def validate(self, state: DualState) -> 'ValidationResult':
        """
        验证当前压缩状态的语义保留率
        
        简化实现：基于压缩比和 fold 深度估算
        实际实现应使用 LLM 评估语义相似度
        """
        # 基于压缩比估算保留率
        # 压缩比越高，保留率越低
        ratio = state.compression_ratio
        
        # 估算公式：保留率 = 1 / (压缩比 * 0.5)
        # 当压缩比 = 2.0 时，保留率 ≈ 1.0
        # 当压缩比 = 2.5 时，保留率 ≈ 0.8
        safe_ratio = max(ratio, 0.01)  # 防止除零
        estimated_retention = min(1.0 / (safe_ratio * 0.5), 1.0)
        
        # fold 深度惩罚（fold 越深，保留率越低）
        fold_penalty = state.fold_depth * 0.02
        estimated_retention -= fold_penalty
        
        # 确保保留率在 [0, 1] 范围内
        estimated_retention = max(0.0, min(1.0, estimated_retention))
        
        return ValidationResult(
            retention=round(estimated_retention, 2),
            ratio=ratio,
            fold_depth=state.fold_depth
        )


@dataclass
class ValidationResult:
    """验证结果"""
    retention: float = 1.0
    ratio: float = 1.0
    fold_depth: int = 0
    passed: bool = False
    
    def __post_init__(self):
        self.passed = self.retention >= 0.85


class DynamicFoldEngine:
    """
    动态折叠引擎
    
    执行单次折叠操作
    """
    
    def fold_once(self, state: DualState) -> DualState:
        """
        执行一次折叠
        
        简化实现：基于当前状态生成压缩输出
        实际实现应使用 LLM 进行语义压缩
        """
        # 模拟折叠：缩短文本长度
        current_text = state.compressed_output or state.query
        
        # 简单压缩策略：保留关键概念，去除修饰
        # 实际实现应使用更复杂的语义压缩
        compressed = self._simple_compress(current_text)
        
        # 更新状态
        state.compressed_output = compressed
        state.compression_ratio = len(state.query) / max(len(compressed), 1)
        
        return state
    
    def _simple_compress(self, text: str) -> str:
        """
        简单压缩（模拟）
        
        实际实现应使用 LLM 进行语义压缩
        """
        # 模拟压缩：保留前 60% 的字符
        # 实际实现应使用语义压缩
        target_length = int(len(text) * 0.6)
        return text[:target_length] + "..."


class CompressionCore:
    """
    压缩核心引擎
    
    整合 orchestrator + core + fold-engine
    
    职责：
    1. 接收 query → 动态 fold → 压缩输出
    2. 四模编码驱动的动态折叠
    3. 双轨验证：压缩率 + 语义保留
    """
    
    def __init__(self):
        self.four_mode_codec = AdaptiveFourModeCodec()
        self.fold_engine = DynamicFoldEngine()
        self.validator = SemanticValidator()
        self.bus = bus
        self.router = router
    
    def compress(self, query: str, 
                 routing: Optional[RoutingDecision] = None,
                 session_id: str = "") -> CompressedOutput:
        """
        主压缩流程
        
        流程：
        1. 路由决策（如果没有提供）
        2. 发射 query 到 TensionBus
        3. 收集技能响应
        4. 构建初始 DualState
        5. 四模编码 + 动态折叠
        6. 生成输出
        7. 发射完成事件
        """
        # Phase 1: 路由决策
        if routing is None:
            routing = self.router.route(query)
        
        # Phase 2: 发射 query 到 TensionBus
        self.bus.emit(CompressionTensionEvent(
            query=query,
            session_id=session_id,
            fold_depth=0,
            target_fold_depth=routing.target_fold_depth,
            target_ratio=routing.target_compression_ratio,
            urgency=routing.urgency
        ))
        
        # Phase 3: 收集技能响应（简化：直接构建 DualState）
        # 实际实现应等待 Dual-Reasoner 和 Semantic-Graph 的响应
        state = self._build_initial_state(query, routing, session_id)
        
        # Phase 4: 四模编码 + 动态折叠
        final_state = self._four_mode_fold(state, routing)
        
        # Phase 5: 生成输出
        output = self._generate_output(final_state)
        
        # Phase 6: 发射完成事件
        self.bus.emit(CompressionCompleteEvent(
            state=final_state,
            output=output.output,
            compression_ratio=output.compression_ratio,
            semantic_retention=output.semantic_retention,
            session_id=session_id
        ))
        
        return output
    
    def _build_initial_state(self, query: str, 
                            routing: RoutingDecision,
                            session_id: str = "") -> DualState:
        """
        构建初始 DualState
        
        简化实现：直接构建
        实际实现应收集 Dual-Reasoner 和 Semantic-Graph 的响应
        """
        return DualState(
            query=query,
            session_id=session_id or f"session_{int(time.time() * 1000000) % 1000000}",
            perspective_A=Perspective(
                name="theoretical",
                characteristics=["分析", "逻辑", "抽象"],
                perspective_type=PerspectiveType.THEORETICAL
            ),
            perspective_B=Perspective(
                name="embodied",
                characteristics=["经验", "直觉", "具体"],
                perspective_type=PerspectiveType.EMBODIED
            ),
            tension=Tension(
                perspective_A="theoretical",
                perspective_B="embodied",
                tension_type="dialectical",
                intensity=0.5
            ),
            target_fold_depth=routing.target_fold_depth,
            target_compression_ratio=routing.target_compression_ratio,
            current_mode="",
            mode_sequence=[],
            decision_ready=False
        )
    
    def _four_mode_fold(self, state: DualState, 
                       routing: RoutingDecision) -> DualState:
        """
        四模编码驱动的动态折叠
        
        流程：
        1. 根据难度选择模式序列
        2. 按模式执行折叠
        3. 检查压缩目标
        4. 达到目标或最大深度后终止
        """
        current = state
        
        # 根据难度选择模式序列
        mode_sequence = self.four_mode_codec.select_mode_sequence(
            query=state.query,
            difficulty=routing.difficulty
        )
        
        for mode in mode_sequence:
            current.current_mode = mode
            current.mode_sequence.append(mode)
            
            if mode == "construct":
                # 建：展开语义空间
                current = self._expand_semantic_space(current)
            
            elif mode == "deconstruct":
                # 破：解构固化概念
                current = self._deconstruct_concepts(current)
            
            elif mode == "validate":
                # 证：验证语义保留
                validation_result = self.validator.validate(current)
                if not validation_result.passed:
                    # 未通过验证 → 回退到 deconstruct
                    current.fold_depth = max(current.fold_depth - 1, 0)
                    continue
            
            elif mode == "interrupt":
                # 截：强制收敛输出
                current.decision_ready = True
                break
            
            # 执行一次折叠
            current = self.fold_engine.fold_once(current)
            current.fold_depth += 1
            
            # 检查是否达到目标
            if self._check_compression_target(current, routing):
                current.decision_ready = True
                break
            
            # 检查是否达到最大 fold 深度
            if current.fold_depth >= routing.target_fold_depth:
                # 强制截断
                current.current_mode = "interrupt"
                current.decision_ready = True
                break
        
        return current
    
    def _expand_semantic_space(self, state: DualState) -> DualState:
        """
        展开语义空间（建）
        
        在压缩前先展开语义空间，确保压缩时有足够的语义密度
        """
        # 简化实现：标记为展开状态
        # 实际实现应使用 LLM 展开相关概念
        state.compressed_output = state.query  # 初始状态
        return state
    
    def _deconstruct_concepts(self, state: DualState) -> DualState:
        """
        解构固化概念（破）
        
        打破固化概念，释放压缩空间
        """
        # 简化实现：执行一次折叠
        # 实际实现应使用 LLM 解构概念
        return self.fold_engine.fold_once(state)
    
    def _check_compression_target(self, state: DualState, 
                                  routing: RoutingDecision) -> bool:
        """
        检查是否达到压缩目标
        
        硬性要求：
        1. 压缩率达标
        2. 语义保留达标
        """
        # 压缩率达标
        ratio_ok = state.compression_ratio >= routing.target_compression_ratio
        
        # 语义保留达标
        validation = self.validator.validate(state)
        retention_ok = validation.retention >= 0.85
        
        return ratio_ok and retention_ok
    
    def _generate_output(self, state: DualState) -> CompressedOutput:
        """
        生成最终输出
        
        将 DualState 转换为 CompressedOutput
        """
        return CompressedOutput(
            output=state.compressed_output or state.query,
            compression_ratio=state.compression_ratio,
            semantic_retention=self.validator.validate(state).retention,
            fold_depth=state.fold_depth,
            mode_sequence=state.mode_sequence,
            decision_ready=state.decision_ready,
            session_id=state.session_id
        )


# 全局单例
compression_core = CompressionCore()
