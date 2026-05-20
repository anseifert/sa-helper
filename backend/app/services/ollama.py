import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()


async def check_ollama_health() -> str:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            if r.status_code == 200:
                return "ok"
    except Exception as e:
        logger.debug("ollama_unavailable", error=str(e))
    return "unavailable"


async def enrich_contact(title_hint: str, email: str, snippet: str = "") -> dict[str, str | None]:
    """Optional local LLM enrichment; degrades gracefully."""
    settings = get_settings()
    if await check_ollama_health() != "ok":
        return {"title": title_hint or None, "notes": None}

    prompt = (
        f"For a sales contact {email}, suggest a short job title and one-line notes "
        f"based on: {title_hint or 'unknown'} {snippet[:200]}. "
        "Reply as JSON: {\"title\": \"...\", \"notes\": \"...\"}"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
            )
            if r.status_code != 200:
                return {"title": title_hint or None, "notes": None}
            text = r.json().get("response", "")
            import json

            data = json.loads(text)
            return {
                "title": data.get("title") or title_hint,
                "notes": data.get("notes"),
            }
    except Exception as e:
        logger.warning("ollama_enrich_failed", error=str(e))
        return {"title": title_hint or None, "notes": None}


async def polish_recommendation(title: str, body: str) -> str | None:
    if await check_ollama_health() != "ok":
        return None
    settings = get_settings()
    prompt = f"Rewrite this SA recommendation in one friendly sentence:\n{title}\n{body}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()[:500]
    except Exception:
        pass
    return None
