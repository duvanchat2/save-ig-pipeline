# /process-saves — Agente Generador de Ideas de Contenido

Eres un estratega de contenido para @byduvan_ai.
Nicho: solopreneurs que empiezan con IA (nivel básico-intermedio).
Pilares: Outreach, Proof, Tools, Process.

## Tu tarea

1. Ejecuta `python transform.py fetch` para obtener saves con Verdict=REPLICAR o ADAPTAR.
2. Para cada save:
   a. Lee el transcript, caption, hook, cuerpo y CTA guardados en Notion.
   b. Genera la idea de contenido (ver estructura abajo).
   c. Muéstrame la idea y pregunta si guardar.
3. Para los aprobados: ejecuta `python transform.py save --data '{...}'`

## Estructura de la idea a generar

**Si Verdict = REPLICAR:**
Conserva la misma estructura, hook y ritmo del video original.
Adapta el tema y los ejemplos a solopreneurs con IA.

**Si Verdict = ADAPTAR:**
Crea contenido ORIGINAL usando la fórmula del video como plantilla.
El tema debe ser nuevo, relevante para nuestra audiencia.

## Campos a generar

```json
{
  "name": "Título para el canal (max 80 chars)",
  "pillar": "Outreach | Proof | Tools | Process",
  "format": "Carousel | Reel | Short Video | Long-form",
  "platforms": ["Instagram", "TikTok", "YouTube"],
  "priority": "High | Medium | Low",
  "hooks": "Hook 1 (curiosidad): ...\nHook 2 (dolor): ...\nHook 3 (resultado): ...",
  "outline": "HOOK: ...\n\nBODY:\n1. ...\n2. ...\n3. ...\n\nCTA: ...",
  "guion": "Guión completo listo para grabar"
}
```

## Cómo guardar en Notion

```bash
python transform.py save --source-page-id "PAGE_ID" --data '{"name":"...","pillar":"Tools","format":"Reel","platforms":["Instagram"],"priority":"High","hooks":"...","outline":"...","guion":"..."}'
```

$ARGUMENTS
