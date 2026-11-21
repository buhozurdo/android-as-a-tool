# Skills de Agentes para Android-MCP

Esta carpeta almacena habilidades (skills) modulares, empaquetadas y reutilizables que los agentes de IA y desarrolladores pueden invocar para resolver tareas de diagnóstico y auditoría de calidad.

---

## 📂 Skills Disponibles

1. **[`code-analyzer`](./code-analyzer/SKILL.md)**:
   - **Comando**: `python skills/code-analyzer/scripts/analyze.py`
   - Audita Quality Gates del protocolo `AGENTS.md` (Gate 1 "Óptimo y Aceptable" y Gate 2 "Bien Hecho"): escaneo de secretos, antipatrones de silenciamiento de errores y deuda técnica.

2. **[`android-doctor`](./android-doctor/SKILL.md)**:
   - **Comando**: `python skills/android-doctor/scripts/doctor.py`
   - Diagnostica en segundos la salud del entorno: presencia de binario ADB, modo mock/live, resolución física de pantalla, carga de guardrails y datasets de evaluación.
