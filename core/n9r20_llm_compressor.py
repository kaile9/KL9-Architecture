"""
9R-2.0 RHIZOME · LLM 压缩器（复用框架 LLM 连接）
────────────────────────────────────────────────────────
接入框架内已有的 LLM 客户端，不再维护独立的 API key / endpoint。

设计变更（Issue #2）：
  原实现：N9R20LLMCompressorConfig 内含 api_endpoint + api_key，自行管理 HTTP 调用。
  现实现：通过 llm_client 依赖注入，与 N9R20LLMFoldEvaluator 保持一致。
  好处：单一 LLM 配置源，避免 key 泄漏面扩大，降级逻辑统一。

依赖注入契约：
  llm_client 只需实现 .generate(prompt: str) -> str 即可，无框架强耦合。
  示例兼容对象：OpenAI client、Anthropic client、Ollama wrapper、自定义适配器。

降级安全：
  llm_client 为 None 或调用异常时，自动回退到 _simple_compress（字符截断）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Protocol

from core.n9r20_structures import N9R20DualState
from core.n9r20_config import n9r20_compression_config as C_CFG


# ════════════════════════════════════════════════════════════════════
# § 0 · LLM 客户端协议（最小化接口，便于注入任何兼容对象）
# ════════════════════════════════════════════════════════════════════

class LLMClientProtocol(Protocol):
    """最小化 LLM 客户端协议。

    任何实现了 generate(prompt: str) -> str 的对象都可注入，
    无需继承或注册。
    """

    def generate(self, prompt: str) -> str: ...


# ════════════════════════════════════════════════════════════════════
# § 1 · LLM 压缩器配置（剥离 API 密钥，仅保留压缩行为参数）
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20LLMCompressorConfig:
    """
    LLM 压缩器配置 —— 仅控制压缩行为，不管理 API 连接。

    API 连接由外部 llm_client 统一提供，参见 N9R20LLMCompressor。
    """

    # ── 压缩行为参数 ──────────────────────────────────────────
    model_name: str = "gpt-4o"        # 仅作标识/日志，不参与实际调用
    max_tokens: int = 500               # 期望 LLM 返回的最大 token 数（提示用）
    temperature: float = 0.3            # 温度参数（提示用）

    # ── 降级配置 ──────────────────────────────────────────────
    fallback_to_simple: bool = True     # LLM 不可用时回退到简单截断
    timeout_seconds: float = 10.0       # 建议的超时时间（由 llm_client 实现）

    # ── 压缩指令模板 ──────────────────────────────────────────
    compress_instruction_template: str = (
        "请将以下文本压缩到原始长度的 {ratio:.0%}，"
        "保留核心语义和关键概念，去除冗余表达：\n\n{text}"
    )


# ════════════════════════════════════════════════════════════════════
# § 2 · LLM 压缩器主类（依赖注入版）
# ════════════════════════════════════════════════════════════════════

class N9R20LLMCompressor:
    """
    LLM 语义压缩器 —— 复用框架内已有 LLM 连接。

    接口与 N9R20DynamicFoldEngine 兼容，可直接替换：
      core.fold_engine = N9R20LLMCompressor(llm_client=my_client)

    使用方式（两种）：
      1. 注入 LLM 客户端（推荐）
         compressor = N9R20LLMCompressor(llm_client=shared_llm)

      2. 仅作占位 / 降级模式
         compressor = N9R20LLMCompressor()   # llm_client=None，恒走简单截断
    """

    def __init__(
        self,
        llm_client: Optional[LLMClientProtocol] = None,
        config: Optional[N9R20LLMCompressorConfig] = None,
    ) -> None:
        """
        初始化 LLM 压缩器。

        Args:
            llm_client: 外部 LLM 客户端，需实现 .generate(prompt) -> str。
                        None 时所有压缩回退到简单截断。
            config:     压缩行为配置，None 时使用默认配置。
        """
        self.llm_client: Optional[LLMClientProtocol] = llm_client
        self.config: N9R20LLMCompressorConfig = config or N9R20LLMCompressorConfig()

        # 调用统计（用于监控和调试）
        self._call_count: int = 0           # LLM API 调用次数
        self._fallback_count: int = 0       # 降级到简单压缩的次数
        self._total_compress_count: int = 0  # 总压缩调用次数

    # ── 主要接口（与 N9R20DynamicFoldEngine 兼容） ──────────────────

    def fold_once(self, state: N9R20DualState) -> N9R20DualState:
        """
        执行一次折叠压缩。

        接口与 N9R20DynamicFoldEngine.fold_once 完全一致，
        可作为 N9R20CompressionCore.fold_engine 的替换。

        Args:
            state: 当前双状态容器

        Returns:
            更新了 compressed_output 和 compression_ratio 的状态
        """
        self._total_compress_count += 1

        current_text = state.compressed_output or state.query
        compressed = self._compress_text(current_text)

        state.compressed_output = compressed
        state.compression_ratio = len(state.query) / max(len(compressed), 1)

        return state

    def compress(
        self,
        text: str,
        target_ratio: float = 0.6,
        instruction: str = "",
    ) -> str:
        """
        独立文本压缩接口（不依赖 N9R20DualState）。

        Args:
            text:         待压缩文本
            target_ratio: 目标保留比例（0.6 = 保留 60%）
            instruction:  附加压缩指令（留空时使用默认模板）

        Returns:
            压缩后的文本
        """
        self._total_compress_count += 1

        if not text:
            return text

        return self._compress_text(text, target_ratio=target_ratio, instruction=instruction)

    # ── 内部压缩逻辑 ─────────────────────────────────────────────

    def _compress_text(
        self,
        text: str,
        target_ratio: Optional[float] = None,
        instruction: str = "",
    ) -> str:
        """
        内部压缩分发器。

        根据 llm_client 可用性决定走 LLM 语义压缩还是简单截断。

        Args:
            text:         待压缩文本
            target_ratio: 目标保留比例，None 时从配置读取
            instruction:  附加压缩指令

        Returns:
            压缩后的文本
        """
        # LLM 路径：客户端存在且未禁用
        if self.llm_client is not None:
            try:
                result = self._compress_with_llm(text, target_ratio, instruction)
                self._call_count += 1
                return result
            except Exception:
                # LLM 调用失败 → 记录并回退
                self._fallback_count += 1
                if not self.config.fallback_to_simple:
                    raise

        # 默认/降级路径：简单截断
        return self._simple_compress(text, target_ratio)

    def _simple_compress(
        self,
        text: str,
        target_ratio: Optional[float] = None,
    ) -> str:
        """
        简单压缩（降级方案）。

        与 N9R20DynamicFoldEngine._simple_compress 逻辑一致，
        作为 LLM 不可用时的保底实现。

        Args:
            text:         待压缩文本
            target_ratio: 目标保留比例，None 时使用 SIMPLE_COMPRESS_RATIO

        Returns:
            截断后的文本（末尾附加 "..."）
        """
        ratio = target_ratio if target_ratio is not None else C_CFG.SIMPLE_COMPRESS_RATIO
        target_length = int(len(text) * ratio)
        return text[:target_length] + "..."

    def _compress_with_llm(
        self,
        text: str,
        target_ratio: Optional[float] = None,
        instruction: str = "",
    ) -> str:
        """
        使用 LLM 进行语义感知压缩。

        流程：
          1. 根据 target_ratio 和 instruction 构建压缩提示词
          2. 调用注入的 llm_client.generate() 获取结果
          3. 基本验证（非空检查）
          4. 返回压缩后文本

        Args:
            text:         待压缩文本
            target_ratio: 目标保留比例
            instruction:  附加压缩指令（覆盖默认模板）

        Returns:
            LLM 压缩后的文本

        Raises:
            RuntimeError: llm_client 未注入时（此路径不应被调用，防御性检查）
        """
        if self.llm_client is None:
            raise RuntimeError(
                "_compress_with_llm 被调用但 llm_client 未注入。"
                "这是内部错误，请检查 _compress_text 的分发逻辑。"
            )

        ratio = target_ratio if target_ratio is not None else C_CFG.SIMPLE_COMPRESS_RATIO

        # 构建提示词
        if instruction:
            prompt = f"{instruction}\n\n{text}"
        else:
            prompt = self.config.compress_instruction_template.format(
                ratio=ratio,
                text=text,
            )

        # 调用注入的 LLM 客户端
        compressed = self.llm_client.generate(prompt)

        # 基本验证
        if not compressed or not compressed.strip():
            raise ValueError("LLM 返回空压缩结果")

        return compressed.strip()

    # ── 统计与监控 ─────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        获取压缩器使用统计。

        Returns:
            包含调用统计的字典：
            - total_compress_count: 总压缩调用次数
            - llm_call_count:       实际 LLM API 调用次数
            - fallback_count:       降级到简单压缩的次数
            - llm_available:        是否注入了 LLM 客户端
            - model_name:           配置中的模型标识名
        """
        return {
            "total_compress_count": self._total_compress_count,
            "llm_call_count": self._call_count,
            "fallback_count": self._fallback_count,
            "llm_available": self.llm_client is not None,
            "model_name": self.config.model_name,
        }

    def reset_stats(self) -> None:
        """重置统计计数器。"""
        self._call_count = 0
        self._fallback_count = 0
        self._total_compress_count = 0

    def __repr__(self) -> str:
        status = "active" if self.llm_client is not None else "fallback-only"
        return (
            f"N9R20LLMCompressor("
            f"status={status}, "
            f"calls={self._total_compress_count})"
        )


# ════════════════════════════════════════════════════════════════════
# § 3 · 模块级便捷访问
# ════════════════════════════════════════════════════════════════════

#: 全局 LLM 压缩器单例（未注入客户端，降级模式）
#: 使用时注入：n9r20_llm_compressor.llm_client = shared_llm
n9r20_llm_compressor: N9R20LLMCompressor = N9R20LLMCompressor()
