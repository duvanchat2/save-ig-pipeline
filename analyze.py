"""
Fase 2 — Agente Analizador de Contenido (4 filtros + desglose completo).

Por cada save analiza:
  - 4 filtros: Origen, Metricas, Nicho, Formula
  - Desglose: Hook / Cuerpo / CTA
  - Por que funciona (mecanismo psicologico)
  - Tipo de formato
  - Nivel de engagement
  - Veredicto: REPLICAR / ADAPTAR / SOLO ESTRUCTURA / DESCARTAR

Transcripcion via AssemblyAI (yt-dlp + cookies del agent-browser).

Uso:
  python analyze.py                    # Interactivo
  python analyze.py --auto             # Sin confirmacion
  python analyze.py --limit 5          # Maximo N saves
  python analyze.py --skip-transcribe  # Solo caption (sin AssemblyAI)
"""
import argparse
import re
import sys
from datetime import datetime, timezone

import anthropic

from config import ANTHROPIC_API_KEY, CONTENT_NICHE
from notion_db import get_unanalyzed_saves, update_save_verdict

# ── Pre-filtro heuristico ──────────────────────────────────────────────────────
_PAID_PATTERNS = [
    r'comenta\s+["\']?\w+["\']?', r'comment\s+["\']?\w+["\']?',
    r'te\s+(env[ii]o|mando|paso)\b', r"i'?ll\s+send\b",
    r'\bantes\s+del\b.*\d', r'\bbefore\s+\w+\s+\d+\b',
    r'\bsolo\s+hoy\b', r'\bonly\s+today\b', r'\blink\s+en\s+bio\b',
]
_NICHE_PATTERNS = [
    r'\b(ia|ai|gpt|claude|gemini|llm|llama|modelo|model)\b',
    r'\b(automat|productividad|productivity|solopreneur|workflow|stack)\b',
    r'\b(herramienta|tool|agent|prompt|api|notebooklm|obsidian)\b',
    r'\b(emprendedor|founder|negocio\s+online|business)\b',
]

_VALID_FORMATS = {
    "Short Reel <30s", "Reel largo 30-90s", "Carousel",
    "Tutorial en pantalla", "Lista", "Historia",
    "Antes-Despues", "Comparativa", "Demo de herramienta",
}
_VALID_ENGAGEMENT = {"VIRAL", "ALTO", "NORMAL", "BAJO", "SIN DATOS"}


def _quick_prefilter(save: dict) -> tuple[bool, str]:
    text = (save.get("caption", "") or "").lower()
    paid = sum(1 for p in _PAID_PATTERNS if re.search(p, text))
    niche = any(re.search(p, text) for p in _NICHE_PATTERNS)
    if paid >= 2 and not niche:
        return False, f"Pre-filtro: {paid} senales pagadas sin keywords de nicho -> DESCARTAR."
    return True, f"Pre-filtro: {paid} senal(es) pagadas, nicho={'SI' if niche else 'NO'} -> procede."


# ── Transcripcion via AssemblyAI ───────────────────────────────────────────────
def _shortcode_from_url(url: str) -> str:
    m = re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else ""


def _transcribe(url: str) -> str:
    try:
        from assemblyai_transcriber import transcribe_reel
        return transcribe_reel(url)
    except Exception as e:
        print(f"  [transcribe] Error: {e}", file=sys.stderr)
        return ""


