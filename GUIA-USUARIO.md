# GUÍA DE INSTALACIÓN COMPLETA
# Sistema de Análisis de Contenido Guardado — @byduvan_ai
> Sigue este documento de arriba a abajo. No saltes pasos.
> Tiempo estimado de instalación: 45–60 minutos.

---

## ¿QUÉ HACE ESTE SISTEMA?

Cada noche mientras duermes, el sistema automáticamente:
1. Entra a tu Instagram y descarga todos los posts que guardaste
2. Analiza cada post con inteligencia artificial (4 filtros)
3. Transcribe el audio de cada reel
4. Decide si el contenido vale la pena replicar o adaptar
5. Genera un guión listo para grabar y lo guarda en Notion

Al despertar encuentras ideas de contenido listas con hook, cuerpo y CTA.

---

## LO QUE VAS A NECESITAR

Antes de empezar, asegúrate de tener:

- [ ] Computador con Windows 10 u 11
- [ ] Cuenta de Instagram (la tuya, donde guardas contenido)
- [ ] Cuenta de Notion (gratuita sirve)
- [ ] Cuenta de Meta for Developers (gratuita)
- [ ] Cuenta de Anthropic con créditos (Claude API)
- [ ] Cuenta de AssemblyAI (gratuita tiene créditos de prueba)
- [ ] Cuenta de GitHub (para descargar el código)

---

## PARTE 1 — DESCARGAR EL CÓDIGO

### Paso 1.1 — Instalar Python

