<p align="center">
  <h1 align="center">KL9-RHIZOME</h1>
  <h3 align="center">A dual-dialectical cognitive architecture that holds two irreconcilable perspectives from the very start</h3>
  <h4 align="center">No synthesis. No third way. Just tension, fully expressed.</h4>
</p>

<p align="center">
  <a href="README.md">中文</a> · English
</p>

---

## 🧬 Origin Story

> *A late-night thoughts project from a graduate-school exam candidate, turned into actual code.*

In the fall of 2025, I was preparing for China's graduate-school entrance exam (the *kaoyan*) in sociology. My days were simple: math in the morning, English in the afternoon,专业课 (specialized courses) at night. But after those late-night study sessions — reading Foucault on discipline, Deleuze on the rhizome, Baudrillard on simulacra — I couldn't sleep.

Not because of anxiety. Because these thinkers were at war in my head.

Foucault says power is everywhere. Deleuze says difference is what's real. Baudrillard says the real is dead. None of them is *wrong* — but none of them can convince the others. And every day, the AI I was using gave me the same answer: "Both sides have their merits. A balanced approach is recommended."

**That's not thinking. That's compromise disguised as wisdom.**

So I started an "off-topic" project: Can we make an AI that doesn't just "see both sides" (stand on one side then pretend to stand on the other), but genuinely holds two irreconcilable perspectives from the very beginning — and **refuses to synthesize them**?

KL9-RHIZOME grew out of that question. It's not an academic project. It's a late-night obsession that got taken seriously.

---

## 🔍 TL;DR

**KL9-RHIZOME is a cognitive operating system that runs on top of LLMs.** It's not another AI framework — it's a protocol. It defines how an AI should hold dual perspectives, manage structural tension, and refuse cheap reconciliation.

It doesn't teach AI *what to do*. It teaches AI *how to exist*.

---

## 🎯 Without KL9 vs With KL9

| | Traditional AI | With KL9-RHIZOME |
|---|---|---|
| **User asks** | "Which is more valid — liberalism or communitarianism?" | Same question |
| **AI answers** | "Both have merits... they can complement each other... balance is key" | ❌ **Synthesis** |
| **KL9 answers** | — | "Liberalism's premise (the individual precedes society) is directly negated by communitarianism's premise (society precedes the individual). These premises cannot be reconciled — not because one is right and the other wrong, but because they don't speak from the same ground." |
| **Reader feels** | Balanced, safe, uninspired | **Torn, unsettled, but thinking** |

**Core conviction:** Every question worth answering deeply contains an irreconcilable tension. The AI's job is not to dissolve it — it's to let it speak fully.

---

## 🚀 Quick Start

### As an Agent Skill (AstrBot / Claude Code / Cursor)

```bash
# Three steps:
cp -r skills/kailejiu-core ~/.agents/skills/
# Then tell your AI: "Activate kailejiu-core skill"
# Then ask a hard question
```

### As a Python Library

```python
from kl9_core import dialogical_activation

state = dialogical_activation("Does AI have consciousness?")
# → DualState loaded: scientific perspective vs phenomenological perspective
```

### Minimal Example (30 seconds)

```python
from kl9_core.perspective_types import PERSPECTIVE_TYPES

for pair in PERSPECTIVE_TYPES.recommended_dualities:
    print(f"  {pair['perspective_A']}  ↔  {pair['perspective_B']}")
    print(f"  Tension: {pair['tension']}")
```

---

## 🧠 Core Concepts (Just 3)

### 1. DualState
Load two equal, irreconcilable perspectives before reasoning begins. Not "stand on A then reflect on B" — hold both simultaneously.

### 2. TensionBus
Modules talk through an event bus. Decentralized — no central orchestrator needed.

### 3. Suspension
**Suspension ≠ resolution.** Tension stays as tension after being fully expressed. The reader should feel torn, not balanced.

---

## 📦 Modules

| Module | Purpose | Lines |
|:---|:---|:---:|
| **kailejiu-core** | Cognitive initialization — DualState loading, Constitutional DNA | 751 |
| **kailejiu-reasoner** | Perspective A — theoretical reasoning operations | 641 |
| **kailejiu-soul** | Perspective B — embodied growth engine | 64+426 |
| **kailejiu-graph** | Concept knowledge graph | 370 |
| **kailejiu-research** | Dialogical theory activation | 511 |
| **kailejiu-memory** | Persistent memory layer | 400 |
| **kailejiu-learner** | Iterative dual learning | 573 |
| **kailejiu-orchestrator** | 6-phase cognitive coordinator | 1114 |
| **kailejiu-shared** | Shared infrastructure (11 modules, 2843 lines) | 173 |

---

## 🏗 Architecture

```
                    ┌──────────────────────────┐
                    │       TensionBus          │
                    │   (Decentralized Event Bus)│
                    └──────┬──────┬──────┬──────┘
                           │      │      │
              ┌────────────┘      │      └────────────┐
              ▼                   ▼                   ▼
      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
      │  kailejiu-   │   │  kailejiu-   │   │  kailejiu-   │
      │   reasoner   │   │    soul      │   │    graph     │
      │ (Perspective │   │ (Perspective │   │ (Knowledge   │
      │   A Theory)  │   │   B Body)    │   │   Graph)     │
      └──────────────┘   └──────────────┘   └──────────────┘
              │                                      │
              └──────────────┬──────────────┬────────┘
                             ▼              ▼
                     ┌────────────┐  ┌────────────┐
                     │ kailejiu-  │  │ kailejiu-  │
                     │  memory    │  │  learner   │
                     └────────────┘  └────────────┘
```

**Design principles:**
- **Decentralized:** No central brain — modules talk through TensionBus
- **Any entry point:** Any module can be the activation entry
- **Resilient:** Cut any node, the rest keep working
- **Dual from the start:** Two irreconcilable perspectives coexist from the first moment

---

## 📚 Further Reading

| Doc | Description |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full architecture walkthrough |
| [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) | Philosophical foundations — Constitutional DNA |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | Concept glossary |
| [docs/CONSTITUTIONAL_DNA.md](docs/CONSTITUTIONAL_DNA.md) | The 5 immutable principles |
| [examples/astrbot.md](examples/astrbot.md) | Deploy in AstrBot |
| [examples/claude-code.md](examples/claude-code.md) | Deploy in Claude Code |

---

## 🤝 Contributing

**You don't need to write code to contribute.**

| You can | How |
|:---|:---|
| 💬 **Use & report** | Ask KL9 a question, share your experience |
| 📝 **Write docs** | Translate, simplify, expand |
| 🧪 **Write tests** | Help us catch regressions |
| 🐛 **Report bugs** | Open an issue |
| 💡 **Suggest ideas** | How can DualState be better? |
| 🌐 **Translate** | Help translate to other languages |

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📜 License

MIT

---

<p align="center">
  <i>Started from a late-night exam prep session.</i><br>
  <i>You are not looking for answers —<br>you are learning to hold questions better.</i>
</p>
