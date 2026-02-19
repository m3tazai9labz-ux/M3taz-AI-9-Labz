# SOP: AI Tool Integrations

## Purpose
Standard operating procedures for each integrated AI tool and messaging platform.

---

## 1. OpenClaw — Multi-Platform AI Agent

**What it does:** Personal AI agent daemon that runs 24/7, connects to 12+ messaging platforms, executes skills, and maintains long-term memory as Markdown files.

**Our usage:**
- Acts as a supplement for platforms not natively supported by our hub
- Hosts custom M3taz skills (callable from any platform)
- Provides fallback routing for automation tasks

**Setup:**
1. Copy `.env.example` values for `OPENCLAW_API_URL` and `OPENCLAW_API_KEY`
2. Deploy via `docker-compose up openclaw`
3. Register custom skills in `execution/openclaw_skills/`
4. OpenClaw will auto-discover skills via ClawHub or local skill directory

**Custom Skills Location:** `execution/openclaw_skills/*.skill.md`

---

## 2. Eigent AI — Multi-Agent Workforce

**What it does:** Deploys specialized AI agents in parallel — Developer, Browser, Document, and Multi-Modal agents — coordinated by CAMEL-AI framework.

**Our usage:**
- Complex multi-step tasks (research + write + format a report)
- Web scraping + data extraction at scale
- Automated document creation for clients (Eagle Eye)
- Parallel task execution for Lotus Group

**Setup:**
1. Set `EIGENT_API_URL` (default: `http://eigent:7070`)
2. Set `EIGENT_API_KEY` in `.env`
3. Deploy: `docker-compose up eigent`
4. Tasks sent via `integrations/eigent.py` → `EigentClient.run_task()`

**Agent Types:**
- `developer` — code writing, terminal commands
- `browser` — web search, form filling, data extraction
- `document` — PDF/Word/slide creation
- `multimodal` — image, audio, video processing

---

## 3. Open WebUI — Chat Interface & API Proxy

**What it does:** Self-hosted UI for chat models. Provides an OpenAI-compatible API that proxies to any backend (Ollama, Anthropic, OpenAI).

**Our usage:**
- Primary interface for simple conversational queries
- Used by Eagle Eye clients as white-labeled chat interface
- API endpoint for `CHAT` intent routing

**Setup:**
1. Set `OPEN_WEBUI_URL` (default: `http://open-webui:3000`)
2. Set `OPEN_WEBUI_API_KEY` in `.env`
3. Deploy: `docker-compose up open-webui`
4. Configure models in Open WebUI admin panel

**API:** OpenAI-compatible at `http://open-webui:3000/api`

---

## 4. Agent Zero — Hierarchical AI Agent

**What it does:** General-purpose agentic framework. Spawns hierarchical sub-agents, writes and executes code, uses persistent memory, supports MCP + A2A protocols.

**Our usage:**
- Deep reasoning tasks requiring multi-step planning
- Code execution (runs sandboxed in Docker)
- Persistent user memory across sessions
- MetaOS/Q3bi development tasks

**Setup:**
1. Set `AGENT_ZERO_URL` (default: `http://agent-zero:80`)
2. Deploy: `docker-compose up agent-zero`
3. Agent Zero is stateful — memory persists in `agent_zero_data/` volume

**API:** HTTP REST at `http://agent-zero:80`

---

## 5. AFFiNE — Knowledge Base & Workspace

**What it does:** All-in-one workspace combining docs, whiteboards, and databases. Our knowledge base for SOPs, research, client deliverables, and MetaOS documentation.

