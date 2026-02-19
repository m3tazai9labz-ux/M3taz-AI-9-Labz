# M3ta'z Kub3 — Master System Architecture

## Overview

M3ta'z A.I. 9 Labz is an enterprise-grade AI automation hub built on the **DOE Framework**:
- **D**irectives — SOPs in Markdown (what to do)
- **O**rchestration — AI agents + routing (how to decide)
- **E**xecution — Python scripts + integrations (how to do it)

All messages from any platform (Telegram, WhatsApp, Discord, Slack) flow through a central **M3taz Router** that classifies intent and dispatches to the right AI backend.

---

## Integrated AI Stack

| Tool | Role | Port | Docker Image |
|------|------|------|--------------|
| **OpenClaw** | Multi-platform AI agent daemon; skills engine; messaging router supplement | 8080 | `ghcr.io/openclaw/openclaw` |
| **Eigent AI** | Multi-agent workforce (Developer, Browser, Document, Multi-Modal agents) | 7070 | `ghcr.io/eigent-ai/eigent` |
| **Open WebUI** | Self-hosted chat UI; OpenAI-compatible API proxy | 3000 | `ghcr.io/open-webui/open-webui` |
| **Agent Zero** | General-purpose hierarchical agent; deep reasoning; code + terminal | 50001 | `agent0ai/agent-zero` |
| **AFFiNE** | All-in-one workspace; knowledge base; SOPs; wikis; whiteboards | 3010 | `ghcr.io/toeverything/affine` |
| **AnythingLLM** | RAG-powered document chat; workspace per business context; private ChatGPT | 3001 | `mintplexlabs/anythingllm` |
| **Ollama** | Local LLM inference (qwen3-coder, glm-4.7, gpt-oss); Claude Code local dev | 11434 | `ollama/ollama` |
| **M3taz Hub** | Central FastAPI hub + all platform bots | 8000 | (this repo) |
| **SurrealDB** | Unified multi-model database | 8001 | `surrealdb/surrealdb` |

---

## Business Contexts & AI Routing

Each business context gets a tailored AI stack:

### Eagle Eye Vision Labz (`eagle_eye`)
*AI Consulting | SaaS | Training | Marketing Automation*
- Complex tasks → **Eigent AI** (multi-agent workforce)
- Code & automation → **Agent Zero**
- Client-facing chat → **Open WebUI**
- SOPs & knowledge → **AFFiNE**

### Lotus Group (`lotus_group`)
*Business operations & team collaboration*
- Team queries → **Open WebUI**
- Business automation → **Eigent AI** (Document + Browser agents)
- Knowledge base → **AFFiNE**
- Platform: Slack primary, Telegram secondary

### Personal (`personal`)
*Personal assistant, research, bookmarks*
- Daily tasks → **OpenClaw** (personal agent)
- Research → **Eigent AI** (Browser agent)
- Memory → **Agent Zero** persistent memory
- Platform: Telegram + WhatsApp

### Family (`family`)
*Photos, memories, sharing*
- Simple content sharing → existing content hub
- Photo organization → Execution layer only
- Platform: WhatsApp primary, Telegram secondary

### Meta/MetaOS/Q3bi (`meta`)
*MetaOS and Q3bi platform development*
- Full stack → all AI tools
- Code → **Agent Zero** + **Eigent AI** (Developer agent)
- Docs → **AFFiNE**

---

## Message Flow Diagram

```
Incoming Message (any platform)
           │
           ▼
┌─────────────────────┐
│   Platform Adapter  │  (Telegram / WhatsApp / Discord / Slack)
└─────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│   M3taz Router      │  orchestration/router.py
│  ┌───────────────┐  │
│  │Intent Classify│  │  Claude API → intent + urgency + topic
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │Business Router│  │  chat_context → preferred AI stack
│  └───────────────┘  │
└─────────┬───────────┘
           │
    ┌──────┴──────────────────────────────┐
    │                                     │
    ▼                                     ▼
CONTENT_INGEST                       AI DISPATCH
(existing handlers)         ┌────────────┴──────────────┐
                            │                           │
                       SIMPLE CHAT              COMPLEX TASK
                       Open WebUI               Eigent AI
                            │                           │
                       DEEP REASON             KNOWLEDGE LOOKUP
                       Agent Zero                   AFFiNE
                            │
                       PLATFORM SKILL
                        OpenClaw
           │
           ▼
┌─────────────────────┐
│   Platform Adapter  │  Response sent back to originating platform
└─────────────────────┘
```

---

## Intent Types

| Intent | Description | Routed To |
|--------|-------------|-----------|
| `CHAT` | Conversational message, simple Q&A | Open WebUI |
| `TASK` | Multi-step autonomous task | Eigent AI |
| `RESEARCH` | Web search, data gathering | Eigent AI (Browser Agent) |
| `CODE` | Code generation, debugging, terminal | Eigent AI (Developer) + Agent Zero |
| `DEEP_REASONING` | Complex analysis, long-form reasoning | Agent Zero |
| `KNOWLEDGE` | SOP lookup, wiki search, docs | AFFiNE |
| `CONTENT_INGEST` | Photo, video, doc, link, voice | Existing ingest handlers |
| `AUTOMATION` | Scheduled or trigger-based task | OpenClaw skills |
| `DOCUMENT` | Create/edit docs, slides, reports | Eigent AI (Document Agent) + AFFiNE |

---

## Platform Adapters

| Platform | Library | Status |
|----------|---------|--------|
| Telegram | python-telegram-bot | ✅ Built |
| Discord | discord.py | ✅ Built |
| Slack | slack-bolt | ✅ Built |
| WhatsApp | twilio / requests (WhatsApp Cloud API) | ✅ Built |
| Signal | (OpenClaw skill) | Planned |
| Microsoft Teams | (OpenClaw skill) | Planned |

---

## Sync & Data Flow

All platforms share a single **SurrealDB** (or SQLite for local dev) database:
- Every message, task, and result is logged
- Memory is shared across platforms — context from Slack is accessible on Telegram
- AFFiNE serves as the long-form knowledge layer (wiki, SOPs, whiteboards)
- Agent Zero persistent memory augments per-user context

---

## Security Notes

- All AI services run inside Docker with no public exposure by default
- Agent Zero runs sandboxed inside its Docker container
- WhatsApp uses official Cloud API (no scraping)
- OpenClaw is susceptible to prompt injection — user allowlists are enforced
- Secrets managed via `.env` (never committed)
