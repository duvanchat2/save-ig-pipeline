"""
CRUD contra las bases de datos de Notion.

DB1: Raw Saves  — recibe posts guardados de Instagram
DB2: Content Ideas — recibe ideas generadas por AI

Nota: este archivo se llama notion_db.py (no notion_client.py) para evitar
conflicto de nombres con el paquete pip 'notion-client' que tambien se importa
como 'notion_client'.
"""
from datetime import datetime, timezone

import notion_client as _nc  # paquete pip: notion-client

from config import NOTION_TOKEN, NOTION_RAW_SAVES_DB_ID, NOTION_CONTENT_IDEAS_DB_ID

# Content OS — base de datos maestra (una sola fila por pieza de contenido)
CONTENT_OS_DB_ID = "5f4358fd9c794640847461294c0aecbb"

_MAX_TEXT = 2000  # Límite de Notion para rich_text


def _client() -> _nc.Client:
    return _nc.Client(auth=NOTION_TOKEN)


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
                "transcript": _extract_text(props.get("Transcript")),
                "verdict": _extract_select(props.get("Verdict")),
                "f4_formula": _extract_text(props.get("F4_Formula")),
                "views": (props.get("Views") or {}).get("number") or 0,
                "likes": (props.get("Likes") or {}).get("number") or 0,
                "comments": (props.get("Comments") or {}).get("number") or 0,
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


def update_save_verdict(page_id: str, verdict: str, f1: str, f2: str, f3: str,
                        f4: str, report: str, transcript: str = "",
                        hook: str = "", cuerpo: str = "", cta: str = "",
                        por_que_funciona: str = "", tipo_formato: str = "",
                        engagement_level: str = ""):
    """Actualiza veredicto, filtros F1-F4, reporte, transcript y campos de desglose."""
    props = {
        "Verdict":        {"select": {"name": verdict}},
        "AnalysisReport": {"rich_text": _rt(report[:_MAX_TEXT])},
        "F4_Formula":     {"rich_text": _rt(f4[:_MAX_TEXT])},
    }
    if f1: props["F1_Origen"]   = {"select": {"name": f1}}
    if f2: props["F2_Metricas"] = {"select": {"name": f2}}
    if f3: props["F3_Nicho"]    = {"select": {"name": f3}}
    if transcript:       props["Transcript"]      = {"rich_text": _rt(transcript[:_MAX_TEXT])}
    if hook:             props["Hook"]            = {"rich_text": _rt(hook[:_MAX_TEXT])}
    if cuerpo:           props["Cuerpo"]          = {"rich_text": _rt(cuerpo[:_MAX_TEXT])}
    if cta:              props["CTA"]             = {"rich_text": _rt(cta[:_MAX_TEXT])}
    if por_que_funciona: props["PorQueFunciona"]  = {"rich_text": _rt(por_que_funciona[:_MAX_TEXT])}
    if tipo_formato:     props["TipoFormato"]     = {"select": {"name": tipo_formato}}
    if engagement_level: props["EngagementLevel"] = {"select": {"name": engagement_level}}
    _client().pages.update(page_id=page_id, properties=props)


def update_save_transcript(page_id: str, transcript: str):
    """Guarda la transcripción en la fila de Raw Saves."""
    _client().pages.update(
        page_id=page_id,
        properties={"Transcript": {"rich_text": _rt(transcript[:_MAX_TEXT])}},
    )


def mark_save_processed(page_id: str):
    """Marca un Raw Save como Processed=true."""
    _client().pages.update(
        page_id=page_id,
        properties={"Processed": {"checkbox": True}},
    )


# ── Transcriber DB — buscar transcript por shortcode ─────────────────────────

TRANSCRIBER_DB_ID = "b9e16d3210a7425dae31edb577638388"


def get_transcript_by_shortcode(shortcode: str) -> str:
    """Busca en la DB del Transcriber el AI Transcript del shortcode dado."""
    client = _client()
    try:
        response = client.databases.query(
            database_id=TRANSCRIBER_DB_ID,
            filter={"property": "Short Code", "title": {"equals": shortcode}},
            page_size=1,
        )
        pages = response.get("results", [])
        if not pages:
            return ""
        props = pages[0].get("properties", {})
        return _extract_text(props.get("AI Transcript"))
    except Exception:
        return ""


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


# ── Content OS — base de datos maestra ───────────────────────────────────────

def add_to_content_os(save: dict) -> str:
    """Agrega un nuevo save al Content OS con Stage=RAW."""
    client = _client()
    titulo = f"{save.get('content_type','Reel')} de @{save.get('author','?')} — {(save.get('caption') or '')[:60]}"
    props = {
        "Titulo": {"title": _rt(titulo)},
        "Stage": {"select": {"name": "RAW"}},
        "Fuente_URL": {"url": save.get("url") or None},
        "Fuente_Autor": {"rich_text": _rt(save.get("author", ""))},
        "Fuente_Caption": {"rich_text": _rt(save.get("caption", ""))},
        "Fuente_Tipo": {"select": {"name": save.get("content_type", "Reel")}},
        "Fuente_Coleccion": {"select": {"name": "Saved"}},
        "Fuente_Views": {"number": save.get("views", 0) or 0},
        "Fuente_Likes": {"number": save.get("likes", 0) or 0},
        "Fuente_Comments": {"number": save.get("comments", 0) or 0},
        "Veredicto": {"select": {"name": "SIN ANALIZAR"}},
    }
    if save.get("taken_at"):
        props["Fuente_Fecha"] = {"date": {"start": save["taken_at"]}}

    page = client.pages.create(
        parent={"database_id": CONTENT_OS_DB_ID},
        properties=props,
    )
    return page.get("url", "")


