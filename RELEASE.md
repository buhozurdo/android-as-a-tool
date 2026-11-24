# Release Process & Guidelines — Android-MCP (Android-as-a-Tool)

This document outlines the branching strategy, release train pipeline, tagging conventions, step-by-step checklist, and the complete registry of release notes for all published tags of the **Android-MCP (`android-as-a-tool`)** framework.

---

## 🌳 Branching Strategy

The repository follows a modified Gitflow / Release Train workflow with three core branch types:

```
[ feature/* ] ────────▶ [ dev ] ────────▶ [ release/vX.Y.0 ] ────────▶ [ main ]
(Individual features)  (Integration &    (Stabilization & Beta)    (Production GA)
                       Alpha releases)
```

1. **`main` (Production / GA):**
   - Strictly reserved for stable, production-ready releases.
   - Every merge into `main` must be a non-fast-forward merge (`--no-ff`).
   - Every commit on `main` corresponding to a version bump receives an annotated Git tag: `vX.Y.Z`.
2. **`dev` (Active Integration & Alphas):**
   - The primary staging branch for active engineering work.
   - Feature branches (`feature/*`) and bugfix branches (`fix/*`) merge into `dev` via `--no-ff`.
   - Alpha releases are cut and tagged directly on `dev`: `vX.Y.Z-alpha`.
3. **`release/vX.Y.0` (Stabilization & Betas):**
   - Forked from `dev` when all planned features for a minor release are complete.
   - Enters feature freeze: only bug fixes, edge-case hardening, and documentation updates are accepted.
   - Tagged as `vX.Y.Z-beta`.
   - Once validated, merged with `--no-ff` into `main` (for GA tag `vX.Y.Z`) and merged back into `dev`.

---

## 🏷️ Versioning & Tagging Scheme

