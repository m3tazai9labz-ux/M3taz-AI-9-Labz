"""Central configuration for M3ta'z A.I. 9 Labz."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
MEDIA_STORE_PATH = Path(os.getenv("MEDIA_STORE_PATH", BASE_DIR / "media_store" / "uploads"))
THUMBNAIL_PATH = Path(os.getenv("THUMBNAIL_PATH", BASE_DIR / "media_store" / "thumbnails"))

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
]
ALLOWED_GROUP_IDS = [
    int(gid.strip())
    for gid in os.getenv("ALLOWED_GROUP_IDS", "").split(",")
    if gid.strip()
]

# Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")

# WhatsApp (Meta Cloud API)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "whatsapp-verify-token")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'm3taz_hub.db'}")

# Web App
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8000"))
WEBAPP_SECRET_KEY = os.getenv("WEBAPP_SECRET_KEY", "change-me")

# Media
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# AI: Anthropic (Claude) — intent classification + orchestration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# AI: Open WebUI — conversational chat proxy
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://localhost:3000")
OPEN_WEBUI_API_KEY = os.getenv("OPEN_WEBUI_API_KEY", "")

# AI: Eigent AI — multi-agent workforce
EIGENT_API_URL = os.getenv("EIGENT_API_URL", "http://localhost:7070")
EIGENT_API_KEY = os.getenv("EIGENT_API_KEY", "")

# AI: Agent Zero — hierarchical agent / deep reasoning
AGENT_ZERO_URL = os.getenv("AGENT_ZERO_URL", "http://localhost:50001")
AGENT_ZERO_API_KEY = os.getenv("AGENT_ZERO_API_KEY", "")

# AI: AFFiNE — knowledge base / workspace
AFFINE_URL = os.getenv("AFFINE_URL", "http://localhost:3010")
AFFINE_API_KEY = os.getenv("AFFINE_API_KEY", "")

# AI: OpenClaw — platform agent daemon / skills engine
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "http://localhost:8080")
OPENCLAW_API_KEY = os.getenv("OPENCLAW_API_KEY", "")

# CRM: GoHighLevel — marketing automation + sales pipeline + SMS/email
GHL_API_KEY = os.getenv("GHL_API_KEY", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")
GHL_WEBHOOK_SECRET = os.getenv("GHL_WEBHOOK_SECRET", "")
GHL_AUTO_REPLY_SMS = os.getenv("GHL_AUTO_REPLY_SMS", "false").lower() == "true"

# Messaging+CRM: Lark (LarkSuite) — enterprise collaboration + Bitable CRM + Docs
# International tenants: https://open.larksuite.com  |  CN tenants: https://open.feishu.cn
LARK_API_BASE = os.getenv("LARK_API_BASE", "https://open.larksuite.com/open-apis")
LARK_APP_ID = os.getenv("LARK_APP_ID", "")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET", "")
LARK_VERIFY_TOKEN = os.getenv("LARK_VERIFY_TOKEN", "")
LARK_ENCRYPT_KEY = os.getenv("LARK_ENCRYPT_KEY", "")
# Lark Base (Bitable) — copy app_token and table_id from your Bitable URL
LARK_CRM_APP_TOKEN = os.getenv("LARK_CRM_APP_TOKEN", "")
LARK_CRM_TABLE_ID = os.getenv("LARK_CRM_TABLE_ID", "")

# AI: Ollama — local model inference (Anthropic-compatible API)
# Run: ollama serve  OR  docker-compose up ollama
# Claude Code + Ollama: ollama launch claude
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder")

# AI: AnythingLLM — RAG-powered document chat with workspace-per-context
# Each business context maps to its own workspace (create these in the UI first)
ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_URL", "http://localhost:3001")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "")
ANYTHINGLLM_DEFAULT_WORKSPACE = os.getenv("ANYTHINGLLM_DEFAULT_WORKSPACE", "personal")

# Content categories
CONTENT_CATEGORIES = [
    "research",       # ChatGPT articles, web research
    "photos",         # Personal/family photos
    "videos",         # Instagram reels, recordings
    "shopping",       # Amazon, product links
    "documents",      # PDFs, docs, files
    "notes",          # Text messages, voice transcripts
    "links",          # Bookmarks, saved URLs
    "social_media",   # Instagram, TikTok, etc.
    "family",         # Family-specific content
    "business",       # Lotus Group, business items
    "meta_os",        # MetaOS / Q3bi related
    "uncategorized",
]

# Conversation contexts — maps chat sources to business contexts
CHAT_CONTEXTS = {
    "personal": "Personal conversations and notes",
    "lotus_group": "Lotus Group business discussions",
    "family": "Family collaboration and sharing",
    "meta": "Meta / MetaOS / Q3bi development",
    "eagle_eye": "Eagle Eye Vision Labz — AI consulting and SaaS",
}

# Per-context preferred AI backend
CONTEXT_AI_PREFERENCE = {
    "eagle_eye":   ["gohighlevel", "eigent", "anythingllm", "agent_zero", "open_webui"],
    "lotus_group": ["gohighlevel", "anythingllm", "open_webui", "eigent"],
    "meta":        ["agent_zero", "eigent", "anythingllm", "open_webui"],
    "personal":    ["openclaw", "anythingllm", "open_webui"],
    "family":      ["open_webui"],
}
