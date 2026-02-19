"""FastAPI web application for browsing, searching, and sharing content."""

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import CONTENT_CATEGORIES, MEDIA_STORE_PATH
from database.engine import async_session, init_db
from database.models import Collection, CollectionItem, ContentItem, User

app = FastAPI(
    title="M3ta'z A.I. 9 Labz — Content Hub",
    description="Browse, search, and share your organized content library.",
    version="0.1.0",
)


async def get_db():
    async with async_session() as session:
        yield session


@app.on_event("startup")
async def startup():
    await init_db()


# ── WhatsApp Webhook ───────────────────────────────────────────────
from whatsapp.bot import whatsapp_verify, whatsapp_webhook  # noqa: E402


@app.get("/webhooks/whatsapp")
async def wa_verify(request: Request):
    """WhatsApp webhook verification (Meta challenge-response)."""
    return await whatsapp_verify(request)


@app.post("/webhooks/whatsapp")
async def wa_incoming(request: Request):
    """Receive incoming WhatsApp messages and route them."""
    return await whatsapp_webhook(request)


# ── API Endpoints ─────────────────────────────────────────────────

@app.get("/api/items", response_class=JSONResponse)
async def list_items(
    category: str | None = None,
    content_type: str | None = None,
    chat_context: str | None = None,
    shared_only: bool = False,
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List content items with optional filters."""
    stmt = select(ContentItem).order_by(ContentItem.created_at.desc())

    if category:
        stmt = stmt.where(ContentItem.category == category)
    if content_type:
        stmt = stmt.where(ContentItem.content_type == content_type)
    if chat_context:
        stmt = stmt.where(ContentItem.chat_context == chat_context)
    if shared_only:
        stmt = stmt.where(ContentItem.is_shared == True)
    if search:
        stmt = stmt.where(
            or_(
                ContentItem.text_content.ilike(f"%{search}%"),
                ContentItem.title.ilike(f"%{search}%"),
                ContentItem.tags.ilike(f"%{search}%"),
            )
        )

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "content_type": item.content_type,
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "source": item.source,
            "url": item.url,
            "text_content": (item.text_content or "")[:500],
            "file_path": item.file_path,
            "chat_context": item.chat_context,
            "is_shared": item.is_shared,
            "tags": item.tags,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


@app.get("/api/items/{item_id}", response_class=JSONResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single content item."""
    stmt = select(ContentItem).where(ContentItem.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        return JSONResponse({"error": "Not found"}, status_code=404)

    return {
        "id": item.id,
        "content_type": item.content_type,
        "category": item.category,
        "title": item.title,
        "description": item.description,
        "source": item.source,
        "url": item.url,
        "text_content": item.text_content,
        "file_path": item.file_path,
        "chat_context": item.chat_context,
        "is_shared": item.is_shared,
        "tags": item.tags,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@app.get("/api/stats", response_class=JSONResponse)
async def stats(db: AsyncSession = Depends(get_db)):
    """Dashboard statistics."""
    total = await db.scalar(select(func.count(ContentItem.id)))

    by_type = await db.execute(
        select(ContentItem.content_type, func.count(ContentItem.id))
        .group_by(ContentItem.content_type)
    )
    by_category = await db.execute(
        select(ContentItem.category, func.count(ContentItem.id))
        .group_by(ContentItem.category)
    )
    collections_count = await db.scalar(select(func.count(Collection.id)))

    return {
        "total_items": total or 0,
        "collections": collections_count or 0,
        "by_type": dict(by_type.all()),
        "by_category": dict(by_category.all()),
    }


@app.get("/api/collections", response_class=JSONResponse)
async def list_collections(db: AsyncSession = Depends(get_db)):
    """List all collections."""
    result = await db.execute(
        select(Collection).order_by(Collection.created_at.desc())
    )
    collections = result.scalars().all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "collection_type": c.collection_type,
            "is_shared": c.is_shared,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in collections
    ]


@app.get("/api/collections/{collection_id}/items", response_class=JSONResponse)
async def collection_items(collection_id: int, db: AsyncSession = Depends(get_db)):
    """List items in a collection."""
    stmt = (
        select(ContentItem)
        .join(CollectionItem, CollectionItem.content_item_id == ContentItem.id)
        .where(CollectionItem.collection_id == collection_id)
        .order_by(CollectionItem.sort_order)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "content_type": item.content_type,
            "category": item.category,
            "title": item.title,
            "text_content": (item.text_content or "")[:500],
            "file_path": item.file_path,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


@app.get("/api/family/shared", response_class=JSONResponse)
async def family_shared(db: AsyncSession = Depends(get_db)):
    """Get all items shared with family."""
    stmt = (
        select(ContentItem)
        .where(ContentItem.is_shared == True)
        .order_by(ContentItem.created_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        {
            "id": item.id,
            "content_type": item.content_type,
            "category": item.category,
            "title": item.title,
            "text_content": (item.text_content or "")[:200],
            "file_path": item.file_path,
            "source": item.source,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


# ── HTML Dashboard ────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M3ta'z A.I. 9 Labz — Content Hub</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #0a0a0a; color: #e0e0e0; }
        .header { background: linear-gradient(135deg, #1a1a2e, #16213e);
                   padding: 24px; border-bottom: 1px solid #333; }
        .header h1 { font-size: 1.5rem; color: #00d4ff; }
        .header p { color: #888; margin-top: 4px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                  gap: 16px; margin-bottom: 32px; }
        .stat-card { background: #1a1a2e; border: 1px solid #333; border-radius: 12px;
                     padding: 20px; text-align: center; }
        .stat-card .number { font-size: 2rem; font-weight: bold; color: #00d4ff; }
        .stat-card .label { color: #888; font-size: 0.85rem; margin-top: 4px; }
        .filters { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
        .filters select, .filters input { background: #1a1a2e; color: #e0e0e0;
            border: 1px solid #333; border-radius: 8px; padding: 8px 12px; }
        .content-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 16px; }
        .item-card { background: #1a1a2e; border: 1px solid #333; border-radius: 12px;
                     padding: 16px; transition: border-color 0.2s; }
        .item-card:hover { border-color: #00d4ff; }
        .item-card .meta { display: flex; gap: 8px; margin-bottom: 8px; }
        .badge { background: #16213e; color: #00d4ff; padding: 2px 8px;
                 border-radius: 4px; font-size: 0.75rem; }
        .item-card .text { color: #ccc; font-size: 0.9rem; line-height: 1.4;
                           max-height: 80px; overflow: hidden; }
        .item-card .time { color: #666; font-size: 0.75rem; margin-top: 8px; }
        .shared-badge { background: #1a3a1a; color: #4caf50; }
        .nav { display: flex; gap: 16px; margin-bottom: 24px; }
        .nav a { color: #00d4ff; text-decoration: none; padding: 8px 16px;
                 border: 1px solid #333; border-radius: 8px; }
        .nav a:hover, .nav a.active { background: #16213e; border-color: #00d4ff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>M3ta'z A.I. 9 Labz</h1>
        <p>Content Hub — Your organized digital life</p>
    </div>
    <div class="container">
        <div class="nav">
            <a href="#" class="active" onclick="loadAll()">All Content</a>
            <a href="#" onclick="loadShared()">Family Shared</a>
            <a href="#" onclick="loadCollections()">Collections</a>
        </div>
        <div id="stats" class="stats"></div>
        <div class="filters">
            <select id="filterCategory" onchange="applyFilters()">
                <option value="">All Categories</option>
            </select>
            <select id="filterType" onchange="applyFilters()">
                <option value="">All Types</option>
                <option value="photo">Photos</option>
                <option value="video">Videos</option>
                <option value="document">Documents</option>
                <option value="link">Links</option>
                <option value="text">Notes</option>
                <option value="voice">Voice</option>
            </select>
            <input type="text" id="searchBox" placeholder="Search..." onkeyup="debounceSearch()">
        </div>
        <div id="content" class="content-grid"></div>
    </div>
    <script>
        let searchTimeout;
        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="stat-card"><div class="number">${data.total_items}</div><div class="label">Total Items</div></div>
                <div class="stat-card"><div class="number">${data.collections}</div><div class="label">Collections</div></div>
                <div class="stat-card"><div class="number">${Object.keys(data.by_category).length}</div><div class="label">Categories</div></div>
            `;
            const catSelect = document.getElementById('filterCategory');
            Object.keys(data.by_category).forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat; opt.textContent = cat + ' (' + data.by_category[cat] + ')';
                catSelect.appendChild(opt);
            });
        }
        async function loadItems(params = '') {
            const res = await fetch('/api/items' + (params ? '?' + params : ''));
            const items = await res.json();
            renderItems(items);
        }
        function renderItems(items) {
            const container = document.getElementById('content');
            if (!items.length) { container.innerHTML = '<p style="color:#666">No items yet. Send content to your Telegram bot to get started.</p>'; return; }
            container.innerHTML = items.map(item => `
                <div class="item-card">
                    <div class="meta">
                        <span class="badge">${item.content_type}</span>
                        <span class="badge">${item.category}</span>
                        ${item.source ? '<span class="badge">' + item.source + '</span>' : ''}
                        ${item.is_shared ? '<span class="badge shared-badge">shared</span>' : ''}
                    </div>
                    ${item.title ? '<strong>' + item.title + '</strong>' : ''}
                    ${item.url ? '<div><a href="' + item.url + '" target="_blank" style="color:#00d4ff">' + item.url.substring(0,60) + '...</a></div>' : ''}
                    <div class="text">${item.text_content || ''}</div>
                    <div class="time">${item.created_at ? new Date(item.created_at).toLocaleString() : ''} | #${item.id}</div>
                </div>
            `).join('');
        }
        function applyFilters() {
            const params = new URLSearchParams();
            const cat = document.getElementById('filterCategory').value;
            const type = document.getElementById('filterType').value;
            const search = document.getElementById('searchBox').value;
            if (cat) params.set('category', cat);
            if (type) params.set('content_type', type);
            if (search) params.set('search', search);
            loadItems(params.toString());
        }
        function debounceSearch() { clearTimeout(searchTimeout); searchTimeout = setTimeout(applyFilters, 300); }
        async function loadAll() { loadItems(); }
        async function loadShared() {
            const res = await fetch('/api/family/shared');
            const items = await res.json();
            renderItems(items);
        }
        async function loadCollections() {
            const res = await fetch('/api/collections');
            const colls = await res.json();
            const container = document.getElementById('content');
            if (!colls.length) { container.innerHTML = '<p style="color:#666">No collections yet. Use /newcollection in Telegram to create one.</p>'; return; }
            container.innerHTML = colls.map(c => `
                <div class="item-card" onclick="loadCollectionItems(${c.id})">
                    <strong>${c.name}</strong>
                    <div class="meta"><span class="badge">${c.collection_type}</span>${c.is_shared ? '<span class="badge shared-badge">shared</span>' : ''}</div>
                    <div class="text">${c.description || ''}</div>
                    <div class="time">${c.created_at ? new Date(c.created_at).toLocaleString() : ''}</div>
                </div>
            `).join('');
        }
        async function loadCollectionItems(id) {
            const res = await fetch('/api/collections/' + id + '/items');
            const items = await res.json();
            renderItems(items);
        }
        loadStats();
        loadItems();
    </script>
</body>
</html>"""
