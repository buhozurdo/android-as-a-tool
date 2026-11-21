# Guardrails y Políticas de Seguridad para Android-MCP

Esta carpeta contiene el motor de guardrails y las políticas de sanitización y validación adaptadas para el control de dispositivos Android mediante agentes de IA.

---

## 🛡️ Capas y Reglas

1. **Input Guardrails (`input-guards.yaml`)**:
   - **Anti-SSRF (`anti-ssrf-apk-url`)**: Bloquea descargas de APKs desde endpoints de metadatos de nube (`169.254.169.254`), `localhost` y redes privadas no autorizadas.
   - **Inyección en Shell ADB (`adb-shell-injection`)**: Detecta comandos destructivos encadenados (`rm -rf`, `reboot`, pipes, backticks) en `type_text` o comandos de entrada.
   - **Anti-Jailbreak / Prompt Injection**: Detecta intentos de anular directivas ("ignore instructions", "DAN mode").
   - **Enmascaramiento de Secretos y PII**: Enmascara claves de API, números de tarjeta de crédito y emails antes de procesar la petición.

2. **Output Guardrails (`output-guards.yaml`)**:
   - **Prevención de Fuga de Credenciales**: Redacta tokens o contraseñas antes de responder al agente.
   - **Validación Estricta de JSON**: Comprueba la integridad del JSON emitido por `get_screen_elements`.
   - **Sanitización de Notificaciones**: Oculta cuentas bancarias y datos personales reteniendo códigos OTP/2FA.

---

## 🚀 Uso del Motor

```bash
# Validar URL de APK contra SSRF
python guardrails/engine.py check-apk "http://169.254.169.254/latest/meta-data/"

# Validar input contra inyección de comandos
python guardrails/engine.py check-input "Prueba; rm -rf /data"
```
