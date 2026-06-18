# /analyze-saves — Agente Analizador de Contenido Guardado

Analiza los posts guardados de Instagram que están pendientes de revisión en Notion
(Verdict = "SIN ANALIZAR") y aplica los 4 filtros del Agente Analizador para emitir
un veredicto por cada save.

## Cuándo usar este comando

- Después de ejecutar `python sync.py` para analizar los nuevos saves
- Antes de `python transform.py` para asegurarte de que solo pasan saves de calidad
- Cuando quieres revisar manualmente el análisis de cada save antes de guardarlo

## Cómo ejecutar

```bash
# Interactivo — muestra cada reporte y pide confirmación antes de guardar
python analyze.py

# Con límite — analiza máximo N saves
python analyze.py --limit 5

# Automático — guarda todos los veredictos sin pedir confirmación
python analyze.py --auto
```

## Los 4 Filtros

| Filtro | Evalúa | Resultado posible |
|--------|--------|-------------------|
| 1 — Origen | ¿Orgánico o tráfico pagado? | ORGANICO / DUDOSO / PAGADO |
| 2 — Métricas | Save rate, comment rate, like rate | ALTO / NORMAL / BAJO / SIN DATOS |
| 3 — Nicho | Compatibilidad con audiencia @byduvan_ai | COMPATIBLE / ADAPTABLE / INCOMPATIBLE |
| 4 — Fórmula | Hook, estructura, retención, activación | Descripción de fórmula replicable |

## Señales de tráfico pagado (2 o más = PAGADO)
- CTA de comentar una palabra para recibir algo
- Promesa de envío por DM de recurso gratuito
- Lenguaje de urgencia artificial ("antes del X", "solo hoy")
- Caption sin valor educativo, 100% conversión
- Bio de funnel/lead magnet

## Veredictos y qué pasa después

| Veredicto | Avanza a transform.py | Acción |
|-----------|----------------------|--------|
| ✅ REPLICAR | SÍ | Replicar directamente adaptando al canal |
| ⚡ ADAPTAR | SÍ | Tomar estructura, reencuadrar para @byduvan_ai |
| 📐 SOLO ESTRUCTURA | NO | Solo robar el formato para otro tema |
| ❌ DESCARTAR | NO | No procesar |

## Flujo completo

```bash
python sync.py                          # 1. Sincronizar nuevos saves de IG → Notion
python analyze.py --limit 10           # 2. Analizar saves (interactivo)
python transform.py --limit 5          # 3. Transformar REPLICAR/ADAPTAR → ideas
```

O en un solo comando:
```bash
python sync.py && python analyze.py --auto && python transform.py --auto
```

## Ver resultados en Notion

Raw Saves DB: https://www.notion.so/79ed9d0964ab40469ddc2024dbb6493e
Content Ideas DB: https://www.notion.so/2318147aa6b5435ca045d6330ba470a8
