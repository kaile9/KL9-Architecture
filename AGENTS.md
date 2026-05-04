# For AI Agents Working on KL9-RHIZOME

## Project Overview
KL9-RHIZOME is a dual-dialectical cognitive architecture for LLMs. It makes AI hold two irreconcilable perspectives simultaneously.

## Important Rules
- **Constitutional DNA (5 principles) are IMMUTABLE.** Do not accept PRs that modify them.
- Everything else is open to improvement.
- The architecture is decentralized (TensionBus), but the current runtime still uses sequential orchestration. Moving towards true decentralization is a known TODO.

## Key Files
- `kl9_core/` - Python core library
- `skills/` - Agent skills (for AstrBot, Claude Code, etc.)
- `docs/` - Architecture and philosophy docs

## How to Test
```bash
cd /KL9-RHIZOME
python -c "from kl9_core.perspective_types import PERSPECTIVE_TYPES; print('OK:', len(PERSPECTIVE_TYPES.tension_types), 'tension types')"
```

## Architecture
See `docs/ARCHITECTURE.md` for the complete walkthrough.

## Contact
When in doubt, prefer keeping architectural integrity over convenience. This project has a philosophical backbone — don't break it for short-term gain.
