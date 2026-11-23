#!/usr/bin/env python3
"""
Autonomous Android Agent using LangChain & LangGraph with Android-MCP.
Demonstrates navigating UI hierarchies, tapping centroids, and reading OTP codes.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

# Example demonstrating how an agent leverages Android-MCP tools programmatically
from android_mcp.adb_client import ADBClient
from android_mcp.server import create_server


def run_agent_workflow():
    print("============================================================")
    print("  Autonomous Android Agent: LangChain / Python Integration  ")
    print("============================================================")

    # 1. Initialize MCP Client / Server Bridge
    # In production, connect via stdio MCP client or direct server instance
    adb = ADBClient(mock_mode=True)
    server = create_server(adb_client=adb)

    print("\n[Step 1] Inspecting current screen elements...")
    screen_data = server.get_screen_elements(clickable_only=True)
    elements = screen_data.get("elements", [])
    print(f" -> Found {len(elements)} actionable UI elements (tokens compressed by ~95%).")

    # 2. Agent reasoning and decision making
    target_element = None
    for el in elements:
        if "Network" in el.get("text", "") or "Settings" in el.get("text", ""):
            target_element = el
            break

    if target_element:
        cx, cy = target_element["center"]
        print(f"\n[Step 2] Agent identified target: '{target_element.get('text')}' at ({cx}, {cy})")
        print(f" -> Executing tap at centroid coordinates: tap(x={cx}, y={cy})")
        tap_result = server.tap(cx, cy)
        print(f" -> Result: {tap_result}")

    # 3. Reading two-factor authentication / notifications
    print("\n[Step 3] Monitoring for 2FA / OTP notifications...")
    notifications = server.get_notifications()
    print(f" -> Notifications retrieved ({len(notifications)} records):")
    for notif in notifications:
        print(f"    • [{notif.get('package')}] {notif.get('title')}: {notif.get('text')}")

    print("\n[Success] Autonomous mobile action loop executed successfully.")


if __name__ == "__main__":
    run_agent_workflow()
