# Agent Skills for Android-MCP

This directory stores modular, packaged, and reusable skills that AI agents and human developers can invoke for diagnostics and quality auditing.

---

## 📂 Available Skills

1. **[`code-analyzer`](./code-analyzer/SKILL.md)**:
   - **Command**: `python skills/code-analyzer/scripts/analyze.py`
   - Audits `AGENTS.md` Quality Gates (Gate 1 "Optimal & Acceptable" and Gate 2 "Well-Crafted"): scans for leaked secrets, silent error suppression (`except Exception: pass`), and documented technical debt.

2. **[`android-doctor`](./android-doctor/SKILL.md)**:
   - **Command**: `python skills/android-doctor/scripts/doctor.py`
   - Diagnoses stack health in seconds: ADB binary presence, mock/live mode, display resolution, guardrails engine status, and eval suite readiness.
