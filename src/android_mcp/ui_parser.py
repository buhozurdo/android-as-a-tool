"""
UI Parser for Android uiautomator dump XML hierarchies.
Optimized for LLM token efficiency by stripping boilerplate layout nodes
and returning only actionable elements with center coordinates (cx, cy).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

# Pattern matching bounds format: "[x1,y1][x2,y2]"
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
        """Extract (x1, y1, x2, y2) from '[x1,y1][x2,y2]' bounds string."""
        if not bounds_str:
            return None
        m = BOUNDS_REGEX.match(bounds_str.strip())
        if not m:
            return None
        x1, y1, x2, y2 = map(int, m.groups())
        return (x1, y1, x2, y2)

    @staticmethod
    def compute_center(bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Calculate centroid (cx, cy) of bounding box."""
        x1, y1, x2, y2 = bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

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

        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            # Handle possible leading garbage from adb output
            first_lt = xml_bytes.find(b"<hierarchy")
            if first_lt != -1:
                try:
                    root = ET.fromstring(xml_bytes[first_lt:])
                except ET.ParseError as e:
                    return {"error": f"Failed to parse XML: {str(e)}", "elements": []}
            else:
                return {"error": "Invalid XML hierarchy format", "elements": []}

        # Deduce screen resolution from root bounds or parameter
        screen_w, screen_h = 0, 0
        root_bounds = root.attrib.get("bounds")
        if root_bounds:
            b = cls.parse_bounds(root_bounds)
            if b:
                screen_w, screen_h = b[2] - b[0], b[3] - b[1]

        if screen_bounds:
            screen_w, screen_h = screen_bounds

        elements: List[UIElement] = []

        for node in root.iter("node"):
            attrib = node.attrib
            bounds_str = attrib.get("bounds", "")
            bounds = cls.parse_bounds(bounds_str)
            if not bounds:
                continue

            x1, y1, x2, y2 = bounds
            width = x2 - x1
            height = y2 - y1

            # Discard non-visible or zero-size elements
            if width <= 0 or height <= 0:
                continue

            # Update screen bounds from top-level nodes if not yet set
            if screen_w == 0 or screen_h == 0:
                screen_w = max(screen_w, x2)
                screen_h = max(screen_h, y2)

            text = attrib.get("text", "").strip()
            desc = attrib.get("content-desc", "").strip()
            resource_id = attrib.get("resource-id", "").strip()
            cls_name = attrib.get("class", "").split(".")[-1]
            clickable = attrib.get("clickable", "false").lower() == "true"
            focusable = attrib.get("focusable", "false").lower() == "true"
            scrollable = attrib.get("scrollable", "false").lower() == "true"
            checkable = attrib.get("checkable", "false").lower() == "true"
            checked = attrib.get("checked", "false").lower() == "true"
            package = attrib.get("package", "").strip()

            is_interactive = (
                clickable
                or focusable
                or scrollable
                or checkable
                or (cls_name in ("Button", "ImageButton", "EditText", "CheckBox", "Switch", "RadioButton"))
            )
            has_content = bool(text or desc)

            # Filtering logic
            if clickable_only:
                if not (is_interactive or has_content):
                    continue
                # Skip layout containers with no semantic content
                if cls_name in ("FrameLayout", "LinearLayout", "RelativeLayout", "ViewGroup", "View") and not (is_interactive and has_content):
                    if not clickable:
                        continue

            center = cls.compute_center(bounds)

            elements.append(
                UIElement(
                    id=resource_id,
                    text=text,
                    desc=desc,
                    class_name=cls_name,
                    clickable=clickable or is_interactive,
                    center=center,
                    bounds=bounds,
                    package=package,
                    checkable=checkable,
                    checked=checked,
                    scrollable=scrollable,
                )
            )

            if len(elements) >= max_elements:
                break

        return {
            "screen": {"width": screen_w, "height": screen_h},
            "elements_count": len(elements),
            "elements": [elem.to_dict() for elem in elements],
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
