# KL9-RHIZOME

> **A cognitive protocol layer on top of LLMs**

Enables AI to hold two irreconcilable perspectives from the very start — no synthesis, no third way.

[中文](README.md)

---

## 📖 Origin

> *// TODO: Write your story here*

---

## 🔍 TL;DR

**KL9-RHIZOME is not an AI framework — it's a cognitive protocol.** It defines how AI holds dual perspectives, manages tension, and refuses cheap reconciliation.

---

## 🎯 Comparison

| | Traditional AI | KL9-RHIZOME |
|:---|:---|:---|
| User asks | "Which is more valid — X or Y?" | Same question |
| AI answers | "Both have merits, balance is key" ❌ Synthesis | The premise of X is negated by Y's premise — they don't speak from the same ground |
| Reader feels | Balanced, safe, uninspired | **Torn, unsettled, thinking** |

**Core conviction:** Every question worth answering deeply contains an irreconcilable tension. The AI's job is not to dissolve it — but to let it speak fully.

---

## 🧠 Core Concepts

### 1. DualState
Load two equal, irreconcilable perspectives before reasoning begins — not "stand on A then reflect on B," but hold both simultaneously.

### 2. TensionBus
A decentralized event bus. No central orchestrator — any module subscribes to what it cares about.

### 3. dual_fold
Operates from both perspectives simultaneously; each fold identifies structural tension and evaluates whether genuine suspension has been reached.

### 4. Suspension
**Suspension ≠ resolution.** After tension is fully expressed, it stays as tension — not synthesized into "higher unity."

### 5. Constitutional DNA
Five immutable principles: Dual Existence · Tension Suspension · Conceptual Dialogue · Structural Affect · Refusal of Closure. Rule-based audit engine, zero LLM cost.

---

## 🏗 Architecture

### Nine Modules

| Module | Role |
|:---|:---|
| **kailejiu-core** | Cognitive initialization: DualState loading, DNA declaration |
| **kailejiu-reasoner** | Perspective A: theoretical reasoning |
| **kailejiu-soul** | Perspective B: embodied growth engine |
| **kailejiu-graph** | Concept knowledge graph (6 tension types × 7 dualities) |
| **kailejiu-research** | Dialogical theory activation (conversation with thinkers) |
| **kailejiu-memory** | Persistent memory (SQLite, all active, no archival gate) |
| **kailejiu-learner** | Iterative dual learning (post-hoc optimization) |
| **kailejiu-orchestrator** | 6-phase cognitive workflow coordinator |
| **kailejiu-shared** | Shared infrastructure (11 modules, ~2843 lines) |

### Tension Type System

6 predefined tension types, each mapping to an irreconcilable dual perspective:

```
eternal_vs_finite     ← temporal.human  ↔  temporal.elf
mediated_vs_real      ← existential.immediate  ↔  existential.mediated
regression_vs_growth  ← social.regression  ↔  social.growth
freedom_vs_security   ← political.freedom_focused  ↔  political.security_focused
economic_vs_grotesque ← economic_grotesque.economic  ↔  economic_grotesque.grotesque
truth_vs_slander      ← truth_construction.truth  ↔  truth_construction.slander
```

### Event System （TensionBus）

| Event | Trigger |
|:---|:---|
| `QueryEvent` | User query received |
| `PerspectiveEvent` | DualState loaded |
| `FoldEvent` | Each recursive fold completed |
| `SuspensionEvent` | Suspension evaluation done |
| `FoldCompleteEvent` | Full pipeline finished |

### 6-Phase Pipeline

```
Phase 0: Detect dual nature
Phase 1: Retrieve concepts
Phase 2: Activate dialogues
Phase 3: Recursive folding (dual_fold)
Phase 4: Emergent style
Phase 5: Generate response
Phase 6: Emit completion event
```

---

## 🚀 Quick Start

### As an Agent Skill

```bash
cp -r skills/kailejiu-core ~/.agents/skills/
# Then tell your AI: "Activate kailejiu-core"
```

### As a Python Library

```python
from kl9_core.perspective_types import PERSPECTIVE_TYPES, TENSION_TYPES
from kl9_core.tension_bus import TensionBus
from kl9_core.dual_fold import dual_fold

# List available dualities
for pair in PERSPECTIVE_TYPES.recommended_dualities:
    print(f"{pair['perspective_A']} ↔ {pair['perspective_B']}")

# Subscribe to events
bus = TensionBus()
bus.subscribe("QueryEvent", lambda e: print(f"Received: {e['data']}"))
```

### Quick Test

```bash
cd tests && python test_basic.py
```

---

## 📚 Further Reading

| Doc | Description |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full architecture walkthrough |
| [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) | Philosophical foundations |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | Concept glossary |
| [skills/kailejiu-core/SKILL.md](skills/kailejiu-core/SKILL.md) | Core skill documentation (751 lines) |

---

## 📦 Statistics

| Category | Count |
|:---|:---:|
| Python modules | 13 |
| Skills | 9 |
| Total code lines | ~8,692 |
| Tension types | 6 |
| Recommended dualities | 7 |
| Emergent styles | 4 |

---

## 🤝 Contributing

No coding skills required: use & feedback / doc translation / tests / bug reports / ideas.

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📜 License

MIT
