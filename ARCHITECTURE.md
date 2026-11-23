# System Architecture & Technical Specification — Android-MCP

This document provides a comprehensive technical breakdown of the **Android-MCP (`android-as-a-tool`)** framework. It details the internal pipeline, token compression algorithms, sub-millisecond telemetry caches, and the Zero-Trust security model.

---

## 1. High-Level System Architecture

Android-MCP bridges autonomous AI agents (Claude Desktop, Cursor, LangChain, Ollama) with real or containerized Android devices via standard Model Context Protocol (MCP) and raw Android Debug Bridge (ADB) protocols:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AI Agent Ecosystem                              │
│       (Claude 3.7 / GPT-4o / Cursor / Windsurf / LangGraph / Ollama)        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Standard MCP Protocol (JSON-RPC stdio)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Android-MCP Runtime Server (`FastMCP`)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tool Registry (12 Core Tools):                                             │
│   • App Lifecycle: install_apk, list_apps, launch_app, uninstall_app        │
│   • UI Interaction: get_screen_elements, tap, long_press, type_text, swipe  │
│   • Context & Vision: take_screenshot, get_notifications, press_key         │
├──────────────────────────────────────┬──────────────────────────────────────┤
│  ⚡ Sub-Millisecond Optimizations    │  🛡️ Enterprise Guardrails Engine    │
│   • State-Aware Hierarchy Cache      │   • Anti-SSRF URL Policy (RFC 1918)  │
│   • LRU Swipe Interpolation          │   • ADB Shell Injection Defense      │
│   • Pre-compiled Keyevent Table      │   • PII Sanitizer & OTP Extractor    │
│   • Zero-Regex Bounds Parser         │   • Output JSON Schema Validator     │
└──────────────────┬───────────────────┴───────────────────┬──────────────────┘
                   │                                       │
                   ▼                                       ▼
┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
│     Streaming UI Parser (SAX)        │  │       Native ADB Client           │
├──────────────────────────────────────┤  ├───────────────────────────────────┤
│ • Event-driven `ET.iterparse()`      │  │ • Native subprocess / bridge      │
│ • Immediate `elem.clear()` memory    │  │ • Zero companion daemon on device│
│ • Token compression (-96% XML tokens)│  │ • Deterministic mock mode for CI  │
└──────────────────┬───────────────────┘  └──────────────────┬────────────────┘
                   │                                         │
                   └────────────────────┬────────────────────┘
                                        │ Raw ADB Commands (TCP 5555 / USB)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Android Device Environment                          │
│  • Cloud Headless Container: ReDroid (AIC - Android In Cloud)               │
│  • Visual Browser Container: Budtmo (QEMU + noVNC Web UI on :6080)          │
│  • Physical Device / Google Android Studio AVD via USB or Wi-Fi             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Pillars

### 2.1. Zero-Daemon Device Footprint
Unlike legacy frameworks (e.g. Appium or `uiautomator2`), Android-MCP **installs zero companion APKs or background daemons on the Android target**.
* Standard ADB protocol execution via native subcommands (`shell input tap`, `shell dumpsys`, `shell uiautomator dump /dev/tty`).
* Preserves device battery, eliminates memory leaks on physical devices, and ensures compatibility across Android 9 through Android 15.

### 2.2. Streaming Token Compression Engine (`UIParser`)
Raw Android XML dumps (`uiautomator dump`) often reach 150KB - 300KB per screen, causing severe LLM context pollution and excessive token latency.
* **Event-driven SAX streaming**: Employs `xml.etree.ElementTree.iterparse()` over raw byte streams rather than in-memory DOM representations.
* **Immediate node purging**: Calls `elem.clear()` immediately upon processing child tags, maintaining $O(1)$ memory consumption (< 800 KB RAM peak).
* **Zero-Regex Bounds Coordinate Slicing**: Replaced iterative regex matches with direct string index partitioning (`split("][", 1)`), reducing bounds resolution down to **1.080 µs** (>15x faster than regex).
* **Token Compression Efficiency**: Achieves **66.7% to 96.1% reduction** in context token count, returning only interactive elements with centroid coordinates `(cx, cy)`.

