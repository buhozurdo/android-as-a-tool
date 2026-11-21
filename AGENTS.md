# Directivas y Protocolos para Agentes de IA (AGENTS.md)

Este documento contiene las reglas de operación, comportamiento y estándares que todo agente de IA (asistente de código, orquestador o subagente) debe respetar al trabajar en el proyecto **Android-MCP (`android-as-a-tool`)**.

---

## 1. Principios Fundamentales

1. **Seguridad y Aislamiento Primero (Zero Trust & Sandboxing)**:
   - Nunca expongas el puerto ADB (`5555`) a redes públicas o interfaces externas (`0.0.0.0`). Mantén la comunicación estrictamente en localhost o red interna de Docker.
   - Respeta los guardrails de validación de URLs (`anti-ssrf`) al procesar fuentes para `install_apk`. Nunca descargues APKs desde endpoints de metadatos de nube (`169.254.169.254`) o redes privadas no autorizadas.
   - Aplica sanitización de PII al leer notificaciones (`get_notifications`) para evitar que números de cuenta, tarjetas o datos personales se filtren al historial de conversación o logs externos del LLM.
   - Respeta estrictamente los guardrails definidos en `guardrails/`.

2. **Optimización de Tokens y Eficiencia de Contexto**:
   - En lugar de enviar volcados XML completos de `uiautomator` o capturas de pantalla pesadas por defecto, utiliza el parser de compresión (`UIParser`) devolviendo únicamente elementos interactivos y sus centroides `(cx, cy)`.
   - Utiliza capturas de pantalla (`take_screenshot`) únicamente cuando sea estrictamente necesario para WebViews, juegos o verificación visual compleja.

3. **Verificación y Menor Impacto**:
   - Toda modificación debe mantener la suite de pruebas unitarias (`python -m pytest`) al 100% de aprobación.
   - Mantén la compatibilidad con el modo simulado (`mock_mode=True`), de modo que el proyecto pueda probarse de forma continua en entornos headless y pipelines CI/CD sin requerir un emulador Android físico encendido.

---

## 2. Protocolo de Calidad Progresiva: De "Óptimo y Aceptable" a "Bien Hecho"

El desarrollo en este repositorio implementa un **enfoque iterativo en dos fases obligatorias**:

```
[ Requerimiento ] ──▶ [ Fase 1: Óptimo y Aceptable ] ──▶ [ Fase 2: Bien Hecho (Excelencia) ] ──▶ [ Producción ]
                             (MVP Sólido y Limpio)             (Hardening, Tipado y Resiliencia)
```

### Fase 1: Estado "Óptimo y Aceptable" (Gate 1 - Obligatorio antes de avanzar)
*Objetivo: Obtener una solución funcional, simple y verificable sin agregar complejidad innecesaria.*
- **Funcionalidad directa**: Resuelve el comando o herramienta MCP requerida sin efectos secundarios.
- **Simplicidad (YAGNI)**: Prefiere la librería estándar (`urllib`, `xml.etree.ElementTree`, `re`, `subprocess`) antes de dependencias externas innecesarias.
- **Seguridad básica**: Cero secretos o credenciales expuestas en el código fuente.
- **Prueba mínima funcional**: Toda nueva herramienta debe contar con su correspondiente test en `tests/` y caso de prueba en `evals/`.
- **Higiene de código**: Cero código muerto. Si se difiere una optimización, debe marcarse explícitamente con `# DEBT: <motivo>`.

### Fase 2: Estado "Bien Hecho" (Gate 2 - Objetivo Final de Producción)
*Objetivo: Endurecer la solución para alcanzar estándares de excelencia, alta mantenibilidad y resiliencia empresarial.*
- **Tipado estricto y contratos**: Type hints completos en firmas públicas y validación de esquemas JSON / Pydantic.
- **Manejo defensivo de excepciones**: Captura de errores específicos (`subprocess.TimeoutExpired`, `SubprocessError`, `ValueError`); prohibido silenciar excepciones (`except Exception: pass`).
- **Resiliencia en ADB y uiautomator**: Manejo de timeouts configurables (`timeout=15.0`) y reintentos ante pantallas en transición.
- **Validación de entradas y salidas**: Verificación anti-inyección en `type_text` y validación de sintaxis de bounds en `UIParser`.
- **Documentación y Trazabilidad**: Docstrings completos y actualización de [RELEASE.md](file:///c:/Users/rkens/Project/BuhoZurdo/Public/android-as-a-tool/RELEASE.md).

> ⚠️ **Regla de Oro**: Ninguna tarea se entrega en modo "rápido e incompleto". Primero se asegura un estado **Óptimo y Aceptable** y, de inmediato sobre esa base sólida, se refactoriza y endurece hasta alcanzar el estado **Bien Hecho**.

---

## 3. Catálogo de Herramientas MCP Soportadas

| Categoría | Herramienta | Parámetros | Comportamiento Esperado |
| :--- | :--- | :--- | :--- |
| **App Lifecycle** | `install_apk` | `source: str` | Instala APK local o URL validada anti-SSRF. |
| | `list_apps` | `third_party_only: bool` | Lista paquetes con filtro de sistema. |
| | `launch_app` | `package: str` | Lanza app vía intent `monkey` sin requerir MainActivity. |
| | `uninstall_app` | `package: str` | Desinstala paquete de usuario. |
| **UI Interaction** | `get_screen_elements` | `clickable_only: bool` | Devuelve árbol comprimido con centroides `(cx, cy)`. |
| | `tap` | `x: int, y: int` | Toca coordenada calculada de centroide. |
| | `long_press` | `x: int, y: int, duration_ms: int` | Mantiene pulsado para menús contextuales. |
| | `type_text` | `text: str` | Escribe texto con escape de comillas y encoding `%s`. |
| | `swipe` | `direction: str` | Desliza pantalla (`up`, `down`, `left`, `right`). |
| | `press_key` | `key: str` | Envía `HOME`, `BACK`, `ENTER`, `APP_SWITCH`. |
| **Context & Vision** | `take_screenshot` | — | Captura en Base64 PNG solo si es indispensable. |
| | `get_notifications` | — | Extrae OTP/2FA y alertas con sanitización PII. |

---

## 4. Estándares de Commits y Versionado

- Usa mensajes de commit semánticos (`feat:`, `fix:`, `docs:`, `eval:`, `refactor:`, `test:`).
- Sigue el proceso y checklists establecidos en [RELEASE.md](file:///c:/Users/rkens/Project/BuhoZurdo/Public/android-as-a-tool/RELEASE.md) bajo SemVer 2.0.0.
