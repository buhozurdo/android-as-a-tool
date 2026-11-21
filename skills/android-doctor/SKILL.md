---
name: android-doctor
description: Diagnostica el estado del entorno Android-MCP: binario ADB, conexión con redroid o emulador, resolución de pantalla, guardrails y suite de evals.
---

# Android Doctor Skill

## Propósito
Permite al agente o desarrollador comprobar en segundos la salud del stack de automatización móvil antes de iniciar misiones de navegación.

## Diagnósticos Realizados
1. **Binario ADB**: Presencia en `$PATH` o conmutación transparente a `mock_mode`.
2. **Conexión al Dispositivo**: Estado de enlace sobre TCP (`localhost:5555`) o USB.
3. **Resolución de Pantalla**: Detección de dimensiones físicas para cálculo de centroides.
4. **Motor de Guardrails**: Carga de reglas anti-SSRF, sanitización PII e inyección en shell.
5. **Suite de Evals**: Disponibilidad del dataset de pruebas.

## Ejecución
```bash
# Diagnóstico en texto legible
python skills/android-doctor/scripts/doctor.py

# Diagnóstico en formato JSON estructurado
python skills/android-doctor/scripts/doctor.py --json
```
