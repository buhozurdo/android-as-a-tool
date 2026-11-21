"""
Guardrails Engine para Android-MCP (Android-as-a-Tool).
Proporciona validación y sanitización para entradas de agentes, fuentes de APK,
comandos hacia la shell ADB y datos sensibles en notificaciones.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class GuardrailEngine:
    """Motor de evaluación de políticas y sanitización para Android-MCP."""

    def __init__(self, guardrails_dir: Optional[str] = None):
        if guardrails_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(guardrails_dir)

        self.input_rules = self._load_rules(self.base_dir / "input-guards.yaml")
        self.output_rules = self._load_rules(self.base_dir / "output-guards.yaml")

    def _load_rules(self, filepath: Path) -> List[Dict[str, Any]]:
        """Carga reglas desde archivo YAML con fallback incorporado."""
        if not filepath.exists():
            return []

        if HAS_YAML:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data.get("rules", []) if isinstance(data, dict) else []
            except Exception as e:
                print(f"[Aviso] Error al parsear {filepath.name} con PyYAML: {e}", file=sys.stderr)

        # Fallback sin PyYAML: parseo liviano de claves clave
        rules: List[Dict[str, Any]] = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            rule_blocks = re.split(r"\n\s*-\s+id:\s*", content)
            for block in rule_blocks[1:]:
                lines = block.splitlines()
                rule_id = lines[0].strip().strip('"').strip("'")
                rule: Dict[str, Any] = {"id": rule_id, "patterns": []}

                for line in lines[1:]:
                    line_str = line.strip()
                    if line_str.startswith("action:"):
                        rule["action"] = line_str.replace("action:", "").strip().strip('"').strip("'")
                    elif line_str.startswith("severity:"):
                        rule["severity"] = line_str.replace("severity:", "").strip().strip('"').strip("'")
                    elif line_str.startswith("description:"):
                        rule["description"] = line_str.replace("description:", "").strip().strip('"').strip("'")
                    elif line_str.startswith("- ") and "patterns:" not in line_str:
                        pat = line_str[2:].strip().strip('"').strip("'")
                        rule["patterns"].append(pat)
                rules.append(rule)
        except Exception as err:
            print(f"[Aviso] Error en fallback de {filepath.name}: {err}", file=sys.stderr)

        return rules

    def validate_input(self, text: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evalúa texto de entrada contra inyecciones y secretos.
        Retorna: (is_allowed, processed_text, violations)
        """
        violations: List[Dict[str, Any]] = []
        processed = text

        for rule in self.input_rules:
            action = rule.get("action", "flag")
            patterns = rule.get("patterns", [])

            for pattern in patterns:
                try:
                    matches = list(re.finditer(pattern, processed))
                except re.error:
                    continue

                if matches:
                    violations.append({
                        "rule_id": rule.get("id"),
                        "severity": rule.get("severity", "medium"),
                        "action": action,
                        "description": rule.get("description"),
                        "matches_count": len(matches),
                    })

                    if action == "block":
                        return False, f"Entrada bloqueada por violación de seguridad: {rule.get('id')}", violations
                    elif action == "mask":
                        processed = re.sub(pattern, "[CONFIDENCIAL-ENMASCARADO]", processed)

        return True, processed, violations

    def validate_output(self, text: str, is_json_required: bool = False) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evalúa texto o datos salientes para evitar fuga de secretos o validar JSON.
        Retorna: (is_valid, sanitized_text, violations)
        """
        violations: List[Dict[str, Any]] = []
        sanitized = text

        for rule in self.output_rules:
            rule_id = rule.get("id")
            action = rule.get("action", "flag")

            if rule_id == "json-structure-check" and is_json_required:
                try:
                    clean_json = sanitized.strip()
                    if clean_json.startswith("```"):
                        clean_json = re.sub(r"^```[a-zA-Z]*\n?", "", clean_json)
                        clean_json = re.sub(r"\n?```$", "", clean_json)
                    json.loads(clean_json)
                except Exception as err:
                    violations.append({
                        "rule_id": rule_id,
                        "severity": rule.get("severity", "high"),
                        "description": f"Fallo al validar JSON: {err}",
                    })
                    return False, sanitized, violations

            patterns = rule.get("patterns", [])
            for pattern in patterns:
                try:
                    matches = list(re.finditer(pattern, sanitized))
                except re.error:
                    continue

                if matches:
                    violations.append({
                        "rule_id": rule_id,
                        "severity": rule.get("severity", "medium"),
                        "action": action,
                        "description": rule.get("description"),
                        "matches_count": len(matches),
                    })
                    if action in ("redact", "mask"):
                        sanitized = re.sub(pattern, "[SECRETO-REDACTADO]", sanitized)

        return True, sanitized, violations

    def validate_apk_source(self, source: str) -> Tuple[bool, str]:
        """
        Valida que una fuente de APK (archivo local o URL) no sea un vector SSRF
        ni apunte a interfaces de loopback o endpoints de metadatos de nube.
        """
        src = source.strip()
        if not src:
            return False, "Ruta o URL de APK vacía."

        # Rutas locales
        if not src.startswith(("http://", "https://")):
            # Bloquea path traversal no seguro hacia archivos del sistema
            normalized = Path(src).as_posix()
            if "/etc/" in normalized or "windows/system32" in normalized.lower():
                return False, f"Acceso denegado a ruta de sistema: {source}"
            return True, "Ruta local aceptada."

        # Validación de URLs remotas (Anti-SSRF)
        parsed = urlparse(src)
        hostname = (parsed.hostname or "").lower()

        # Bloquear IPs de metadatos de nube y loopback
        blocked_hosts = {
            "169.254.169.254",
            "metadata.google.internal",
            "metadata.google.internal.",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
        }

        if hostname in blocked_hosts or hostname.endswith(".internal"):
            return False, f"Descarga bloqueada por política anti-SSRF: {hostname} está restringido."

        # Bloquear redes privadas RFC 1918 salvo configuración explícita
        if re.match(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname) or \
           re.match(r"^192\.168\.\d{1,3}\.\d{1,3}$", hostname) or \
           re.match(r"^172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}$", hostname):
            return False, f"Descarga bloqueada por política anti-SSRF: Red privada restringida ({hostname})."

        return True, "URL de APK verificada y segura."

    def sanitize_notification(self, notif: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza datos sensibles en un diccionario de notificación, enmascarando
        números de tarjeta o cuenta y conservando el código OTP.
        """
        cleaned = dict(notif)
        for field in ("title", "text", "ticker"):
            if field in cleaned and isinstance(cleaned[field], str):
                val = cleaned[field]
                # Enmascarar números de tarjeta
                val = re.sub(r"\b(?:\d{4}[ -]?){3}\d{4}\b", "[TARJETA-ENMASCARADA]", val)
                # Enmascarar emails
                val = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL-ENMASCARADO]", val)
                cleaned[field] = val
        return cleaned


def main():
    if len(sys.argv) < 3:
        print("Uso: python guardrails/engine.py [check-input|check-output|check-apk] <texto_o_url>")
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2]
    engine = GuardrailEngine()

    if cmd == "check-input":
        allowed, res, viols = engine.validate_input(arg)
        print(f"Permitido: {allowed}")
        print(f"Resultado: {res}")
        if viols:
            print(f"Violaciones ({len(viols)}): {json.dumps(viols, indent=2)}")
    elif cmd == "check-output":
        valid, res, viols = engine.validate_output(arg)
        print(f"Válido: {valid}")
        print(f"Sanitizado: {res}")
    elif cmd == "check-apk":
        allowed, reason = engine.validate_apk_source(arg)
        print(f"Seguro: {allowed} ({reason})")


if __name__ == "__main__":
    main()
