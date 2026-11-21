"""
Android Model Context Protocol (MCP) Server.
Exposes Android device automation tools over MCP for LLM agents.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

from android_mcp.adb_client import ADBClient
from android_mcp.ui_parser import UIParser


def get_adb_client(mock_mode: bool = False) -> ADBClient:
    host = os.environ.get("ANDROID_ADB_HOST", "localhost")
    port = int(os.environ.get("ANDROID_ADB_PORT", "5555"))
    adb_bin = os.environ.get("ADB_BINARY_PATH", "adb")
    return ADBClient(host=host, port=port, adb_binary=adb_bin, mock_mode=mock_mode)


class AndroidMCPServer:
    """
    Core MCP server implementing universal Android control tools.
    """

    def __init__(self, adb_client: Optional[ADBClient] = None):
        self.adb = adb_client or get_adb_client()
        self._mcp_server = None
        self._setup_mcp()

    def _setup_mcp(self) -> None:
        """Initialize MCP Server with compatibility across mcp 1.x and 2.x."""
        try:
            from mcp.server.mcpserver import MCPServer
            self._mcp_server = MCPServer(name="android-mcp")
            self._register_tools_mcpserver(self._mcp_server)
        except ImportError:
            try:
                from mcp.server.fastmcp import FastMCP
                self._mcp_server = FastMCP(name="android-mcp")
                self._register_tools_mcpserver(self._mcp_server)
            except ImportError:
                # Standalone fallback if mcp package is not installed
                self._mcp_server = None

    def _register_tools_mcpserver(self, server: Any) -> None:
        """Register tools on FastMCP / MCPServer instance."""

        @server.tool()
        def install_apk(source: str) -> str:
            """Install an APK onto the Android device from local file or URL."""
            return self.install_apk(source)

        @server.tool()
        def list_apps(third_party_only: bool = True) -> List[str]:
            """List package names of installed applications on the device."""
            return self.list_apps(third_party_only)

        @server.tool()
        def launch_app(package: str) -> str:
            """Launch an application directly by package name."""
            return self.launch_app(package)

        @server.tool()
        def uninstall_app(package: str) -> str:
            """Uninstall an application by package name."""
            return self.uninstall_app(package)

        @server.tool()
        def get_screen_elements(clickable_only: bool = True) -> Dict[str, Any]:
            """Parse active UI hierarchy and return compact interactive elements with (cx, cy) coordinates."""
            return self.get_screen_elements(clickable_only)

        @server.tool()
        def tap(x: int, y: int) -> str:
            """Tap at specific screen coordinates (x, y)."""
            return self.tap(x, y)

        @server.tool()
        def long_press(x: int, y: int, duration_ms: int = 1000) -> str:
            """Long press at screen coordinates (x, y) for duration_ms milliseconds."""
            return self.long_press(x, y, duration_ms)

        @server.tool()
        def type_text(text: str) -> str:
            """Type text into currently focused input field."""
            return self.type_text(text)

        @server.tool()
        def swipe(direction: str) -> str:
            """Swipe screen in direction ('up', 'down', 'left', 'right')."""
            return self.swipe(direction)

        @server.tool()
        def press_key(key: str) -> str:
            """Press a hardware/navigation key (HOME, BACK, ENTER, APP_SWITCH, etc.)."""
            return self.press_key(key)

        @server.tool()
        def take_screenshot() -> Dict[str, str]:
            """Capture screenshot of device screen as base64-encoded PNG."""
            return self.take_screenshot()

        @server.tool()
        def get_notifications() -> List[Dict[str, Any]]:
            """Read active notifications from the system (for OTP/2FA or status codes)."""
            return self.get_notifications()

    # -----------------------------------------------------------------------
    # Direct Business Logic Methods (Callable via MCP or directly in tests)
    # -----------------------------------------------------------------------

    def install_apk(self, source: str) -> str:
        return self.adb.install_apk(source)

    def list_apps(self, third_party_only: bool = True) -> List[str]:
        return self.adb.list_apps(third_party_only=third_party_only)

    def launch_app(self, package: str) -> str:
        return self.adb.launch_app(package)

    def uninstall_app(self, package: str) -> str:
        return self.adb.uninstall_app(package)

    def get_screen_elements(self, clickable_only: bool = True) -> Dict[str, Any]:
        xml_dump = self.adb.dump_ui_hierarchy()
        res = self.adb.get_resolution()
        return UIParser.parse(xml_dump, clickable_only=clickable_only, screen_bounds=res)

    def tap(self, x: int, y: int) -> str:
        return self.adb.tap(x, y)

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> str:
        return self.adb.long_press(x, y, duration_ms)

    def type_text(self, text: str) -> str:
        return self.adb.type_text(text)

    def swipe(self, direction: str) -> str:
        return self.adb.swipe(direction)

    def press_key(self, key: str) -> str:
        return self.adb.press_key(key)

    def take_screenshot(self) -> Dict[str, str]:
        b64 = self.adb.take_screenshot()
        return {
            "format": "image/png;base64",
            "data": b64,
            "length": str(len(b64)),
        }

    def get_notifications(self) -> List[Dict[str, Any]]:
        return self.adb.get_notifications()

    def run_stdio(self) -> None:
        """Run MCP stdio transport loop."""
        if self._mcp_server:
            self._mcp_server.run()
        else:
            raise RuntimeError("MCP SDK not installed. Please install 'mcp>=1.0.0'.")


def create_server(adb_client: Optional[ADBClient] = None) -> AndroidMCPServer:
    """Factory creating configured AndroidMCPServer."""
    return AndroidMCPServer(adb_client=adb_client)


def main() -> None:
    server = create_server()
    server.run_stdio()


if __name__ == "__main__":
    main()
