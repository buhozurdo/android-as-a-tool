# Android-MCP Client Integration Cookbooks

This directory contains ready-to-run configurations, client setups, and scripts demonstrating how to integrate **Android-MCP** across popular AI agent frameworks.

---

## 1. Claude Desktop Integration

Add the configuration snippet from [`claude_desktop_config.json`](claude_desktop_config.json) to your Claude Desktop configuration file:

* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
* **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "android": {
      "command": "android-mcp",
      "args": [],
      "env": {
        "ADB_HOST": "localhost",
        "ADB_PORT": "5555",
        "MOCK_MODE": "false"
      }
    }
  }
}
```

Once configured, restart Claude Desktop and prompt:
> *"Inspect the Android screen, open the Settings app, and tell me what Wi-Fi network we are connected to."*

---

## 2. Cursor IDE Integration

Add the configuration snippet from [`cursor_mcp.json`](cursor_mcp.json) to `.cursor/mcp.json` or through Cursor Settings $\rightarrow$ Features $\rightarrow$ MCP Servers:

```json
{
  "mcpServers": {
    "android": {
      "command": "python",
      "args": ["-m", "android_mcp.server"],
      "env": {
        "ADB_HOST": "localhost",
        "ADB_PORT": "5555",
        "MOCK_MODE": "false"
      }
    }
  }
}
```

---

## 3. LangChain & LangGraph Autonomous Agent

Run the automated agent script:
```bash
python examples/langchain_agent.py
```

---

## 4. Local Offline Agent via Ollama

Run local open-weight models (`qwen2.5:0.5b`, `llama3.2`) with zero external API calls:
```bash
python examples/ollama_local_agent.py
```
