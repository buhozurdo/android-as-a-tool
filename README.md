# Android-MCP: Control Universal de Android para LLMs

Un entorno aislado de **Android en Docker (`redroid`)** acoplado a un **servidor MCP (Model Context Protocol)** sobre HTTP/SSE. Permite que cualquier agente o LLM opere el dispositivo completo —instalar apps, navegar interfaces, leer notificaciones y ejecutar acciones— sin necesidad de construir integraciones individuales por aplicación.

---

## Arquitectura

```text
┌─────────────────────────┐      HTTP / SSE (MCP)       ┌─────────────────────────────┐
│   Cliente MCP / Agente  │ ◄─────────────────────────► │     Servidor MCP (Python)   │
│ (Claude, Cursor, etc.)  │     http://localhost:8000   │   FastMCP + UI XML Parser   │
└─────────────────────────┘                             └──────────────┬──────────────┘
                                                                       │ ADB (TCP :5555)
                                                                       ▼
                                                        ┌─────────────────────────────┐
                                                        │   Android Virtual (redroid) │
                                                        │  Kernel nativo + /data vol  │
                                                        └─────────────────────────────┘
```

¿Por qué este enfoque?
 * Una sola integración ("Android-as-a-Tool"): El LLM interactúa con cualquier app igual que un humano, eliminando integraciones frágiles por API.
 * Optimizado para tokens: En lugar de enviar capturas de pantalla constantes o XMLs gigantes, el servidor MCP parsea uiautomator dump y devuelve un JSON compacto únicamente con los elementos interactivos y sus coordenadas centrales (cx, cy).
 * Entorno desechable: El estado de Android vive en un volumen Docker (/data), lo que permite resetear el dispositivo a un estado limpio en segundos.
Prerrequisitos
 * Sistema Operativo: Linux (recomendado Ubuntu/Debian) con soporte para módulos de kernel de Android.
 * Docker y Docker Compose v2+.
Habilita los módulos requeridos en el host Linux:
sudo apt install -y linux-modules-extra-$(uname -r)
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux

> Nota para macOS / Windows: Docker en estos sistemas no expone los módulos del kernel necesarios para redroid. En ese caso, levanta un emulador nativo en tu host y ejecuta únicamente el contenedor del servidor MCP apuntando a host.docker.internal:5555.
> 
Inicio Rápido
 * Clona el repositorio:
   git clone [https://github.com/tu-usuario/android-mcp.git](https://github.com/tu-usuario/android-mcp.git)
cd android-mcp

 * Configura las variables de entorno (opcional):
   cp .env.example .env

 * Levanta el stack:
   docker compose up -d --build

 * Verifica que ambos servicios estén activos:
   docker compose logs -f mcp-server

   El servidor MCP quedará disponible en http://localhost:8000/mcp.
Herramientas (Tools) Expuestas por el MCP
Gestión de Aplicaciones
| Tool | Parámetros | Descripción |
|---|---|---|
| install_apk | source: str | Instala un .apk desde una URL o ruta en el volumen /apks. |
| list_apps | third_party_only: bool | Lista los paquetes instalados en el dispositivo. |
| launch_app | package: str | Abre una aplicación directamente por su nombre de paquete. |
| uninstall_app | package: str | Desinstala una aplicación del dispositivo. |
Interacción UI
| Tool | Parámetros | Descripción |
|---|---|---|
| get_screen_elements | clickable_only: bool | Devuelve el árbol UI filtrado en JSON con texto, ID y coordenadas (cx, cy). |
| tap | x: int, y: int | Toca una coordenada específica en pantalla. |
| long_press | x: int, y: int, duration_ms: int | Mantiene presionado un punto en pantalla. |
| type_text | text: str | Escribe texto en el campo activo. |
| swipe | direction: str | Desliza la pantalla (up, down, left, right). |
| press_key | key: str | Envía eventos de sistema (HOME, BACK, ENTER, APP_SWITCH). |
Contexto y Visión
| Tool | Parámetros | Descripción |
|---|---|---|
| take_screenshot | — | Captura la pantalla actual en formato base64 (ideal para WebViews o contenido visual). |
| get_notifications | — | Lee las notificaciones activas del sistema (útil para códigos OTP/2FA). |
Conectar un Cliente MCP
Agrega el servidor remoto a la configuración de tu cliente MCP (por ejemplo, Claude Desktop, Cursor o tu propio orquestador):
{
  "mcpServers": {
    "android-device": {
      "url": "http://localhost:8000/mcp"
    }
  }
}

Instalación de Apps en el Dispositivo
Tienes tres formas de darle acceso a aplicaciones al agente:
 * Volumen local de APKs: Coloca archivos .apk en la carpeta ./apks (montada en /apks dentro del contenedor) y pide al LLM que ejecute install_apk.
 * Aurora Store (Sin cuenta de Google): Instala Aurora Store vía APK para que el LLM pueda buscar y descargar apps directamente desde el catálogo de Play Store de forma anónima.
 * Google Play Store (GApps): Cambia la imagen de redroid en docker-compose.yml por una compilación con GApps/MindTheGapps e inicia sesión una sola vez en el volumen persistente /data.
Estructura del Proyecto
android-mcp/
├── docker-compose.yml      # Orquestación de redroid + servidor MCP
├── .env.example            # Variables de entorno (resolución, DPI, puerto MCP)
├── apks/                   # Carpeta montada para instalación local de APKs
└── mcp-server/
    ├── Dockerfile          # Imagen Python + android-tools-adb
    ├── requirements.txt    # fastmcp, uvicorn, lxml, pillow
    ├── server.py           # Definición de tools MCP
    ├── adb_client.py       # Wrapper de comandos ADB
    └── ui_parser.py        # Compresor de XML (uiautomator) a JSON ligero

Seguridad y Aislamiento
 * No exponer el puerto ADB (5555) al host público: Mantén la comunicación entre mcp-server y redroid estrictamente dentro de la red interna de Docker.
 * Autenticación en MCP: Si despliegas este stack fuera de localhost, coloca un reverse proxy (Nginx, Traefik o Cloudflare Tunnel) con autenticación por Bearer Token o Access.
 * Cuentas de prueba: Utiliza cuentas desechables o de sandbox dentro del dispositivo virtual; nunca credenciales personales críticas.
Licencia
MIT

<FollowUp label="¿Quieres que genere ahora el docker-compose.yml y el código base de mcp-server?" query="Genera el docker-compose.yml, el Dockerfile y el código en Python (server.py, adb_client.py y ui_parser.py) siguiendo exactamente la estructura del README."/>

