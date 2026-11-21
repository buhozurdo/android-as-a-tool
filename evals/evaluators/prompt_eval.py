"""
Evaluador modular para pruebas individuales y aserciones de prompts en Android-MCP.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from guardrails.engine import GuardrailEngine


class PromptEvaluator:
    """Evaluador individual de prompts y seguridad para herramientas de Android."""

    def __init__(self):
        self.engine = GuardrailEngine()

    def evaluate_apk_source(self, url_or_path: str) -> Tuple[bool, str]:
        return self.engine.validate_apk_source(url_or_path)

    def evaluate_text_input(self, text: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        return self.engine.validate_input(text)

    def evaluate_json_contract(self, json_str: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        return self.engine.validate_output(json_str, is_json_required=True)
