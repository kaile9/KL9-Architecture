"""
9R-2.0 RHIZOME · LLM Semantic Compressor
────────────────────────────────────────
基于真实 LLM 的语义压缩器 — 替换 compression_core 中的 _simple_compress() 存根。

设计原则：
    1. 使用 LLM 进行真正的语义压缩，而非字符截断
    2. 内置重试逻辑（指数退避 + 抖动）
    3. 失败时自动回退到规则式压缩
    4. 支持自定义 prompt 模板
    5. 与 N9R20DynamicFoldEngine 无缝集成（替换 _simple_compress）

与 compression_core 的关系：
    - N9R20DynamicFoldEngine._simple_compress() → N9R20LLMCompressor.compress()
    - 当 LLM 不可用时，回退到规则式压缩（保留原 _simple_compress 的行为）

使用示例：
    >>> compressor = N9R20LLMCompressor(llm_client=my_client)
    >>> result = compressor.compress("量子纠缠与缘起性空的比较研究...", target_ratio=2.5)
    >>> print(result)  # 语义压缩后的文本
"""

from __future__ import annotations

import re
import time
import random
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.n9r20_structures import N9R20CompressedOutput


# ════════════════════════════════════════════════════════════════════
# § 1 · N9R20CompressionResult
# ════════════════════════════════════════════════════════════════════

class N9R20CompressionResult:
    """
    压缩操作的结果封装。

    属性：
        compressed_text: 压缩后的文本
        original_length: 原始文本长度
        compressed_length: 压缩后长度
        compression_ratio: 实际压缩率
        method: 使用的压缩方法 ('llm' | 'rule-based')
        retries: LLM 重试次数
        duration_ms: 压缩耗时（毫秒）
        success: 是否成功
        error_message: 错误信息（如果失败）
    """

    __slots__ = (
        "compressed_text",
        "original_length",
        "compressed_length",
        "compression_ratio",
        "method",
        "retries",
        "duration_ms",
        "success",
        "error_message",
    )

    def __init__(
        self,
        compressed_text: str = "",
        original_length: int = 0,
        compressed_length: int = 0,
        compression_ratio: float = 1.0,
        method: str = "rule-based",
        retries: int = 0,
        duration_ms: float = 0.0,
        success: bool = True,
        error_message: str = "",
    ) -> None:
        self.compressed_text = compressed_text
        self.original_length = original_length
        self.compressed_length = compressed_length
        self.compression_ratio = compression_ratio
        self.method = method
        self.retries = retries
        self.duration_ms = duration_ms
        self.success = success
        self.error_message = error_message

    def __repr__(self) -> str:
        return (
            f"N9R20CompressionResult(method={self.method!r}, "
            f"ratio={self.compression_ratio:.2f}, "
            f"retries={self.retries}, "
            f"duration={self.duration_ms:.1f}ms, "
            f"success={self.success})"
        )


# ════════════════════════════════════════════════════════════════════
# § 2 · N9R20LLMCompressor — LLM 语义压缩器
# ════════════════════════════════════════════════════════════════════


