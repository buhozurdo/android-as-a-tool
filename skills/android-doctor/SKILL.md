---
name: android-doctor
description: Diagnoses Android-MCP environment health: ADB binary, redroid or emulator connectivity, screen resolution, guardrails, and evals suite.
---

# Android Doctor Skill

## Purpose
Enables agents and developers to verify the health and readiness of the mobile automation stack before initiating interaction workflows.

## Checks Performed
1. **ADB Binary**: Presence in `$PATH` or transparent fallback to `mock_mode`.
2. **Device Connectivity**: Link status over TCP (`localhost:5555`) or USB.
3. **Screen Resolution**: Physical display dimension detection for centroid calculation.
4. **Guardrails Engine**: Operational status and rule counts (anti-SSRF, PII, shell injection).
5. **Evals Suite**: Availability of test datasets.

## Execution
```bash
# Human-readable output
python skills/android-doctor/scripts/doctor.py

# Machine-readable JSON output
python skills/android-doctor/scripts/doctor.py --json
```
