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

SOURCE = Path("notes/diagrams/reference.drawio")
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
        "notes/diagrams/reference-page1.svg": _ref_page(diagrams[0]),
        "notes/diagrams/reference-mvc.svg": _ref_page(diagrams[1]),
    }


def implementation_svg(root: Path) -> str:
    """Derive an SVG of real tracked Python modules and package imports."""
    source_root = root / "packages"
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "packages/*.py", "packages/**/*.py"],
        capture_output=True,
        check=True,
    ).stdout.split(bytes([0]))
    grouped = {}
    deps = Counter()
    for raw in tracked:
        if not raw:
            continue
        file = root / raw.decode("utf-8")
        if not file.is_file() or file.suffix != ".py":
            continue
        path = file.relative_to(source_root)
        group = path.parts[0]
        grouped[group] = grouped.get(group, 0) + 1
        try:
            module = ast.parse(file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(module):
            targets = []
            if isinstance(node, ast.Import):
                targets = [name.name.split(".")[0] for name in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module.split(".")[0]]
            for target in targets:
                if target != group and target in ("engine", "chess", "checkers"):
                    deps[(group, target)] += 1
    for package in ("engine", "chess", "checkers"):
        if (source_root / package / "__init__.py").exists():
            grouped.setdefault(package, 0)
    order = sorted(grouped, key=lambda name: (name != "engine", name))
    width = 880
    height = 160 + max(len(order), 1) * 155
    output = [
        f'{SVG_HEAD} viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        'aria-label="Generated architecture of installed Python packages">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="40" y="44" {FONT} font-size="22" font-weight="bold" fill="#101828">'
        "Implemented Python Package Architecture</text>",
        f'<text x="40" y="69" {FONT} font-size="12" fill="#475467">'
        "Generated from tracked package files and Python import statements</text>",
    ]
    for index, group in enumerate(order):
        y = 98 + index * 155
        count = grouped[group]
        output += [
            f'<rect x="40" y="{y}" rx="12" width="800" height="118" '
            'fill="#f8faff" stroke="#98a2b3" stroke-width="1.5"/>',
            f'<text x="61" y="{y+35}" {FONT} font-size="20" font-weight="bold" '
            f'fill="#1d2939">{escape("packages/" + group + "/")}</text>',
            f'<text x="61" y="{y+61}" {FONT} font-size="14" fill="#475467">'
            f'{count} tracked Python module{"" if count == 1 else "s"}</text>',
        ]
        outgoing = [(other, n) for (origin, other), n in sorted(deps.items()) if origin == group]
        description = ", ".join(f"imports {other} ({n})" for other, n in outgoing)
        if not description:
            description = "No top-level cross-package imports detected"
        output.append(
            f'<text x="61" y="{y+87}" {FONT} font-size="13" fill="#667085">'
            f"{escape(description)}</text>"
        )
    output.append("</svg>")
    return "\n".join(output) + "\n"



def implementation_classes_svg(root: Path) -> str:
    """Generate a UML-style inventory and inheritance edges from real ASTs."""
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "packages"],
        capture_output=True,
        check=True,
    ).stdout.split(bytes([0]))
    found = []
    for raw in tracked:
        if not raw:
            continue
        path = root / raw.decode("utf-8")
        if path.suffix != ".py" or not path.is_file():
            continue
        module = ".".join(path.relative_to(root / "packages").with_suffix("").parts)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [ast.unparse(base) for base in node.bases]
            methods = [
                entry.name
                for entry in node.body
                if isinstance(entry, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not entry.name.startswith("_")
            ]
            found.append((module, node.name, bases, methods))
    found.sort(key=lambda x: (x[0], x[1]))
    columns = [[], [], []]
    for record in found:
        module = record[0]
        if module.startswith("engine.model.game"):
            col = 0
        elif module.startswith("engine.model.pieces"):
            col = 1
        else:
            col = 2
        columns[col].append(record)
    card_w, card_h, gap_y = 448, 124, 16
    width = 1480
    height = 146 + max((len(items) for items in columns), default=0) * (card_h + gap_y)
    positions = {}
    for column, entries in enumerate(columns):
        for row, (_, name, _, _) in enumerate(entries):
            positions[(column, row)] = (32 + column * 492, 104 + row * (card_h + gap_y))
    output = [
        f'{SVG_HEAD} viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        'aria-label="Implementation class diagram extracted from Python AST">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="32" y="39" {FONT} font-size="24" font-weight="bold" fill="#101828">'
        'Implemented Class Model (Generated)</text>',
        f'<text x="32" y="70" {FONT} font-size="14" fill="#475467">'
        f'{len(found)} classes found in tracked packages/ Python files; inheritance extracted from AST</text>',
    ]
    by_name = {}
    for column, entries in enumerate(columns):
        for row, (_, name, _, _) in enumerate(entries):
            by_name.setdefault(name, []).append(positions[(column, row)])
    for column, entries in enumerate(columns):
        for row, (_, _, bases, _) in enumerate(entries):
            x, y = positions[(column, row)]
            for base in bases:
                if base.split(".")[-1] not in by_name:
                    continue
                if len(by_name[base.split(".")[-1]]) != 1:
                    continue
                parent_x, parent_y = by_name[base.split(".")[-1]][0]
                if (x, y) == (parent_x, parent_y):
                    continue
                x1, y1 = x + card_w / 2, y + card_h / 2
                x2, y2 = parent_x + card_w / 2, parent_y + card_h / 2
                output.append(
                    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                    'stroke="#667085" stroke-width="1.5" opacity="0.45" stroke-dasharray="7 4"/>'
                )
    for column, entries in enumerate(columns):
        for row, (module, name, bases, methods) in enumerate(entries):
            x, y = positions[(column, row)]
            base_label = "Extends " + ", ".join(bases) if bases else "Class"
            method_label = ", ".join(methods[:4]) if methods else "(no public methods)"
            if len(methods) > 4:
                method_label += ", ..."
            output.extend([
                f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="9" '
                'fill="#f8faff" stroke="#98a2b3" stroke-width="1.5"/>',
                f'<rect x="{x}" y="{y}" width="{card_w}" height="39" rx="9" '
                'fill="#edf2ff"/>',
                f'<text x="{x+14}" y="{y+26}" {FONT} font-size="17" font-weight="bold" '
                f'fill="#101828">{escape(name)}</text>',
                f'<text x="{x+14}" y="{y+60}" {FONT} font-size="11" fill="#475467">'
                f'{escape(module)}</text>',
                f'<text x="{x+14}" y="{y+80}" {FONT} font-size="12" fill="#344054">'
                f'{escape(base_label[:61])}</text>',
                f'<text x="{x+14}" y="{y+102}" {FONT} font-size="12" fill="#344054">'
                f'{escape(method_label[:61])}</text>',
            ])
    output.append("</svg>")
    return "\n".join(output) + "\n"


def generated_assets(root: Path) -> dict[str, str]:
    """Produce diagrams consumed as virtual documentation assets."""
    reference = (root / SOURCE).read_text(encoding="utf-8")
    return {
        **reference_svgs(reference),
        "notes/diagrams/implementation.svg": implementation_svg(root),
        "notes/diagrams/implementation-classes.svg": implementation_classes_svg(root),
    }


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    for name, svg in generated_assets(repo).items():
        dest = repo / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(svg, encoding="utf-8")
        print(name)