def get_content_os_for_analysis() -> list[dict]:
    """Retorna filas de Content OS donde Veredicto='SIN ANALIZAR'."""
    client = _client()
    results = []
    cursor = None
    while True:
        kwargs = {
            "database_id": CONTENT_OS_DB_ID,
            "filter": {"property": "Veredicto", "select": {"equals": "SIN ANALIZAR"}},
        }
        if cursor:
            kwargs["start_cursor"] = cursor
        response = client.databases.query(**kwargs)
        for page in response.get("results", []):
            props = page.get("properties", {})
            results.append({
                "page_id": page["id"],
                "url": (props.get("Fuente_URL") or {}).get("url", ""),
                "author": _extract_text(props.get("Fuente_Autor")),
                "caption": _extract_text(props.get("Fuente_Caption")),
                "content_type": _extract_select(props.get("Fuente_Tipo")),
                "collection": _extract_select(props.get("Fuente_Coleccion")),
                "views": (props.get("Fuente_Views") or {}).get("number") or 0,
                "likes": (props.get("Fuente_Likes") or {}).get("number") or 0,
                "comments": (props.get("Fuente_Comments") or {}).get("number") or 0,
            })
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return results


def update_content_os_analysis(page_id: str, verdict: str, f1: str, f2: str, f3: str,
                                f4: str, report: str):
    """Actualiza el análisis de 4 filtros y avanza Stage a ANALIZADO."""
    _client().pages.update(
        page_id=page_id,
        properties={
            "Stage": {"select": {"name": "ANALIZADO"}},
            "Veredicto": {"select": {"name": verdict}},
            "F1_Origen": {"select": {"name": f1}} if f1 else {},
            "F2_Metricas": {"select": {"name": f2}} if f2 else {},
            "F3_Nicho": {"select": {"name": f3}} if f3 else {},
            "F4_Formula": {"rich_text": _rt(f4[:_MAX_TEXT])},
            "Reporte_Analisis": {"rich_text": _rt(report[:_MAX_TEXT])},
        },
    )


def get_content_os_for_transform() -> list[dict]:
    """Retorna filas Stage=ANALIZADO con Veredicto REPLICAR o ADAPTAR."""
    client = _client()
    results = []
    cursor = None
    while True:
        kwargs = {
            "database_id": CONTENT_OS_DB_ID,
            "filter": {
                "and": [
                    {"property": "Stage", "select": {"equals": "ANALIZADO"}},
                    {"or": [
                        {"property": "Veredicto", "select": {"equals": "REPLICAR"}},
                        {"property": "Veredicto", "select": {"equals": "ADAPTAR"}},
                    ]},
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
                "url": (props.get("Fuente_URL") or {}).get("url", ""),
                "author": _extract_text(props.get("Fuente_Autor")),
                "caption": _extract_text(props.get("Fuente_Caption")),
                "content_type": _extract_select(props.get("Fuente_Tipo")),
                "verdict": _extract_select(props.get("Veredicto")),
                "f4_formula": _extract_text(props.get("F4_Formula")),
                "transcript": _extract_text(props.get("Fuente_Transcript")),
                "views": (props.get("Fuente_Views") or {}).get("number") or 0,
                "likes": (props.get("Fuente_Likes") or {}).get("number") or 0,
                "comments": (props.get("Fuente_Comments") or {}).get("number") or 0,
            })
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return results


def update_content_os_transcript(page_id: str, transcript: str):
    """Guarda la transcripción en la fila de Content OS."""
    _client().pages.update(
        page_id=page_id,
        properties={"Fuente_Transcript": {"rich_text": _rt(transcript[:_MAX_TEXT])}},
    )


def update_content_os_idea(page_id: str, idea: dict):
    """Guarda la idea/guión generado y avanza Stage a IDEA GENERADA."""
    platforms = idea.get("platforms", [])
    if isinstance(platforms, str):
        platforms = [p.strip() for p in platforms.split(",")]

    props = {
        "Stage": {"select": {"name": "IDEA GENERADA"}},
        "Titulo": {"title": _rt(idea.get("titulo", idea.get("name", "Idea")))},
        "Pilar": {"select": {"name": idea.get("pilar", idea.get("pillar", "Tools"))}},
        "Formato": {"select": {"name": idea.get("formato", idea.get("format", "Reel corto <30s"))}},
        "Plataforma": {"multi_select": [{"name": p} for p in platforms]},
        "Prioridad": {"select": {"name": idea.get("prioridad", idea.get("priority", "Media"))}},
        "Hooks": {"rich_text": _rt(idea.get("hooks", "")[:_MAX_TEXT])},
        "Outline": {"rich_text": _rt(idea.get("outline", "")[:_MAX_TEXT])},
        "Estado_Produccion": {"select": {"name": "Sin empezar"}},
    }
    if idea.get("guion_final"):
        props["Guion_Final"] = {"rich_text": _rt(idea["guion_final"][:_MAX_TEXT])}
    if idea.get("semana"):
        props["Semana_Publicacion"] = {"date": {"start": idea["semana"]}}

    _client().pages.update(page_id=page_id, properties=props)


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
