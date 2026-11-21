"""
ADB (Android Debug Bridge) Client wrapper for Android device orchestration.
Supports both real ADB connection (over TCP/USB) and deterministic mock simulation
for unit testing, CI pipelines, and environments without active emulators.
"""

from __future__ import annotations

import base64
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from guardrails.engine import GuardrailEngine
    _GUARDRAILS_ENGINE: Optional[GuardrailEngine] = GuardrailEngine()
except Exception:
    _GUARDRAILS_ENGINE = None

KEY_MAPPINGS: Dict[str, int] = {
    "HOME": 3,
    "BACK": 4,
    "CALL": 5,
    "ENDCALL": 6,
    "VOLUME_UP": 24,
    "VOLUME_DOWN": 25,
    "POWER": 26,
    "CAMERA": 27,
    "CLEAR": 28,
    "ENTER": 66,
    "DEL": 67,
    "ESCAPE": 111,
    "FORWARD_DEL": 112,
    "MOVE_HOME": 122,
    "MOVE_END": 123,
    "PAGE_UP": 92,
    "PAGE_DOWN": 93,
    "APP_SWITCH": 187,
    "MENU": 82,
}

SAMPLE_UIAUTOMATOR_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.settings" bounds="[0,0][1080,2400]">
    <node index="0" text="Search settings" resource-id="com.android.settings:id/search_action_bar_title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,132][996,252]" />
    <node index="1" text="Network &amp; internet" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,300][996,400]" />
    <node index="2" text="Connected devices" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,420][996,520]" />
    <node index="3" text="Apps" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,540][996,640]" />
    <node index="4" text="Notifications" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,660][996,760]" />
    <node index="5" text="Battery" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,780][996,880]" />
    <node index="6" text="Storage" resource-id="android:id/title" class="android.widget.TextView" package="com.android.settings" clickable="true" bounds="[198,900][996,1000]" />
    <node index="7" text="" resource-id="com.android.settings:id/switch_widget" class="android.widget.Switch" package="com.android.settings" checkable="true" checked="true" clickable="true" bounds="[880,1050][1000,1130]" />
  </node>
</hierarchy>"""

SAMPLE_DUMPSYS_NOTIFICATIONS = """
Notification Record:
  pkg=com.google.android.apps.messaging user=0 id=101 tag=null
  uid=10080
  contentView=null
  tickerText=Your verification code is 492810
  title=Bank Alert
  text=Your verification code is 492810 for transfer of $150.00
  time=2026-11-20T22:30:00Z
Notification Record:
  pkg=com.android.vending user=0 id=102 tag=null
  uid=10045
  title=Google Play Store
  text=Updates completed for 3 applications.
  time=2026-11-20T22:15:00Z
