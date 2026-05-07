"""
9R-2.0 RHIZOME · User Configuration
────────────────────────────────────
用户自定义配置 — prompt 模板 / 偏好设置 / 持久化加载。

设计原则：
    1. N9R20UserConfig: 用户可自定义的 prompt 模板集合
    2. N9R20UserConfigLoader: JSON 文件加载/保存，支持默认回退
    3. 模板变量使用 {placeholder} 格式，与 LLM 压缩器一致
    4. 所有字段有合理默认值，用户配置为可选层

使用示例：
    >>> config = N9R20UserConfig()
    >>> config.set_prompt("compression", "请将以下文本压缩到 {target_ratio}x: {text}")
    >>> loader = N9R20UserConfigLoader()
    >>> loader.save(config, "user_config.json")
    >>> restored = loader.load("user_config.json")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# ════════════════════════════════════════════════════════════════════
# § 1 · N9R20UserConfig — 用户自定义配置
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20UserConfig:
    """
    用户自定义配置数据类。

    包含四类 prompt 模板：
    - compression_prompt: 语义压缩提示词
    - routing_prompt: 路由决策提示词（LLM 路由模式用）
    - validation_prompt: 语义验证提示词
    - tension_prompt: 张力检测提示词

    以及用户偏好：
    - preferred_fold_depth: 偏好 fold 深度（覆盖自动分配）
    - preferred_compression_ratio: 偏好压缩率
    - language: 界面语言偏好 ('zh' | 'en')
    - custom_keywords: 用户自定义专用关键词（扩充路由器关键词表）

    所有字段均有合理默认值。
    """

    # ── Prompt 模板 ───────────────────────────────────────────

    compression_prompt: str = (
        "你是一位认知压缩专家。请将以下文本进行语义压缩，"
        "保留核心概念和关键逻辑关系，去除修饰性语言和冗余信息。\n\n"
        "原始文本:\n{text}\n\n"
        "目标压缩率: {target_ratio}x\n"
        "保留关键概念: {concepts}\n\n"
        "请输出压缩后的文本（仅输出压缩文本，不要添加解释）："
    )
    """语义压缩 prompt 模板。变量: {text}, {target_ratio}, {concepts}"""

    routing_prompt: str = (
        "你是 9R-2.0 路由决策系统。请评估以下查询的认知复杂度。\n\n"
        "查询: {query}\n\n"
        "评估维度：\n"
        "1. 概念复杂度 (0-1)\n"
        "2. 张力强度 (0-1)\n"
        "3. 认知负载 (0-1)\n"
        "4. 是否为专用文本 (true/false)\n\n"
        "输出 JSON: {{\"difficulty\": float, \"is_specialized\": bool, "
        "\"fold_depth\": int, \"compression_target\": float}}"
    )
    """路由决策 prompt 模板。变量: {query}"""

    validation_prompt: str = (
        "你是一位语义质量评估专家。请评估压缩后的文本是否保留了原文的核心语义。\n\n"
        "原始文本: {original}\n"
        "压缩文本: {compressed}\n\n"
        "请评估语义保留率 (0-1)，并指出丢失的关键概念（如果有）：\n"
        "JSON: {{\"retention\": float, \"lost_concepts\": [str], \"assessment\": str}}"
    )
    """语义验证 prompt 模板。变量: {original}, {compressed}"""

    tension_prompt: str = (
        "你是一位认知张力分析师。请识别以下文本中的结构性张力。\n\n"
        "文本: {text}\n\n"
        "识别对立概念、矛盾关系、不可调和的视角差异：\n"
        "JSON: {{\"has_tension\": bool, \"tension_type\": str, "
        "\"perspective_a\": str, \"perspective_b\": str, \"intensity\": float}}"
    )
    """张力检测 prompt 模板。变量: {text}"""

    # ── 用户偏好 ──────────────────────────────────────────────

    preferred_fold_depth: Optional[int] = None
    """
    偏好 fold 深度（2-9）。
    设置后会覆盖路由器的自动分配。
    None = 使用自动分配。
    """

    preferred_compression_ratio: Optional[float] = None
    """
    偏好压缩率（2.0-2.5）。
    设置后会覆盖路由器的自动计算。
    None = 使用自动计算。
    """

    language: str = "zh"
    """界面语言偏好: 'zh' (中文) | 'en' (英文)"""

    custom_keywords: list = field(default_factory=list)
    """
    用户自定义专用关键词列表。
    这些词会被追加到路由器的 specialized_keywords 中。
    """

    custom_tension_keywords: list = field(default_factory=list)
    """
    用户自定义张力关键词列表。
    这些词会被追加到张力检测关键词中。
    """

    # ── 元数据 ────────────────────────────────────────────────

    version: str = "9R-2.0"
    """配置版本号"""

    description: str = ""
    """用户配置描述/备注"""

    # ── 公共方法 ──────────────────────────────────────────────

    def set_prompt(self, prompt_type: str, template: str) -> None:
        """
        设置指定类型的 prompt 模板。

        参数：
            prompt_type: 模板类型 ('compression' | 'routing' | 'validation' | 'tension')
            template: 模板字符串

        异常：
            ValueError: 如果 prompt_type 无效
        """
        field_map: Dict[str, str] = {
            "compression": "compression_prompt",
            "routing": "routing_prompt",
            "validation": "validation_prompt",
            "tension": "tension_prompt",
        }

        field_name = field_map.get(prompt_type)
        if field_name is None:
            raise ValueError(
                f"Unknown prompt_type: '{prompt_type}'. "
                f"Valid: {list(field_map.keys())}"
            )
        setattr(self, field_name, template)

    def get_prompt(self, prompt_type: str) -> str:
        """
        获取指定类型的 prompt 模板。

        参数：
            prompt_type: 模板类型

        返回：
            模板字符串

        异常：
            ValueError: 如果 prompt_type 无效
        """
        field_map: Dict[str, str] = {
            "compression": "compression_prompt",
            "routing": "routing_prompt",
            "validation": "validation_prompt",
            "tension": "tension_prompt",
        }

        field_name = field_map.get(prompt_type)
        if field_name is None:
            raise ValueError(
                f"Unknown prompt_type: '{prompt_type}'. "
                f"Valid: {list(field_map.keys())}"
            )
        return getattr(self, field_name)

    def add_keywords(self, keywords: list) -> None:
        """
        追加自定义专用关键词。

        参数：
            keywords: 关键词列表
        """
        for kw in keywords:
            if kw not in self.custom_keywords:
                self.custom_keywords.append(kw)

    def add_tension_keywords(self, keywords: list) -> None:
        """
        追加自定义张力关键词。

        参数：
            keywords: 关键词列表
        """
        for kw in keywords:
            if kw not in self.custom_tension_keywords:
                self.custom_tension_keywords.append(kw)

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典。

        返回：
            配置字典
        """
        return {
            "version": self.version,
            "description": self.description,
            "language": self.language,
            "preferred_fold_depth": self.preferred_fold_depth,
            "preferred_compression_ratio": self.preferred_compression_ratio,
            "custom_keywords": list(self.custom_keywords),
            "custom_tension_keywords": list(self.custom_tension_keywords),
            "prompts": {
                "compression": self.compression_prompt,
                "routing": self.routing_prompt,
                "validation": self.validation_prompt,
                "tension": self.tension_prompt,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "N9R20UserConfig":
        """
        从字典反序列化。

        参数：
            data: 配置字典

        返回：
            N9R20UserConfig 实例
        """
        prompts = data.get("prompts", {})
        return cls(
            version=data.get("version", "9R-2.0"),
            description=data.get("description", ""),
            language=data.get("language", "zh"),
            preferred_fold_depth=data.get("preferred_fold_depth"),
            preferred_compression_ratio=data.get("preferred_compression_ratio"),
            custom_keywords=data.get("custom_keywords", []),
            custom_tension_keywords=data.get("custom_tension_keywords", []),
            compression_prompt=prompts.get("compression", cls.compression_prompt),
            routing_prompt=prompts.get("routing", cls.routing_prompt),
            validation_prompt=prompts.get("validation", cls.validation_prompt),
            tension_prompt=prompts.get("tension", cls.tension_prompt),
        )


# ════════════════════════════════════════════════════════════════════
# § 2 · N9R20UserConfigLoader — 加载/保存用户配置
# ════════════════════════════════════════════════════════════════════


class N9R20UserConfigLoader:
    """
    用户配置加载器。

    功能：
    - load(): 从 JSON 文件加载配置（文件不存在时返回默认配置）
    - save(): 将配置保存到 JSON 文件
    - default_config(): 获取默认配置实例
    - merge(): 合并两个配置（用户配置优先）

    线程安全：本类为无状态工具类，所有方法均为静态方法。
    """

    @staticmethod
    def load(filepath: str) -> N9R20UserConfig:
        """
        从 JSON 文件加载用户配置。

        文件不存在时返回默认配置（不抛异常）。

        参数：
            filepath: JSON 文件路径

        返回：
            N9R20UserConfig 实例
        """
        if not os.path.exists(filepath):
            return N9R20UserConfigLoader.default_config()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
            return N9R20UserConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # 文件损坏或格式错误 → 返回默认配置
            return N9R20UserConfigLoader.default_config()

    @staticmethod
    def save(config: N9R20UserConfig, filepath: str) -> None:
        """
        将用户配置保存到 JSON 文件。

        参数：
            config: 用户配置实例
            filepath: 目标 JSON 文件路径
        """
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        data = config.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def default_config() -> N9R20UserConfig:
        """
        获取默认配置实例。

        返回：
            使用所有默认值的 N9R20UserConfig
        """
        return N9R20UserConfig()

    @staticmethod
    def merge(
        base: N9R20UserConfig,
        override: N9R20UserConfig,
    ) -> N9R20UserConfig:
        """
        合并两个配置：override 中的非默认值覆盖 base。

        策略：
        - None 值视为「未设置」，不覆盖
        - 空列表视为「未设置」，不覆盖
        - 其他值直接覆盖

        参数：
            base: 基础配置
            override: 覆盖配置（用户自定义，优先级高）

        返回：
            合并后的新 N9R20UserConfig
        """
        merged = N9R20UserConfig()

        # 从 base 复制所有字段
        merged.version = override.version or base.version
        merged.description = override.description or base.description
        merged.language = override.language or base.language

        # preferred 字段：None = 不覆盖
        merged.preferred_fold_depth = (
            override.preferred_fold_depth
            if override.preferred_fold_depth is not None
            else base.preferred_fold_depth
        )
        merged.preferred_compression_ratio = (
            override.preferred_compression_ratio
            if override.preferred_compression_ratio is not None
            else base.preferred_compression_ratio
        )

        # 关键词：合并去重
        merged.custom_keywords = list(
            dict.fromkeys(base.custom_keywords + override.custom_keywords)
        )
        merged.custom_tension_keywords = list(
            dict.fromkeys(
                base.custom_tension_keywords + override.custom_tension_keywords
            )
        )

        # Prompt 模板：override 的默认值等于类默认值 → 不覆盖
        default = N9R20UserConfig()
        for prompt_type in ("compression", "routing", "validation", "tension"):
            override_val = getattr(override, f"{prompt_type}_prompt")
            default_val = getattr(default, f"{prompt_type}_prompt")
            base_val = getattr(base, f"{prompt_type}_prompt")

            # 如果 override 的值与默认值相同但 base 不同，使用 base
            if override_val == default_val and base_val != default_val:
                setattr(merged, f"{prompt_type}_prompt", base_val)
            else:
                setattr(merged, f"{prompt_type}_prompt", override_val)

        return merged


# ════════════════════════════════════════════════════════════════════
# § 3 · 全局单例
# ════════════════════════════════════════════════════════════════════

#: 全局用户配置单例（默认配置）
n9r20_user_config: N9R20UserConfig = N9R20UserConfig()

#: 全局用户配置加载器单例
n9r20_user_config_loader: N9R20UserConfigLoader = N9R20UserConfigLoader()


__all__ = [
    "N9R20UserConfig",
    "N9R20UserConfigLoader",
    "n9r20_user_config",
    "n9r20_user_config_loader",
]