1. Ir a [python.org/downloads](https://www.python.org/downloads/)
2. Descargar Python **3.12** (o la versión más reciente)
3. Al instalar, **marcar la casilla "Add Python to PATH"** antes de hacer click en Install
4. Verificar: abrir CMD y escribir `python --version` → debe mostrar `Python 3.12.x`

### Paso 1.2 — Descargar el proyecto

1. Ir a [github.com/duvanchat2/save-ig-pipeline](https://github.com/duvanchat2/save-ig-pipeline)
2. Click en el botón verde **"Code"**
3. Click en **"Download ZIP"**
4. Extraer el ZIP en una carpeta fácil de recordar, por ejemplo:
   ```
   C:\save-ig-pipeline\
   ```
5. Abrir esa carpeta — debe contener archivos como `sync.py`, `analyze.py`, `config.py`, etc.

### Paso 1.3 — Instalar dependencias de Python

1. Abrir CMD (buscador de Windows → escribir "cmd" → Enter)
2. Navegar a la carpeta del proyecto:
   ```
   cd C:\save-ig-pipeline
   ```
3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Esperar a que termine. Debe decir "Successfully installed..." al final.

### Paso 1.4 — Instalar FFmpeg (opcional pero recomendado)

FFmpeg mejora la calidad del audio para la transcripción.

1. Ir a [ffmpeg.org/download.html](https://ffmpeg.org/download.html) → Windows → descargar la versión "essentials"
2. Extraer el ZIP, por ejemplo en `C:\ffmpeg\`
3. Agregar al PATH:
   - Buscador de Windows → "Variables de entorno" → "Editar las variables de entorno del sistema"
   - Click en "Variables de entorno"
   - En "Variables del sistema", seleccionar "Path" → "Editar"
   - "Nuevo" → escribir `C:\ffmpeg\bin`
   - Aceptar todo
4. Verificar: abrir CMD nuevo y escribir `ffmpeg -version`

---

## PARTE 2 — CONFIGURAR NOTION

### Paso 2.1 — Duplicar la plantilla

1. Ir a este link: [Duplicar plantilla Notion](https://principled-typhoon-80d.notion.site/IG-Saver-360b04d2a7d68009b23cea0bd8529e88)
2. En la esquina superior derecha, click en **"Duplicate"**
3. Seleccionar tu workspace de Notion
4. La página "IG Saver" aparecerá en tu Notion con las dos bases de datos ya configuradas

### Paso 2.2 — Copiar los IDs de las bases de datos

Necesitas el ID de cada base de datos. Lo encuentras en la URL.

**Raw Saves DB:**
1. En tu Notion, abrir "📥 Instagram Raw Saves"
2. La URL se verá así: `https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. Copiar los 32 caracteres después del último `/` — ese es el ID

**Content Ideas DB:**
1. Abrir "💡 Content Ideas — AI Pipeline"
2. Copiar el ID de la misma forma

Guarda ambos IDs, los necesitarás en el Paso 5.

### Paso 2.3 — Crear integración de Notion

1. Ir a [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click en **"+ New integration"**
3. Nombre: `save-ig-pipeline` (o el que quieras)
4. Workspace: seleccionar el tuyo
5. Capacidades: dejar todas marcadas (Read, Update, Insert)
6. Click en **"Submit"**
7. Copiar el **"Internal Integration Token"** (empieza con `secret_...`)

### Paso 2.4 — Conectar la integración a las páginas

Esto es importante: la integración debe tener acceso a las páginas.

1. En Notion, abrir la página **"IG Saver"** (la que duplicaste)
2. Click en los tres puntos `...` (esquina superior derecha)
3. Click en **"Connections"** → **"Add connections"**
4. Buscar y seleccionar `save-ig-pipeline` (la integración que creaste)
5. Click en **"Confirm"**

La integración ahora tiene acceso a la página y a todas sus bases de datos.

---

## PARTE 3 — CONFIGURAR META API (INSTAGRAM)

Esta es la parte más larga pero solo la haces una vez.

### Paso 3.1 — Crear cuenta de desarrollador Meta

1. Ir a [developers.facebook.com](https://developers.facebook.com)
2. Iniciar sesión con tu cuenta de Facebook
3. Si es la primera vez, aceptar los términos de desarrollador

### Paso 3.2 — Crear una app

1. Click en **"My Apps"** → **"Create App"**
2. Seleccionar tipo: **"Consumer"** → Next
3. App name: `save-ig-pipeline` (o cualquier nombre)
4. App contact email: tu email
5. Click en **"Create app"**

### Paso 3.3 — Agregar Instagram a la app

1. En el dashboard de tu app, buscar **"Instagram"** en los productos disponibles
2. Click en **"Set up"** debajo de Instagram
3. Seleccionar **"Instagram API with Instagram Login"**

### Paso 3.4 — Generar el token de acceso

1. En el menú lateral ir a **"Tools"** → **"Graph API Explorer"**
   - Link directo: [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. En el dropdown de la app (arriba a la derecha), seleccionar **tu app**
3. En "User or Page", seleccionar **"Get User Access Token"**
4. En la lista de permisos, buscar y marcar:
   - `user_saved_media` ✓
   - `instagram_basic` ✓
5. Click en **"Generate Access Token"**
6. Autorizar cuando te pida permisos
7. Copiar el token que aparece (válido solo por 1 hora — lo convertiremos a 60 días en el siguiente paso)

### Paso 3.5 — Convertir a token de larga duración (60 días)

Necesitas el App ID y el App Secret de tu app:
1. En el dashboard → **"Settings"** → **"Basic"**
2. Copiar **"App ID"** y **"App Secret"** (click en "Show" para ver el secret)

Ahora en CMD, ejecutar (reemplazando los valores):
```
curl "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=TU_APP_ID&client_secret=TU_APP_SECRET&fb_exchange_token=TU_TOKEN_CORTO"
```

Recibirás una respuesta así:
```json
{"access_token":"EAAxxxxx...","token_type":"bearer","expires_in":5183944}
```

Copiar el `access_token` largo — este es tu `META_ACCESS_TOKEN`.

### Paso 3.6 — Obtener tu Instagram User ID

En CMD ejecutar (reemplazando tu token):
```
curl "https://graph.facebook.com/me?fields=id,name&access_token=TU_TOKEN_LARGO"
```

Respuesta:
```json
{"id":"123456789012345","name":"Tu Nombre"}
```

Copiar el `id` numérico — este es tu `IG_USER_ID`.

---

## PARTE 4 — OBTENER CLAVES DE API

### Paso 4.1 — Claude API (Anthropic)

1. Ir a [console.anthropic.com](https://console.anthropic.com)
2. Crear cuenta o iniciar sesión
3. Ir a **"API Keys"** → **"Create Key"**
4. Nombre: `save-ig-pipeline`
5. Copiar la clave (empieza con `sk-ant-...`)
6. Agregar créditos: ir a **"Billing"** → comprar créditos (mínimo $5 USD para empezar)

> El sistema usa ~$0.01–0.03 por save analizado. Con $5 puedes analizar ~200–500 saves.

### Paso 4.2 — AssemblyAI (transcripción)

1. Ir a [assemblyai.com](https://www.assemblyai.com)
2. Click en **"Get Started Free"**
3. Crear cuenta
4. En el dashboard, copiar el **"API Key"**
5. La cuenta gratuita incluye $50 en créditos de prueba

---

## PARTE 5 — CREAR EL ARCHIVO DE CONFIGURACIÓN

### Paso 5.1 — Crear el archivo .env

1. Abrir la carpeta del proyecto (`C:\save-ig-pipeline\`)
2. Buscar el archivo `.env.example`
3. Hacer una copia y renombrarla exactamente como `.env` (sin el `.example`)

   > En Windows Explorer puede que no veas el `.` al inicio. Abre el archivo con el Bloc de Notas haciendo click derecho → "Abrir con" → Bloc de Notas.

4. Rellenar cada línea con tus datos:

```
NOTION_TOKEN=secret_xxx                          ← del Paso 2.3
NOTION_RAW_SAVES_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxx  ← del Paso 2.2
NOTION_CONTENT_IDEAS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxx ← del Paso 2.2

META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxx            ← del Paso 3.5
IG_USER_ID=123456789012345                       ← del Paso 3.6

ANTHROPIC_API_KEY=sk-ant-api03-xxx               ← del Paso 4.1
ASSEMBLYAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx      ← del Paso 4.2

CONTENT_NICHE=beginner AI solo founders
CONTENT_PILLARS=Outreach,Proof,Tools,Process
```

5. Guardar el archivo

### Paso 5.2 — Actualizar run_pipeline.bat

1. Abrir `run_pipeline.bat` con el Bloc de Notas
2. Cambiar las primeras líneas con tu información:
   ```
   SET PROJECT_DIR=C:\save-ig-pipeline
   SET PYTHON=C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python312\python.exe
   ```
   Para encontrar el path exacto de Python: abrir CMD y escribir `where python`

3. Guardar

---

## PARTE 6 — VERIFICAR QUE TODO FUNCIONA

Abre CMD y navega al proyecto:
```
cd C:\save-ig-pipeline
```

### Verificación 1 — Token de Instagram

```
python ig_fetcher.py --test
```

✅ Correcto:
```
[ig] Token valido — ID: 123456789 | Nombre: Tu Nombre
[ig] Saves obtenidos: 3
  • @autor1 — Reel — https://www.instagram.com/reel/xxx/
```

❌ Error `code: 190` → Token expirado, repetir Paso 3.4 y 3.5
❌ Error `code: 200` → Falta el permiso `user_saved_media`, repetir Paso 3.4

---

### Verificación 2 — Sync a Notion

```
python sync.py --limit 5
```

✅ Correcto:
```
Iniciando sync -> Raw Saves DB...
Posts guardados: 50 total | 5 nuevos
  + @autor1 (Reel) -> Verdict:SIN ANALIZAR -> https://www.notion.so/xxx
```

Revisar en Notion que aparecieron filas nuevas en "📥 Instagram Raw Saves".

❌ Error `Could not find database` → Revisar Paso 2.4 (conectar integración a la página)

---

### Verificación 3 — Análisis de 1 save

```
python analyze.py --limit 1
```

Verás el análisis completo, al final pregunta:
```
Guardar en Notion? [s/n/q]:
```
Escribir `s` y Enter.

✅ Correcto: en Notion aparecen los campos F1, F2, F3, Hook, Cuerpo, CTA, Veredicto rellenos.

❌ Error de Anthropic API → Verificar créditos en console.anthropic.com y la clave en `.env`

---

### Verificación 4 — Transcripción de audio

Si el analyze anterior fue exitoso, deberías ver líneas como:
```
[assemblyai] Descargando audio de https://www.instagram.com/reel/xxx/...
[assemblyai] Subiendo 1234 KB a AssemblyAI...
[assemblyai] Transcript OK -- 87 palabras.
```

❌ Error en descarga → El reel puede ser privado. El análisis continúa solo con el caption.

---

### Verificación 5 — Transformar a idea de contenido

Solo funciona si hay saves con Veredicto = REPLICAR o ADAPTAR.

```
python transform.py --limit 1
```

✅ Correcto: aparece una idea en "💡 Content Ideas — AI Pipeline" en Notion.

---

## PARTE 7 — CONFIGURAR AUTOMATIZACIÓN NOCTURNA

El sistema corre solo a las 2 AM todos los días.

### Paso 7.1 — Crear las tareas automáticas

**Ejecutar CMD como Administrador:**
1. Buscador de Windows → escribir "cmd"
2. Click derecho → **"Ejecutar como administrador"**
3. Navegar al proyecto:
   ```
   cd C:\save-ig-pipeline
   ```
4. Ejecutar:
   ```
   python setup_scheduler.py
   ```

✅ Correcto:
```
Sync 08:00  [InstagramSavesSync_AM]: OK
Pipeline 02:00 [IGSavesPipeline_Night]: OK
```

### Paso 7.2 — Verificar las tareas

```
python setup_scheduler.py --status
```

Debe mostrar las tareas con estado "Ready".

### Paso 7.3 — Configurar para que corra con la PC en suspensión

1. Buscador de Windows → **"Task Scheduler"** (Programador de tareas)
2. En el panel izquierdo, expandir "Task Scheduler Library"
3. Buscar la tarea **"IGSavesPipeline_Night"**
4. Click derecho → **"Properties"**
5. Pestaña **"Conditions"**
6. Desmarcar **"Start the task only if the computer is on AC power"**
7. Marcar **"Wake the computer to run this task"**
8. Click OK

Repetir para **"InstagramSavesSync_AM"**.

---

## PARTE 8 — USO DIARIO

### Ver resultados cada mañana

1. Abrir Notion → **"💡 Content Ideas — AI Pipeline"**
2. Los posts nuevos con Status = "Not started" son ideas listas para producir
3. Revisar: Hook, Outline, formato recomendado

### Ejecutar manualmente cuando quieras

```bash
# Solo sincronizar nuevos saves
python sync.py

# Analizar saves pendientes (te pregunta antes de guardar)
python analyze.py --limit 5

# Analizar todo automáticamente
python analyze.py --auto

# Convertir ideas aprobadas en guiones
python transform.py

# Todo de una vez
python sync.py && python analyze.py --auto && python transform.py --auto
```

### Ver el log de la automatización nocturna

Abrir el archivo `pipeline.log` en la carpeta del proyecto. Muestra qué pasó cada noche.

---

## PARTE 9 — RENOVAR EL TOKEN DE INSTAGRAM (CADA 60 DÍAS)

El token de Meta expira cada 60 días. Cuando empiece a fallar:

1. Ir a [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. Generar nuevo token corto (Paso 3.4)
3. Convertir a token largo (Paso 3.5)
4. Abrir el archivo `.env` → reemplazar el valor de `META_ACCESS_TOKEN`
5. Guardar

---

## PARTE 10 — CÓMO USAR CON CLAUDE CODE (OPCIONAL)

Si usas Claude Code (el asistente de IA en terminal), tienes comandos especiales:

### Analizar saves guardados

```
/analyze-saves
```

Claude analiza los posts pendientes usando los 4 filtros del sistema.

### Procesar ideas de contenido

```
/process-saves
```

Claude transforma los saves aprobados en guiones listos para grabar.

---

## PERSONALIZAR EL SISTEMA PARA TU CANAL

Para adaptar el sistema a tu nicho, editar el archivo `.env`:

```
# Describe quién es tu audiencia
CONTENT_NICHE=tu descripción de audiencia

# Los 4 temas principales de tu canal (separados por coma)
CONTENT_PILLARS=Pilar1,Pilar2,Pilar3,Pilar4
```

Ejemplo para un canal de finanzas personales:
```
CONTENT_NICHE=millennials que quieren salir de deudas y construir patrimonio
CONTENT_PILLARS=Ahorro,Inversión,Mentalidad,Deuda
```

---

## RESOLUCIÓN DE PROBLEMAS FRECUENTES

| Problema | Solución |
|----------|----------|
| `python: command not found` | Reinstalar Python marcando "Add to PATH" |
| Token expirado (error 190) | Repetir Partes 3.4 y 3.5, actualizar `.env` |
| Sin permiso (error 200) | En Graph API Explorer, agregar `user_saved_media` al token |
| Notion no guarda datos | Verificar que conectaste la integración a la página (Paso 2.4) |
| No transcribe audio | Normal para reels privados, el análisis usa solo el caption |
| Sin créditos de Claude | Recargar en console.anthropic.com → Billing |
| Pipeline no corre en la noche | Verificar Task Scheduler, desmarcar "Solo con AC power" |

---

## ESTRUCTURA DE COSTOS ESTIMADOS

| Servicio | Costo | Consumo estimado |
|----------|-------|-----------------|
| Claude API | ~$0.01–0.03 por save analizado | $3–5/mes (100 saves) |
| AssemblyAI | ~$0.37/hora de audio | $1–3/mes |
| Notion | Gratis (plan básico) | — |
| Meta API | Gratis | — |
| GitHub | Gratis | — |

**Total estimado: $4–8 USD/mes** para un uso normal de 100-150 saves analizados.

---

## CHECKLIST FINAL

- [ ] Python instalado y en PATH
- [ ] Proyecto descargado en `C:\save-ig-pipeline\`
- [ ] `pip install -r requirements.txt` completado
- [ ] Plantilla de Notion duplicada
- [ ] IDs de las 2 DBs copiados
- [ ] Integración de Notion creada y conectada a "IG Saver"
- [ ] App de Meta creada con producto Instagram
- [ ] Token de Meta generado (60 días)
- [ ] Instagram User ID obtenido
- [ ] API key de Anthropic con créditos
- [ ] API key de AssemblyAI
- [ ] Archivo `.env` creado con todos los valores
- [ ] `run_pipeline.bat` actualizado con tus paths
- [ ] `python ig_fetcher.py --test` → Token valido
- [ ] `python sync.py --limit 5` → Saves en Notion
- [ ] `python analyze.py --limit 1` → Análisis en Notion
- [ ] `python setup_scheduler.py` → Tareas creadas
- [ ] Task Scheduler configurado para despertar la PC

---

*¿Problemas? Abrir un issue en [github.com/duvanchat2/save-ig-pipeline/issues](https://github.com/duvanchat2/save-ig-pipeline/issues)*
