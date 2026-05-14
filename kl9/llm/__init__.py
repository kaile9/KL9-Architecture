# DEPRECATED: These standalone providers are not used by the main pipeline.
# The plugin uses AstrBotLLM adapter wrapping the user's configured provider.
# Preserved for direct use by advanced users or future standalone mode.

from .deepseek import DeepSeekV4Provider
from .kimi import KimiProvider, KIMI_OPTIMIZED_SYSTEM_APPENDIX
from .opus import Opus47Provider, OPUS47_PROMPT_RULES
