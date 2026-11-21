"""
Android-MCP: Universal Android Control for LLM Agents via Model Context Protocol.
"""

from android_mcp.adb_client import ADBClient
from android_mcp.server import AndroidMCPServer, create_server
from android_mcp.ui_parser import UIElement, UIParser

__version__ = "0.3.0"

__all__ = [
    "AndroidMCPServer",
    "create_server",
    "ADBClient",
    "UIParser",
    "UIElement",
    "__version__",
]