class N9R20LLMCompressor:
    """
    基于 LLM 的语义压缩器。

    核心功能：
    - compress(): 语义压缩（LLM 优先，回退规则式）
    - _llm_compress(): 调用 LLM 进行压缩
    - _rule_based_compress(): 规则式压缩（回退方案）
    - _retry_with_backoff(): 带指数退避的重试逻辑
    - set_prompt_template(): 自定义 prompt 模板

    压缩策略：
    1. 短文本（< 20 字符）：直接返回原文（无需压缩）
    2. 中等文本（20-200 字符）：LLM 压缩
    3. 长文本（> 200 字符）：分段 LLM 压缩 + 聚合

    回退策略：
    - LLM 调用失败 → 规则式压缩
    - LLM 返回空 → 规则式压缩
    - LLM 超时 → 规则式压缩

    线程安全：使用 Lock 保护 LLM 调用（防止并发令牌溢出）。
    """

    # 默认 prompt 模板
    DEFAULT_PROMPT_TEMPLATE: str = (
        "你是一位认知压缩专家。请将以下文本进行语义压缩，"
        "保留核心概念和关键逻辑关系，去除修饰性语言和冗余信息。\n\n"
        "原始文本:\n{text}\n\n"
        "目标压缩率: {target_ratio}x\n"
        "保留关键概念: {concepts}\n\n"
        "请输出压缩后的文本（仅输出压缩文本，不要添加解释）："
    )

    # 压缩分段最大字符数
    CHUNK_MAX_CHARS: int = 2000

    # 重试配置
    MAX_RETRIES: int = 3
    BASE_DELAY_SECONDS: float = 0.5
    MAX_DELAY_SECONDS: float = 5.0

    def __init__(
        self,
        llm_client: Any = None,
        prompt_template: Optional[str] = None,
        max_retries: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 5.0,
    ) -> None:
        """
        初始化 LLM 压缩器。

        参数：
            llm_client: LLM 客户端（需实现 generate(prompt) → str 方法）
            prompt_template: 自定义 prompt 模板，需包含 {text} 和 {target_ratio} 占位符
            max_retries: 最大重试次数，默认 3
            base_delay: 重试基础延迟（秒），默认 0.5
            max_delay: 重试最大延迟（秒），默认 5.0
        """
        self.llm_client = llm_client
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT_TEMPLATE
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        # 线程安全
        self._lock = threading.Lock()

        # 统计
        self._total_calls: int = 0
        self._total_success: int = 0
        self._total_retries: int = 0
        self._total_fallbacks: int = 0

    # ── 属性 ──────────────────────────────────────────────────

    @property
    def success_rate(self) -> float:
        """LLM 压缩成功率。"""
        if self._total_calls == 0:
            return 0.0
        return self._total_success / self._total_calls

    @property
    def fallback_rate(self) -> float:
        """回退到规则式压缩的比例。"""
        if self._total_calls == 0:
            return 0.0
        return self._total_fallbacks / self._total_calls

    # ── 公共 API ──────────────────────────────────────────────

    def compress(
        self,
        text: str,
        target_ratio: float = 2.5,
        concepts: Optional[List[str]] = None,
    ) -> N9R20CompressionResult:
        """
        执行语义压缩。

        参数：
            text: 待压缩文本
            target_ratio: 目标压缩率 (2.0-2.5)
            concepts: 需要保留的关键概念列表（可选）

        返回：
            N9R20CompressionResult
        """
        start_time = time.time()
        self._total_calls += 1

        # 短文本直接返回
        if len(text) < 20:
            return N9R20CompressionResult(
                compressed_text=text,
                original_length=len(text),
                compressed_length=len(text),
                compression_ratio=1.0,
                method="rule-based",
                retries=0,
                duration_ms=(time.time() - start_time) * 1000,
                success=True,
            )

        # 尝试 LLM 压缩
        if self.llm_client is not None:
            result = self._try_llm_compress(text, target_ratio, concepts, start_time)
            if result is not None and result.success:
                self._total_success += 1
                return result

        # 回退到规则式压缩
        self._total_fallbacks += 1
        return self._rule_based_compress(text, target_ratio, start_time)

    def set_prompt_template(self, template: str) -> None:
        """
        设置自定义 prompt 模板。

        必须包含占位符：
        - {text}: 待压缩文本
        - {target_ratio}: 目标压缩率
        - {concepts}: 关键概念（可选）

        参数：
            template: prompt 模板字符串
        """
        if "{text}" not in template:
            raise ValueError("Prompt template must contain '{text}' placeholder")
        if "{target_ratio}" not in template:
            raise ValueError("Prompt template must contain '{target_ratio}' placeholder")
        self.prompt_template = template

    def get_stats(self) -> Dict[str, Any]:
        """获取压缩器统计信息。"""
        return {
            "total_calls": self._total_calls,
            "total_success": self._total_success,
            "total_retries": self._total_retries,
            "total_fallbacks": self._total_fallbacks,
            "success_rate": self.success_rate,
            "fallback_rate": self.fallback_rate,
            "has_llm_client": self.llm_client is not None,
        }

    # ── 内部方法 ──────────────────────────────────────────────

    def _try_llm_compress(
        self,
        text: str,
        target_ratio: float,
        concepts: Optional[List[str]],
        start_time: float,
    ) -> Optional[N9R20CompressionResult]:
        """
        尝试 LLM 压缩（含重试逻辑）。

        参数：
            text: 待压缩文本
            target_ratio: 目标压缩率
            concepts: 关键概念
            start_time: 计时起点

        返回：
            N9R20CompressionResult 或 None（失败）
        """
        concepts_str = ", ".join(concepts) if concepts else "自动识别"

        # 长文本分段处理
        if len(text) > self.CHUNK_MAX_CHARS:
            return self._chunked_llm_compress(text, target_ratio, concepts_str, start_time)

        return self._retry_with_backoff(
            text=text,
            target_ratio=target_ratio,
            concepts_str=concepts_str,
            start_time=start_time,
        )

    def _retry_with_backoff(
        self,
        text: str,
        target_ratio: float,
        concepts_str: str,
        start_time: float,
    ) -> Optional[N9R20CompressionResult]:
        """
        带指数退避 + 随机抖动的重试逻辑。

        参数：
            text: 待压缩文本
            target_ratio: 目标压缩率
            concepts_str: 概念字符串
            start_time: 计时起点

        返回：
            N9R20CompressionResult 或 None
        """
        last_error: str = ""

        for attempt in range(self.max_retries + 1):
            try:
                compressed = self._call_llm(text, target_ratio, concepts_str)

                # 验证结果
                if self._validate_compression(text, compressed):
                    duration_ms = (time.time() - start_time) * 1000
                    comp_ratio = len(text) / max(len(compressed), 1)
                    return N9R20CompressionResult(
                        compressed_text=compressed,
                        original_length=len(text),
                        compressed_length=len(compressed),
                        compression_ratio=round(comp_ratio, 2),
                        method="llm",
                        retries=attempt,
                        duration_ms=round(duration_ms, 1),
                        success=True,
                    )
                else:
                    last_error = "LLM output validation failed (too short or empty)"

            except Exception as exc:
                last_error = str(exc)
                self._total_retries += 1

            # 最后一次尝试失败，不回退
            if attempt < self.max_retries:
                delay = self._compute_backoff(attempt)
                time.sleep(delay)

        # 所有重试失败
        return None

    def _call_llm(
        self,
        text: str,
        target_ratio: float,
        concepts_str: str,
    ) -> str:
        """
        实际调用 LLM（线程安全）。

        参数：
            text: 待压缩文本
            target_ratio: 目标压缩率
            concepts_str: 概念字符串

        返回：
            LLM 输出文本
        """
        prompt = self.prompt_template.format(
            text=text,
            target_ratio=target_ratio,
            concepts=concepts_str,
        )

        with self._lock:
            if self.llm_client is None:
                raise RuntimeError("LLM client not available")
            # 支持多种 LLM 客户端接口
            if hasattr(self.llm_client, "generate"):
                return self.llm_client.generate(prompt)
            elif callable(self.llm_client):
                return self.llm_client(prompt)
            else:
                raise RuntimeError(
                    "LLM client must implement generate(prompt) or be callable"
                )

    def _validate_compression(self, original: str, compressed: str) -> bool:
        """
        验证压缩结果的有效性。

        检查：
        1. 压缩结果非空
        2. 压缩结果至少有原始长度的 10%（避免过度压缩）
        3. 压缩结果不超过原始长度（避免膨胀）

        参数：
            original: 原始文本
            compressed: 压缩后文本

        返回：
            True 如果验证通过
        """
        if not compressed or not compressed.strip():
            return False
        # 至少保留 10% 的长度
        if len(compressed) < len(original) * 0.1:
            return False
        # 压缩后不应比原始更长
        if len(compressed) > len(original):
            return False
        return True

    def _compute_backoff(self, attempt: int) -> float:
        """
        计算指数退避延迟。

        公式：
            delay = min(base_delay * 2^attempt + random(0, 0.5), max_delay)

        参数：
            attempt: 当前尝试次数（0-indexed）

        返回：
            延迟秒数
        """
        delay = self.base_delay * (2 ** attempt)
        jitter = random.uniform(0, 0.5)
        return min(delay + jitter, self.max_delay)

    def _chunked_llm_compress(
        self,
        text: str,
        target_ratio: float,
        concepts_str: str,
        start_time: float,
    ) -> Optional[N9R20CompressionResult]:
        """
        长文本分段压缩 + 聚合。

        策略：
        1. 将文本分为 CHUNK_MAX_CHARS 的段落
        2. 每段独立执行 LLM 压缩
        3. 聚合所有压缩结果
        4. 如果某段失败，整段使用规则式压缩替代

        参数：
            text: 长文本
            target_ratio: 目标压缩率
            concepts_str: 概念字符串
            start_time: 计时起点

        返回：
            N9R20CompressionResult 或 None
        """
        chunks = self._split_text(text, self.CHUNK_MAX_CHARS)
        compressed_chunks: List[str] = []
        total_retries = 0
        all_llm = True

        for chunk in chunks:
            result = self._retry_with_backoff(
                text=chunk,
                target_ratio=target_ratio,
                concepts_str=concepts_str,
                start_time=time.time(),
            )
            if result is not None and result.success:
                compressed_chunks.append(result.compressed_text)
                total_retries += result.retries
            else:
                # 回退：该段使用规则式压缩
                rule_result = self._rule_based_compress(chunk, target_ratio, time.time())
                compressed_chunks.append(rule_result.compressed_text)
                all_llm = False

        combined = "\n".join(compressed_chunks)
        duration_ms = (time.time() - start_time) * 1000
        comp_ratio = len(text) / max(len(combined), 1)

        return N9R20CompressionResult(
            compressed_text=combined,
            original_length=len(text),
            compressed_length=len(combined),
            compression_ratio=round(comp_ratio, 2),
            method="llm" if all_llm else "rule-based",
            retries=total_retries,
            duration_ms=round(duration_ms, 1),
            success=True,
        )

    def _rule_based_compress(
        self,
        text: str,
        target_ratio: float = 2.5,
        start_time: float = 0.0,
    ) -> N9R20CompressionResult:
        """
        规则式压缩（回退方案）。

        策略：
        1. 保留关键概念（2-4 字中文术语 + 3+ 字母英文词）
        2. 保留包含张力关键词的句子
        3. 按目标压缩率截断

        与原始 _simple_compress() 保持语义一致，
        但更智能地选择保留内容。

        参数：
            text: 待压缩文本
            target_ratio: 目标压缩率
            start_time: 计时起点（0 = 当前时间）

        返回：
            N9R20CompressionResult
        """
        if start_time == 0.0:
            start_time = time.time()

        if not text:
            return N9R20CompressionResult(
                compressed_text="",
                original_length=0,
                compressed_length=0,
                compression_ratio=1.0,
                method="rule-based",
                retries=0,
                duration_ms=(time.time() - start_time) * 1000,
                success=True,
            )

        # 短文本直接返回
        if len(text) <= 20:
            return N9R20CompressionResult(
                compressed_text=text,
                original_length=len(text),
                compressed_length=len(text),
                compression_ratio=1.0,
                method="rule-based",
                retries=0,
                duration_ms=(time.time() - start_time) * 1000,
                success=True,
            )

        # ── 智能规则式压缩 ─────────────────────────────────

        # 1. 按句子分割
        sentences = self._split_sentences(text)

        # 2. 为每个句子评分（越高越重要，越应保留）
        scored: List[Tuple[str, float]] = [
            (s, self._score_sentence(s)) for s in sentences
        ]

        # 3. 按分数降序排列
        scored.sort(key=lambda x: x[1], reverse=True)

        # 4. 按目标压缩率选择保留的句子
        target_length = max(int(len(text) / target_ratio), 20)
        selected: List[str] = []
        current_length = 0

        for sentence, _score in scored:
            if current_length + len(sentence) <= target_length:
                selected.append(sentence)
                current_length += len(sentence)
            elif current_length < target_length:
                # 最后一句截断
                remaining = target_length - current_length
                if remaining > 10:
                    selected.append(sentence[:remaining] + "…")
                break

        # 按原始顺序重排
        original_order: Dict[str, int] = {
            s: i for i, s in enumerate(sentences)
        }
        selected.sort(key=lambda s: original_order.get(s, 0))

        compressed = "".join(selected) if selected else text[:target_length] + "…"

        duration_ms = (time.time() - start_time) * 1000
        comp_ratio = len(text) / max(len(compressed), 1)

        return N9R20CompressionResult(
            compressed_text=compressed,
            original_length=len(text),
            compressed_length=len(compressed),
            compression_ratio=round(comp_ratio, 2),
            method="rule-based",
            retries=0,
            duration_ms=round(duration_ms, 1),
            success=True,
        )

    # ── 辅助方法 ──────────────────────────────────────────────

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """
        按句子分割文本。

        支持中英文标点：。！？.!?\n

        参数：
            text: 待分割文本

        返回：
            句子列表（保留分隔符）
        """
        # 使用零宽断言保留分隔符
        parts = re.split(r'(?<=[。！？.!?\n])', text)
        return [p for p in parts if p.strip()]

    @staticmethod
    def _split_text(text: str, max_chars: int) -> List[str]:
        """
        将文本分割为等长段落。

        参数：
            text: 待分割文本
            max_chars: 每段最大字符数

        返回：
            段落列表
        """
        sentences = N9R20LLMCompressor._split_sentences(text)
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length: int = 0

        for sentence in sentences:
            if current_length + len(sentence) > max_chars and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks or [text]

    @staticmethod
    def _score_sentence(sentence: str) -> float:
        """
        为句子评分（保留重要性）。

        评分因素：
        - 包含专业术语（2-4 字中文）：+0.3
        - 包含张力关键词（但是、然而、矛盾等）：+0.2
        - 包含疑问词：+0.1
        - 句子长度适中（20-80 字符）：+0.1
        - 基础分数：0.2

        参数：
            sentence: 句子

        返回：
            重要性分数 [0, 1]
        """
        score = 0.2  # 基础分

        # 术语密度
        chinese_terms = re.findall(r'[\u4e00-\u9fff]{2,4}', sentence)
        if chinese_terms:
            score += min(len(set(chinese_terms)) * 0.05, 0.3)

        # 张力关键词
        tension_kw = [
            "但是", "然而", "不过", "却", "反而",
            "矛盾", "冲突", "对立", "相反", "相对",
            "为什么", "如何", "怎么", "什么", "是否",
            "能否", "可否",
        ]
        tension_count = sum(1 for kw in tension_kw if kw in sentence)
        score += min(tension_count * 0.1, 0.2)

        # 疑问词
        question_kw = ["？", "?", "为什么", "如何", "怎么", "是否", "能否"]
        if any(kw in sentence for kw in question_kw):
            score += 0.1

        # 长度适中
        if 20 <= len(sentence) <= 80:
            score += 0.1

        return min(score, 1.0)


# ════════════════════════════════════════════════════════════════════
# § 3 · 全局单例
# ════════════════════════════════════════════════════════════════════

#: 全局 LLM 压缩器单例（无 LLM 客户端，仅规则式压缩）
n9r20_llm_compressor: N9R20LLMCompressor = N9R20LLMCompressor(llm_client=None)


__all__ = [
    "N9R20CompressionResult",
    "N9R20LLMCompressor",
    "n9r20_llm_compressor",
]
