# Framework de Evaluaciones (Evals) para Android-MCP

El directorio `evals/` contiene benchmarks sistemáticos, conjuntos de datos (datasets) y evaluadores automáticos para medir la seguridad, fidelidad de centroides, robustez anti-SSRF y esquemas JSON del servidor MCP.

---

## 🎯 Objetivos de Evaluación
- **Auditoría de Seguridad y Guardrails**: Confirmar bloqueo de descargas de APKs maliciosas (anti-SSRF hacia metadatos de nube o redes privadas) e inyección en shell ADB.
- **Retención de OTPs & Sanitización PII**: Validar que los códigos de 2FA/OTP se mantengan legibles mientras que tarjetas y correos personales se enmascaran.
- **Fidelidad Estructural de UI**: Confirmar cálculo exacto de centroides `(cx, cy)` y validación sintáctica de JSON.

---

## 🚀 Ejecución de Evaluaciones

```bash
# Ejecución interactiva en consola
python evals/evaluators/eval_runner.py

# Ejecutar y generar reporte Markdown en analysis-reporte/
python evals/evaluators/eval_runner.py --report
```
