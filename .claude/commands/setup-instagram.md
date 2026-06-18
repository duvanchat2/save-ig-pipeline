# /setup-instagram — Configurar autenticación de Instagram via Chrome

Configura el acceso a Instagram usando las cookies del navegador Chrome.
Usa este comando cuando el usuario no tiene o no puede obtener un token de Meta API.

## Tu tarea

1. Abre Chrome con la extensión de Claude navegando a https://www.instagram.com
2. Verifica si el usuario ya tiene sesión iniciada:
   - Si la página muestra el feed o el perfil → ya está logueado, continúa al paso 3
   - Si muestra pantalla de login → pídele al usuario que inicie sesión manualmente y avísate cuando termine
3. Una vez con sesión activa, extrae las cookies de Instagram desde el navegador
4. Guarda las cookies en el archivo `ig_cookies.json` en la raíz del proyecto con este formato:
   ```json
   [
     {"name": "sessionid", "value": "xxx", "domain": ".instagram.com", "secure": true, "expirationDate": 9999999999},
     {"name": "csrftoken", "value": "xxx", "domain": ".instagram.com", "secure": false, "expirationDate": 9999999999},
     ...
   ]
   ```
5. Ejecuta `python ig_fetcher.py --test` para verificar que las cookies funcionan
6. Si el test muestra `sessionid: SI` y saves encontrados → éxito
7. Agrega `ig_cookies.json` al `.gitignore` si no está ya (contiene datos sensibles)

## Cookies críticas a extraer

Las más importantes son:
- `sessionid` — identifica tu sesión
- `csrftoken` — token de seguridad
- `ds_user_id` — tu user ID de Instagram
- `mid`, `ig_did`, `datr` — cookies de sesión adicionales

## Cómo extraer las cookies con la extensión Chrome

Usa las herramientas del navegador para leer las cookies del dominio `.instagram.com` y guárdalas en formato JSON en `ig_cookies.json`.

## Notas

- Las cookies duran mientras la sesión de Instagram esté activa (semanas o meses)
- Si el sistema empieza a fallar con error 401, repetir este comando
- El sistema detecta automáticamente si usar Meta token o cookies: si existe `ig_cookies.json` y no hay `META_ACCESS_TOKEN`, usa las cookies
- Si existen ambos, prioriza el Meta token
