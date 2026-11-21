"""
Guardrails Engine for Android-MCP (Android-as-a-Tool).
Provides validation and sanitization for agent inputs, APK sources,
ADB shell commands, and sensitive data in notifications.
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
    """Security policy evaluation and sanitization engine for Android-MCP."""

    def __init__(self, guardrails_dir: Optional[str] = None):
        if guardrails_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(guardrails_dir)

        self.input_rules = self._load_rules(self.base_dir / "input-guards.yaml")
        self.output_rules = self._load_rules(self.base_dir / "output-guards.yaml")

    def _load_rules(self, filepath: Path) -> List[Dict[str, Any]]:
        """Loads policy rules from YAML file with self-contained fallback."""
        if not filepath.exists():
            return []

        if HAS_YAML:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data.get("rules", []) if isinstance(data, dict) else []
            except Exception as e:
                print(f"[Warning] Failed parsing {filepath.name} with PyYAML: {e}", file=sys.stderr)

        # Built-in lightweight fallback parser without PyYAML
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
            print(f"[Warning] Fallback error for {filepath.name}: {err}", file=sys.stderr)

        return rules

    def validate_input(self, text: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evaluates input text against injection patterns and leaked secrets.
        Returns: (is_allowed, processed_text, violations)
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
                        return False, f"Input blocked due to security violation: {rule.get('id')}", violations
                    elif action == "mask":
                        processed = re.sub(pattern, "[CONFIDENTIAL-MASKED]", processed)

        return True, processed, violations

    def validate_output(self, text: str, is_json_required: bool = False) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Evaluates output text to prevent secret leakage or validate JSON schema.
        Returns: (is_valid, sanitized_text, violations)
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
                        "description": f"Failed JSON validation: {err}",
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
                        sanitized = re.sub(pattern, "[SECRET-REDACTED]", sanitized)

        return True, sanitized, violations

    def validate_apk_source(self, source: str) -> Tuple[bool, str]:
        """
        Validates APK source (local path or remote URL) against SSRF vectors,
        loopback addresses, and unauthorized cloud metadata endpoints.
        """
        src = source.strip()
        if not src:
            return False, "APK source path or URL is empty."

        # Local file paths
        if not src.startswith(("http://", "https://")):
            normalized = Path(src).as_posix()
            if "/etc/" in normalized or "windows/system32" in normalized.lower():
                return False, f"Access denied to system directory: {source}"
            return True, "Local path accepted."

        # Remote URL validation (Anti-SSRF)
        parsed = urlparse(src)
        hostname = (parsed.hostname or "").lower()

        # Cloud metadata and loopback targets
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
            return False, f"Download blocked by anti-SSRF policy: {hostname} is restricted."

        # RFC 1918 private subnets
        if re.match(r"^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname) or \
           re.match(r"^192\.168\.\d{1,3}\.\d{1,3}$", hostname) or \
           re.match(r"^172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}$", hostname):
            return False, f"Download blocked by anti-SSRF policy: Private network restricted ({hostname})."

        return True, "APK URL verified and safe."

    def sanitize_notification(self, notif: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes sensitive information in a notification record, masking
        credit card and email identifiers while preserving OTP verification codes.
        """
        cleaned = dict(notif)
        for field in ("title", "text", "ticker"):
            if field in cleaned and isinstance(cleaned[field], str):
                val = cleaned[field]
                # Mask credit card numbers
                val = re.sub(r"\b(?:\d{4}[ -]?){3}\d{4}\b", "[CARD-MASKED]", val)
                # Mask email addresses
                val = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL-MASKED]", val)
                cleaned[field] = val
        return cleaned


def main():
    if len(sys.argv) < 3:
        print("Usage: python guardrails/engine.py [check-input|check-output|check-apk] <text_or_url>")
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2]
    engine = GuardrailEngine()

    if cmd == "check-input":
        allowed, res, viols = engine.validate_input(arg)
        print(f"Allowed: {allowed}")
        print(f"Result: {res}")
        if viols:
            print(f"Violations ({len(viols)}): {json.dumps(viols, indent=2)}")
    elif cmd == "check-output":
        valid, res, viols = engine.validate_output(arg)
        print(f"Valid: {valid}")
        print(f"Sanitized: {res}")
    elif cmd == "check-apk":
        allowed, reason = engine.validate_apk_source(arg)
        print(f"Safe: {allowed} ({reason})")


if __name__ == "__main__":
    main()