"""


class ADBClient:
    """
    Client for dispatching commands to an Android target over ADB.
    Supports auto-fallback to simulated device state when no live ADB daemon is reachable.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5555,
        adb_binary: str = "adb",
        mock_mode: bool = False,
        timeout: float = 15.0,
    ):
        self.host = host
        self.port = port
        self.adb_binary = adb_binary
        self.timeout = timeout
        self.mock_mode = mock_mode

        # Check ADB binary availability
        if not self.mock_mode:
            has_adb = shutil.which(self.adb_binary) is not None
            if not has_adb:
                self.mock_mode = True

        # Simulated state for testing / mock mode
        self.mock_packages = [
            "com.android.settings",
            "com.android.systemui",
            "com.android.vending",
            "com.google.android.youtube",
            "com.aurora.store",
            "org.mozilla.firefox",
            "com.whatsapp",
        ]
        self.mock_screen_xml = SAMPLE_UIAUTOMATOR_XML
        self.mock_notifications = SAMPLE_DUMPSYS_NOTIFICATIONS
        self.mock_screen_size = (1080, 2400)
        self.mock_active_app: Optional[str] = "com.android.settings"
        self.recorded_actions: List[Dict[str, Any]] = []

    def _target_args(self) -> List[str]:
        target = f"{self.host}:{self.port}"
        return [self.adb_binary, "-s", target]

    def execute_raw(self, args: List[str]) -> Tuple[int, str, str]:
        """Execute low-level adb command subprocess."""
        if self.mock_mode:
            return 0, "", ""
        try:
            full_cmd = self._target_args() + args
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
            return res.returncode, res.stdout, res.stderr
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            return 1, "", str(e)

    def connect(self) -> str:
        """Connect to remote device via adb connect host:port."""
        if self.mock_mode:
            return f"connected to {self.host}:{self.port} (simulated)"
        try:
            cmd = [self.adb_binary, "connect", f"{self.host}:{self.port}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
            return res.stdout.strip()
        except Exception as e:
            self.mock_mode = True
            return f"ADB not available, switched to mock mode: {str(e)}"

    def shell(self, command: str) -> str:
        """Execute a shell command on the Android device."""
        if self.mock_mode:
            self.recorded_actions.append({"action": "shell", "cmd": command})
            return f"executed: {command}"
        ret, out, err = self.execute_raw(["shell", command])
        if ret != 0 and err:
            return f"Error: {err.strip()}"
        return out.strip()

    def get_resolution(self) -> Tuple[int, int]:
        """Get physical screen resolution (width, height)."""
        if self.mock_mode:
            return self.mock_screen_size
        out = self.shell("wm size")
        m = re.search(r"Physical size:\s*(\d+)x(\d+)", out)
        if m:
            return (int(m.group(1)), int(m.group(2)))
        return (1080, 2400)

    def install_apk(self, source: str) -> str:
        """Install .apk from local path or URL."""
        if _GUARDRAILS_ENGINE:
            is_safe, reason = _GUARDRAILS_ENGINE.validate_apk_source(source)
            if not is_safe:
                return f"Security Error: {reason}"

        self.recorded_actions.append({"action": "install_apk", "source": source})
        if self.mock_mode:
            pkg_name = Path(source).stem.replace("-", ".").lower()
            if pkg_name not in self.mock_packages:
                self.mock_packages.append(pkg_name)
            return f"Success: Installed {source} (package: {pkg_name})"

        path_to_install = source
        temp_file = None
        if source.startswith(("http://", "https://")):
            import urllib.request
            temp_file = f"/tmp/{os.path.basename(source)}"
            urllib.request.urlretrieve(source, temp_file)
            path_to_install = temp_file

        try:
            ret, out, err = self.execute_raw(["install", "-r", path_to_install])
            if "Success" in out:
                return f"Success: {out.strip()}"
            return f"Install failed: {err.strip() or out.strip()}"
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    def uninstall_app(self, package: str) -> str:
        """Uninstall package from device."""
        self.recorded_actions.append({"action": "uninstall_app", "package": package})
        if self.mock_mode:
            if package in self.mock_packages:
                self.mock_packages.remove(package)
                return f"Success: Uninstalled {package}"
            return f"Failure: Package {package} not installed"
        out = self.shell(f"pm uninstall {package}")
        return out.strip()

    def list_apps(self, third_party_only: bool = True) -> List[str]:
        """List packages installed on device."""
        if self.mock_mode:
            if third_party_only:
                return [p for p in self.mock_packages if not p.startswith("com.android.")]
            return sorted(self.mock_packages)

        flag = "-3" if third_party_only else ""
        out = self.shell(f"pm list packages {flag}").strip()
        packages = []
        for line in out.splitlines():
            if line.startswith("package:"):
                packages.append(line.replace("package:", "").strip())
        return sorted(packages)

    def launch_app(self, package: str) -> str:
        """Launch an application by package name."""
        self.recorded_actions.append({"action": "launch_app", "package": package})
        if self.mock_mode:
            self.mock_active_app = package
            return f"Launched application: {package}"
        # Use monkey tool to open default launcher intent without needing specific activity class
        out = self.shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
        if "No activities found" in out:
            return f"Error: No launcher activity found for {package}"
        return f"Application {package} launched"

    def tap(self, x: int, y: int) -> str:
        """Send touch tap event to (x, y) coordinates."""
        self.recorded_actions.append({"action": "tap", "x": x, "y": y})
        if self.mock_mode:
            return f"Tapped at ({x}, {y})"
        self.shell(f"input tap {x} {y}")
        return f"Tapped at ({x}, {y})"

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> str:
        """Send long press event at (x, y)."""
        self.recorded_actions.append({"action": "long_press", "x": x, "y": y, "duration": duration_ms})
        if self.mock_mode:
            return f"Long pressed at ({x}, {y}) for {duration_ms}ms"
        self.shell(f"input swipe {x} {y} {x} {y} {duration_ms}")
        return f"Long pressed at ({x}, {y}) for {duration_ms}ms"

    def type_text(self, text: str) -> str:
        """Type text into focused input element."""
        if _GUARDRAILS_ENGINE:
            allowed, sanitized, _ = _GUARDRAILS_ENGINE.validate_input(text)
            if not allowed:
                return f"Security Error: {sanitized}"
            text = sanitized

        self.recorded_actions.append({"action": "type_text", "text": text})
        if self.mock_mode:
            return f"Typed text: '{text}'"
        # In Android input text, spaces must be encoded as '%s' and quotes escaped
        escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        self.shell(f"input text '{escaped}'")
        return f"Typed text: '{text}'"

    def swipe(self, direction: str) -> str:
        """Swipe screen in specified direction ('up', 'down', 'left', 'right')."""
        w, h = self.get_resolution()
        cx, cy = w // 2, h // 2

        d = direction.lower().strip()
        if d == "up":
            # Swipe from lower half to upper half
            x1, y1, x2, y2 = cx, int(h * 0.8), cx, int(h * 0.2)
        elif d == "down":
            x1, y1, x2, y2 = cx, int(h * 0.2), cx, int(h * 0.8)
        elif d == "left":
            x1, y1, x2, y2 = int(w * 0.85), cy, int(w * 0.15), cy
        elif d == "right":
            x1, y1, x2, y2 = int(w * 0.15), cy, int(w * 0.85), cy
        else:
            return f"Error: Invalid direction '{direction}'. Choose from 'up', 'down', 'left', 'right'."

        self.recorded_actions.append({"action": "swipe", "direction": d, "coords": (x1, y1, x2, y2)})
        if self.mock_mode:
            return f"Swiped {d} ({x1},{y1}) -> ({x2},{y2})"
        self.shell(f"input swipe {x1} {y1} {x2} {y2} 300")
        return f"Swiped {d} ({x1},{y1}) -> ({x2},{y2})"

    def press_key(self, key: str) -> str:
        """Send keyevent (e.g. HOME, BACK, ENTER, APP_SWITCH)."""
        k = key.upper().strip()
        keycode = KEY_MAPPINGS.get(k)
        if keycode is None:
            # Check if integer was passed
            if k.isdigit():
                keycode = int(k)
            else:
                return f"Error: Unknown key '{key}'. Supported: {list(KEY_MAPPINGS.keys())}"

        self.recorded_actions.append({"action": "press_key", "key": k, "keycode": keycode})
        if self.mock_mode:
            return f"Pressed key {k} (code {keycode})"
        self.shell(f"input keyevent {keycode}")
        return f"Pressed key {k} (code {keycode})"

    def take_screenshot(self) -> str:
        """Capture screenshot and return as base64-encoded PNG string."""
        self.recorded_actions.append({"action": "take_screenshot"})
        if self.mock_mode:
            # 1x1 transparent PNG base64
            dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            return base64.b64encode(dummy_png).decode("utf-8")

        # Fast direct capture via adb exec-out
        try:
            full_cmd = self._target_args() + ["exec-out", "screencap", "-p"]
            res = subprocess.run(full_cmd, capture_output=True, timeout=self.timeout)
            if res.returncode == 0 and res.stdout:
                return base64.b64encode(res.stdout).decode("utf-8")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            pass
        return ""

    def dump_ui_hierarchy(self) -> str:
        """Dump UI XML hierarchy using uiautomator."""
        self.recorded_actions.append({"action": "dump_ui_hierarchy"})
        if self.mock_mode:
            return self.mock_screen_xml

        # Dump to device /sdcard/window_dump.xml and retrieve
        self.shell("uiautomator dump /sdcard/window_dump.xml")
        xml_content = self.shell("cat /sdcard/window_dump.xml")
        return xml_content

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Parse system notifications for 2FA/OTP and incoming alerts."""
        self.recorded_actions.append({"action": "get_notifications"})
        raw = self.mock_notifications if self.mock_mode else self.shell("dumpsys notification --noredact")

        notifications: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}

        for line in raw.splitlines():
            line_str = line.strip()
            if "Notification Record:" in line_str:
                if current and ("title" in current or "text" in current or "ticker" in current):
                    notifications.append(current)
                current = {}
            elif line_str.startswith("pkg="):
                m = re.search(r"pkg=([^\s]+)", line_str)
                if m:
                    current["package"] = m.group(1)
            elif line_str.startswith("title="):
                current["title"] = line_str.replace("title=", "").strip()
            elif line_str.startswith("text="):
                current["text"] = line_str.replace("text=", "").strip()
            elif line_str.startswith("tickerText="):
                ticker = line_str.replace("tickerText=", "").strip()
                if ticker and ticker != "null":
                    current["ticker"] = ticker
            elif line_str.startswith("time="):
                current["time"] = line_str.replace("time=", "").strip()

        if current and ("title" in current or "text" in current or "ticker" in current):
            notifications.append(current)

        if _GUARDRAILS_ENGINE:
            notifications = [_GUARDRAILS_ENGINE.sanitize_notification(n) for n in notifications]

        return notifications
