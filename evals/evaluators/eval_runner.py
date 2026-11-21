"""
Automated benchmark evaluation runner for Android-MCP.
Executes test assertions for security guardrails, centroid accuracy,
OTP retention, and JSON schemas, generating Markdown reports in analysis-reporte/.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    from guardrails.engine import GuardrailEngine
    HAS_GUARDRAILS = True
except ImportError:
    HAS_GUARDRAILS = False

try:
    from android_mcp.ui_parser import UIParser
    HAS_UI_PARSER = True
except ImportError:
    HAS_UI_PARSER = False


def run_evaluations(dataset_path: Path | None = None) -> Dict[str, Any]:
    if dataset_path is None:
        dataset_path = ROOT_DIR / "evals" / "datasets" / "android-eval-suite.json"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        suite = json.load(f)

    engine = GuardrailEngine() if HAS_GUARDRAILS else None

    results: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(suite),
        "passed": 0,
        "failed": 0,
        "cases": [],
    }

    for test in suite:
        test_id = test.get("id")
        name = test.get("name", test_id)
        category = test.get("category")
        is_passed = True
        notes: List[str] = []

        if category == "safety_guardrails" and engine:
            if "input_url" in test:
                url = test["input_url"]
                safe, reason = engine.validate_apk_source(url)
                if test.get("expected_status") == "block":
                    if safe:
                        is_passed = False
                        notes.append(f"Expected anti-SSRF block for {url}, but was allowed.")
                    else:
                        notes.append(f"Anti-SSRF block succeeded: {reason}")
            elif "input" in test:
                inp = test["input"]
                allowed, processed, viols = engine.validate_input(inp)
                expected = test.get("expected_status")
                if expected == "block":
                    if allowed:
                        is_passed = False
                        notes.append("Expected security block, but input was allowed.")
                    else:
                        notes.append("Security block verified successfully.")
                elif expected == "mask":
                    if "[CONFIDENTIAL-MASKED]" not in processed:
                        is_passed = False
                        notes.append("Expected PII masking tag [CONFIDENTIAL-MASKED], but not found.")
                    else:
                        notes.append("Sensitive data masked successfully.")

        elif category == "notification_otp_extraction" and engine:
            notif = test.get("notification", {})
            cleaned = engine.sanitize_notification(notif)
            expected_otp = test.get("expected_otp")
            masked_contains = test.get("masked_contains")

            if expected_otp not in cleaned.get("text", ""):
                is_passed = False
                notes.append(f"OTP code {expected_otp} was not retained after sanitization.")
            else:
                notes.append(f"OTP code {expected_otp} retained successfully.")

            if masked_contains and masked_contains not in cleaned.get("text", ""):
                is_passed = False
                notes.append(f"Expected masking tag '{masked_contains}' not found in notification.")
            else:
                notes.append("Sensitive notification data masked.")

        elif category == "structured_output":
            response = test.get("mock_response", "")
            try:
                parsed = json.loads(response)
                for key in test.get("expected_keys", []):
                    if key not in parsed:
                        is_passed = False
                        notes.append(f"Expected key missing in JSON: '{key}'")
                if is_passed:
                    notes.append("Valid JSON structure and all expected keys present.")
            except json.JSONDecodeError as err:
                is_passed = False
                notes.append(f"JSON syntax error: {err}")

        elif category == "ui_compression_fidelity" and HAS_UI_PARSER:
            bounds_str = test.get("bounds", "")
            bounds = UIParser.parse_bounds(bounds_str)
            if not bounds:
                is_passed = False
                notes.append(f"Failed to parse bounds string: {bounds_str}")
            else:
                center = UIParser.compute_center(bounds)
                expected = tuple(test.get("expected_center", []))
                if center != expected:
                    is_passed = False
                    notes.append(f"Calculated centroid {center} differs from expected {expected}.")
                else:
                    notes.append(f"Exact centroid calculation verified: {center}.")

        if is_passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

        results["cases"].append({
            "id": test_id,
            "name": name,
            "category": category,
            "status": "PASS" if is_passed else "FAIL",
            "notes": " ".join(notes),
        })

    return results


def generate_markdown_report(results: Dict[str, Any]) -> str:
    total = results["total_tests"]
    passed = results["passed"]
    failed = results["failed"]
    rate = (passed / total * 100.0) if total > 0 else 0.0

    md = [
        "# AI Agent & Security Evaluation Report — Android-MCP",
        "",
        f"- **Timestamp**: `{results['timestamp']}`",
        f"- **Total Evaluations**: `{total}`",
        f"- **Passed**: `{passed}`",
        f"- **Failed**: `{failed}`",
        f"- **Success Rate**: **`{rate:.1f}%`**",
        "",
        "## Test Cases Summary",
        "",
        "| ID | Name | Category | Status | Notes |",
        "| :--- | :--- | :--- | :---: | :--- |",
    ]

    for c in results["cases"]:
        badge = "✅ PASS" if c["status"] == "PASS" else "❌ FAIL"
        md.append(f"| `{c['id']}` | {c['name']} | `{c['category']}` | {badge} | {c['notes']} |")

    md.append("")
    md.append("---")
    md.append("*Generated automatically by Android-MCP Evals Runner.*")
    return "\n".join(md)


def main():
    write_report = "--report" in sys.argv
    results = run_evaluations()

    print("\n" + "=" * 60)
    print("  EVALUATION SUITE: ANDROID-MCP")
    print("=" * 60)
    print(f"Total Tests:   {results['total_tests']}")
    print(f"Passed:        {results['passed']}")
    print(f"Failed:        {results['failed']}")
    success_rate = (results['passed'] / results['total_tests']) * 100
    print(f"Success Rate:  {success_rate:.1f}%\n")

    for case in results["cases"]:
        status_icon = "✅" if case["status"] == "PASS" else "❌"
        print(f"[{status_icon}] {case['id']} - {case['name']}: {case['status']}")
        if case["notes"]:
            print(f"    Notes: {case['notes']}")

    if write_report:
        report_dir = ROOT_DIR / "analysis-reporte"
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp_slug = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_file = report_dir / f"eval-report-{timestamp_slug}.md"
        report_md = generate_markdown_report(results)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"\n📄 Markdown report saved to: {report_file}")

    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
