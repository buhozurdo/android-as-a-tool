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
        self._cached_screen_elements: Optional[Dict[str, Any]] = None
        self._cached_clickable_only: Optional[bool] = None
        self._setup_mcp()

    def invalidate_cache(self) -> None:
        """Invalidate cached screen hierarchy following interaction gestures."""
        self._cached_screen_elements = None
        self._cached_clickable_only = None

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

        @server.tool()
        def batch_actions(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Execute an ordered sequence of MCP actions in a single compound transaction (Macro Execution)."""
            return self.batch_actions(actions)

    # -----------------------------------------------------------------------
    # Direct Business Logic Methods (Callable via MCP or directly in tests)
    # -----------------------------------------------------------------------

    def install_apk(self, source: str) -> str:
        self.invalidate_cache()
        return self.adb.install_apk(source)

    def list_apps(self, third_party_only: bool = True) -> List[str]:
        return self.adb.list_apps(third_party_only=third_party_only)

    def launch_app(self, package: str) -> str:
        self.invalidate_cache()
        return self.adb.launch_app(package)

    def uninstall_app(self, package: str) -> str:
        self.invalidate_cache()
        return self.adb.uninstall_app(package)

    def get_screen_elements(self, clickable_only: bool = True, force_refresh: bool = False) -> Dict[str, Any]:
        if not force_refresh and self._cached_screen_elements is not None and self._cached_clickable_only == clickable_only:
            return self._cached_screen_elements

        xml_dump = self.adb.dump_ui_hierarchy()
        res = self.adb.get_resolution()
        elements = UIParser.parse(xml_dump, clickable_only=clickable_only, screen_bounds=res)
        self._cached_screen_elements = elements
        self._cached_clickable_only = clickable_only
        return elements

    def tap(self, x: int, y: int) -> str:
        self.invalidate_cache()
        return self.adb.tap(x, y)

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> str:
        self.invalidate_cache()
        return self.adb.long_press(x, y, duration_ms)

    def type_text(self, text: str) -> str:
        self.invalidate_cache()
        return self.adb.type_text(text)

    def swipe(self, direction: str) -> str:
        self.invalidate_cache()
        return self.adb.swipe(direction)

    def press_key(self, key: str) -> str:
        self.invalidate_cache()
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

    def batch_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute an ordered pipeline of MCP actions in a single compound transaction (Macro Execution).
        Supported action types: 'tap', 'long_press', 'type_text', 'swipe', 'press_key',
        'launch_app', 'install_apk', 'uninstall_app', 'get_screen_elements', 'get_notifications', 'take_screenshot'.
        """
        results = []
        for item in actions:
            action_name = item.get("action")
            if not action_name:
                continue
            if action_name == "tap":
                res = self.tap(int(item["x"]), int(item["y"]))
            elif action_name == "type_text":
                res = self.type_text(str(item["text"]))
            elif action_name == "long_press":
                res = self.long_press(int(item["x"]), int(item["y"]), int(item.get("duration_ms", 1000)))
            elif action_name == "swipe":
                res = self.swipe(str(item["direction"]))
            elif action_name == "press_key":
                res = self.press_key(str(item["key"]))
            elif action_name == "launch_app":
                res = self.launch_app(str(item["package"]))
            elif action_name == "install_apk":
                res = self.install_apk(str(item["source"]))
            elif action_name == "uninstall_app":
                res = self.uninstall_app(str(item["package"]))
            elif action_name == "get_screen_elements":
                res = self.get_screen_elements(clickable_only=item.get("clickable_only", True))
            elif action_name == "get_notifications":
                res = self.get_notifications()
            elif action_name == "take_screenshot":
                res = self.take_screenshot()
            else:
                res = f"Unknown action: {action_name}"
            results.append({"action": action_name, "result": res})
        return {"status": "success", "count": len(results), "results": results}

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
