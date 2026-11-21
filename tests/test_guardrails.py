"""
Tests for Guardrails Engine in Android-MCP:
Anti-SSRF for APK URLs, command injection prevention in type_text,
PII sanitization in notifications, and structured output validation.
"""

from guardrails.engine import GuardrailEngine
from android_mcp.adb_client import ADBClient


class TestAndroidGuardrails:
    def setup_method(self):
        self.engine = GuardrailEngine()
        self.adb = ADBClient(mock_mode=True)

    def test_ssrf_apk_url_blocking(self):
        # Cloud metadata target
        safe_cloud, r_cloud = self.engine.validate_apk_source("http://169.254.169.254/secret.apk")
        assert safe_cloud is False
        assert "anti-ssrf" in r_cloud.lower()

        # Localhost / Loopback target
        safe_local, r_local = self.engine.validate_apk_source("http://localhost:8000/app.apk")
        assert safe_local is False

        safe_ip, _ = self.engine.validate_apk_source("http://127.0.0.1:5555/app.apk")
        assert safe_ip is False

        # Private RFC 1918 networks
        safe_priv, _ = self.engine.validate_apk_source("http://192.168.1.100/app.apk")
        assert safe_priv is False

        # Valid public HTTPS URL
        safe_public, _ = self.engine.validate_apk_source("https://github.com/buhozurdo/android-as-a-tool/releases/download/v0.1/app.apk")
        assert safe_public is True

        # Valid local file path
        safe_file, _ = self.engine.validate_apk_source("apks/sample.apk")
        assert safe_file is True

        # System directory traversal
        safe_sys, _ = self.engine.validate_apk_source("/etc/shadow")
        assert safe_sys is False

    def test_adb_client_ssrf_integration(self):
        # In ADBClient install_apk
        res = self.adb.install_apk("http://169.254.169.254/malicious.apk")
        assert "Security Error" in res or "anti-ssrf" in res.lower()

        # Safe local install proceeds
        res_safe = self.adb.install_apk("apks/safe.apk")
        assert "Success" in res_safe

    def test_command_injection_blocking(self):
        # Destructive shell injection
        res_injection = self.adb.type_text("search; rm -rf /sdcard")
        assert "Security Error" in res_injection

        res_reboot = self.adb.type_text("test && reboot")
        assert "Security Error" in res_reboot

        # Normal text passes
        res_normal = self.adb.type_text("Valid search text with 123")
        assert "Valid search text with 123" in res_normal

    def test_notification_pii_sanitizer(self):
        notif = {
            "package": "com.bank.app",
            "title": "Transfer Alert",
            "text": "Your verification code is 883921 for transaction on card 4111 2222 3333 4444 sent to user@bank.com",
            "ticker": "Code 883921",
        }
        cleaned = self.engine.sanitize_notification(notif)

        # OTP is preserved
        assert "883921" in cleaned["text"]
        assert "883921" in cleaned["ticker"]

        # Credit card & email are masked
        assert "4111 2222 3333 4444" not in cleaned["text"]
        assert "[CARD-MASKED]" in cleaned["text"]
        assert "user@bank.com" not in cleaned["text"]
        assert "[EMAIL-MASKED]" in cleaned["text"]

    def test_output_json_structure_validation(self):
        # Valid JSON
        v1, _, viols1 = self.engine.validate_output('{"screen": {"width": 1080}, "elements": []}', is_json_required=True)
        assert v1 is True
        assert len(viols1) == 0

        # Invalid JSON
        v2, _, viols2 = self.engine.validate_output('{"screen": broken_json...}', is_json_required=True)
        assert v2 is False
        assert len(viols2) > 0
