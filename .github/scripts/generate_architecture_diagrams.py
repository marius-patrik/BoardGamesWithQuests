"""Generate faithful reference and live implementation diagrams for documentation.

Reference SVGs are rendered from the original diagrams.net mxGraphModel,
never from inferred class names. The implementation SVG is derived on each
documentation build from tracked Python imports, not manually edited.
"""

from __future__ import annotations

import ast
from collections import Counter
from html import escape, unescape
from pathlib import Path
import re
import subprocess
from xml.etree import ElementTree as ET

SOURCE = Path(".agents/notes/diagrams/reference.drawio")
SVG_HEAD = '<svg xmlns="http://www.w3.org/2000/svg" role="img"'
FONT = 'font-family="DejaVu Sans,Arial,sans-serif"'


def _label(raw: str) -> str:
    """Normalize labels from draw.io's text/html attributes."""
    raw = re.sub(r"(?i)<br\s*/?>|</div>|</p>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return unescape(raw).strip()


def _ref_page(diagram: ET.Element) -> str:
    """Render a page from the actual source geometry and labels."""
    graph = diagram.find("./mxGraphModel/root")
    if graph is None:
        raise ValueError("reference diagram has no mxGraphModel")
    cells = {cell.get("id"): cell for cell in graph if cell.tag == "mxCell"}
    positions = {}

    def position(cell):
        ident = cell.get("id")
        if ident in positions:
            return positions[ident]
        geometry = cell.find("mxGeometry")
        if geometry is None:
            return (0.0, 0.0, 0.0, 0.0)
        x = float(geometry.get("x", "0"))
        y = float(geometry.get("y", "0"))
        width = float(geometry.get("width", "0"))
        height = float(geometry.get("height", "0"))
        parent = cells.get(cell.get("parent"))
        if parent is not None and parent.get("vertex") == "1":
            px, py, _, _ = position(parent)
            x, y = x + px, y + py
        positions[ident] = (x, y, width, height)
        return positions[ident]

    vertices = [
        item
        for item in cells.values()
        if item.get("vertex") == "1"
        and "edgeLabel" not in item.get("style", "")
        and item.find("mxGeometry") is not None
    ]
    bounds = [position(item) for item in vertices]
    if not bounds:
        raise ValueError("reference diagram has no shapes")
    left = min(box[0] for box in bounds) - 36
    top = min(box[1] for box in bounds) - 36
    right = max(box[0] + box[2] for box in bounds) + 36
    bottom = max(box[1] + box[3] for box in bounds) + 36
    output = [
        f'{SVG_HEAD} viewBox="{left:.0f} {top:.0f} {right-left:.0f} {bottom-top:.0f}" '
        f'width="{right-left:.0f}" height="{bottom-top:.0f}" '
        f'aria-label="Reference architecture: {escape(diagram.get("name", ""))}">',
        '<rect x="-10000" y="-10000" width="30000" height="30000" fill="#ffffff"/>',
    ]

    # Connections render behind boxes. mxGeometry waypoint points are preserved.
    for cell in graph:
        if cell.get("edge") != "1":
            continue
        first = cells.get(cell.get("source"))
        last = cells.get(cell.get("target"))
        geometry = cell.find("mxGeometry")
        if first is not None:
            x, y, w, h = position(first)
            start = (x + w / 2, y + h / 2)
        elif (
            geometry is not None
            and geometry.find("./mxPoint[@as='sourcePoint']") is not None
            and all(
                geometry.find("./mxPoint[@as='sourcePoint']").get(axis) is not None
                for axis in ("x", "y")
            )
        ):
            p = geometry.find("./mxPoint[@as='sourcePoint']")
            start = (float(p.get("x")), float(p.get("y")))
        else:
            continue
        if last is not None:
            x, y, w, h = position(last)
            end = (x + w / 2, y + h / 2)
        elif (
            geometry is not None
            and geometry.find("./mxPoint[@as='targetPoint']") is not None
            and all(
                geometry.find("./mxPoint[@as='targetPoint']").get(axis) is not None
                for axis in ("x", "y")
            )
        ):
            p = geometry.find("./mxPoint[@as='targetPoint']")
            end = (float(p.get("x")), float(p.get("y")))
        else:
            continue
        waypoints = []
        if geometry is not None:
            points = geometry.find("./Array[@as='points']")
            if points is not None:
                waypoints = [
                    (float(p.get("x")), float(p.get("y")))
                    for p in points
                    if p.get("x") is not None and p.get("y") is not None
                ]
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in [start, *waypoints, end])
        output.append(
            f'<polyline points="{points}" fill="none" stroke="#667085" stroke-width="1.7"/>'
        )

    for cell in vertices:
        x, y, w, h = position(cell)
        style = cell.get("style", "")
        label = _label(cell.get("value", ""))
        if "swimlane" in style:
            output.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                'fill="#fcfdff" stroke="#344054" stroke-width="1.2"/>'
            )
            output.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="26" fill="#eef2ff"/>'
            )
            output.append(
                f'<text x="{x+w/2:.1f}" y="{y+18:.1f}" text-anchor="middle" '
                f'{FONT} font-weight="bold" font-size="13" fill="#1d2939">{escape(label)}</text>'
            )
        elif style.startswith("line"):
            output.append(
                f'<path d="M{x:.1f},{y+4:.1f} h{w:.1f}" stroke="#98a2b3" stroke-width="1"/>'
            )
        elif label:
            for line_number, line in enumerate(label.split("\n")[:4]):
                output.append(
                    f'<text x="{x+4:.1f}" y="{y+15+15*line_number:.1f}" '
                    f'{FONT} font-size="11" fill="#344054">{escape(line)}</text>'
                )
    output.append("</svg>")
    return "\n".join(output) + "\n"


def reference_svgs(source: str) -> dict[str, str]:
    """Export each original diagrams.net page as an independently embeddable SVG."""
    root = ET.fromstring(source)
    if root.tag != "mxfile":
        raise ValueError("not an original draw.io document")
    diagrams = root.findall("diagram")
    if len(diagrams) < 2:
        raise ValueError("reference diagram is missing one of its two pages")
    return {
        "agents/notes/diagrams/reference-page1.svg": _ref_page(diagrams[0]),
        "agents/notes/diagrams/reference-mvc.svg": _ref_page(diagrams[1]),
    }


def implementation_svg(root: Path) -> str:
    """Render connected UML components and dependencies from actual imports."""
    from render_implementation_uml import render_component_diagram

    return render_component_diagram(root)


def implementation_classes_svg(root: Path) -> str:
    """Render reference-style class compartments and actual relationships."""
    from render_implementation_uml import render_class_diagram

    return render_class_diagram(root)


def generated_assets(root: Path) -> dict[str, str]:
    """Produce diagrams consumed as virtual documentation assets."""
    reference = (root / SOURCE).read_text(encoding="utf-8")
    return {
        **reference_svgs(reference),
        "agents/notes/diagrams/implementation.svg": implementation_svg(root),
        "agents/notes/diagrams/implementation-classes.svg": implementation_classes_svg(root),
    }


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    for name, svg in generated_assets(repo).items():
        # The public Docs URL omits the leading dot from .agents.
        dest = repo / ("." + name if name.startswith("agents/") else name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(svg, encoding="utf-8")
        print(name)