**Our usage:**
- Primary SOP/documentation system (lives alongside this repo's `directives/`)
- Client deliverables for Eagle Eye Vision Labz
- Lotus Group shared workspace and project tracking
- MetaOS/Q3bi architecture docs and whiteboards

**Setup:**
1. Set `AFFINE_URL` (default: `http://affine:3010`)
2. Deploy: `docker-compose up affine`
3. Create workspaces: Eagle Eye, Lotus Group, Personal, MetaOS

**API:** JSON-RPC at `http://affine:3010/api`

---

## 6. AnythingLLM — RAG Document Chat

**What it does:** All-in-one private ChatGPT with built-in RAG. Upload your business documents, SOPs, research, and client files — then chat with them directly. Workspace-per-context means Eagle Eye, Lotus Group, and MetaOS each have their own isolated document library.

**Our usage:**
- Primary `KNOWLEDGE` intent backend — chat with your uploaded business docs
- `RESEARCH` intent — search indexed documents before hitting the web
- Eagle Eye: client proposals, SOP docs, market research, training materials
- Lotus Group: meeting notes, contracts, business plans
- MetaOS/Q3bi: architecture docs, design specs, feature roadmaps
- Personal: saved articles, notes, web clippings

**Setup:**
1. Set `ANYTHINGLLM_URL` (default: `http://anythingllm:3001`)
2. Set `ANYTHINGLLM_API_KEY` in `.env` (generate in AnythingLLM UI → Settings → API Keys)
3. Deploy: `docker-compose up anythingllm`
4. Create workspaces in UI matching these slug names:
   - `eagle-eye-vision-labz`
   - `lotus-group`
   - `metaos-q3bi`
   - `personal`
   - `family`
5. Upload documents to each workspace (drag & drop in UI, or use `/api/v1/workspace/{slug}/upload`)

**API:**
- Chat: `POST /api/v1/workspace/{slug}/chat`
- Upload: `POST /api/v1/workspace/{slug}/upload/raw-text`
- Swagger docs: `http://anythingllm:3001/api/docs`

---

## 7. Messaging Platforms

### Telegram (✅ Active)
- Bot: M3taz Hub bot (@your_bot)
- Contexts: personal, lotus_group, family, meta
- All content types supported (photo, video, doc, voice, text, links)

### WhatsApp (✅ Built — needs credentials)
- Uses WhatsApp Cloud API (Meta developer account required)
- Webhook at `POST /webhooks/whatsapp`
- Set `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_VERIFY_TOKEN` in `.env`

### Discord (✅ Built — needs credentials)
- Bot with slash commands + message handling
- Set `DISCORD_BOT_TOKEN` in `.env`
- Invite bot with `bot` + `applications.commands` scopes

### Slack (✅ Built — needs credentials)
- Bolt framework (Socket Mode)
- Set `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET` in `.env`
- Enable Socket Mode in Slack App settings

---

## Content Flow (All Platforms)

```
1. Ingest    — Any message sent to any bot
2. Classify  — Intent + business context identified
3. Route     — Dispatched to correct AI backend
4. Execute   — AI processes and responds
5. Log       — Result stored in SurrealDB
6. Respond   — Answer sent back to originating platform
7. Sync      — Summary available on web dashboard
```

---

## 8. GoHighLevel (GHL) — CRM & Marketing Automation

**What it does:** Cloud-based all-in-one CRM and marketing platform. Eagle Eye and Lotus Group use it to manage leads, contacts, sales pipelines, SMS/email campaigns, and automations. Our hub receives real-time GHL webhook events and can query/update contacts and opportunities programmatically.

**Our usage:**
- `CRM` intent → GoHighLevel first (search contacts, view pipeline)
- Inbound SMS auto-reply (if `GHL_AUTO_REPLY_SMS=true`) — AI drafts and sends replies
- Opportunity stage changes trigger AI-generated next-action recommendations
- New contact webhooks notify the hub (log, tag, trigger nurture sequence)

**Setup:**
1. Log in to GHL → **Settings → Business Profile → API Keys**
2. Click **Generate API Key** (or copy existing Agency API key)
3. Copy your **Location ID** from the URL: `https://app.gohighlevel.com/v2/location/<LOCATION_ID>/...`
4. Add to `.env`:
   ```
   GHL_API_KEY=your-api-key-here
   GHL_LOCATION_ID=your-location-id-here
   GHL_WEBHOOK_SECRET=pick-any-random-string
   GHL_AUTO_REPLY_SMS=false   # set true when ready
   ```
5. In GHL → **Settings → Integrations → Webhooks** → Add Webhook:
   - URL: `https://your-domain.com/webhooks/gohighlevel`
   - Events: `ContactCreate`, `ContactUpdate`, `OpportunityCreate`, `OpportunityStatusChange`, `InboundMessage`
   - Secret: same value as `GHL_WEBHOOK_SECRET`

**API:** `https://services.leadconnectorhq.com` — docs at `https://highlevel.stoplight.io/docs/integrations/`

**Webhook endpoint in hub:** `POST /webhooks/gohighlevel` (handled by `ghl_webhook/bot.py`)

---

## 9. Lark (LarkSuite) — Enterprise Messaging + Bitable CRM + Docs

**What it does:** ByteDance's enterprise collaboration platform (Slack + Notion + Airtable in one). We use it as:
- A **messaging bot** in Eagle Eye and Lotus Group Lark workspaces
- A **Bitable CRM** — tables for leads, clients, tasks (lightweight alternative to GHL for internal tracking)
- A **Docs/Wiki** source — read Lark docs into AnythingLLM for RAG

**Our usage:**
- Lark bot receives messages → routes to AI hub → replies in thread
- Bot menu quick-actions: CRM status, daily brief, knowledge base search
- Lark Base (Bitable) records sync with business context data
- Lark Docs ingested to AnythingLLM workspace for RAG

**Setup:**
1. Go to **https://open.larksuite.com/app** → Create App → **Custom App**
2. Under **Credentials & Basic Info**, copy **App ID** and **App Secret**
3. Enable **Bot** capability → add bot to your Lark workspace
4. Go to **Event Subscriptions**:
   - Set webhook URL: `https://your-domain.com/webhooks/lark`
   - Copy **Verification Token** and **Encrypt Key**
   - Subscribe to: `im.message.receive_v1`
5. Under **Permissions & Scopes**, enable:
   - `im:message` (send/receive messages)
   - `bitable:app` (read/write Bitable tables)
   - `docx:document:readonly` (read Lark Docs)
   - `wiki:wiki:readonly` (read Wiki pages)
6. Publish the app (or add to workspace in dev mode)
7. Add to `.env`:
   ```
   LARK_APP_ID=cli_xxxxxxxxxxxxxxxxxxxx
   LARK_APP_SECRET=your-app-secret
   LARK_VERIFY_TOKEN=your-verification-token
   LARK_ENCRYPT_KEY=your-encrypt-key
   LARK_CRM_APP_TOKEN=token-from-bitable-url
   LARK_CRM_TABLE_ID=tblxxxxxxxxxxxxxxxx
   ```
8. In `lark_bot/bot.py`, update `CHAT_CONTEXT_MAP` with your actual Lark chat `open_id` values

**For Bitable CRM:**
- Create a Base at `https://your-tenant.larksuite.com/base/`
- Copy the token from the URL after `/base/` → `LARK_CRM_APP_TOKEN`
- Copy the table ID from the table URL fragment → `LARK_CRM_TABLE_ID`
- Suggested fields: Name, Email, Phone, Company, Stage, Source, Notes, Tags

**API:** `https://open.larksuite.com/open-apis/` — Swagger at `https://open.larksuite.com/document`

**Webhook endpoint in hub:** `GET/POST /webhooks/lark` (handled by `lark_bot/bot.py`)

---

## 10. Getting Your API Keys — Step-by-Step

### GoHighLevel API Key
1. Log in at `https://app.gohighlevel.com`
2. Go to **Settings** (bottom left) → **Business Profile**
3. Scroll to **API Keys** → click **Generate API Key**
4. Copy the key → paste into `.env` as `GHL_API_KEY`
5. Your **Location ID** is in the page URL after `/location/`

> For sub-account (location) API keys instead of Agency key:
> Settings → Company → Integrations → API → Generate

### Lark App Credentials
1. Go to `https://open.larksuite.com/app` → **Create App**
2. Choose **Custom App** → give it a name (e.g. "M3taz Hub Bot")
3. **Credentials & Basic Info** → copy App ID (`cli_xxx`) and App Secret
4. **Bot** → enable bot, set bot name and avatar
5. **Event Subscriptions** → enable events → set webhook URL → copy Verification Token and Encrypt Key
6. **Permissions & Scopes** → add: `im:message`, `bitable:app`, `docx:document:readonly`, `wiki:wiki:readonly`
7. **Version Management & Release** → create a version → publish (or use dev mode for testing)

### AnythingLLM API Key
1. Open AnythingLLM UI at `http://localhost:3001`
2. Click the gear icon → **Settings** → **API Keys**
3. Click **Generate New API Key**
4. Copy → paste into `.env` as `ANYTHINGLLM_API_KEY`

---

## Adding a New Platform

1. Create `<platform>_bot/` package with `bot.py` and `handlers.py`
2. Implement `PlatformAdapter` interface from `orchestration/router.py`
3. Add startup call in `main.py`
4. Add credentials to `.env.example`
5. Add service to `docker-compose.yml`
6. Document here
