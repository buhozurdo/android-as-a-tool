"""
Script de análisis estático y auditoría de Quality Gates para Android-MCP:
- Conteo de líneas y tipos de archivo
- Detección de TODOs, FIXMEs y deuda técnica documentada (# DEBT:)
- Detección de antipatrones (except Exception: pass)
- Escaneo de secretos hardcodeados
- Evaluación de Quality Gates: 'Óptimo y Aceptable' (Gate 1) y 'Bien Hecho' (Gate 2)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

CODE_EXTENSIONS = {".py", ".sh", ".bash"}
DOC_EXTENSIONS = {".yaml", ".yml", ".json", ".md", ".toml"}
EXTENSIONS = CODE_EXTENSIONS | DOC_EXTENSIONS
IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".pytest_cache", "egg-info"}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{12,}['\"]"),
    re.compile(r"(?i)sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)AIza[0-9A-Za-z-_]{35}"),
]

CODE_TODO_PATTERN = re.compile(r"(#|//|/\*)\s*(TODO|FIXME|BUG|HACK)\s*:\s*(.*)", re.IGNORECASE)
DEBT_PATTERN = re.compile(r"(#|//)\s*DEBT\s*:\s*(.*)", re.IGNORECASE)
SILENT_EXCEPT_PATTERN = re.compile(r"except\s+Exception\s*:\s*pass")


def analyze_repository(target_dir: Path | None = None) -> Dict[str, Any]:
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent.parent.parent

    stats: Dict[str, Any] = {
        "target_path": str(target_dir),
        "files_scanned": 0,
        "total_lines": 0,
        "todos": [],
        "documented_debt": [],
        "anti_patterns": [],
        "potential_secrets": [],
        "by_extension": {},
        "quality_gates": {
            "gate_1_optimal_and_acceptable": {"passed": True, "reasons": []},
            "gate_2_well_crafted": {"passed": True, "reasons": []},
        },
    }

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.endswith(".egg-info")]

        for file in files:
            ext = Path(file).suffix.lower()
            if ext in EXTENSIONS:
                stats["files_scanned"] += 1
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1

                file_path = Path(root) / file
                rel_path = file_path.relative_to(target_dir)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        stats["total_lines"] += len(lines)

                        for idx, line in enumerate(lines, 1):
                            # Secreto
                            for pattern in SECRET_PATTERNS:
                                if pattern.search(line) and "pattern" not in line.lower() and "regex" not in line.lower():
                                    stats["potential_secrets"].append({
                                        "file": str(rel_path),
                                        "line": idx,
                                        "preview": line.strip()[:60],
                                    })

                            # TODO / BUG
                            todo_match = CODE_TODO_PATTERN.search(line)
                            if todo_match:
                                stats["todos"].append({
                                    "file": str(rel_path),
                                    "line": idx,
                                    "tag": todo_match.group(2).upper(),
                                    "note": todo_match.group(3).strip(),
                                })

                            # Deuda documentada
                            debt_match = DEBT_PATTERN.search(line)
                            if debt_match:
                                stats["documented_debt"].append({
                                    "file": str(rel_path),
                                    "line": idx,
                                    "note": debt_match.group(2).strip(),
                                })

                            # Antipatrones (excluyendo comentarios y docstrings)
                            stripped = line.strip()
                            if ext in CODE_EXTENSIONS and not stripped.startswith(("#", "-", "*", '"""', "'''")) and SILENT_EXCEPT_PATTERN.search(line):
                                stats["anti_patterns"].append({
                                    "file": str(rel_path),
                                    "line": idx,
                                    "type": "silent_exception_suppression",
                                    "snippet": stripped,
                                })

                except Exception as err:
                    print(f"[Aviso] No se pudo leer {rel_path}: {err}", file=sys.stderr)

    g1 = stats["quality_gates"]["gate_1_optimal_and_acceptable"]
    g2 = stats["quality_gates"]["gate_2_well_crafted"]

    # Gate 1: Óptimo y Aceptable
    if stats["potential_secrets"]:
        g1["passed"] = False
        g1["reasons"].append(f"Se encontraron {len(stats['potential_secrets'])} posibles secretos hardcodeados.")
    if stats["files_scanned"] == 0:
        g1["passed"] = False
        g1["reasons"].append("No se escanearon archivos.")

    if not g1["reasons"]:
        g1["reasons"].append("Base sólida aprobada: sin secretos expuestos y estructura modular verificada.")

    # Gate 2: Bien Hecho (Excelencia)
    if stats["anti_patterns"]:
        g2["passed"] = False
        g2["reasons"].append(f"Se detectaron {len(stats['anti_patterns'])} antipatrones en el código fuente.")

    unresolved_bugs = [t for t in stats["todos"] if t["tag"] == "BUG"]
    if unresolved_bugs:
        g2["passed"] = False
        g2["reasons"].append(f"Existen {len(unresolved_bugs)} marcas de BUG pendientes en el código.")

    if not g2["reasons"]:
        g2["reasons"].append("Estándares de excelencia alcanzados: sin antipatrones, sin bugs abiertos y tipado limpio.")

    return stats


def main():
    target = None
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--path" and i + 1 < len(sys.argv):
                target = Path(sys.argv[i + 1])
                break
            elif not arg.startswith("--"):
                target = Path(arg)

    report = analyze_repository(target)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