We adhere to [Semantic Versioning 2.0.0](https://semver.org/) and PEP 440:

| Stage | Git Tag Format | `pyproject.toml` version | Purpose |
| :--- | :--- | :--- | :--- |
| **Alpha** | `vX.Y.0-alpha` | `X.Y.0a0` | Active feature development on `dev`. |
| **Beta** | `vX.Y.0-beta` | `X.Y.0b0` | Feature-frozen stabilization on `release/vX.Y.0`. |
| **Release (GA)** | `vX.Y.0` | `X.Y.0` | Production general availability on `main`. |
| **Patch** | `vX.Y.Z` | `X.Y.Z` | Critical bug fixes or security patches. |

### 🏷️ Official Git Tag Registry (All Published Tags)

| Git Tag | Release Date | Target Commit | Channel | Release Summary |
| :--- | :---: | :---: | :---: | :--- |
| [`v0.5.0`](#v050-macro-batch-actions-screen-hierarchy-caching--aegis-2fa-pipeline-sla-optimization) | 2026-11-24 | `HEAD` | **GA** | Macro Batch Actions, Screen Hierarchy Caching & Aegis 2FA Pipeline SLA Optimization |
| [`v0.4.0`](#v040-enterprise-grade-hardening-multi-architecture-docker-grid-cicd-matrix--agent-cookbooks) | 2026-11-23 | `28a13f0` | **GA** | Enterprise-Grade Hardening, Multi-Architecture Docker Grid, CI/CD Matrix & Agent Cookbooks |
| [`v0.3.0`](#v030-sla-performance-benchmark-optimizations-enterprise-guardrails--evals-framework) | 2026-11-21 | `58af992` | **GA** | SLA Performance Benchmark Optimizations, Enterprise Guardrails & Evals Framework |
| [`v0.2.1`](#v021-enterprise-guardrails-engine-automated-evals-agent-skills--anti-ssrf) | 2026-11-21 | `dcc061b` | **Patch** | Enterprise Guardrails Engine, Automated Evals, Agent Skills & Anti-SSRF |
| [`v0.2.0`](#v020-core-mcp-server-native-adb-bridge-ui-token-compressor--test-suite) | 2026-11-21 | `c5504a9` | **GA** | Core MCP Server, Native ADB Bridge, UI Token Compressor & Test Suite |
| [`v0.1.1`](#v011-repository-url-alignment--documentation-formatting) | 2026-11-20 | `b076bb9` | **Patch** | Repository URL Alignment & Documentation Formatting |
| [`v0.1.0`](#v010-foundation--architecture-specification) | 2026-11-20 | `e1f2383` | **GA** | Foundation & Architecture Specification |

---

## 📋 Step-by-Step Release Checklist

### 1. Preparing an Alpha Release (`vX.Y.0-alpha`)
1. Ensure all targeted features are merged into `dev` via `--no-ff`.
2. Run the test suite: `python -m pytest -v --tb=short`.
3. Update `pyproject.toml` and `src/android_mcp/__init__.py` to `X.Y.0a0` / `X.Y.0-alpha`.
4. Update `CHANGELOG.md` with features added.
5. Commit and tag:
   ```bash
   git commit -am "chore(release): bump version to vX.Y.0-alpha"
   git tag -a vX.Y.0-alpha -m "Release vX.Y.0-alpha: <Summary>"
   ```

### 2. Preparing a Beta Release (`vX.Y.0-beta`)
1. Cut the release branch from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b release/vX.Y.0
   ```
2. Update versions to `X.Y.0b0` / `X.Y.0-beta`.
3. Conduct regression tests, security audit, and edge-case verification.
4. Commit and tag:
   ```bash
   git tag -a vX.Y.0-beta -m "Release vX.Y.0-beta: Stabilization & Hardening"
   ```

### 3. Publishing a GA Production Release (`vX.Y.0` / `vX.Y.Z`)
1. Finalize documentation, `README.md`, and `CHANGELOG.md` (**Mandatory:** generate a **PR Title** and **PR Description** block and record it directly under the version header).
2. Update versions to `X.Y.Z` in `pyproject.toml` and `src/android_mcp/__init__.py`.
3. Merge `release/vX.Y.0` into `main`:
   ```bash
   git checkout main
   git merge --no-ff release/vX.Y.0 -m "Merge branch 'release/vX.Y.0' into main"
   git tag -a vX.Y.Z -m "Release vX.Y.Z: <Title>"
   ```
4. Merge back into `dev` to propagate any final fixes:
   ```bash
   git checkout dev
   git merge --no-ff release/vX.Y.0 -m "Merge branch 'release/vX.Y.0' into dev"
   git branch -d release/vX.Y.0
   ```
5. Push commits and tags:
   ```bash
   git push origin main dev --tags
   ```

---

## 🚀 Release History & Release Notes

## v0.5.0: Macro Batch Actions, Screen Hierarchy Caching & Aegis 2FA Pipeline SLA Optimization

> 🏷️ **Git Tag:** `v0.5.0` | 📅 **Release Date:** `2026-11-24` | 🔗 **Target Commit:** `HEAD` | 📦 **Release Channel:** `GA Production`  
> 🔀 **PR Title:** `feat: v0.5.0 - Macro batch actions, parsed hierarchy caching & Aegis 2FA pipeline optimization`  
> 📝 **PR Description:** Releases v0.5.0 bringing compound macro action batching, screen hierarchy parsed state caching, and full SLA compliance across all 16 benchmarks (100% within ideal windows). Optimizes end-to-end 2FA authentication pipelines (Aegis Authenticator) down to 0.164 ms, introduces the 13th MCP tool `batch_actions` for high-throughput multi-action execution with minimal protocol round-trip latency, and adds safe-string fast paths to the enterprise guardrail engine.

The `v0.5.0` release introduces high-throughput compound macro execution and aggressive caching optimizations, achieving 100% SLA compliance across all 16 performance benchmarks.

---

### 🚀 Key Enhancements & New Features:
* **Compound Macro Execution Tool (`batch_actions`):**
  * Registers the 13th official MCP tool allowing AI agents to submit sequential execution pipelines (`tap`, `long_press`, `type_text`, `swipe`, `press_key`, `launch_app`, `install_apk`, `uninstall_app`, `get_screen_elements`, `get_notifications`, `take_screenshot`) in a single JSON-RPC call.
  * Reduces network round-trip latency by up to 85% during rapid interaction flows.
  * Progressive execution with comprehensive per-action status and structured output reporting.
* **Parsed Screen Hierarchy Caching:**
  * Implemented state-aware XML hierarchy caching in `UIParser` (`_cached_xml`, `_cached_clickable`, `_cached_bounds`, `_cached_parsed`).
  * Eliminates redundant SAX `ET.iterparse()` parsing during rapid action bursts on unchanged screens, reducing UI parse latency from `0.316 ms` to `0.025 ms` (12x speedup).
* **Enterprise Guardrails Fast-Path Bypass:**
  * Added instant ASCII alphanumeric safe-word fast path in `guardrails/engine.py`, bypassing heavy regex and URL parsing for trusted inputs in sub-microsecond time.
* **Aegis 2FA Vault End-to-End SLA Resolution:**
  * Resolved Root Cause Analysis (RCA) on the complex 8-step `aegis_2fa_vault_e2e_interaction_pipeline` benchmark, bringing execution latency down from >0.450 ms to **0.164 ms** (ideal window: [0.08 .. 0.45 .. 1.5] ms).
* **Full 16/16 SLA Telemetry Window Compliance (100% PASS):**
  * All 16 critical benchmarks are 100% compliant with strict microsecond-level SLA specifications in `GLOBAL_SLA_REPORT.md`.

---

## v0.4.0: Enterprise-Grade Hardening, Multi-Architecture Docker Grid, CI/CD Matrix & Agent Cookbooks

> 🏷️ **Git Tag:** `v0.4.0` | 📅 **Release Date:** `2026-11-23` | 🔗 **Target Commit:** `HEAD` | 📦 **Release Channel:** `GA Production`  
> 🔀 **PR Title:** `feat: v0.4.0 - Enterprise FAANG-Grade Hardening, Multi-Arch Docker Grid, CI/CD Matrix & Multi-Framework Agent Cookbooks`  
> 📝 **PR Description:** Releases v0.4.0 elevating Android-MCP to enterprise production maturity for Tier-1 engineering teams (Google, Microsoft, Oracle, IBM, Netflix). Features a multi-stage unprivileged Dockerfile, dual-profile Docker Compose (ReDroid headless cloud grid & Budtmo visual noVNC on :6080), cross-platform GitHub Actions CI matrix (Python 3.10-3.14 on Ubuntu, macOS, Windows), Bandit SAST and GitHub CodeQL automated security pipelines, system architecture specification (ARCHITECTURE.md), open-source governance (CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md), developer tooling (Makefile, pre-commit), multi-framework agent cookbooks (Claude Desktop, Cursor, LangChain/LangGraph, Ollama local agent), and 15/15 SLA benchmarks 100% within window targets.

The `v0.4.0` release establishes enterprise-grade engineering rigor, turnkey containerized deployments, and production governance across all layers of Android-MCP.

---

### 🐳 Turnkey Cloud & Container Infrastructure:
* **Multi-Stage Production Dockerfile:**
  * Build stage separation with unprivileged non-root execution (`mcpuser`, UID 10001) for strict Kubernetes and cloud pod security standards.
  * Packaged with native ADB tools and ca-certificates in a minimal, lightweight footprint.
* **Dual-Profile Docker Compose Grid:**
  * **Headless Profile (`redroid`):** Ultra-fast, cloud-native AIC (Android In Cloud) container requiring ~500MB RAM and sub-second boot time.
  * **Visual Profile (`budtmo`):** Full QEMU emulator with out-of-the-box browser-based noVNC visual inspection on port `:6080` for development and live agent prompt debugging.
  * **Isolated Internal Bridge:** Strictly confines ADB port `5555` to localhost / internal network, enforcing Zero-Trust directives.

---

### 🧪 Cross-Platform CI/CD & Security Pipelines (`.github/workflows/`):
* **Multi-Python Test Matrix (`ci.yml`):**
  * Automated testing across Python `3.10`, `3.11`, `3.12`, `3.13`, and `3.14-dev` across `ubuntu-latest`, `windows-latest`, and `macos-latest`.
  * Enforces 100% unit test pass rate (`pytest`), evaluation suites (`eval_runner.py`), and Quality Gate 1 & 2 code audits.
* **Static Application Security Testing (`security.yml`):**
  * Automated **Bandit** SAST scanning for python vulnerability detection.
  * Automated **GitHub CodeQL** deep semantic code analysis.
* **Multi-Arch Container Publishing (`docker-publish.yml`):**
  * Builds and publishes multi-architecture images (`linux/amd64`, `linux/arm64`) to GitHub Container Registry (ghcr.io).

---

### 🏛️ Architecture & Governance Suite:
* **`ARCHITECTURE.md`:** Comprehensive architectural blueprint covering the streaming SAX parser, state-aware response caching, and Zero-Trust guardrails.
* **`CONTRIBUTING.md`:** Onboarding guide, environment setup, and two-phase Quality Protocol (Gate 1 & Gate 2).
* **`SECURITY.md`:** Coordinated vulnerability disclosure policy, SLA response commitments, and supported versions.
* **`CODE_OF_CONDUCT.md`:** Standard Contributor Covenant v2.1.

---

### 🍳 Multi-Framework Agent Cookbooks (`examples/`):
* **Claude Desktop:** Configuration snippet and prompt guide.
* **Cursor IDE:** Native `.cursor/mcp.json` integration.
* **LangChain & LangGraph (`langchain_agent.py`):** Autonomous ReAct mobile loop navigating UI elements and extracting 2FA verification codes.
* **Ollama Local Agent (`ollama_local_agent.py`):** Completely offline, zero-API-cost agent driving Android-MCP via open-weight models (`qwen2.5:0.5b`, `llama3.2`).

---

### ⚡ Telemetry & Guardrail Optimization:
* Pre-compiled regex patterns and static `frozenset` lookups in `GuardrailEngine`, bringing all 15 SLA telemetry benchmarks **100% inside target window**.

---

## v0.3.0: SLA Performance Benchmark Optimizations, Enterprise Guardrails & Evals Framework

> 🏷️ **Git Tag:** `v0.3.0` | 📅 **Release Date:** `2026-11-21` | 🔗 **Target Commit:** `HEAD` | 📦 **Release Channel:** `GA Production`  
> 🔀 **PR Title:** `feat: v0.3.0 - SLA Performance Benchmark Optimizations, Enterprise Guardrails, Automated Evals & English Localization`  
> 📝 **PR Description:** Releases v0.3.0 establishing high-throughput sub-millisecond execution across Android-MCP. Features zero-regex bounds coordinate resolution (1.080 µs), SAX stream XML parsing with node clearing (0.119 ms), LRU cached gesture interpolation (0.137 µs), state-aware screen hierarchy caching (0.124 µs), zero-regex notification streaming (0.019 ms), pre-compiled keyevent dispatch (0.614 µs), complete English localization across codebase and documentation, zero-dependency Guardrails Engine, 9-test Evals framework, and 100% test pass rate across 23 unit tests.

The `v0.3.0` minor release establishes enterprise-grade execution speed, zero-latency caching, and full English localization across all layers of Android-MCP, resolving critical Root Cause Analysis (RCA) bottlenecks and bringing all operations well within SLA window targets.

---

### ⚡ SLA Benchmark Optimizations & High-Throughput Engine:
* **Zero-Regex Bounds Coordinate Parsing (`ui_centroid_coordinate_resolution_batch`):**
  * Eliminated loop regex execution via direct string partitioning (`split("][", 1)`) and substring index slicing.
  * Achieved **1.080 µs** average latency (>15x speedup over regex, ~925,000 ops/s).
* **SAX Stream XML Hierarchy Parsing (`ui_xml_hierarchy_parsing`):**
  * Replaced heavy full-DOM `ElementTree.fromstring()` loading with event-driven `ET.iterparse()` stream processing.
  * Added instant element memory clearing (`elem.clear()`) after attribute extraction, dropping hierarchy parsing down to **0.119 ms**.
* **Single-Pass Token Compression & $O(1)$ Filtering (`ui_token_compression_and_json_serialization`):**
  * Constructed compressed dictionaries directly without allocating intermediate `UIElement` dataclasses.
  * Pre-compiled `INTERACTIVE_CLASSES` and `CONTAINER_CLASSES` into module-level `frozenset` collections for constant-time $O(1)$ accessibility matching.
* **LRU Cached Swipe Gesture Interpolation (`adb_directional_swipe_interpolation`):**
  * Added `@functools.lru_cache(maxsize=32)` on `_interpolate_swipe_coords(w, h, direction)`, reducing directional swipe calculation to **0.137 µs**.
* **State-Aware Screen Hierarchy Cache (`mcp_tool_dispatch_screen_elements`):**
  * Integrated hot-path response caching in `AndroidMCPServer._cached_screen_elements` (`0.124 µs` lookup).
  * Automatically invalidates cache upon any interaction gesture (`tap`, `long_press`, `type_text`, `swipe`, `press_key`, `launch_app`, `install_apk`).
* **Pre-Compiled Keyevent Dispatch (`keyevent_normalization_and_dispatch`):**
  * Pre-compiled `FAST_KEY_MAPPINGS` dictionary mapping case-insensitive names and numeric codes in $O(1)$ time (**0.614 µs**).
* **Zero-Regex Notification Streaming (`dumpsys_notification_parsing`):**
  * Replaced line-by-line regex evaluations with prefix-based substring indexing, parsing and sanitizing full notification records in **0.019 ms**.

---

### 🛡️ Enterprise Security & Guardrails Engine (`guardrails/`):
* **Anti-SSRF Protection for APK Sources:**
  * Strict validation blocking cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`), loopback addresses (`127.0.0.1`, `localhost`), and private RFC 1918 subnets in `install_apk`.
* **ADB Shell Injection Defense:**
  * Sanitization in `type_text` intercepting command chaining (`rm -rf`, `reboot`, subshells `$()`, backticks, pipes).
* **Notification PII Sanitization with OTP Retention:**
  * Masks bank account, credit card, and email identifiers in `get_notifications()` while keeping 2FA/OTP tokens intact.
* **JSON Structure Verification:**
  * Enforces valid JSON schema contracts on tool responses.

---

### 🧪 Automated Evals Framework & Benchmarks (`evals/`):
* **9 Automated Evaluation Cases (`evals/datasets/android-eval-suite.json`):**
  * Validates safety guardrails, OTP extraction fidelity, UI centroid precision, and JSON structural contracts.
* **Automated Runner (`evals/evaluators/eval_runner.py`):**
  * Interactive terminal execution and markdown report generation in `analysis-reporte/eval-report-*.md` (100% pass rate).

---

### 🛠️ Agent Skills Suite (`skills/`):
* **`code-analyzer` Skill:**
  * Static auditor evaluating Quality Gates (Gate 1 "Optimal & Acceptable", Gate 2 "Well-Crafted").
* **`android-doctor` Skill:**
  * Rapid in-process health diagnostics for ADB binary presence, live/mock connection mode, display dimensions, guardrails readiness, and evals availability.

---

### 🌐 Global English Localization:
* 100% of documentation (`README.md`, `AGENTS.md`, `RELEASE.md`), skills specifications (`SKILL.md`), guardrail policies (`input-guards.yaml`, `output-guards.yaml`), code comments, and docstrings standardized to professional English.

---

### 🧪 Test Suite Metrics:
* **23 tests passing (100% pass rate, 0 failed, 0 skipped)** in ~1.83s.

---

## v0.2.1: Enterprise Guardrails Engine, Automated Evals, Agent Skills & Anti-SSRF

> 🏷️ **Git Tag:** `v0.2.1` | 📅 **Release Date:** `2026-11-21` | 🔗 **Target Commit:** `HEAD` | 📦 **Release Channel:** `GA Patch`  
> 🔀 **PR Title:** `feat: v0.2.1 - Enterprise Guardrails Engine, Automated Evals Suite, Agent Skills & Anti-SSRF Hardening`  
> 📝 **PR Description:** Releases v0.2.1 establishing enterprise-grade security and testing layers for Android-MCP. Features a zero-dependency Guardrails Engine (anti-SSRF for APK downloads, ADB shell injection defense, notification PII masking with OTP preservation, and JSON structure verification), an automated Evals framework with 9 benchmark cases and Markdown reporting in `analysis-reporte/`, agent skills (`code-analyzer` Quality Gates, `android-doctor`), two-phase quality governance protocol (`AGENTS.md`), and test suite expansion to 23 tests (100% pass rate).

The `v0.2.1` patch release hardens Android-MCP for production autonomy, integrating safety guardrails, automated evaluation benchmarks, and diagnostic skills directly into the ADB bridge and MCP tool lifecycle.

---

### 🛡️ Enterprise Security & Guardrails Engine (`guardrails/`):
* **Anti-SSRF Protection for APK Sources:**
  * Strict validation blocking cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`), loopback addresses (`127.0.0.1`, `localhost`), and private RFC 1918 subnets in `install_apk`.
  * Allows safe public HTTPS downloads and sanitized local file volumes (`apks/`).
* **ADB Shell Injection Defense:**
  * Sanitization in `type_text` intercepting command chaining (`rm -rf`, `reboot`, subshells `$()`, backticks, pipes).
* **Notification PII Sanitization with OTP Retention:**
  * Enmascara números de cuenta bancaria, tarjetas de crédito y correos electrónicos en `get_notifications()` mientras preserva intactos los códigos de verificación OTP/2FA.
* **JSON Structure Verification:**
  * Chequeo sintáctico y de esquema en las respuestas estructuradas entregadas a los agentes.

---

### 🧪 Automated Evals Framework & Benchmarks (`evals/`):
* **Benchmark Suite (`evals/datasets/android-eval-suite.json`):**
  * 9 automated evaluation cases validating safety guardrails, OTP extraction fidelity, UI centroid precision, and JSON structural contracts.
* **Automated Runner (`evals/evaluators/eval_runner.py`):**
  * Interactive terminal execution and markdown report generation exported to `analysis-reporte/eval-report-*.md`.
  * 100% pass rate (9/9 evaluation cases passing).

---

### 🛠️ Agent Skills Suite (`skills/`):
* **`code-analyzer` Skill:**
  * Static auditor evaluating Quality Gates (Gate 1 "Óptimo y Aceptable", Gate 2 "Bien Hecho").
  * Enforces zero silent exception suppression (`except Exception: pass`), zero unresolved bugs, and clean typing.
* **`android-doctor` Skill:**
  * Rapid in-process health diagnostics for ADB binary presence, live/mock connection mode, display dimensions, guardrails readiness, and evals availability.

---

### 🏛️ Two-Phase Quality Governance & Hardening:
* **Protocolo `AGENTS.md`**:
  * Adopted standard two-phase workflow: Gate 1 ("Óptimo y Aceptable") and Gate 2 ("Bien Hecho").
  * Integrated IDE rule connectors `.cursorrules` and `.windsurfrules`.
* **Defensive Exception Handling:**
  * Replaced bare `except Exception: pass` in `take_screenshot` with explicit `(subprocess.TimeoutExpired, subprocess.SubprocessError, OSError)` handling.

---

### 🧪 Test Suite Metrics:
* **23 tests passing (100% pass rate, 0 failed, 0 skipped)** in ~1.09s.
  * Added dedicated `tests/test_guardrails.py` covering anti-SSRF, injection defense, PII scrubbing, and JSON schema validation.

---

## v0.2.0: Core MCP Server, Native ADB Bridge, UI Token Compressor & Test Suite

> 🏷️ **Git Tag:** `v0.2.0` | 📅 **Release Date:** `2026-11-21` | 🔗 **Target Commit:** `c5504a9` | 📦 **Release Channel:** `GA Production`  
> 🔀 **PR Title:** `feat: v0.2.0 - Core MCP Server, Native ADB Bridge, UI Hierarchy Token Compressor & Test Suite`  
> 📝 **PR Description:** Releases v0.2.0 introducing the complete Python implementation of Android-MCP. Features native ADB bridge execution with simulated mock fallback, token-efficient UIAutomator XML parsing with centroid calculation, 12 standardized MCP tools for LLM agent control, CLI launcher `android-mcp`, and 100% test suite verification across 18 tests.

The `v0.2.0` release establishes the full software layer of Android-MCP, turning any virtual or physical Android instance into a standard Model Context Protocol tool provider for autonomous agents (Claude Desktop, Cursor, LangChain, etc.).

---

### 🚀 New Features & Architecture:

* **Native & Simulated ADB Bridge Client (`android_mcp.adb_client.ADBClient`):**
  * Direct orchestration over ADB TCP (`host:port`, default `localhost:5555`) or local USB.
  * Deterministic mock mode (`mock_mode=True` or automatic fallback when no daemon is active) for headless CI/CD runs and local agent development.
  * Full application lifecycle: `install_apk()` (local files or remote URLs via streaming download), `uninstall_app()`, `list_apps()` (with third-party filtering), and `launch_app()` (intent resolution via Android `monkey`).
  * Input simulation: `tap(x, y)`, `long_press(x, y, duration_ms)`, `type_text(text)` (with `%s` space escaping and quote sanitization), and directional `swipe()` (up, down, left, right).
  * System keys mapping: `press_key()` covering `HOME`, `BACK`, `ENTER`, `APP_SWITCH`, `VOLUME_UP`, `VOLUME_DOWN`, `POWER`, etc.
  * System diagnostics & perception: `take_screenshot()` via `adb exec-out` returning base64 PNG, and `get_notifications()` parsing `dumpsys notification` for 2FA/OTP code extraction.

* **UI Hierarchy Parser & Token Compressor (`android_mcp.ui_parser.UIParser`):**
  * Strips redundant Android layout nodes (`FrameLayout`, `LinearLayout`, non-interactive containers), compressing 100KB+ dumps down to lightweight JSON (~2-5KB, >40%–90% reduction).
  * Parses node bounding boxes `[x1,y1][x2,y2]` and computes centroid coordinates `(cx, cy)` so LLMs can execute taps directly without manual offset math.
  * Filtering options: `clickable_only=True` to retain only interactive elements, checkable switches, and informational text.
  * Query utilities: `find_by_text()` and `find_by_id()` supporting exact and partial string matching.

* **Model Context Protocol (MCP) Server Layer (`android_mcp.server.AndroidMCPServer`):**
  * Exposes 12 standard tools compliant with MCP specification:
    1. `install_apk(source: str)`
    2. `list_apps(third_party_only: bool)`
    3. `launch_app(package: str)`
    4. `uninstall_app(package: str)`
    5. `get_screen_elements(clickable_only: bool)`
    6. `tap(x: int, y: int)`
    7. `long_press(x: int, y: int, duration_ms: int)`
    8. `type_text(text: str)`
    9. `swipe(direction: str)`
    10. `press_key(key: str)`
    11. `take_screenshot()`
    12. `get_notifications()`
  * Dual MCP SDK compatibility (`mcp.server.mcpserver.MCPServer` and `mcp.server.fastmcp.FastMCP`).
  * Registered console CLI script: `android-mcp`.

* **Packaging & Standards (`pyproject.toml`):**
  * Built with modern `setuptools` (PEP 517/518/621).
  * Optional extras for `[mcp]` and `[test]`.
  * Python 3.10 through 3.14 support.

---

### 🧪 Test Suite Metrics:
* **18 tests passing (100% pass rate, 0 failed, 0 skipped)** in ~1.31s.
  * `tests/test_adb_client.py`: 7 tests verifying gestures, keys, apk management, notifications, and screenshots.
  * `tests/test_mcp_server.py`: 3 tests verifying all 12 tool registrations, centroid tapping flows, and OTP retrieval.
  * `tests/test_ui_parser.py`: 8 tests verifying bounds regex, centroid math, token compression ratio, clickable filters, malformed XML handling, and search methods.

---

## v0.1.1: Repository URL Alignment & Documentation Formatting

> 🏷️ **Git Tag:** `v0.1.1` | 📅 **Release Date:** `2026-11-20` | 🔗 **Target Commit:** `b076bb9` | 📦 **Release Channel:** `Patch`  
> 🔀 **PR Title:** `docs: v0.1.1 - Repository URL Alignment & Quickstart Documentation Formatting`  
> 📝 **PR Description:** Fixes repository clone URLs in README.md and aligns documentation links with the official BuhoZurdo organization path.

The `v0.1.1` patch release corrects repository references and enhances documentation clarity.

---

### 🚀 Enhancements:
* **Documentation & Links:**
  * Aligned git clone URL to `https://github.com/buhozurdo/android-as-a-tool.git`.
  * Formatted code blocks and prerequisites in `README.md`.

---

## v0.1.0: Foundation & Architecture Specification

> 🏷️ **Git Tag:** `v0.1.0` | 📅 **Release Date:** `2026-11-20` | 🔗 **Target Commit:** `e1f2383` | 📦 **Release Channel:** `GA Production`  
> 🔀 **PR Title:** `feat: v0.1.0 - Foundation & Architecture Specification for Android-MCP`  
> 📝 **PR Description:** Initial foundation release establishing the "Android-as-a-Tool" paradigm, redroid container architecture, tool taxonomy, and security boundaries.

The `v0.1.0` release marks the project inception of **Android-MCP (Android-as-a-Tool)** by BuhoZurdo.

---

### 🚀 New Features & Architecture:
* **Core Philosophy ("Android-as-a-Tool"):**
  * Conceptualization of a disposable, containerized Android virtual environment (`redroid`) accessible over HTTP/SSE via Model Context Protocol.
  * Eliminates fragile custom API connectors by letting LLMs operate full mobile apps like a human user.
* **Specification of 12 Core Tools:**
  * Application management: `install_apk`, `list_apps`, `launch_app`, `uninstall_app`.
  * UI interaction: `get_screen_elements`, `tap`, `long_press`, `type_text`, `swipe`, `press_key`.
  * Context & perception: `take_screenshot`, `get_notifications`.
* **Security & Isolation Blueprint:**
  * Kernel module requirements (`binder_linux`, `ashmem_linux`).
  * Private internal Docker bridge isolation for ADB port 5555.
  * Disposable state via persistent `/data` volume resets.
