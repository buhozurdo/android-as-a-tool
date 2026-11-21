# Android-MCP: Universal Android Control for LLM Agents

An isolated **Android environment in Docker (`redroid`)** coupled with a **Model Context Protocol (MCP)** server over HTTP/SSE and stdio. It enables any AI agent or LLM (Claude Desktop, Cursor, LangChain, custom frameworks) to operate the entire mobile device—installing apps, navigating UI hierarchies, reading notifications, and executing gestures—without building brittle per-application integrations.

---

## 🏛️ Architecture

```text
┌─────────────────────────┐      HTTP / SSE / Stdio     ┌─────────────────────────────┐
│   MCP Client / Agent    │ ◄─────────────────────────► │     MCP Server (Python)     │
│ (Claude, Cursor, etc.)  │     http://localhost:8000   │  FastMCP + UI Token Parser  │
└─────────────────────────┘                             └──────────────┬──────────────┘
                                                                       │ ADB (TCP :5555)
                                                                       ▼
                                                        ┌─────────────────────────────┐
                                                        │  Virtual Android (redroid)  │
                                                        │  Native Kernel + /data vol  │
                                                        └─────────────────────────────┘
```

### Why this approach?
* **Single Integration ("Android-as-a-Tool")**: The LLM interacts with any application just like a human user, eliminating the need to maintain bespoke REST/GraphQL connectors per service.
* **Token-Optimized UI Parsing**: Instead of sending expensive screenshots or raw 100KB–300KB XML dumps from `uiautomator`, the server parses and compresses the hierarchy into lightweight JSON (~2-5KB) providing actionable elements and exact centroids `(cx, cy)` for zero-math tapping.
* **Disposable Sandbox**: The Android OS state lives in an isolated volume (`/data`), enabling clean resets to a pristine snapshot in seconds.
* **Enterprise Guardrails & Evals**: Built-in anti-SSRF protection for APK installations, ADB shell injection defense, and PII masking for OTP/2FA notification retrieval.

---

## 📋 Prerequisites

* **Operating System**: Linux (recommended Ubuntu/Debian) with Android kernel module support, or macOS / Windows with a native Android emulator or physical device.
* **Docker & Docker Compose v2+** (for redroid virtual stack).

Enable required kernel modules on Linux hosts:
```bash
sudo apt install -y linux-modules-extra-$(uname -r)
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux
```

> **Note for macOS / Windows users:** Docker on macOS and Windows does not expose the Android kernel modules required by redroid. In that case, run a local Android emulator (Android Studio / Genymotion) or connect a physical device via USB, then point the MCP server to `localhost:5555` or your host emulator port.

---

## 🚀 Quickstart

### 1. Clone and Install
```bash
git clone https://github.com/buhozurdo/android-as-a-tool.git
cd android-as-a-tool

# Install package and dependencies
pip install -e ".[mcp,test]"
```

### 2. Run Environment Doctor
Check that your environment, ADB bridge, and security guardrails are operational:
```bash
python skills/android-doctor/scripts/doctor.py
```

### 3. Launch MCP Server
Run locally over standard I/O (compatible with Claude Desktop, Cursor, etc.):
```bash
android-mcp
```
Or start via Docker Compose:
```bash
docker compose up -d --build
```
The MCP server endpoint will be available at `http://localhost:8000/mcp`.

---

## 🛠️ MCP Tools Catalog

### Application Lifecycle

| Tool | Parameters | Description |
|---|---|---|
| `install_apk` | `source: str` | Installs an `.apk` from a local path or validated remote URL (anti-SSRF protected). |
| `list_apps` | `third_party_only: bool` | Lists installed application package names on the device. |
| `launch_app` | `package: str` | Launches an application directly by package name using launcher intent resolution. |
| `uninstall_app` | `package: str` | Uninstalls an application package from the device. |

### UI Navigation & Interaction

