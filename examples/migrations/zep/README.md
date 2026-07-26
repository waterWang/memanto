# Zep → Memanto Migration Showcase

This showcase demonstrates the **full freedom loop**: take your agent memories from **Zep Cloud**, migrate them into **Memanto**, and export them as portable **OKF (Open Knowledge Format)**.

## Why Zep?

[Zep](https://www.getzep.com/) is an enterprise-grade memory layer for AI agents. It stores conversational threads, messages, summaries, and extracted facts in a temporal knowledge graph. If you've been using Zep to persist your agent's long-term memory, this migration lets you:

- **Own your memory** — break free from Zep's vendor lock-in
- **Port to OKF** — export as plain, git-friendly markdown bundles
- **Compare performance** — see how Memanto's retrieval quality stacks up
- **Use any Memanto frontend** — Claude Code, LangGraph, CrewAI, MCP, or Hermes

## The Freedom Loop

```
Zep Cloud → memanto migrate zep → Memanto agent → memanto memory export --okf → OKF bundle
```

### Step 1: Export from Zep

```bash
# Export all Zep threads, messages, and summaries
memanto migrate zep --dry-run

# Preview the mapping without writing to your agent
```

This will prompt for your Zep Cloud API key (saved to `~/.memanto/.env`).

### Step 2: Migrate to Memanto

```bash
# Actually migrate
memanto migrate zep --agent my-agent

# Or use a saved export file
memanto migrate zep --file ./zep_export.json --agent my-agent
```

### Step 3: Export as OKF

```bash
# Prove the freedom loop — export as portable OKF
memanto memory export --okf
```

## What Gets Mapped

| Zep Entity | Memanto Type | Description |
|-----------|-------------|-------------|
| Thread message | `observation` | Each message becomes a tagged observation with role prefix (`[User]:`, `[Assistant]:`) |
| Thread summary | `summary` | Conversation summaries with confidence 0.9 |
| User ID → tag | `user=<id>` | Tagged on every memory from that user |
| Thread ID → tag | `thread=<id>` | Tagged on every memory from that thread |

All Zep metadata (role, name, project UUID) is preserved in the `[Supporting data]` footer of each memory.

## Example Data Flow

```python
# A Zep thread with 3 messages:
#   "What's the capital of France?" (user)
#   "The capital of France is Paris." (assistant)
#   "Thanks! What about Italy?" (user)

# Becomes 3 Memanto memories:
#   [Observation] [User]: What's the capital of France?
#   [Observation] [Assistant]: The capital of France is Paris.
#   [Observation] [User]: Thanks! What about Italy?

# Thread summary (if available):
#   [Summary] User asked about European capitals. Assistant provided answers.
```

## Requirements

- Zep Cloud API key (get one at https://app.getzep.com)
- Memanto agent (run `memanto agent activate <id>`)
- Python 3.11+

## Files

| File | Purpose |
|------|---------|
| `memanto/cli/analyze/zep_export.py` | Zep Cloud API export script |
| `memanto/cli/analyze/zep_compare.py` | Migration metrics and report |
| `memanto/cli/migrate/mappers.py` | `map_zep()` mapper function |
| `memanto/cli/commands/migrate.py` | `memanto migrate zep` CLI command |
| `memanto/cli/config/manager.py` | Zep API key storage |