# ── System Prompt del Agente ───────────────────────────────────────────────────
_SYSTEM_PROMPT = f"""Eres el Agente Analizador de Contenido para @byduvan_ai.
Nicho objetivo: {CONTENT_NICHE}.
Audiencia: solopreneurs que empiezan con IA, nivel basico-intermedio, buscan productividad y monetizacion.

Tienes el CAPTION y la TRANSCRIPCION COMPLETA del video (si esta disponible). Usa ambas.

---

FILTRO 1 - ORIGEN (ORGANICO | DUDOSO | PAGADO)
Senales de PAGADO (2 o mas = PAGADO): comentar palabra para recibir recurso, promesa de DM,
urgencia artificial ("solo hoy", "antes del X"), caption 100% conversion sin valor educativo, bio-funnel.

FILTRO 2 - METRICAS (ALTO RENDIMIENTO | RENDIMIENTO NORMAL | BAJO RENDIMIENTO | SIN DATOS)
Benchmarks: Comment rate viral >= 2% | bueno >= 0.5% | Like rate bueno >= 3% | Save rate excelente >= 8%
Calcula con los numeros reales si estan disponibles. Si no hay datos, usar SIN DATOS.

FILTRO 3 - NICHO (COMPATIBLE | ADAPTABLE | INCOMPATIBLE)
COMPATIBLE = tema directo para solopreneurs con IA.
ADAPTABLE = tema con angulo reencuadrable a nuestra audiencia.
INCOMPATIBLE = audiencia completamente distinta, sin adaptacion posible.

FILTRO 4 - FORMULA
Analiza la formula narrativa completa del video usando el transcript.

---

NIVEL DE ENGAGEMENT (VIRAL | ALTO | NORMAL | BAJO | SIN DATOS)
VIRAL = comment rate >= 2% o señales cualitativas de viralidad masiva.
ALTO = metricas por encima del promedio o contenido muy compartible.
NORMAL = metricas estandar del nicho.
BAJO = metricas debiles o contenido de bajo impacto.
SIN DATOS = no hay metricas disponibles (evalua cualitativamente si puedes).

---

TIPO DE FORMATO (elige exactamente uno):
Short Reel <30s | Reel largo 30-90s | Carousel | Tutorial en pantalla | Lista | Historia | Antes-Despues | Comparativa | Demo de herramienta

---

VEREDICTO:
REPLICAR -- organico + metricas buenas + nicho compatible + formula clara
ADAPTAR -- pagado o metricas mediocres PERO tema/formula valioso para nuestra audiencia
SOLO ESTRUCTURA -- tema incompatible pero formula brillante (robar solo el formato)
DESCARTAR -- pagado sin valor real, nicho incompatible, formula generica

---

RESPONDE EXACTAMENTE EN ESTE FORMATO (sin agregar ni quitar secciones):

FILTRO 1 - ORIGEN: [ORGANICO / DUDOSO / PAGADO]
[razonamiento en 1-2 lineas]

FILTRO 2 - METRICAS: [ALTO RENDIMIENTO / RENDIMIENTO NORMAL / BAJO RENDIMIENTO / SIN DATOS]
[numeros calculados y conclusion]

FILTRO 3 - NICHO: [COMPATIBLE / ADAPTABLE / INCOMPATIBLE]
[razonamiento en 1-2 lineas]

FILTRO 4 - FORMULA: [nombre descriptivo de la formula]
[descripcion breve de la estructura general]

HOOK:
[Cita verbatim las primeras 1-3 oraciones del transcript. Si no hay transcript, usa el opening del caption o infiere del titulo del video]

CUERPO:
[Estructura numerada del desarrollo: Punto 1: ... Punto 2: ... Punto 3: ... con las ideas clave de cada segmento del video]

CTA:
[Como termina el video exactamente. Que accion pide o implica. Si es implicito, describelo]

POR QUE FUNCIONA:
[3-4 lineas explicando el mecanismo psicologico: que emocion activa (curiosidad/miedo/FOMO/aspiracion), que loop abre, por que la audiencia guarda/comenta/comparte este contenido especificamente]

NIVEL DE ENGAGEMENT: [VIRAL / ALTO / NORMAL / BAJO / SIN DATOS]
[justificacion en 1 linea basada en metricas o señales cualitativas]

TIPO DE FORMATO: [uno de los 9 tipos definidos]
[1 linea explicando por que aplica este formato]

VEREDICTO: [REPLICAR / ADAPTAR / SOLO ESTRUCTURA / DESCARTAR]
[2-3 lineas de justificacion con referencia concreta al transcript o caption]"""


