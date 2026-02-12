# SOP: Telegram Content Hub

## Purpose
Central hub for ingesting, organizing, and sharing all digital content through Telegram.

## Chat Contexts
| Context | Purpose | Who |
|---------|---------|-----|
| `personal` | Personal notes, research, bookmarks | You |
| `lotus_group` | Lotus Group business discussions | Business team |
| `family` | Family photos, memories, sharing | Tata, Kolelecsa, Tata Ma Ma, etc. |
| `meta` | MetaOS / Q3bi development notes | Meta development |

## Content Flow
1. **Ingest** — Send anything to the bot (photo, video, doc, link, text, voice)
2. **Auto-categorize** — Bot detects source (Instagram, Amazon, ChatGPT, etc.)
3. **Tag** — Use `/tag <category>` to refine categorization
4. **Organize** — Create collections with `/newcollection`, add items
5. **Share** — Use `/share <id>` to make items visible to family
6. **Browse** — Use the web app dashboard to search, filter, and view

## Categories
- `research` — ChatGPT articles, web research
- `photos` — Personal/family photos
- `videos` — Instagram reels, recordings
- `shopping` — Amazon, product links
- `documents` — PDFs, docs, files
- `notes` — Text messages, voice transcripts
- `links` — Bookmarks, saved URLs
- `social_media` — Instagram, TikTok, etc.
- `family` — Family-specific content
- `business` — Lotus Group items
- `meta_os` — MetaOS / Q3bi related

## Bot Commands
- `/start` — Welcome
- `/status` — Stats
- `/search <query>` — Search
- `/categories` — List categories
- `/tag <category>` — Tag last item
- `/collections` — List collections
- `/newcollection <name>` — Create collection
- `/setchat <context>` — Map this chat to a context
- `/share <id>` — Share with family
- `/help` — Full help
