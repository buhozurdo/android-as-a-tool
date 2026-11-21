"""
UI Parser for Android uiautomator dump XML hierarchies.
Optimized for high-throughput LLM token compression and sub-millisecond execution:
- Zero-regex bounds parsing via string splitting and slicing
- Single-pass JSON dictionary generation without intermediate object allocation
- Fast frozenset attribute and class matching
- Stream-based XML parsing with element clearing for minimal memory footprint
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Pre-compiled frozensets for O(1) membership testing
INTERACTIVE_CLASSES: frozenset[str] = frozenset({
    "Button",
    "ImageButton",
    "EditText",
    "CheckBox",
    "Switch",
    "RadioButton",
    "ToggleButton",
    "CompoundButton",
    "SeekBar",
})

CONTAINER_CLASSES: frozenset[str] = frozenset({
    "FrameLayout",
    "LinearLayout",
    "RelativeLayout",
    "ViewGroup",
    "View",
    "AbsoluteLayout",
    "CoordinatorLayout",
    "DrawerLayout",
})

# Backward compatibility alias
BOUNDS_REGEX = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


@dataclass(frozen=True)
class UIElement:
    """Compact representation of an interactive or informational Android UI element."""
    id: str
    text: str
    desc: str
    class_name: str
    clickable: bool
    center: Tuple[int, int]  # (cx, cy)
    bounds: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    package: str = ""
    checkable: bool = False
    checked: bool = False
    scrollable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "class": self.class_name,
            "center": [self.center[0], self.center[1]],
            "bounds": [self.bounds[0], self.bounds[1], self.bounds[2], self.bounds[3]],
        }
        if self.id:
            d["id"] = self.id
        if self.text:
            d["text"] = self.text
        if self.desc:
            d["desc"] = self.desc
        if self.clickable:
            d["clickable"] = True
        if self.checked:
            d["checked"] = True
        if self.scrollable:
            d["scrollable"] = True
        return d


class UIParser:
    """
    Parses Android uiautomator XML into token-compact JSON representations.
    Reduces 100KB+ raw XML into ~2KB-5KB structured elements JSON.
    """

    @staticmethod
    def parse_bounds(bounds_str: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Fast zero-regex bounds parser.
        Extracts (x1, y1, x2, y2) from '[x1,y1][x2,y2]' bounds string.
        """
        if not bounds_str:
            return None
        s = bounds_str.strip()
        # Must match format '[x1,y1][x2,y2]'
        if len(s) < 9 or s[0] != "[" or s[-1] != "]":
            return None
        split_idx = s.find("][")
        if split_idx == -1:
            return None

        try:
            p1 = s[1:split_idx]
            p2 = s[split_idx + 2:-1]
            c1 = p1.find(",")
            c2 = p2.find(",")
            if c1 == -1 or c2 == -1:
                return None
            x1 = int(p1[:c1])
            y1 = int(p1[c1 + 1:])
            x2 = int(p2[:c2])
            y2 = int(p2[c2 + 1:])
            return (x1, y1, x2, y2)
        except (ValueError, IndexError):
            return None

    @staticmethod
    def compute_center(bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Calculate centroid (cx, cy) of bounding box."""
        return ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)

    @classmethod
    def parse(
        cls,
        xml_content: str | bytes,
        clickable_only: bool = True,
        max_elements: int = 150,
        screen_bounds: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Parse XML hierarchy and return token-compressed dictionary of elements.

        Args:
            xml_content: Raw XML from `uiautomator dump`.
            clickable_only: If True, only keep clickable/interactive/text elements.
            max_elements: Safety cap on elements returned to prevent token explosion.
            screen_bounds: Optional (width, height) override.

        Returns:
            Dict containing screen resolution, element count, and compact elements list.
        """
        if isinstance(xml_content, str):
            xml_bytes = xml_content.strip().encode("utf-8")
        else:
            xml_bytes = xml_content.strip()

        if not xml_bytes:
            return {"screen": {"width": 0, "height": 0}, "elements_count": 0, "elements": []}

        # Check for possible leading garbage from adb before <hierarchy
        if not xml_bytes.startswith(b"<?xml") and not xml_bytes.startswith(b"<hierarchy"):
            first_lt = xml_bytes.find(b"<hierarchy")
            if first_lt != -1:
                xml_bytes = xml_bytes[first_lt:]
            else:
                return {"error": "Invalid XML hierarchy format", "elements": [], "elements_count": 0}

        screen_w, screen_h = 0, 0
        if screen_bounds:
            screen_w, screen_h = screen_bounds

        elements: List[Dict[str, Any]] = []

        try:
            # Event-driven stream parsing with node clearing for ultra-fast throughput
            context = ET.iterparse(io.BytesIO(xml_bytes), events=("start", "end"))

            for event, elem in context:
                if event == "start" and elem.tag == "node" and screen_w == 0:
                    b_top = cls.parse_bounds(elem.attrib.get("bounds", ""))
                    if b_top:
                        screen_w = b_top[2] - b_top[0]
                        screen_h = b_top[3] - b_top[1]

                elif event == "end" and elem.tag == "node":
                    attrib = elem.attrib
                    bounds_str = attrib.get("bounds", "")
                    bounds = cls.parse_bounds(bounds_str)

                    if bounds is not None:
                        x1, y1, x2, y2 = bounds
                        width = x2 - x1
                        height = y2 - y1

                        if width > 0 and height > 0:
                            if screen_w == 0:
                                screen_w = max(screen_w, x2)
                                screen_h = max(screen_h, y2)

                            cls_raw = attrib.get("class", "")
                            dot_idx = cls_raw.rfind(".")
                            cls_name = cls_raw[dot_idx + 1:] if dot_idx != -1 else cls_raw

                            clickable = attrib.get("clickable") == "true"
                            focusable = attrib.get("focusable") == "true"
                            scrollable = attrib.get("scrollable") == "true"
                            checkable = attrib.get("checkable") == "true"
                            checked = attrib.get("checked") == "true"

                            is_interactive = (
                                clickable
                                or focusable
                                or scrollable
                                or checkable
                                or (cls_name in INTERACTIVE_CLASSES)
                            )

                            text = attrib.get("text", "").strip()
                            desc = attrib.get("content-desc", "").strip()
                            has_content = bool(text or desc)

                            # Filtering logic
                            include = True
                            if clickable_only:
                                if not (is_interactive or has_content):
                                    include = False
                                elif cls_name in CONTAINER_CLASSES and not (is_interactive and has_content):
                                    if not clickable:
                                        include = False

                            if include:
                                elem_dict: Dict[str, Any] = {
                                    "class": cls_name,
                                    "center": [(x1 + x2) // 2, (y1 + y2) // 2],
                                    "bounds": [x1, y1, x2, y2],
                                }
                                resource_id = attrib.get("resource-id", "").strip()
                                if resource_id:
                                    elem_dict["id"] = resource_id
                                if text:
                                    elem_dict["text"] = text
                                if desc:
                                    elem_dict["desc"] = desc
                                if clickable or is_interactive:
                                    elem_dict["clickable"] = True
                                if checked:
                                    elem_dict["checked"] = True
                                if scrollable:
                                    elem_dict["scrollable"] = True

                                elements.append(elem_dict)

                    # Free element memory immediately
                    elem.clear()

                    if len(elements) >= max_elements:
                        break

        except ET.ParseError as e:
            return {"error": f"Failed to parse XML: {str(e)}", "elements": [], "elements_count": 0}

        return {
            "screen": {"width": screen_w, "height": screen_h},
            "elements_count": len(elements),
            "elements": elements,
        }

    @classmethod
    def find_by_text(cls, elements_payload: Dict[str, Any], query: str, exact: bool = False) -> List[Dict[str, Any]]:
        """Find interactive elements matching a text query (case-insensitive)."""
        q = query.lower()
        results = []
        for elem in elements_payload.get("elements", []):
            text = elem.get("text", "").lower()
            desc = elem.get("desc", "").lower()
            if exact:
                if q == text or q == desc:
                    results.append(elem)
            else:
                if q in text or q in desc:
                    results.append(elem)
        return results

    @classmethod
    def find_by_id(cls, elements_payload: Dict[str, Any], resource_id: str) -> List[Dict[str, Any]]:
        """Find elements matching a resource-id (suffix or exact)."""
        rid = resource_id.lower()
        results = []
        for elem in elements_payload.get("elements", []):
            elem_id = elem.get("id", "").lower()
            if rid == elem_id or elem_id.endswith(f":id/{rid}"):
                results.append(elem)
        return results
