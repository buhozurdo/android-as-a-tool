---
name: code-analyzer
description: Realiza un escaneo estático y auditoría de calidad evaluando Quality Gates: 'Óptimo y Aceptable' (Gate 1) y 'Bien Hecho' (Gate 2).
---

# Code Analyzer Skill

## Propósito
Permite al agente auditor o desarrollador evaluar objetivamente la calidad del código en Android-MCP, asegurando el cumplimiento de los Quality Gates del protocolo `AGENTS.md`.

## Quality Gates Auditadas
1. **Gate 1 - Óptimo y Aceptable**:
   - Cero secretos expuestos o credenciales hardcodeadas.
   - Integridad estructural y lectura sin fallos.
2. **Gate 2 - Bien Hecho**:
   - Cero antipatrones de silenciamiento de errores (`except Exception: pass`).
   - Cero comentarios de `BUG:` sin resolver en código fuente.
   - Seguimiento explícito de deuda técnica documentada (`# DEBT:`).

## Ejecución
```bash
python skills/code-analyzer/scripts/analyze.py
```
