# CLONAR-SISTEMA.md
# Sistema @byduvan_ai — Guía de Clonación Completa
> Cualquier persona que abra este archivo puede reproducir el sistema completo sin hablar con el creador original.
> Generado el 2026-06-18. Documenta lo que **existe**, no lo que debería existir.

---

## ÍNDICE

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Árbol de Carpetas](#4-árbol-de-carpetas)
5. [Contenido de Archivos Clave](#5-contenido-de-archivos-clave)
6. [Estructura de Notion](#6-estructura-de-notion)
7. [Conexiones MCP](#7-conexiones-mcp)
8. [Variables de Entorno](#8-variables-de-entorno)
9. [Instalación Paso a Paso](#9-instalación-paso-a-paso)
10. [Brand DNA del Canal](#10-brand-dna-del-canal)
11. [Operación Diaria](#11-operación-diaria)
12. [Resolución de Problemas](#12-resolución-de-problemas)
13. [Checklist de Verificación](#13-checklist-de-verificación)
14. [Mejoras Futuras Identificadas](#14-mejoras-futuras-identificadas)

---

## 1. RESUMEN EJECUTIVO

**Qué hace este sistema:** Automatiza el proceso de convertir posts guardados de Instagram en ideas de contenido listas para producción, filtradas por relevancia, métricas y calidad narrativa.

**Canal objetivo:** `@byduvan_ai`
**Nicho:** Fundadores solopreneurs que empiezan con IA (nivel básico-intermedio)
**Objetivo:** Educación práctica sobre herramientas IA, productividad y monetización

**Flujo de extremo a extremo:**
```
Instagram (posts guardados)
        ↓ sync.py  [extrae + sube a Notion]
📥 Raw Saves DB (Notion)
        ↓ analyze.py  [4 filtros + Claude AI + AssemblyAI transcripción]
📥 Raw Saves DB (Notion)  ← con Verdict + Hook + Cuerpo + CTA + PorQueFunciona + TipoFormato + EngagementLevel
        ↓ transform.py  [solo REPLICAR/ADAPTAR]
💡 Content Ideas DB (Notion)  ← guión listo para producción
```

**Automatización:**
- `08:00 AM` diario → solo `sync.py` (sincroniza nuevos saves)
- `02:00 AM` diario → pipeline completo: `sync → analyze → transform`

---

## 2. STACK TECNOLÓGICO

| Componente | Tecnología | Versión mínima |
|------------|-----------|----------------|
| Runtime | Python | 3.12 |
| Autenticación Instagram | Meta Graph API (User Access Token) | API v19.0 |
| API Instagram | Meta Graph API (`/saved_media`) | — |
| Transcripción audio | AssemblyAI API | API v2 |
| Descarga de audio | yt-dlp | ≥2024.1.0 |
| Base de datos | Notion (2 DBs) | API v1 |
| Cliente Notion | notion-client pip | ≥2.2.1 |
| LLM análisis | Claude claude-sonnet-4-5 | via Anthropic SDK ≥0.40.0 |
| LLM transformación | Claude claude-sonnet-4-5 | via Anthropic SDK ≥0.40.0 |
| Automatización | Windows Task Scheduler | Windows 11 |
| Variables entorno | python-dotenv | ≥1.0.0 |

**NOTA CRÍTICA — `notion-client`:** Usar versión `>=2.2.1` y `<3.0`. La v3.0 eliminó el método `.query()` que usa `notion_db.py`. El sistema fallará silenciosamente con v3.0+.

**NOTA CRÍTICA — `ig_fetcher.py`:** Usa Meta Graph API con un User Access Token. Requiere permiso `user_saved_media` en el token. Para uso personal (tu propia cuenta como admin de la app), no necesita App Review de Meta.

---

## 3. ARQUITECTURA DEL SISTEMA

### Autenticación Instagram

El sistema usa la **Meta Graph API** con un User Access Token. No depende de cookies ni de proyectos externos. El token se obtiene desde el [Meta Developer Portal](https://developers.facebook.com) y se renueva cada 60 días (token de larga duración). Ver instrucciones completas en la Sección 9.

### Flujo de datos detallado

```
┌─────────────────────────────────────────────────────┐
│                    SYNC.PY                          │
│  1. Lee state.json → IDs ya sincronizados           │
│  2. ig_fetcher.fetch_saved_posts()                  │
│     → get_instagram_cookies() (agent-browser)       │
│     → GET /api/v1/feed/saved/posts/                 │
│  3. Filtra IDs nuevos                               │
│  4. notion_db.add_raw_save() por cada save nuevo    │
│  5. Actualiza state.json                            │
└─────────────────────┬───────────────────────────────┘
                      ↓ Verdict = "SIN ANALIZAR"
┌─────────────────────────────────────────────────────┐
│                   ANALYZE.PY                        │
│  1. notion_db.get_unanalyzed_saves()                │
│  2. Por cada save:                                  │
│     a. Pre-filtro heurístico (regex en caption)     │
│     b. assemblyai_transcriber.transcribe_reel()     │
│        → get_instagram_cookies()                    │
│        → yt-dlp descarga audio                      │
│        → AssemblyAI API upload + poll               │
│     c. Claude claude-sonnet-4-5 (4 filtros + desglose) │
│     d. Parse del reporte → campos estructurados     │
│  3. notion_db.update_save_verdict()                 │
└─────────────────────┬───────────────────────────────┘
                      ↓ Verdict = "REPLICAR" | "ADAPTAR"
┌─────────────────────────────────────────────────────┐
│                  TRANSFORM.PY                       │
│  1. notion_db.get_unprocessed_saves()               │
│     (Processed=false, Verdict IN REPLICAR|ADAPTAR)  │
│  2. Por cada save:                                  │
│     a. Busca transcript (Raw Save → WhisperX local) │
│     b. Claude claude-sonnet-4-5 genera guión/idea   │
│     c. notion_db.add_content_idea()                 │
│     d. notion_db.mark_save_processed()              │
└─────────────────────────────────────────────────────┘
```

### Los 4 Filtros del Agente Analizador

```
F1 — ORIGEN      → ORGANICO | DUDOSO | PAGADO
F2 — METRICAS    → ALTO RENDIMIENTO | RENDIMIENTO NORMAL | BAJO RENDIMIENTO | SIN DATOS
F3 — NICHO       → COMPATIBLE | ADAPTABLE | INCOMPATIBLE
F4 — FORMULA     → Descripción libre de la estructura narrativa

VEREDICTO:
  REPLICAR      → Orgánico + buenas métricas + compatible + fórmula clara
  ADAPTAR       → Pagado o métricas mediocres PERO fórmula/tema valioso
  SOLO ESTRUCTURA → Tema incompatible pero fórmula brillante
  DESCARTAR     → Pagado sin valor, incompatible, fórmula genérica
```

---

## 4. ÁRBOL DE CARPETAS

```
C:\Users\duvan\OneDrive\Documentos\save IG\
│
├── .env                          # Secretos (NO commitear) — ver Sección 8
├── .claude/
│   ├── settings.local.json       # Permisos MCP de Claude Code
│   └── commands/
│       ├── analyze-saves.md      # Skill: /analyze-saves
│       └── process-saves.md      # Skill: /process-saves
│
├── CLAUDE.md                     # System prompt del agente (rol @byduvan_ai)
├── CLONAR-SISTEMA.md             # Este archivo
│
├── analyze.py                    # Fase 2: 4 filtros + Claude + AssemblyAI
├── assemblyai_transcriber.py     # Transcripción via AssemblyAI API
├── config.py                     # Carga de variables de entorno
├── ig_fetcher.py                 # Extracción de saves de Instagram
├── notion_db.py                  # CRUD contra Notion (Raw Saves + Content Ideas)
├── run_pipeline.bat              # Orquestador nocturno (sync→analyze→transform)
├── setup_scheduler.py            # Configura Windows Task Scheduler
├── sync.py                       # Fase 1: Instagram → Notion Raw Saves
├── transform.py                  # Fase 3: Raw Saves → Content Ideas via Claude
│
├── requirements.txt              # Dependencias Python
├── state.json                    # Control de duplicados (media_ids sincronizados)
├── pipeline.log                  # Log de ejecuciones nocturnas automáticas
│
├── notion_client_legacy.py       # [OBSOLETO] Versión anterior, no usar
├── fetch_byduvan_reels.py        # [EXPERIMENTAL] Propósito no documentado
│
├── _ids_to_delete.json           # [TEMPORAL] Usado para script de borrado masivo
├── last5_saves.json              # [TEMPORAL] Archivo de prueba
├── reels_raw.json                # [TEMPORAL] Archivo de prueba
└── saved_test.json               # [TEMPORAL] Archivo de prueba
```

**Dependencia externa (proyecto separado):**
```
C:\Users\duvan\OneDrive\Documentos\scraperinstagram\instagram-transcriber\
└── scraper/
    └── agent_browser_session.py  # Exporta get_instagram_cookies()
```

---

## 5. CONTENIDO DE ARCHIVOS CLAVE

### 5.1 `config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

BASE_DIR = Path(__file__).parent

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_RAW_SAVES_DB_ID = os.getenv("NOTION_RAW_SAVES_DB_ID", "")
NOTION_CONTENT_IDEAS_DB_ID = os.getenv("NOTION_CONTENT_IDEAS_DB_ID", "")

# Instagram
IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_SESSION_FILE = Path(os.getenv("IG_SESSION_FILE", str(BASE_DIR / "ig_session.json")))

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# AssemblyAI
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "34d09095781945cabf5d95a87998d336")

# Pipeline settings
INSTAGRAM_COLLECTIONS = [
    c.strip()
    for c in os.getenv("INSTAGRAM_COLLECTIONS", "Content Ideas,Inspiration").split(",")
    if c.strip()
]
CONTENT_NICHE = os.getenv("CONTENT_NICHE", "beginner AI solo founders")
CONTENT_PILLARS = [
    p.strip()
    for p in os.getenv("CONTENT_PILLARS", "Outreach,Proof,Tools,Process").split(",")
    if p.strip()
]

STATE_FILE = BASE_DIR / "state.json"
```

> **REVISIÓN REQUERIDA:** `ASSEMBLYAI_API_KEY` tiene un valor hardcodeado como fallback. En producción moverlo completamente al `.env` sin valor default.

---

### 5.2 `requirements.txt`

```
instagrapi>=2.1.3
notion-client>=2.2.1
anthropic>=0.40.0
python-dotenv>=1.0.0
requests>=2.32.0
yt-dlp>=2024.1.0
```

> **NOTA:** `instagrapi` aparece en requirements.txt pero `ig_fetcher.py` no lo importa. Fue parte del plan original pero se reemplazó por HTTP directo. No rompe la instalación pero es una dependencia innecesaria.

---

### 5.3 `ig_fetcher.py` — Extracción de Instagram

**Función principal:** `fetch_saved_posts(max_posts=50) -> list[dict]`

**Retorna dicts con:**
```python
{
    "media_id": str,       # ID único del post (usado para deduplicación)
    "url": str,            # https://www.instagram.com/reel/{shortcode}/
    "author": str,         # @username del creador
    "caption": str,        # Texto del caption (max 2000 chars)
    "content_type": str,   # "Post" | "Reel" | "Carousel" | "Video"
    "collection": str,     # "Saved"
    "taken_at": str,       # ISO-8601 datetime
    "views": int,          # view_count / play_count
    "likes": int,          # like_count
    "comments": int,       # comment_count
}
```

**Autenticación:** Usa `get_instagram_cookies()` del proyecto `instagram-transcriber`. No usa usuario/contraseña de Instagram directamente.

**Endpoint:** `GET https://www.instagram.com/api/v1/feed/saved/posts/`

**Test:** `python ig_fetcher.py --test`

---

### 5.4 `sync.py` — Fase 1

```bash
python sync.py                  # Sync normal
python sync.py --dry-run        # Solo muestra, sin escribir en Notion
python sync.py --limit 5        # Máximo 5 saves nuevos
```

**Lógica:**
1. Carga `state.json` → set de `media_id` ya procesados
2. `ig_fetcher.fetch_saved_posts()` → todos los saves
3. Filtra IDs nuevos (no en state)
4. `notion_db.add_raw_save()` por cada nuevo → Verdict=`SIN ANALIZAR`
5. Actualiza `state.json`

---

### 5.5 `analyze.py` — Fase 2 (Agente Analizador)

```bash
python analyze.py               # Interactivo: muestra reporte y pide confirmación
python analyze.py --auto        # Guarda todos los veredictos automáticamente
python analyze.py --limit 5     # Analiza máximo 5 saves
python analyze.py --skip-transcribe  # Solo caption, sin AssemblyAI
```

**Flujo por cada save:**
1. Pre-filtro regex en caption (detecta señales de tráfico pagado)
2. Si pasa: `assemblyai_transcriber.transcribe_reel(url)`
3. Claude `claude-sonnet-4-5` con system prompt de 4 filtros
4. `_parse_report()` extrae campos estructurados via regex
5. `notion_db.update_save_verdict()` escribe en Notion

**Campos que escribe en Notion:**
- `Verdict` (select): REPLICAR / ADAPTAR / SOLO ESTRUCTURA / DESCARTAR
- `F1_Origen` (select): ORGANICO / DUDOSO / PAGADO
- `F2_Metricas` (select): ALTO RENDIMIENTO / RENDIMIENTO NORMAL / BAJO RENDIMIENTO / SIN DATOS
- `F3_Nicho` (select): COMPATIBLE / ADAPTABLE / INCOMPATIBLE
- `AnalysisReport` (text): Reporte completo de Claude
- `Transcript` (text): Transcripción AssemblyAI
- `Hook` (text): Primeras 1-3 oraciones del video
- `Cuerpo` (text): Estructura numerada del desarrollo
- `CTA` (text): Cómo termina el video y qué acción pide
- `PorQueFunciona` (text): Mecanismo psicológico
- `TipoFormato` (select): 9 opciones (ver Sección 6)
- `EngagementLevel` (select): VIRAL / ALTO / NORMAL / BAJO / SIN DATOS

**Pre-filtro rápido (sin API):** Si caption tiene ≥2 señales de tráfico pagado Y no tiene keywords de nicho → DESCARTAR directamente sin llamar a Claude.

**Señales de tráfico pagado detectadas (regex):**
- "comenta [palabra]" / "comment [palabra]"
- "te envío" / "te mando" / "I'll send"
- "antes del [fecha]" / "before [day] [number]"
- "solo hoy" / "only today"
- "link en bio"

---

### 5.6 `assemblyai_transcriber.py` — Transcripción

**Función principal:** `transcribe_reel(url: str) -> str`

**Flujo:**
1. `get_instagram_cookies()` → lista de dicts de cookies
2. `_write_netscape_cookies()` → archivo Netscape en directorio temporal
3. `yt-dlp` descarga audio usando el archivo de cookies (`--cookiefile`)
4. POST a `https://api.assemblyai.com/v2/upload` → `upload_url`
5. POST a `https://api.assemblyai.com/v2/transcript` (con `language_detection: true`)
6. Polling cada 5s hasta `status=completed` (timeout: 300s)

**Dependencia de path hardcodeado:**
```python
_TRANSCRIBER_DIR = Path(r"C:\Users\duvan\OneDrive\Documentos\scraperinstagram\instagram-transcriber")
```
> **REVISIÓN REQUERIDA al clonar:** Este path debe actualizarse al clonar en otra máquina.

---

### 5.7 `notion_db.py` — CRUD Notion

**DBs que maneja:**
| Variable | ID | Uso |
|----------|----|-----|
| `NOTION_RAW_SAVES_DB_ID` | `79ed9d0964ab40469ddc2024dbb6493e` | Raw Saves |
| `NOTION_CONTENT_IDEAS_DB_ID` | `2318147aa6b5435ca045d6330ba470a8` | Content Ideas |
| `TRANSCRIBER_DB_ID` | `b9e16d3210a7425dae31edb577638388` | Transcriber (lectura) |
| `CONTENT_OS_DB_ID` | `5f4358fd9c794640847461294c0aecbb` | Content OS (legacy) |

**Funciones principales:**

| Función | Descripción |
|---------|-------------|
| `add_raw_save(save)` | Crea fila en Raw Saves DB con Verdict=SIN ANALIZAR |
| `get_unanalyzed_saves()` | Retorna saves donde Verdict=SIN ANALIZAR |
| `update_save_verdict(...)` | Actualiza todos los campos del análisis |
| `update_save_transcript(page_id, transcript)` | Solo actualiza Transcript |
| `get_unprocessed_saves()` | Retorna saves donde Processed=false y Verdict IN (REPLICAR,ADAPTAR) |
| `mark_save_processed(page_id)` | Marca Processed=true |
| `add_content_idea(idea)` | Crea fila en Content Ideas DB |
| `get_transcript_by_shortcode(shortcode)` | Busca transcript en Transcriber DB |

**Cliente Notion:** Instancia nueva por llamada (`_client()`). Usa `notion_client.Client(auth=NOTION_TOKEN)`.

**Límite de texto:** 2000 chars por campo `rich_text` (limitación de la API de Notion).

> **NOTA LEGACY en código:** `get_unprocessed_saves()` referencia el campo `F4_Formula` y `Collection` que ya no existen en la DB de Notion. No rompe la ejecución (retornan `""`) pero es código muerto.

---

### 5.8 `transform.py` — Fase 3

```bash
python transform.py             # Interactivo
python transform.py --auto      # Sin confirmación
python transform.py --limit 5   # Máximo 5
python transform.py --skip-transcribe  # No transcribe (usa transcript guardado)
```

**Sistema de prompts:**
- `REPLICAR` → conserva estructura y ritmo del original, adapta tema a @byduvan_ai
- `ADAPTAR` → crea contenido original usando la fórmula del video como plantilla

**Output en Content Ideas DB:**
```json
{
  "name": "Título (max 80 chars)",
  "pillar": "Outreach|Proof|Tools|Process",
  "format": "Carousel|Reel|Short Video|Long-form",
  "platforms": ["Instagram", "TikTok", "YouTube"],
  "priority": "High|Medium|Low",
  "hooks": "Hook 1 (curiosidad):\nHook 2 (dolor):\nHook 3 (resultado):",
  "outline": "HOOK:...\nBODY:\n1...\nCTA:...",
  "guion": "Guión completo listo para grabar"
}
```

> **NOTA:** `transform.py` intenta buscar transcript en `results.json` local del proyecto `instagram-transcriber` y también puede invocar WhisperX. En la práctica actual, el transcript ya está guardado en Notion desde `analyze.py`.

---

### 5.9 `run_pipeline.bat` — Orquestador Nocturno

```bat
SET PROJECT_DIR=C:\Users\duvan\OneDrive\Documentos\save IG
SET PYTHON=C:\Users\duvan\AppData\Local\Programs\Python\Python312\python.exe
SET LOG=%PROJECT_DIR%\pipeline.log
```

**Lógica:**
1. `sync.py` → si falla, aborta el pipeline
2. `analyze.py --auto` → si falla, muestra WARN pero continúa
3. `transform.py --auto` → si falla, muestra WARN

**Log:** Appends a `pipeline.log` con timestamps.

> **REVISIÓN REQUERIDA al clonar:** El path de Python está hardcodeado. Actualizar al path del intérprete en la nueva máquina.

---

### 5.10 `setup_scheduler.py` — Task Scheduler

```bash
python setup_scheduler.py           # Crea/actualiza todas las tareas
python setup_scheduler.py --remove  # Elimina las tareas
python setup_scheduler.py --status  # Ver estado actual
```

**Tareas creadas:**
| Nombre de tarea | Horario | Comando |
|----------------|---------|---------|
| `InstagramSavesSync_AM` | 08:00 diario | `python sync.py` |
| `InstagramSavesSync_PM` | 20:00 diario | `python sync.py` |
| `IGSavesPipeline_Night` | 02:00 diario | `run_pipeline.bat` |

> **NOTA:** La tarea `InstagramSavesSync_PM` (20:00) fue cancelada manualmente en junio 2026. El código en `setup_scheduler.py` aún la define. Si se re-ejecuta `setup_scheduler.py`, la tarea se recreará. Para desactivarla permanentemente, eliminar del array `SYNC_TASKS` en el script.

---

### 5.11 `state.json` — Control de Duplicados

**Estructura:**
```json
{
  "synced_ids": ["3639487123456789", "3648292934567890", "..."]
}
```

Contiene todos los `media_id` de Instagram ya sincronizados con Notion. Si se pierde este archivo, `sync.py` intentará volver a subir todos los saves y creará duplicados en Notion.

> **REVISIÓN REQUERIDA:** El archivo actual en producción tiene los IDs reales. Al clonar, iniciar con `{"synced_ids": []}`.

---

## 6. ESTRUCTURA DE NOTION

### Jerarquía en Notion

```
Sistema @byduvan_ai IG  (página raíz)
└── IG Saver  (página contenedora)
    ├── 📥 Instagram Raw Saves  (DB)  — ID: 79ed9d0964ab40469ddc2024dbb6493e
    └── 💡 Content Ideas — AI Pipeline  (DB)  — ID: 2318147aa6b5435ca045d6330ba470a8
```

---

### 6.0 Plantillas Notion (duplicar antes de instalar)

> Para clonar el sistema, duplica estas plantillas en tu propio workspace de Notion y luego conecta tu integración a las páginas duplicadas.

| Plantilla | Link para duplicar |
|-----------|-------------------|
| 🗂️ IG Saver (contiene ambas DBs) | [Duplicar en Notion](https://principled-typhoon-80d.notion.site/IG-Saver-360b04d2a7d68009b23cea0bd8529e88) |

> Al duplicar obtienes la página "IG Saver" con las dos DBs ya configuradas (📥 Raw Saves + 💡 Content Ideas). Copia los IDs de cada DB desde su URL y pégalos en `.env`.

---

### 6.1 DB: 📥 Instagram Raw Saves

**URL:** https://app.notion.com/p/79ed9d0964ab40469ddc2024dbb6493e

| Propiedad | Tipo | Valores posibles / Notas |
|-----------|------|--------------------------|
| `Name` | title | @username del autor |
| `URL` | url | URL del reel/post |
| `Author` | text | @username |
| `Caption` | text | Texto del caption (max 2000 chars) |
| `ContentType` | select | Post, Reel, Carousel, Video |
| `SavedAt` | date | Fecha de publicación original |
| `Views` | number | view_count del video |
| `Likes` | number | like_count |
| `Comments` | number | comment_count |
| `Verdict` | select | **SIN ANALIZAR** (gris), **REPLICAR** (verde), **ADAPTAR** (amarillo), **SOLO ESTRUCTURA** (naranja), **DESCARTAR** (rojo) |
| `Processed` | checkbox | true = ya pasó a Content Ideas |
| `F1_Origen` | select | ORGANICO (verde), DUDOSO (amarillo), PAGADO (rojo) |
| `F2_Metricas` | select | ALTO RENDIMIENTO (verde), RENDIMIENTO NORMAL (amarillo), BAJO RENDIMIENTO (naranja), SIN DATOS (gris) |
| `F3_Nicho` | select | COMPATIBLE (verde), ADAPTABLE (amarillo), INCOMPATIBLE (rojo) |
| `AnalysisReport` | text | Reporte completo de Claude (max 2000 chars) |
| `Transcript` | text | Transcripción AssemblyAI (max 2000 chars) |
| `Hook` | text | Primeras oraciones del video |
| `Cuerpo` | text | Estructura numerada del desarrollo |
| `CTA` | text | Final del video y acción que pide |
| `PorQueFunciona` | text | Mecanismo psicológico |
| `TipoFormato` | select | Short Reel <30s (azul), Reel largo 30-90s (morado), Carousel (verde), Tutorial en pantalla (naranja), Lista (amarillo), Historia (rosa), Antes-Despues (gris), Comparativa (rojo), Demo de herramienta (default) |
| `EngagementLevel` | select | VIRAL (rojo), ALTO (naranja), NORMAL (amarillo), BAJO (gris), SIN DATOS (default) |

**Vista por defecto:** tabla con columnas Name, Author, Caption, ContentType, Processed, SavedAt, URL, AnalysisReport, F1_Origen, F2_Metricas, F3_Nicho, Transcript, Verdict, Hook, Cuerpo, CTA, PorQueFunciona, TipoFormato.

**Benchmarks de métricas (F2):**
- Comment rate viral ≥ 2% | bueno ≥ 0.5%
- Like rate bueno ≥ 3%
- Save rate excelente ≥ 8%

---

### 6.2 DB: 💡 Content Ideas — AI Pipeline

**URL:** https://app.notion.com/p/2318147aa6b5435ca045d6330ba470a8

| Propiedad | Tipo | Valores posibles / Notas |
|-----------|------|--------------------------|
| `Name` | title | Título de la idea (max 80 chars) |
| `Pillar` | select | Outreach (azul), Proof (verde), Tools (naranja), Process (morado) |
| `Format` | select | Carousel (azul), Reel (rojo), Short Video (naranja), Long-form (morado) |
| `Platform` | multi_select | Instagram, TikTok, YouTube |
| `Priority` | select | High (rojo), Medium (amarillo), Low (gris) |
| `Status` | select | Not started (gris), In progress (amarillo), Done (verde) |
| `HookOptions` | text | 3 variaciones de hook separadas por \n |
| `Outline` | text | HOOK → BODY → CTA estructurado |
| `SourceSaveID` | text | page_id del Raw Save origen |
| `WeekOf` | date | Semana planificada de publicación |

**Vista por defecto:** tabla con todas las columnas.

---

### 6.3 DB auxiliar: Transcriber DB

**ID:** `b9e16d3210a7425dae31edb577638388`

Base de datos del proyecto `instagram-transcriber`. `notion_db.py` la consulta en `get_transcript_by_shortcode()` para buscar transcripciones previas antes de invocar AssemblyAI. Es de solo lectura desde este sistema.

---

## 7. CONEXIONES MCP

Claude Code usa el servidor MCP de Notion para inspección y edición del esquema de bases de datos:

**Servidor:** `mcp__6a0bc57f-19bf-4de0-a303-dec0be6fe825__*`

**Herramientas utilizadas:**
- `notion-fetch` — Leer esquema y contenido de DBs
- `notion-update-page` — Actualizar páginas individuales
- `notion-update-data-source` — Modificar esquema de propiedades
- `notion-create-pages` — Crear páginas en DBs

**Configuración:** En `.claude/settings.local.json`. No requiere configuración manual adicional si el token de Notion está en `.env`.

---

## 8. VARIABLES DE ENTORNO

Crear archivo `.env` en la raíz del proyecto (copiar de `.env.example` y rellenar):

```bash
# ── Notion ──────────────────────────────────────────────────────────────────────
NOTION_TOKEN=secret_xxx
NOTION_RAW_SAVES_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_CONTENT_IDEAS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Meta / Instagram Graph API ───────────────────────────────────────────────────
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxx
IG_USER_ID=123456789012345

# ── APIs de IA ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-xxx
ASSEMBLYAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Configuración del pipeline ───────────────────────────────────────────────────
CONTENT_NICHE=beginner AI solo founders
CONTENT_PILLARS=Outreach,Proof,Tools,Process
```

**Cómo obtener cada credencial:**

| Variable | Dónde obtenerla |
|----------|----------------|
| `NOTION_TOKEN` | notion.com → Settings → Connections → Develop or manage integrations → New integration → "Internal Integration Token" |
| `NOTION_RAW_SAVES_DB_ID` | URL de la DB duplicada: `app.notion.com/p/{ID}` |
| `NOTION_CONTENT_IDEAS_DB_ID` | Igual que arriba |
| `META_ACCESS_TOKEN` | Ver Sección 9 — Paso de configuración Meta API |
| `IG_USER_ID` | `GET https://graph.facebook.com/me?fields=id&access_token=TU_TOKEN` |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `ASSEMBLYAI_API_KEY` | assemblyai.com → Dashboard → API Key |

**Permisos requeridos de la integración Notion:**
- Read content ✓
- Update content ✓
- Insert content ✓
- Conectar la integración a la página "IG Saver" (página contenedora de ambas DBs)

---

## 9. INSTALACIÓN PASO A PASO

### Prerrequisitos
- [ ] Windows 10/11 con Python 3.12+ instalado
- [ ] Cuenta de Meta Developer (gratuita) con una app creada
- [ ] Cuenta de Notion con integración creada
- [ ] API key de Anthropic (con créditos disponibles)
- [ ] API key de AssemblyAI
- [ ] FFmpeg instalado en PATH (opcional, mejora calidad de audio)

### Paso 1 — Clonar / copiar carpeta

```bash
# Copiar toda la carpeta "save IG" a la nueva ubicación
# El path importa: varios archivos tienen paths hardcodeados (ver paso 4)
```

### Paso 2 — Crear entorno virtual e instalar dependencias

```bash
cd "C:\ruta\a\save IG"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Paso 3 — Crear archivo `.env`

```bash
# Copiar la plantilla de la Sección 8 y rellenar con tus credenciales reales
# NUNCA commitear el .env a git
```

### Paso 4 — Configurar Meta API token (Instagram)

El sistema usa la Meta Graph API para acceder a tus posts guardados.

**4a — Crear app en Meta Developer Portal**
1. Ir a [developers.facebook.com](https://developers.facebook.com) → "My Apps" → "Create App"
2. Tipo: **Consumer** (uso personal)
3. Agregar producto: **Instagram** → "Instagram API"

**4b — Generar User Access Token**
1. En el portal → "Tools" → [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Seleccionar tu app en el dropdown
3. Click "Generate Access Token"
4. Agregar permiso: `user_saved_media` (buscar en la lista)
5. Copiar el token generado (válido por 1 hora)

**4c — Convertir a token de larga duración (60 días)**
```bash
curl "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={SHORT_TOKEN}"
```
Copiar el `access_token` de la respuesta → pegarlo como `META_ACCESS_TOKEN` en `.env`

**4d — Obtener tu Instagram User ID**
```bash
curl "https://graph.facebook.com/me?fields=id&access_token=TU_TOKEN_LARGA_DURACION"
```
Copiar el `id` → pegarlo como `IG_USER_ID` en `.env`

**4e — Actualizar paths en `run_pipeline.bat`**
```bat
SET PROJECT_DIR=C:\Users\{TU_USUARIO}\ruta\al\proyecto
SET PYTHON=C:\Users\{TU_USUARIO}\AppData\Local\Programs\Python\Python312\python.exe
```

### Paso 5 — Crear Notion DBs (si clonando desde cero)

Si las DBs no existen aún, crearlas con el mismo esquema documentado en la Sección 6. Luego actualizar los IDs en `.env`.

Si las DBs ya existen (copiando el sistema), solo actualizar los IDs en `.env`.

**Permisos:** Ir a cada DB en Notion → `...` → Connections → Add connection → seleccionar tu integración.

### Paso 6 — Verificar token de Meta

```bash
python ig_fetcher.py --test
```

Debe mostrar:
```
[ig] Token valido — ID: 123456789 | Nombre: Tu Nombre
[ig] Saves obtenidos: 3
  • @autor1 — Reel — https://www.instagram.com/reel/xxx/
```

Si aparece error `code: 190` → token expirado, generar uno nuevo.
Si aparece error `code: 200` → permiso `user_saved_media` no habilitado, revisar Paso 4b.

### Paso 7 — Verificar conexión a Notion

```bash
python sync.py --dry-run --limit 3
```

Debe mostrar los saves que subiría sin escribirlos.

### Paso 8 — Primer sync real

```bash
python sync.py --limit 10
```

Verificar en Notion Raw Saves DB que aparecieron filas con Verdict=SIN ANALIZAR.

### Paso 9 — Primer análisis

```bash
python analyze.py --limit 3
```

Verificar que se llenaron los campos F1, F2, F3, Hook, Cuerpo, CTA, PorQueFunciona, TipoFormato, EngagementLevel.

> **Nota:** Si Anthropic API no tiene créditos, `analyze.py` fallará en el paso de Claude. Usar `--skip-transcribe` no ayuda; el problema es la llamada a la API de Claude, no la transcripción.

### Paso 10 — Configurar automatización nocturna

```bash
# Ejecutar como Administrador
python setup_scheduler.py
python setup_scheduler.py --status
```

Verificar que las 3 tareas aparecen como "Ready" en Task Scheduler.

---

## 10. BRAND DNA DEL CANAL

**Canal:** `@byduvan_ai`

```
QUIÉN SOY:    Fundador solopreneur que usa IA para construir y escalar
PARA QUIÉN:   Emprendedores individuales que están comenzando con IA
NIVEL:        Básico-intermedio (no desarrolladores, sí curiosos activos)

PILARES DE CONTENIDO:
  • Outreach   — Cómo conseguir clientes usando IA
  • Proof      — Resultados, casos de estudio, antes/después
  • Tools      — Herramientas IA específicas con demostración práctica
  • Process    — Flujos, sistemas, automatizaciones del día a día

TONO:        Educativo, directo, aspiracional (no corporativo, no técnico avanzado)
FORMATO:     Reels cortos (<30s preferido), Carruseles, Tutoriales en pantalla
PLATAFORMAS: Instagram (principal), TikTok, YouTube

CRITERIO DE SELECCIÓN DE CONTENIDO A REPLICAR:
  ✓ Orgánico (sin tráfico pagado)
  ✓ Métricas por encima de benchmark (like rate ≥3%, comment rate ≥0.5%)
  ✓ Tema aplicable a solopreneurs con IA
  ✓ Fórmula narrativa clara y replicable
```

---

## 11. OPERACIÓN DIARIA

### Comandos principales

```bash
# Sincronizar nuevos saves de Instagram → Notion
python sync.py

# Analizar saves pendientes (interactivo)
python analyze.py --limit 5

# Analizar todos automáticamente (para uso en automatización)
python analyze.py --auto

# Transformar saves aprobados → ideas de contenido (interactivo)
python transform.py --limit 3

# Flujo completo manual
python sync.py && python analyze.py --auto && python transform.py --auto
```

### Skills de Claude Code

```
/analyze-saves   → Ejecuta analyze.py con contexto del agente analizador
/process-saves   → Ejecuta transform.py con contexto de estratega de contenido
```

### Flujo automático nocturno (2 AM)

```
Task Scheduler → run_pipeline.bat → sync.py → analyze.py --auto → transform.py --auto → pipeline.log
```

### Ver resultados

| Qué ver | Dónde |
|---------|-------|
| Saves nuevos sin analizar | Notion Raw Saves, filtrar Verdict = SIN ANALIZAR |
| Saves listos para producción | Notion Content Ideas |
| Log de ejecución nocturna | `pipeline.log` en la raíz del proyecto |
| Estado del Task Scheduler | `python setup_scheduler.py --status` |

### Ciclo semanal recomendado

1. Revisar `pipeline.log` → verificar que la automatización corrió sin errores
2. Abrir Notion Content Ideas → revisar ideas generadas esta semana
3. Asignar `WeekOf` a las ideas que se van a producir
4. Cambiar `Status` de Done a las publicadas

---

## 12. RESOLUCIÓN DE PROBLEMAS

### Error: `code: 190` — Token expirado

**Causa:** El `META_ACCESS_TOKEN` tiene 60 días de vida y expiró.
**Solución:** Volver a Paso 4b-4c de la instalación: generar short token en Graph API Explorer y convertir a long-lived token. Actualizar en `.env`.

---

### Error: `code: 200` — Permiso denegado

**Causa:** El token no tiene el permiso `user_saved_media`.
**Solución:** En Graph API Explorer, regenerar el token asegurándose de marcar `user_saved_media` en la lista de permisos.

---

### Error: `code: 100` — IG_USER_ID incorrecto

**Causa:** El `IG_USER_ID` en `.env` no corresponde a tu cuenta de Instagram.
**Solución:** Ejecutar `curl "https://graph.facebook.com/me?fields=id&access_token=TU_TOKEN"` y usar ese ID.

---

### Error: `notion_client.errors.APIResponseError: Could not find database`

**Causa 1:** `NOTION_TOKEN` incorrecto o expirado.
**Causa 2:** La integración no tiene acceso a las páginas de Notion.
**Solución:** Verificar token en `.env`. Ir a las páginas padre en Notion → Connections → agregar la integración.

---

### Error: `anthropic.BadRequestError: 400`

**Causa:** Créditos de Anthropic API agotados.
**Solución:** Recargar créditos en console.anthropic.com. `analyze.py` y `transform.py` requieren Claude para funcionar.
**Workaround temporal:** Usar `--skip-transcribe` en analyze.py (solo evita AssemblyAI, no resuelve el problema de créditos de Claude).

---

### Error: AssemblyAI devuelve `status=error`

**Causas comunes:**
1. Audio de Instagram no descargado (yt-dlp falló)
2. Cookies de Instagram vencidas
3. ASSEMBLYAI_API_KEY incorrecta

**Debug:**
```bash
python analyze.py --limit 1
# Observar el output de [assemblyai] para ver en qué paso falla
```

---

### `pipeline.log` muestra "ERROR en sync.py - abortando pipeline"

**Causa:** `sync.py` retornó código de error (usualmente problema de conexión a Instagram).
**Solución:** `python ig_fetcher.py --test` para diagnosticar.

---

### Windows Task Scheduler no ejecuta el pipeline

**Verificar:**
1. `python setup_scheduler.py --status` → la tarea debe estar "Ready"
2. El usuario de la tarea tiene permiso de ejecución
3. El path de Python en `run_pipeline.bat` es correcto para la máquina actual
4. La máquina está encendida a las 2 AM (no en suspensión profunda)

**Activar ejecución aunque el equipo esté dormido:**
En Task Scheduler → propiedades de la tarea → Conditions → desmarcar "Start the task only if the computer is on AC power"

---

### Duplicados en Notion Raw Saves

**Causa:** Se perdió o corrompió `state.json`.
**Solución:**
1. Exportar todos los `media_id` actuales de Notion
2. Reconstruir `state.json`:
```json
{"synced_ids": ["id1", "id2", ...]}
```

---

### `notion-client` falla con AttributeError en `.query()`

**Causa:** Versión de `notion-client` ≥3.0 instalada (eliminó el método `.query()`).
**Solución:** `pip install "notion-client>=2.2.1,<3.0"`

---

### UnicodeEncodeError en Windows al ejecutar scripts

**Causa:** Terminal Windows con encoding cp1252 no puede mostrar emojis.
**Solución:** Ejecutar con: `set PYTHONIOENCODING=utf-8 && python analyze.py`

---

## 13. CHECKLIST DE VERIFICACIÓN

### Verificación de instalación nueva

- [ ] `python ig_fetcher.py --test` → sessionid: SI
- [ ] `python sync.py --dry-run --limit 3` → muestra saves sin error
- [ ] `python sync.py --limit 5` → aparecen filas en Notion Raw Saves
- [ ] `python analyze.py --limit 1` → Verdict se escribe en Notion
- [ ] Notion Raw Saves: Hook, Cuerpo, CTA, TipoFormato, EngagementLevel se llenaron
- [ ] `python transform.py --limit 1` → aparece idea en Content Ideas DB
- [ ] `python setup_scheduler.py --status` → 3 tareas activas

### Verificación de sistema en producción

- [ ] `pipeline.log` tiene entradas recientes (últimas 24h)
- [ ] No hay errores "ERROR en sync.py" en el log
- [ ] Notion Raw Saves: hay filas nuevas con Verdict=SIN ANALIZAR o con veredicto asignado
- [ ] Notion Content Ideas: hay ideas con Status=Not started pendientes de producción
- [ ] `ig_fetcher.py --test` sigue respondiendo con sessionid: SI

---

## 14. MEJORAS FUTURAS IDENTIFICADAS

### Técnicas

1. **Externalizar paths hardcodeados** — `_TRANSCRIBER_DIR` en `ig_fetcher.py`, `assemblyai_transcriber.py` y `transform.py` deberían ser variables de entorno (`TRANSCRIBER_DIR`).

2. **Eliminar dependencias obsoletas de `notion_db.py`** — Los campos `F4_Formula` y `Collection` ya no existen en la DB pero siguen referenciados en `get_unprocessed_saves()`. Limpiar.

3. **Remover `instagrapi` de `requirements.txt`** — Ya no se usa. Peso innecesario.

4. **Logs estructurados** — `pipeline.log` es texto plano. Considerar JSON Lines para análisis programático.

5. **Retry logic en AssemblyAI** — Si falla la descarga de audio, no hay reintentos. Agregar 2-3 reintentos con backoff.

6. **Separar ASSEMBLYAI_API_KEY del fallback hardcodeado** — El default en `config.py` expone la clave en el código fuente.

7. **Tarea `InstagramSavesSync_PM` en código** — Fue cancelada pero sigue en `setup_scheduler.py`. Si se re-corre el script, se recrea. Eliminar del array o convertir en variable de configuración.

### Funcionales

8. **Dashboard de métricas** — No hay forma de ver qué porcentaje de saves termina siendo REPLICAR vs DESCARTAR. Agregar conteo semanal en log.

9. **Notificación cuando hay ideas listas** — El pipeline corre silenciosamente a las 2 AM. Agregar notificación (email/Telegram) cuando transform.py genera ≥1 idea nueva.

10. **Soporte para Carouseles** — `ig_fetcher.py` detecta el tipo Carousel pero no extrae imágenes. `analyze.py` los transcribe como si fueran Reels (solo audio). Para carouseles, el análisis debería basarse solo en caption.

11. **Límite de text extendido** — El límite de 2000 chars de Notion trunca transcripts largos. Considerar guardar en páginas separadas con bloques.

---

## ESTADÍSTICAS DEL DOCUMENTO

| Métrica | Valor |
|---------|-------|
| Archivos documentados | 14 (9 activos, 4 temporales/obsoletos, 1 skill) |
| Bases de datos Notion documentadas | 3 (2 activas + 1 auxiliar) |
| Variables de entorno | 9 |
| Secciones REVISIÓN REQUERIDA | 4 |
| Mejoras futuras identificadas | 11 |
| Tareas de automatización | 3 (2 sync + 1 pipeline) |
| Generado | 2026-06-18 |

---

*Fin del documento. Para reproducir el sistema completo, seguir la Sección 9 en orden.*
