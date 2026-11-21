# AI Agent Directives & Operational Protocols (AGENTS.md)

This document establishes the operational rules, behavior guidelines, and development standards that every AI agent (coding assistant, supervisor, or subagent) must adhere to when working on the **Android-MCP (`android-as-a-tool`)** project.

---

## 1. Core Principles

1. **Security & Sandboxing First (Zero Trust)**:
   - Never expose the ADB port (`5555`) to public networks or external interfaces (`0.0.0.0`). Strictly restrict communication to localhost or Docker internal bridge networks.
   - Respect URL validation guardrails (`anti-ssrf`) when handling sources for `install_apk`. Never download APKs from cloud metadata endpoints (`169.254.169.254`) or unauthorized private subnets.
   - Enforce PII sanitization when reading notifications (`get_notifications`) to prevent bank accounts, credit cards, or personal emails from leaking into LLM conversation logs.
   - Strictly honor guardrail policies configured in `guardrails/`.

2. **Token Efficiency & Context Optimization**:
   - Never feed raw `uiautomator` XML dumps or heavy screenshots by default. Always leverage `UIParser` to return token-compressed JSON containing only interactive elements and their centroid coordinates `(cx, cy)`.
   - Use screenshots (`take_screenshot`) only when strictly necessary for WebViews, games, or complex visual verification.

3. **Verification & Minimal Blast Radius**:
   - Every change must maintain the test suite (`python -m pytest`) at 100% pass rate.
   - Preserve deterministic simulation mode (`mock_mode=True`) so the project can be tested reliably in headless environments and CI/CD pipelines without physical emulators.

---

## 2. Progressive Quality Protocol: From "Optimal & Acceptable" to "Well-Crafted"

Development in this repository strictly enforces a **two-phase iterative quality workflow**:

```
[ Requirement ] ──▶ [ Phase 1: Optimal & Acceptable ] ──▶ [ Phase 2: Well-Crafted (Excellence) ] ──▶ [ Production ]
                               (Solid & Clean MVP)               (Hardening, Typing & Resilience)
```

### Phase 1: "Optimal & Acceptable" State (Gate 1 - Mandatory before advancing)
*Goal: Obtain a simple, working, and verifiable solution without speculative complexity.*
- **Direct functionality**: Solves the requested MCP tool or command with zero side effects.
- **Simplicity (YAGNI)**: Favor standard library modules (`urllib`, `xml.etree.ElementTree`, `re`, `subprocess`) before pulling in unneeded external packages.
- **Baseline security**: Zero hardcoded secrets or credentials in source code.
- **Minimal test coverage**: Every new tool must include corresponding unit tests in `tests/` and test cases in `evals/`.
- **Code hygiene**: Zero dead code. If an optimization is deferred, it must be explicitly marked with `# DEBT: <reason>`.

### Phase 2: "Well-Crafted" State (Gate 2 - Production Excellence Target)
*Goal: Harden the implementation to achieve enterprise-grade resilience, maintainability, and security.*
- **Strict typing & contracts**: Complete type annotations on public signatures and validation of JSON / Pydantic schemas.
- **Defensive exception handling**: Explicitly catch domain exceptions (`subprocess.TimeoutExpired`, `SubprocessError`, `ValueError`); silent suppression (`except Exception: pass`) is prohibited.
- **ADB & UI resilience**: Configurable timeouts (`timeout=15.0`) and graceful handling of screen transitions.
- **Input/Output validation**: Anti-injection checks on `type_text` and robust bounds parsing in `UIParser`.
- **Documentation & Traceability**: Clear docstrings and version synchronization in [RELEASE.md](file:///c:/Users/rkens/Project/BuhoZurdo/Public/android-as-a-tool/RELEASE.md).

> ⚠️ **Golden Rule**: No task is delivered in a "quick and incomplete" state. First establish a solid **Optimal & Acceptable** foundation, then immediately refactor and harden it to the **Well-Crafted** standard.

---

## 3. Supported MCP Tools Catalog

| Category | Tool | Parameters | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **App Lifecycle** | `install_apk` | `source: str` | Installs local APK or anti-SSRF validated remote URL. |
| | `list_apps` | `third_party_only: bool` | Lists installed packages with system filter. |
| | `launch_app` | `package: str` | Launches app via launcher intent without requiring MainActivity. |
| | `uninstall_app` | `package: str` | Uninstalls package from device. |
| **UI Interaction** | `get_screen_elements` | `clickable_only: bool` | Returns compressed element tree with `(cx, cy)` centroids. |
| | `tap` | `x: int, y: int` | Taps calculated centroid coordinates. |
| | `long_press` | `x: int, y: int, duration_ms: int` | Long presses for contextual menus. |
| | `type_text` | `text: str` | Types text with quote escaping and `%s` space encoding. |
| | `swipe` | `direction: str` | Swipes display (`up`, `down`, `left`, `right`). |
| | `press_key` | `key: str` | Sends keyevents (`HOME`, `BACK`, `ENTER`, `APP_SWITCH`). |
| **Context & Vision** | `take_screenshot` | — | Base64 PNG capture when visual inspection is necessary. |
| | `get_notifications` | — | Reads system alerts and OTP/2FA with PII redaction. |

---

## 4. Commits & Versioning Standards

- Use semantic commit messages (`feat:`, `fix:`, `docs:`, `eval:`, `refactor:`, `test:`).
- Follow the release checklist and tagging conventions in [RELEASE.md](file:///c:/Users/rkens/Project/BuhoZurdo/Public/android-as-a-tool/RELEASE.md) adhering to SemVer 2.0.0.
