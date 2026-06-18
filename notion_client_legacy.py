"""
CRUD contra las dos bases de datos de Notion.

DB1: Raw Saves  — recibe posts guardados de Instagram
DB2: Content Ideas — recibe ideas generadas por AI
"""
from datetime import datetime, timezone
from notion_client import Client

from config import NOTION_TOKEN, NOTION_RAW_SAVES_DB_ID, NOTION_CONTENT_IDEAS_DB_ID

_MAX_TEXT = 2000  # Límite de Notion para rich_text


def _client() -> Client:
    return Client(auth=NOTION_TOKEN)


def _rt(text: str) -> list:
    if not text:
        return []
    return [{"type": "text", "text": {"content": str(text)[:_MAX_TEXT]}}]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


# ── DB1: Raw Saves ────────────────────────────────────────────────────────────

def add_raw_save(save: dict) -> str:
    """Crea una página en Raw Saves DB. Retorna el URL de la página creada."""
    client = _client()
    props = {
        "Name": {"title": _rt(save.get("author", save.get("url", "save")))},
        "URL": {"url": save.get("url") or None},
        "Author": {"rich_text": _rt(save.get("author", ""))},
        "Caption": {"rich_text": _rt(save.get("caption", ""))},
        "Collection": {"select": {"name": save.get("collection", "General")}},
        "ContentType": {"select": {"name": save.get("content_type", "Post")}},
        "Processed": {"checkbox": False},
        "SavedAt": {"date": {"start": save.get("taken_at") or _now_iso()}},
        "Views": {"number": save.get("views", 0) or 0},
        "Likes": {"number": save.get("likes", 0) or 0},
        "Comments": {"number": save.get("comments", 0) or 0},
        "Verdict": {"select": {"name": "SIN ANALIZAR"}},
    }

    page = client.pages.create(
        parent={"database_id": NOTION_RAW_SAVES_DB_ID},
        properties=props,
    )
    return page.get("url", "")


def get_unprocessed_saves() -> list[dict]:
    """Retorna Raw Saves donde Processed=false y Verdict IN (REPLICAR, ADAPTAR)."""
    client = _client()
    results = []
    cursor = None

    while True:
        kwargs = {
            "database_id": NOTION_RAW_SAVES_DB_ID,
            "filter": {
                "and": [
                    {"property": "Processed", "checkbox": {"equals": False}},
                    {
                        "or": [
                            {"property": "Verdict", "select": {"equals": "REPLICAR"}},
                            {"property": "Verdict", "select": {"equals": "ADAPTAR"}},
                        ]
                    },
                ]
            },
        }
        if cursor:
            kwargs["start_cursor"] = cursor

        response = client.databases.query(**kwargs)
        for page in response.get("results", []):
            props = page.get("properties", {})
            results.append({
                "page_id": page["id"],
                "url": (props.get("URL") or {}).get("url", ""),
                "author": _extract_text(props.get("Author")),
                "caption": _extract_text(props.get("Caption")),
                "collection": _extract_select(props.get("Collection")),
                "content_type": _extract_select(props.get("ContentType")),
            })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return results


def get_unanalyzed_saves() -> list[dict]:
    """Retorna Raw Saves donde Verdict = 'SIN ANALIZAR'."""
    client = _client()
    results = []
    cursor = None

    while True:
        kwargs = {
            "database_id": NOTION_RAW_SAVES_DB_ID,
            "filter": {"property": "Verdict", "select": {"equals": "SIN ANALIZAR"}},
        }
        if cursor:
            kwargs["start_cursor"] = cursor

        response = client.databases.query(**kwargs)
        for page in response.get("results", []):
            props = page.get("properties", {})
            results.append({
                "page_id": page["id"],
                "url": (props.get("URL") or {}).get("url", ""),
                "author": _extract_text(props.get("Author")),
                "caption": _extract_text(props.get("Caption")),
                "collection": _extract_select(props.get("Collection")),
                "content_type": _extract_select(props.get("ContentType")),
                "views": (props.get("Views") or {}).get("number") or 0,
                "likes": (props.get("Likes") or {}).get("number") or 0,
                "comments": (props.get("Comments") or {}).get("number") or 0,
            })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return results


def update_save_verdict(page_id: str, verdict: str, report: str):
    """Actualiza el veredicto y el reporte de análisis de un Raw Save."""
    _MAX_REPORT = 1900  # Notion rich_text límite por bloque
    _client().pages.update(
        page_id=page_id,
        properties={
            "Verdict": {"select": {"name": verdict}},
            "AnalysisReport": {"rich_text": _rt(report[:_MAX_REPORT])},
        },
    )


def mark_save_processed(page_id: str):
    """Marca un Raw Save como Processed=true."""
    _client().pages.update(
        page_id=page_id,
        properties={"Processed": {"checkbox": True}},
    )


# ── DB2: Content Ideas ────────────────────────────────────────────────────────

def add_content_idea(idea: dict) -> str:
    """Crea una página en Content Ideas DB. Retorna el URL de la página creada."""
    client = _client()

    platforms = [{"name": p} for p in idea.get("platforms", [])]
    props = {
        "Name": {"title": _rt(idea.get("name", "Content Idea"))},
        "Pillar": {"select": {"name": idea.get("pillar", "Tools")}},
        "Status": {"select": {"name": "Not started"}},
        "Format": {"select": {"name": idea.get("format", "Carousel")}},
        "Platform": {"multi_select": platforms},
        "HookOptions": {"rich_text": _rt(idea.get("hooks", ""))},
        "Outline": {"rich_text": _rt(idea.get("outline", ""))},
        "Priority": {"select": {"name": idea.get("priority", "Medium")}},
        "SourceSaveID": {"rich_text": _rt(idea.get("source_page_id", ""))},
    }

    if idea.get("week_of"):
        props["WeekOf"] = {"date": {"start": idea["week_of"]}}

    page = client.pages.create(
        parent={"database_id": NOTION_CONTENT_IDEAS_DB_ID},
        properties=props,
    )
    return page.get("url", "")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_text(prop) -> str:
    if not prop:
        return ""
    rich_texts = prop.get("rich_text", [])
    return "".join(rt.get("plain_text", "") for rt in rich_texts)


def _extract_select(prop) -> str:
    if not prop:
        return ""
    sel = prop.get("select")
    return sel.get("name", "") if sel else ""
