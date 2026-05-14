"""
9R-2.1 — Platform Adapters

kl9 core is platform-agnostic. It only needs an LLMProvider implementation.
Each platform contributes a thin adapter that bridges its native LLM system into kl9.

┌─────────────────────────────────────────────────────────┐
│                   kl9 core (platform-agnostic)            │
│  models · dna · router · fold · gate · validator · agg   │
│  Only dependency: LLMProvider (abstract)                  │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  AstrBot       │  │  OpenClaw     │  │  Hermas       │
│  adapter       │  │  adapter      │  │  adapter      │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ Star plugin    │  │ MCP tool      │  │ Agent tool    │
│ provider mgr   │  │ registration  │  │ registration  │
│ _conf_schema   │  │ openclaw.yaml │  │ hermas.yaml   │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
  /deep /standard   @kl9_deep()      KL9.fold()
  /quick /kl9       tool call        tool call

Union:
┌───────────────┐
│  Pi / Script   │
│  standalone    │
├───────────────┤
│ pip install    │
│ from kl9 import│
└───────────────┘
"""

# Each adapter follows this minimal contract:
#   class PlatformAdapter:
#       def get_llm(self, task: str) -> LLMProvider: ...
#       def register_commands(self) -> None: ...

# The kl9 core never imports platform code.
# Platforms import kl9 and wrap it.
