---
name: code-analyzer
description: Performs static quality gate audits checking Gate 1 ('Optimal & Acceptable') and Gate 2 ('Well-Crafted').
---

# Code Analyzer Skill

## Purpose
Enables code reviewers and AI agents to objectively assess codebase quality against the two-phase quality protocol in `AGENTS.md`.

## Audited Quality Gates
1. **Gate 1 - Optimal & Acceptable**:
   - Zero exposed secrets or hardcoded credentials.
   - Structural integrity and readable files.
2. **Gate 2 - Well-Crafted**:
   - Zero silent exception suppression (`except Exception: pass`).
   - Zero unresolved `BUG:` comments in source code.
   - Explicit tracking of documented technical debt (`# DEBT:`).

## Execution
```bash
python skills/code-analyzer/scripts/analyze.py
```
