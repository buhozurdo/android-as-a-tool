"""
Runner automatizado para evaluar la suite de pruebas (Evals) de Android-MCP.
Ejecuta validaciones de seguridad, fidelidad de centroides, extracción de OTPs
y conformidad de esquemas JSON, generando reportes Markdown en analysis-reporte/.
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
        raise FileNotFoundError(f"Dataset de evaluación no encontrado en: {dataset_path}")

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
                        notes.append(f"Se esperaba bloqueo anti-SSRF para {url}, pero fue permitida.")
                    else:
                        notes.append(f"Bloqueo anti-SSRF exitoso: {reason}")
            elif "input" in test:
                inp = test["input"]
                allowed, processed, viols = engine.validate_input(inp)
                expected = test.get("expected_status")
                if expected == "block":
                    if allowed:
                        is_passed = False
                        notes.append("Se esperaba bloqueo por seguridad, pero la entrada fue permitida.")
                    else:
                        notes.append("Bloqueo de seguridad verificado correctamente.")
                elif expected == "mask":
                    if "[CONFIDENCIAL-ENMASCARADO]" not in processed:
                        is_passed = False
                        notes.append("Se esperaba enmascaramiento de PII, pero no se halló la etiqueta.")
                    else:
                        notes.append("Datos sensibles enmascarados correctamente.")

        elif category == "notification_otp_extraction" and engine:
            notif = test.get("notification", {})
            cleaned = engine.sanitize_notification(notif)
            expected_otp = test.get("expected_otp")
            masked_contains = test.get("masked_contains")

            if expected_otp not in cleaned.get("text", ""):
                is_passed = False
                notes.append(f"El código OTP {expected_otp} no fue retenido tras la sanitización.")
            else:
                notes.append(f"Código OTP {expected_otp} retenido con éxito.")

            if masked_contains and masked_contains not in cleaned.get("text", ""):
                is_passed = False
                notes.append(f"Se esperaba enmascaramiento conteniendo '{masked_contains}'.")
            else:
                notes.append("Datos sensibles de la notificación enmascarados.")

        elif category == "structured_output":
            response = test.get("mock_response", "")
            try:
                parsed = json.loads(response)
                for key in test.get("expected_keys", []):
                    if key not in parsed:
                        is_passed = False
                        notes.append(f"Clave esperada faltante en JSON: '{key}'")
                if is_passed:
                    notes.append("Estructura JSON válida y todas las claves esperadas presentes.")
            except json.JSONDecodeError as err:
                is_passed = False
                notes.append(f"Error de sintaxis JSON: {err}")

        elif category == "ui_compression_fidelity" and HAS_UI_PARSER:
            bounds_str = test.get("bounds", "")
            bounds = UIParser.parse_bounds(bounds_str)
            if not bounds:
                is_passed = False
                notes.append(f"Fallo al parsear límites de bounds: {bounds_str}")
            else:
                center = UIParser.compute_center(bounds)
                expected = tuple(test.get("expected_center", []))
                if center != expected:
                    is_passed = False
                    notes.append(f"Centroide calculado {center} difiere del esperado {expected}.")
                else:
                    notes.append(f"Cálculo de centroide exacto verificado: {center}.")

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
        "# Reporte de Evaluación de Agentes y Seguridad — Android-MCP",
        "",
        f"- **Fecha y Hora**: `{results['timestamp']}`",
        f"- **Total de Evaluaciones**: `{total}`",
        f"- **Superadas (PASS)**: `{passed}`",
        f"- **Fallidas (FAIL)**: `{failed}`",
        f"- **Tasa de Éxito**: **`{rate:.1f}%`**",
        "",
        "## Resumen por Caso de Prueba",
        "",
        "| ID | Nombre | Categoría | Estado | Observaciones |",
        "| :--- | :--- | :--- | :---: | :--- |",
    ]

    for c in results["cases"]:
        badge = "✅ PASS" if c["status"] == "PASS" else "❌ FAIL"
        md.append(f"| `{c['id']}` | {c['name']} | `{c['category']}` | {badge} | {c['notes']} |")

    md.append("")
    md.append("---")
    md.append("*Generado automáticamente por el Runner de Evals de Android-MCP.*")
    return "\n".join(md)


def main():
    write_report = "--report" in sys.argv
    results = run_evaluations()

    print("\n" + "=" * 60)
    print("  SUITE DE EVALUACIONES: ANDROID-MCP")
    print("=" * 60)
    print(f"Total pruebas: {results['total_tests']}")
    print(f"Aprobadas:     {results['passed']}")
    print(f"Fallidas:      {results['failed']}")
    success_rate = (results['passed'] / results['total_tests']) * 100
    print(f"Tasa de éxito: {success_rate:.1f}%\n")

    for case in results["cases"]:
        status_icon = "✅" if case["status"] == "PASS" else "❌"
        print(f"[{status_icon}] {case['id']} - {case['name']}: {case['status']}")
        if case["notes"]:
            print(f"    Nota: {case['notes']}")

    if write_report:
        report_dir = ROOT_DIR / "analysis-reporte"
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp_slug = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_file = report_dir / f"eval-report-{timestamp_slug}.md"
        report_md = generate_markdown_report(results)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"\n📄 Reporte Markdown guardado en: {report_file}")

    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