def _build_msg(save: dict, transcript: str) -> str:
    v = save.get("views", 0) or 0
    l = save.get("likes", 0) or 0
    c = save.get("comments", 0) or 0
    cr = f"{c/v*100:.2f}%" if v > 0 else "N/D"
    lr = f"{l/v*100:.2f}%" if v > 0 else "N/D"
    tx = f"TRANSCRIPCION COMPLETA:\n{transcript}" if transcript else "TRANSCRIPCION: No disponible (analiza solo con caption)."
    return (
        f"Creador: @{save.get('author','?')}\n"
        f"Tipo de contenido: {save.get('content_type','Reel')}\n"
        f"URL: {save.get('url','')}\n\n"
        f"METRICAS:\n"
        f"  Views: {v or 'N/D'}\n"
        f"  Likes: {l or 'N/D'} ({lr})\n"
        f"  Comments: {c or 'N/D'} ({cr})\n\n"
        f"CAPTION:\n{save.get('caption','(sin caption)')}\n\n"
        f"{tx}"
    )


def _analyze(save: dict, transcript: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    r = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_msg(save, transcript)}],
    )
    return r.content[0].text.strip()


def _find(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else default


def _find_block(start_pattern: str, end_pattern: str, text: str) -> str:
    m = re.search(
        rf"{start_pattern}\s*\n(.*?)(?={end_pattern}|\Z)",
        text, re.DOTALL | re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _parse_report(report: str) -> dict:
    verdict = _find(r"VEREDICTO:\s*(REPLICAR|ADAPTAR|SOLO ESTRUCTURA|DESCARTAR)", report)
    f1 = _find(r"FILTRO 1 - ORIGEN:\s*(ORGANICO|DUDOSO|PAGADO)", report)
    f2 = _find(r"FILTRO 2 - METRICAS:\s*(ALTO RENDIMIENTO|RENDIMIENTO NORMAL|BAJO RENDIMIENTO|SIN DATOS)", report)
    f3 = _find(r"FILTRO 3 - NICHO:\s*(COMPATIBLE|ADAPTABLE|INCOMPATIBLE)", report)

    f4_m = re.search(r"FILTRO 4 - FORMULA:(.+?)(?=HOOK:|$)", report, re.DOTALL | re.IGNORECASE)
    f4 = f4_m.group(1).strip() if f4_m else ""

    hook   = _find_block(r"HOOK:",          r"CUERPO:|CTA:|POR QUE FUNCIONA:|NIVEL DE ENGAGEMENT:|TIPO DE FORMATO:|VEREDICTO:", report)
    cuerpo = _find_block(r"CUERPO:",        r"CTA:|POR QUE FUNCIONA:|NIVEL DE ENGAGEMENT:|TIPO DE FORMATO:|VEREDICTO:", report)
    cta    = _find_block(r"CTA:",           r"POR QUE FUNCIONA:|NIVEL DE ENGAGEMENT:|TIPO DE FORMATO:|VEREDICTO:", report)
    porq   = _find_block(r"POR QUE FUNCIONA:", r"NIVEL DE ENGAGEMENT:|TIPO DE FORMATO:|VEREDICTO:", report)

    engagement_raw = _find(r"NIVEL DE ENGAGEMENT:\s*(VIRAL|ALTO|NORMAL|BAJO|SIN DATOS)", report)
    engagement = engagement_raw if engagement_raw in _VALID_ENGAGEMENT else "SIN DATOS"

    formato_raw = _find(r"TIPO DE FORMATO:\s*([^\n]+)", report)
    # Normalizar al valor exacto del select
    tipo_formato = ""
    for valid in _VALID_FORMATS:
        if valid.lower() in formato_raw.lower():
            tipo_formato = valid
            break
    if not tipo_formato and formato_raw:
        # Usar el texto raw si no matchea exactamente (Notion lo rechazara, mejor vacío)
        tipo_formato = ""

    if not verdict:
        print("  [warn] No se pudo parsear el veredicto, usando DESCARTAR.", file=sys.stderr)
        verdict = "DESCARTAR"

    return {
        "verdict": verdict,
        "f1": f1 or "DUDOSO",
        "f2": f2 or "SIN DATOS",
        "f3": f3 or "INCOMPATIBLE",
        "f4": f4,
        "hook": hook,
        "cuerpo": cuerpo,
        "cta": cta,
        "por_que_funciona": porq,
        "engagement_level": engagement,
        "tipo_formato": tipo_formato,
    }


# ── Orquestador ────────────────────────────────────────────────────────────────
def run(auto: bool = False, limit: int = 0, skip_transcribe: bool = False):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{ts}] Leyendo Raw Saves DB -- Verdict:SIN ANALIZAR...")

    saves = get_unanalyzed_saves()
    if limit:
        saves = saves[:limit]
    if not saves:
        print("No hay saves pendientes de analizar.")
        return

    print(f"A analizar: {len(saves)}")
    analyzed = discarded_fast = skipped = 0

    for i, save in enumerate(saves, 1):
        print(f"\n[{i}/{len(saves)}] @{save.get('author','?')} -- {save.get('url','')}")

        # Paso 1: pre-filtro rapido
        proceed, reason = _quick_prefilter(save)
        print(f"  {reason}")

        if not proceed:
            verdict, f1, f2, f3 = "DESCARTAR", "PAGADO", "SIN DATOS", "INCOMPATIBLE"
            f4 = "Lead magnet puro, sin estructura educativa replicable."
            report = (
                "FILTRO 1 - ORIGEN: PAGADO\n" + reason + "\n\n"
                "FILTRO 2 - METRICAS: SIN DATOS\n\n"
                "FILTRO 3 - NICHO: INCOMPATIBLE\n\n"
                "FILTRO 4 - FORMULA: N/A -- descartado en pre-filtro.\n\n"
                "HOOK:\nN/A\n\nCUERPO:\nN/A\n\nCTA:\nN/A\n\n"
                "POR QUE FUNCIONA:\nTrafico pagado, mecanismo de lead magnet sin valor educativo.\n\n"
                "NIVEL DE ENGAGEMENT: SIN DATOS\n\n"
                "TIPO DE FORMATO: N/A\n\n"
                "VEREDICTO: DESCARTAR\nPre-filtro: trafico pagado sin contenido de nicho."
            )
            print("  [fast] -> DESCARTAR (sin API ni transcripcion)")

            if not auto:
                ans = input("  Confirmar DESCARTAR? [s/n/q]: ").strip().lower()
                if ans == "q":
                    break
                if ans != "s":
                    skipped += 1
                    continue

            update_save_verdict(
                save["page_id"], verdict, f1, f2, f3, f4, report,
                engagement_level="SIN DATOS",
            )
            discarded_fast += 1
            analyzed += 1
            continue

        # Paso 2: transcribir con AssemblyAI
        transcript = ""
        if not skip_transcribe and save.get("url"):
            transcript = _transcribe(save["url"])

        # Paso 3: analisis con Claude
        print(f"  [claude] Analizando con {'transcript+caption' if transcript else 'solo caption'}...")
        try:
            report = _analyze(save, transcript)
        except Exception as exc:
            print(f"  [error] Claude API: {exc}", file=sys.stderr)
            skipped += 1
            continue

        parsed = _parse_report(report)
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"ANALISIS @{save.get('author','?')}")
        print(sep)
        print(report)
        print(sep)
        print(f"\nHOOK:     {parsed['hook'][:120]}...")
        print(f"FORMATO:  {parsed['tipo_formato']}")
        print(f"ENGAGEMENT: {parsed['engagement_level']}")
        print(f"VEREDICTO: {parsed['verdict']}")

        if not auto:
            ans = input("\nGuardar en Notion? [s/n/q]: ").strip().lower()
            if ans == "q":
                break
            if ans != "s":
                skipped += 1
                continue

        update_save_verdict(
            save["page_id"],
            parsed["verdict"],
            parsed["f1"],
            parsed["f2"],
            parsed["f3"],
            parsed["f4"],
            report,
            transcript=transcript,
            hook=parsed["hook"],
            cuerpo=parsed["cuerpo"],
            cta=parsed["cta"],
            por_que_funciona=parsed["por_que_funciona"],
            tipo_formato=parsed["tipo_formato"],
            engagement_level=parsed["engagement_level"],
        )
        print(f"  Notion actualizado: {parsed['verdict']} | {parsed['tipo_formato']} | {parsed['engagement_level']}")
        analyzed += 1

    print(f"\nResumen: {analyzed} analizados ({discarded_fast} descartados rapido), {skipped} omitidos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-transcribe", action="store_true")
    args = parser.parse_args()
    run(auto=args.auto, limit=args.limit, skip_transcribe=args.skip_transcribe)
