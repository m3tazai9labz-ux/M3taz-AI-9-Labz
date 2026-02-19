# M3ta'z A.I. 9 Labz

**AI Consulting | SaaS | Training | Marketing Automation**

Enterprise-grade AI automation hub for Eagle Eye Vision Labz and Lotus Group.
Built on the **M3ta'z Kub3 DOE Framework** — Directives → Orchestration → Execution.

---

## AI Stack

| Tool | Role | Port |
|------|------|------|
| **OpenClaw** | Multi-platform AI agent daemon + skills engine | 8080 |
| **Eigent AI** | Multi-agent workforce (Developer, Browser, Document, Multi-Modal) | 7070 |
| **Open WebUI** | Self-hosted chat UI + OpenAI-compatible API proxy | 3000 |
| **Agent Zero** | Hierarchical agent — deep reasoning, code, persistent memory | 50001 |
| **AFFiNE** | All-in-one workspace — docs, wikis, whiteboards, databases | 3010 |
| **Ollama** | Local LLM inference — privacy-first, no cloud required | 11434 |
| **M3taz Hub** | Central router — all bots + web dashboard + WhatsApp webhook | 8000 |

## Messaging Platforms

| Platform | Status | Context Routing |
|----------|--------|-----------------|
| Telegram | ✅ Active | personal, lotus_group, family, meta |
| WhatsApp | ✅ Built | personal, family (via Meta Cloud API) |
| Discord | ✅ Built | channel name → business context |
| Slack | ✅ Built | channel name → business context + Socket Mode |
| Signal / Teams / iMessage | Planned | via OpenClaw skills |

## Business Contexts

| Context | Business | Primary AI Stack |
|---------|----------|-----------------|
| `eagle_eye` | Eagle Eye Vision Labz | Eigent AI + Agent Zero + Open WebUI |
| `lotus_group` | Lotus Group | Open WebUI + Eigent AI |
| `meta` | MetaOS / Q3bi | Agent Zero + Eigent AI |
| `personal` | Personal | OpenClaw + Open WebUI |
| `family` | Family | Open WebUI |

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — add bot tokens and API keys

# 2. Start everything
docker-compose up -d

# 3. Or run locally (minimal setup — just Telegram + web dashboard)
pip install -r requirements.txt
python main.py
```

## Claude Code + Ollama (Local Models)

Run Claude Code using local models via Ollama:

```bash
# Option 1: one-command setup
ollama launch claude

# Option 2: manual setup
export ANTHROPIC_AUTH_TOKEN=ollama
export ANTHROPIC_API_KEY=""
export ANTHROPIC_BASE_URL=http://localhost:11434
claude --model qwen3-coder
```

Recommended models: `qwen3-coder`, `glm-4.7`, `gpt-oss:20b`, `gpt-oss:120b`

## Project Structure

```
main.py                   All bots + web app entry point
config.py                 Central configuration
requirements.txt          Python dependencies
docker-compose.yml        Full stack (all services)

telegram_bot/             Telegram bot (handlers, content ingestion)
discord_bot/              Discord bot (slash commands + mentions)
slack_bot/                Slack bot (Socket Mode + /m3taz command)
whatsapp/                 WhatsApp webhook (Meta Cloud API)
webapp/                   FastAPI web dashboard + WhatsApp endpoint

orchestration/
  router.py               Central message router
  intent_classifier.py    Claude-powered intent classification
  business_router.py      Context-aware AI backend selection

integrations/
  open_webui.py           Open WebUI client
  eigent.py               Eigent AI client (multi-agent workforce)
  agent_zero.py           Agent Zero client (hierarchical agent)
  affine.py               AFFiNE client (knowledge base)
  openclaw.py             OpenClaw client (skills engine)
  ollama.py               Ollama client (local LLM inference)

database/                 SQLAlchemy models and async engine
directives/               SOPs and architecture docs
execution/
  openclaw_skills/        Custom OpenClaw skill definitions
media_store/              Uploaded files (gitignored)
```

## Documentation

- [`directives/architecture.md`](directives/architecture.md) — Full system architecture + message flow
- [`directives/integrations_sop.md`](directives/integrations_sop.md) — Setup SOPs for each tool
- [`directives/telegram_hub_sop.md`](directives/telegram_hub_sop.md) — Telegram content hub SOP
