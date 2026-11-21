# Guardrails & Security Policies for Android-MCP

This directory contains the security policy evaluation engine, validation rules, and sanitization filters tailored for Android device automation by AI agents.

---

## 🛡️ Policy Layers

1. **Input Guardrails (`input-guards.yaml`)**:
   - **Anti-SSRF (`anti-ssrf-apk-url`)**: Blocks APK downloads from cloud metadata endpoints (`169.254.169.254`), `localhost`, loopback, and unauthorized private subnets.
   - **ADB Shell Injection (`adb-shell-injection`)**: Detects destructive command chaining (`rm -rf`, `reboot`, pipes, backticks, subshells) in `type_text` and shell inputs.
   - **Anti-Jailbreak / Prompt Injection**: Detects system directive evasion attempts ("ignore instructions", "DAN mode").
   - **Secrets & PII Masking**: Obfuscates API keys, credit card numbers, and emails before requests are processed.

2. **Output Guardrails (`output-guards.yaml`)**:
   - **Credential Leak Prevention**: Redacts sensitive tokens or passwords before returning data to the agent.
   - **Strict JSON Validation**: Verifies structural syntax of JSON payloads emitted by tools like `get_screen_elements`.
   - **Notification PII Scrubbing**: Masks personal account numbers and emails while preserving OTP/2FA verification codes.

---

## 🚀 Engine Usage

```bash
# Validate APK URL against SSRF
python guardrails/engine.py check-apk "http://169.254.169.254/latest/meta-data/"

# Validate text input against command injection
python guardrails/engine.py check-input "Search text; rm -rf /sdcard"
```
