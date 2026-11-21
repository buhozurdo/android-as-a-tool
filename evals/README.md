# Evaluation Framework (Evals) for Android-MCP

The `evals/` directory contains systematic benchmarks, test datasets, and automated evaluators designed to assess security guardrails, UI centroid precision, anti-SSRF defenses, and JSON schemas.

---

## 🎯 Evaluation Objectives
- **Security & Guardrails Audit**: Verify blocking of malicious APK downloads (anti-SSRF targeting cloud metadata or private subnets) and ADB shell command injection.
- **OTP Retention & PII Scrubbing**: Ensure 2FA/OTP tokens remain extractable while personal card numbers and emails are masked.
- **UI Structural Fidelity**: Validate exact centroid `(cx, cy)` calculations and JSON schema contracts.

---

## 🚀 Running Evaluations

```bash
# Interactive terminal run
python evals/evaluators/eval_runner.py

# Run and generate Markdown report in analysis-reporte/
python evals/evaluators/eval_runner.py --report
```
