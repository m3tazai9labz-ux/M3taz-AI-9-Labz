# M3taz Hub Skill

## Description
Routes messages and tasks through the M3ta'z A.I. 9 Labz central hub. Use this skill when you need to save content, query the knowledge base, run a multi-agent task, or interact with the Eagle Eye or Lotus Group business contexts.

## Triggers
- "save this"
- "add to knowledge base"
- "lotus group task"
- "eagle eye"
- "run a task through the hub"
- "m3taz"

## Implementation

```python
import httpx

async def run(params: dict) -> str:
    message = params.get("message", "")
    context = params.get("context", "personal")
    user = params.get("user", "openclaw")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "http://hub:8000/api/route",
            json={
                "platform": "openclaw",
                "user_id": user,
                "username": user,
                "chat_id": "openclaw",
                "text": message,
                "chat_context": context,
            },
        )
        resp.raise_for_status()
        return resp.json().get("text", "Done.")
```

## Parameters
- `message` (str): The message or task to route
- `context` (str): Business context — personal | lotus_group | eagle_eye | family | meta
- `user` (str): Username for logging purposes

## Examples
- "Save this article to my knowledge base" → context=personal
- "Create a Lotus Group task: prepare Q1 report" → context=lotus_group
- "Eagle Eye: research AI consulting pricing 2026" → context=eagle_eye
