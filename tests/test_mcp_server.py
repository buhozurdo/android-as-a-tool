"""
Integration tests for AndroidMCPServer: tool execution,
parameter handling, UI queries, and error states.
"""

from android_mcp.adb_client import ADBClient
from android_mcp.server import AndroidMCPServer, create_server


class TestAndroidMCPServerTools:
    def setup_method(self):
        self.mock_adb = ADBClient(mock_mode=True)
        self.server = create_server(adb_client=self.mock_adb)

    def test_all_13_tools_registered(self):
        """Verify the 13 tools defined in README specification are implemented and callable."""
        # 1. install_apk
        r1 = self.server.install_apk("sample.apk")
        assert "Success" in r1 or "Installed" in r1

        # 2. list_apps
        r2 = self.server.list_apps(third_party_only=True)
        assert isinstance(r2, list)

        # 3. launch_app
        r3 = self.server.launch_app("com.whatsapp")
        assert "Launched" in r3

        # 4. uninstall_app
        r4 = self.server.uninstall_app("com.whatsapp")
        assert "Success" in r4 or "Failure" in r4

        # 5. get_screen_elements
        r5 = self.server.get_screen_elements(clickable_only=True)
        assert "screen" in r5
        assert "elements" in r5
        assert isinstance(r5["elements"], list)

        # 6. tap
        r6 = self.server.tap(200, 400)
        assert "Tapped" in r6

        # 7. long_press
        r7 = self.server.long_press(200, 400, duration_ms=1500)
        assert "Long pressed" in r7

        # 8. type_text
        r8 = self.server.type_text("Search text")
        assert "Typed" in r8

        # 9. swipe
        r9 = self.server.swipe("up")
        assert "Swiped" in r9

        # 10. press_key
        r10 = self.server.press_key("HOME")
        assert "Pressed key" in r10

        # 11. take_screenshot
        r11 = self.server.take_screenshot()
        assert r11["format"] == "image/png;base64"
        assert len(r11["data"]) > 0

        # 12. get_notifications
        r12 = self.server.get_notifications()
        assert isinstance(r12, list)
        assert len(r12) > 0

        # 13. batch_actions
        r13 = self.server.batch_actions([{"action": "press_key", "key": "HOME"}])
        assert r13["status"] == "success"
        assert len(r13["results"]) == 1

    def test_screen_elements_interactive_centers(self):
        """Verify UI elements returned by server provide exact centroid for tap target."""
        elements_doc = self.server.get_screen_elements(clickable_only=True)
        elements = elements_doc["elements"]
        assert len(elements) > 0

        first = elements[0]
        assert "center" in first
        cx, cy = first["center"]
        assert isinstance(cx, int) and isinstance(cy, int)
        assert cx >= 0 and cy >= 0

        # Agent can directly invoke tap using the center coordinates
        tap_res = self.server.tap(cx, cy)
        assert f"({cx}, {cy})" in tap_res

    def test_notification_otp_extraction_flow(self):
        """Verify agent can read 2FA verification codes from system notifications."""
        notifications = self.server.get_notifications()
        msg_notifs = [n for n in notifications if "verification code" in n.get("text", "").lower()]
        assert len(msg_notifs) >= 1
        assert "492810" in msg_notifs[0]["text"]

    def test_batch_actions_macro_pipeline(self):
        """Verify compound batch actions execution for macro pipelines."""
        actions = [
            {"action": "tap", "x": 850, "y": 180},
            {"action": "type_text", "text": "GitHub"},
            {"action": "tap", "x": 950, "y": 470},
            {"action": "press_key", "key": "BACK"},
        ]
        res = self.server.batch_actions(actions)
        assert res["status"] == "success"
        assert res["count"] == 4
        assert len(res["results"]) == 4