### 2.3. State-Aware Response Caching
* **Screen Hierarchy Cache (`_cached_screen_elements`)**: Consecutive inspections by the LLM (e.g. `get_screen_elements`) resolve in **0.0009 ms (~0.9 µs)** without touching the device.
* **Auto-Invalidation State Machine**: The cache is automatically purged whenever an interactive gesture or package modification occurs (`tap`, `long_press`, `type_text`, `swipe`, `press_key`, `launch_app`, `install_apk`, `uninstall_app`).

---

## 3. Zero-Trust Enterprise Security Model

```
Agent Input ──▶ [ Guardrails Engine ] ──▶ [ Policy Validation ] ──▶ Execution
                       │                          │
                       ├── Anti-SSRF Check        ├── Blocks 169.254.169.254 & RFC 1918
                       ├── Shell Sanitization     ├── Intercepts '; rm -rf' & subshells
                       └── PII Masking Engine     └── Redacts credit cards/emails (Preserves OTP)
```

1. **Anti-SSRF Protection for APK Sources**:
   - Blocks cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`), loopback interfaces (`127.0.0.1`, `localhost`), and private RFC 1918 networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
   - Uses pre-compiled regex and static `frozenset` lookups ($O(1)$ evaluation time: **~0.055 ms**).

2. **Command Injection Interception**:
   - Validates all input text strings in `type_text` to prevent shell chaining (`rm -rf`, `reboot`, `$()`, backticks, pipes).

3. **Real-Time PII Sanitization with OTP Preservation**:
   - Redacts personal identifiers, email addresses, and credit card numbers from incoming notification streams.
   - Preserves 4-to-8 digit 2FA/OTP tokens (`\b\d{4,8}\b`), enabling verification workflows without leaking private client data into LLM chat logs.

---

## 4. Benchmark & SLA Performance Matrix

Microbenchmark results on CPython 3.14 (15/15 tests within target SLA window):

| Operation | Latency (Mean) | Throughput (ops/s) | Strategy |
| :--- | :---: | :---: | :--- |
| `mcp_tool_dispatch_screen_elements` | **0.0009 ms** | 1,111,111 | State-aware hierarchy cache |
| `adb_command_formatting_and_sanitization`| **0.0034 ms** | 294,117 | Pre-compiled string escape |
| `adb_directional_swipe_interpolation` | **0.0047 ms** | 212,765 | `@functools.lru_cache` |
| `mcp_tool_dispatch_tap` | **0.0056 ms** | 178,571 | Direct ADB dispatch |
| `ui_element_search_by_text_and_id` | **0.0200 ms** | 50,000 | In-memory indexed lookup |
| `keyevent_normalization_and_dispatch` | **0.0240 ms** | 41,666 | Pre-compiled dispatch table |
| `dumpsys_notification_parsing` | **0.0584 ms** | 17,123 | Sequential prefix slicing |
| `guardrail_command_injection_detection` | **0.0503 ms** | 19,880 | Fast substring filter |
| `guardrail_anti_ssrf_url_validation` | **0.0552 ms** | 18,115 | $O(1)$ frozenset domain check |
| `guardrail_pii_sanitization_and_masking` | **0.1364 ms** | 7,331 | Pre-compiled regex pattern mask |
| `ui_xml_hierarchy_parsing` | **0.3164 ms** | 3,160 | SAX stream `ET.iterparse()` |
| `ui_token_compression_and_json_serialization` | **0.4805 ms** | 2,081 | Direct single-pass compression |
| `ui_centroid_coordinate_resolution_batch` | **0.5739 ms** | 1,742 | 100 bounds parsed in 5.7 µs ea |
