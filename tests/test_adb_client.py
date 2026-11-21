"""
Tests for ADBClient: gesture coordinates, command execution,
package management, screenshot capture, and notifications parser.
"""

from android_mcp.adb_client import ADBClient, KEY_MAPPINGS


class TestADBClientMockOperations:
    def setup_method(self):
        self.adb = ADBClient(mock_mode=True)

    def test_connect_mock(self):
        msg = self.adb.connect()
        assert "connected" in msg.lower() or "simulated" in msg.lower()

    def test_get_resolution(self):
        w, h = self.adb.get_resolution()
        assert w == 1080
        assert h == 2400

    def test_package_management_lifecycle(self):
        # Initial list
        apps = self.adb.list_apps(third_party_only=False)
        assert "com.android.settings" in apps
        assert "org.mozilla.firefox" in apps

        third_party = self.adb.list_apps(third_party_only=True)
        assert "com.android.settings" not in third_party
        assert "org.mozilla.firefox" in third_party

        # Install new app
        res_install = self.adb.install_apk("com.mycorp.banking.apk")
        assert "Success" in res_install
        assert "com.mycorp.banking" in self.adb.list_apps(third_party_only=True)

        # Launch app
        res_launch = self.adb.launch_app("com.mycorp.banking")
        assert "Launched" in res_launch
        assert self.adb.mock_active_app == "com.mycorp.banking"

        # Uninstall app
        res_uninstall = self.adb.uninstall_app("com.mycorp.banking")
        assert "Success" in res_uninstall
        assert "com.mycorp.banking" not in self.adb.list_apps(third_party_only=True)

    def test_input_gestures(self):
        # Tap
        tap_res = self.adb.tap(500, 1200)
        assert "500" in tap_res and "1200" in tap_res

        # Long press
        lp_res = self.adb.long_press(300, 600, duration_ms=2000)
        assert "2000ms" in lp_res

        # Type text
        type_res = self.adb.type_text("Search query with spaces")
        assert "Search query with spaces" in type_res

        # Swipe directions
        for d in ("up", "down", "left", "right"):
            swipe_res = self.adb.swipe(d)
            assert f"Swiped {d}" in swipe_res

        # Invalid swipe
        invalid_swipe = self.adb.swipe("diagonal")
        assert "Error" in invalid_swipe

    def test_keyevent_mappings(self):
        for key in ("HOME", "BACK", "ENTER", "APP_SWITCH", "VOLUME_UP"):
            res = self.adb.press_key(key)
            assert f"Pressed key {key}" in res
            expected_code = KEY_MAPPINGS[key]
            assert str(expected_code) in res

        # Numeric keycode directly
        res_num = self.adb.press_key("66")
        assert "code 66" in res_num

        # Invalid key
        res_inv = self.adb.press_key("NON_EXISTENT_KEY")
        assert "Error" in res_inv

    def test_screenshot_base64(self):
        b64 = self.adb.take_screenshot()
        assert len(b64) > 20
        import base64
        decoded = base64.b64decode(b64)
        assert decoded.startswith(b"\x89PNG")

    def test_get_notifications_parser(self):
        notifs = self.adb.get_notifications()
        assert len(notifs) >= 1

        # Check bank alert notification containing OTP
        otp_notif = next((n for n in notifs if "492810" in n.get("text", "")), None)
        assert otp_notif is not None
        assert otp_notif["package"] == "com.google.android.apps.messaging"
        assert "Bank Alert" in otp_notif["title"]
        assert "492810" in otp_notif["ticker"]
