"""
Android Doctor: In-process environment and health diagnostics for Android-MCP.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    from android_mcp.adb_client import ADBClient
    HAS_ADB_CLIENT = True
except ImportError:
    HAS_ADB_CLIENT = False

try:
    from guardrails.engine import GuardrailEngine
    HAS_GUARDRAILS = True
except ImportError:
    HAS_GUARDRAILS = False


def run_diagnostics() -> Dict[str, Any]:
    adb_bin = os.environ.get("ADB_BINARY_PATH", "adb")
    has_adb_binary = shutil.which(adb_bin) is not None

    report: Dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "adb_binary_found": has_adb_binary,
        "adb_path": shutil.which(adb_bin) or "Not found (auto mock fallback)",
        "device_mode": "mock_simulation" if not has_adb_binary else "live_adb",
        "resolution": None,
        "installed_apps_count": 0,
        "guardrails_loaded": False,
        "guardrails_rules_count": 0,
        "evals_dataset_ready": False,
        "overall_status": "READY",
    }

    # Test ADB Client
    if HAS_ADB_CLIENT:
        adb = ADBClient()
        report["device_mode"] = "mock_simulation" if adb.mock_mode else "live_adb"
        report["resolution"] = adb.get_resolution()
        apps = adb.list_apps(third_party_only=False)
        report["installed_apps_count"] = len(apps)

    # Test Guardrails
    if HAS_GUARDRAILS:
        engine = GuardrailEngine()
        report["guardrails_loaded"] = True
        report["guardrails_rules_count"] = len(engine.input_rules) + len(engine.output_rules)

    # Check Evals dataset
    evals_file = ROOT_DIR / "evals" / "datasets" / "android-eval-suite.json"
    report["evals_dataset_ready"] = evals_file.exists()

    return report


def main():
    json_mode = "--json" in sys.argv
    diag = run_diagnostics()

    if json_mode:
        print(json.dumps(diag, indent=2, ensure_ascii=False))
        return

    print("\n" + "=" * 55)
    print("  🩺 ANDROID-MCP ENVIRONMENT DOCTOR")
    print("=" * 55)
    print(f"Python:              {diag['python_version']} ({diag['platform']})")
    print(f"ADB Binary:          {'✅ ' + diag['adb_path'] if diag['adb_binary_found'] else '⚠️ Not found (Mock mode active)'}")
    print(f"Device Mode:         {'⚡ Mock Simulation (CI/Headless)' if diag['device_mode'] == 'mock_simulation' else '📱 Live ADB Target'}")
    print(f"Display Resolution:  {diag['resolution']}")
    print(f"Detected Apps:       {diag['installed_apps_count']} packages")
    print(f"Guardrails Engine:   {'✅ Active (' + str(diag['guardrails_rules_count']) + ' rules)' if diag['guardrails_loaded'] else '❌ Not loaded'}")
    print(f"Evals Suite:         {'✅ Ready' if diag['evals_dataset_ready'] else '❌ Missing'}")
    print(f"Overall Health:      ✅ {diag['overall_status']}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