| Tool | Parameters | Description |
|---|---|---|
| `get_screen_elements` | `clickable_only: bool` | Returns compressed UI elements JSON with text, resource ID, and `(cx, cy)` centroids. |
| `tap` | `x: int, y: int` | Taps at specific screen coordinates `(x, y)`. |
| `long_press` | `x: int, y: int, duration_ms: int` | Holds a touch at `(x, y)` for `duration_ms` milliseconds. |
| `type_text` | `text: str` | Types text into the currently focused input field with shell escaping. |
| `swipe` | `direction: str` | Swipes the screen in a given direction (`up`, `down`, `left`, `right`). |
| `press_key` | `key: str` | Sends hardware navigation keyevents (`HOME`, `BACK`, `ENTER`, `APP_SWITCH`). |

### Context & Perception

| Tool | Parameters | Description |
|---|---|---|
| `take_screenshot` | — | Captures device display as a Base64-encoded PNG (for WebViews or visual verification). |
| `get_notifications` | — | Reads active system notifications with automated PII redaction and OTP extraction. |

---

## 🔌 Connecting MCP Clients

### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "android-device": {
      "command": "android-mcp",
      "env": {
        "ANDROID_ADB_HOST": "localhost",
        "ANDROID_ADB_PORT": "5555"
      }
    }
  }
}
```

### Remote HTTP / SSE Client (Cursor, Custom Agents)
```json
{
  "mcpServers": {
    "android-device": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## 🛡️ Enterprise Security Guardrails

Android-MCP integrates a zero-dependency safety engine in `guardrails/`:
* **Anti-SSRF URL Validation**: Rejects `install_apk` downloads targeting cloud metadata services (`169.254.169.254`, `metadata.google.internal`), loopback addresses, and private RFC 1918 subnets.
* **ADB Shell Injection Defense**: Intercepts command chaining (`rm -rf`, `reboot`, subshells `$()`, backticks, pipes) in `type_text`.
* **PII Sanitization**: Redacts credit card numbers and personal emails in notifications, keeping 2FA/OTP tokens intact for automated verification flows.
* **JSON Schema Verification**: Enforces valid JSON formatting on structured outputs before dispatching them to LLMs.

---

## 🧪 Evaluation Framework & Benchmarks

Run automated benchmarks to evaluate security, UI centroid math, and OTP retention:

```bash
# Run evaluations and generate Markdown report in analysis-reporte/
python evals/evaluators/eval_runner.py --report
```

---

## 🩺 Agent Skills

Modular skills located in `skills/` allow agents and developers to audit and monitor the environment:
* **`code-analyzer`**: Audits codebase compliance against Quality Gates (Gate 1 "Optimal and Acceptable", Gate 2 "Well-Crafted").
  ```bash
  python skills/code-analyzer/scripts/analyze.py
  ```
* **`android-doctor`**: Performs health checks on ADB connectivity, screen resolution, and guardrails.
  ```bash
  python skills/android-doctor/scripts/doctor.py
  ```

---

## 🧪 Running Tests

Run the full pytest suite (compatible with mock simulation mode without a running device):

```bash
python -m pytest -v
```

---

## 📁 Repository Structure

```text
android-as-a-tool/
├── AGENTS.md               # Quality protocols & agent directives (Gate 1 & Gate 2)
├── RELEASE.md              # Branching strategy, checklist & release notes
├── pyproject.toml          # Modern PEP 517/518 build configuration
├── src/android_mcp/        # Core package
│   ├── adb_client.py       # ADB bridge wrapper with deterministic mock mode
│   ├── server.py           # FastMCP / MCPServer tool registry
│   └── ui_parser.py        # Token-compact UI hierarchy compressor
├── guardrails/             # Security engine (Anti-SSRF, PII, Shell defense)
├── evals/                  # Automated eval benchmarks and runner
├── skills/                 # Agent diagnostic and audit skills
└── tests/                  # Unit and integration test suite
```

---

## 📄 License
[MIT](LICENSE) © BuhoZurdo Team
