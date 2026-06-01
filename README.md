# M3ta'z A.I. 9 Labz

**AI Consulting | SaaS | Training | Marketing Automation**

Enterprise-grade AI automation system for Eagle Eye Vision Labz.

## Services

- AI Consulting
- SaaS Productization
- Training Content Development
- Automation Design
- AI Marketing Systems

## Architecture

Follows the M3ta'z Kub3 3-layer DOE framework:
- **Directives** - What to do (SOPs in Markdown)
- **Orchestration** - Decision making (AI agents)
- **Execution** - Doing the work (Python scripts)

## Telegram Content Hub

Central hub for ingesting, organizing, and sharing all digital content through Telegram.

### Quick Start

1. **Create a Telegram Bot** — Message @BotFather on Telegram, use `/newbot`, and save the token
2. **Configure** — Copy `.env.example` to `.env` and add your bot token
3. **Install** — `pip install -r requirements.txt`
4. **Run** — `python main.py` (starts both bot and web app)

### What It Does

Send anything to the Telegram bot and it gets automatically stored, categorized, and made searchable:
- Photos (camera, Instagram, screenshots)
- Videos (reels, recordings)
- Documents (PDFs, files)
- Links (Amazon, ChatGPT, articles)
- Text notes and voice messages
- Forwarded messages from any chat

### Chat Contexts

Map different Telegram chats to purposes:
- `personal` — Personal notes and research
- `lotus_group` — Lotus Group business
- `family` — Family photos, memories, sharing (Tata, Kolelecsa, etc.)
- `meta` — MetaOS / Q3bi development

### Web Dashboard

Browse, search, filter, and share your content at `http://localhost:8000`

### Docker

```bash
cp .env.example .env
# Edit .env with your bot token
docker-compose up -d
```

## Twin.so AI Automation

[Twin.so](https://twin.so) lets you build and run AI agents that automate web tasks using
plain-language instructions.  The integration in this repo consists of:

| Component | Location |
|-----------|----------|
| HTTP client wrapper | `execution/twin_client.py` |
| Webhook receiver endpoint | `POST /webhook/twin` (FastAPI) |
| Configuration | `.env` — `TWIN_API_KEY`, `TWIN_WEBHOOK_SECRET` |

### Setup

1. **Sign up** at <https://twin.so> and create an API key.
2. **Configure** your `.env`:
   ```env
   TWIN_API_KEY=sk_live_...
   TWIN_WEBHOOK_SECRET=your-webhook-secret   # optional — enables signature verification
   ```
3. **Trigger a task** from Python:
   ```python
   from execution.twin_client import TwinClient

   async with TwinClient() as client:
       task = await client.create_task(
           description="Go to amazon.com and find top-rated wireless headphones",
           webhook_url="https://your-host.example.com/webhook/twin",
       )
       print(task["id"])
   ```
4. **View results** in the dashboard — completed tasks are stored as content items with source `twin_ai`.

### Webhook signature verification

Set `TWIN_WEBHOOK_SECRET` to the same value you configure in the Twin.so dashboard.
Incoming webhooks will be verified with HMAC-SHA256 and rejected with `401` if the
signature does not match.



```
telegram_bot/     Telegram bot (handlers, content ingestion)
webapp/           FastAPI web app (dashboard, API)
database/         SQLAlchemy models and engine
directives/       SOPs and operational docs
orchestration/    AI agent layer
execution/        Python automation scripts
media_store/      Uploaded files (gitignored)
```
