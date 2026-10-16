"""Build a lossless, cross-language syntax forest for every Git-tracked file.

There is no configured source-directory, package-name, language or file exclusion.
The repository's only required declaration is repo.dfconfig. Parsed files retain
*every* grammar node (named and anonymous); all files retain their exact source
bytes, making the output reconstructable rather than an illustrative UML.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


def tracked_paths(root: Path) -> list[Path]:
    """Enumerate the repository's actual tracked regular files, including dotfiles."""
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        check=True,
        capture_output=True,
    ).stdout
    paths = [
        root / raw.decode("utf-8", errors="surrogateescape") for raw in listing.split(b"\0") if raw
    ]
    return sorted(
        (p for p in paths if p.is_file() or p.is_symlink()),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def parse_language(path: Path) -> str | None:
    """Detect languages by filename/extension using the installed grammar registry."""
    from tree_sitter_language_pack import detect_language

    if path.name.endswith(".dfconfig"):
        return "json"
    return detect_language(path.as_posix())


def _source_dependencies(path: str, language: str | None, source: bytes) -> list[str]:
    """Extract explicit import specifiers only; never invent dependency edges."""
    text = source.decode("utf-8", errors="replace")
    names: list[str] = []
    if language == "python":
        import ast

        try:
            tree = ast.parse(text)
        except SyntaxError:
            return names
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append("." * node.level + (node.module or ""))
    elif language in {"javascript", "typescript", "tsx", "jsx"}:
        names.extend(
            re.findall(
                r"""(?:\bfrom\s*|\bimport\s*\(|\brequire\s*\()\s*['"]([^'"]+)['"]""",
                text,
            )
        )
        names.extend(re.findall(r"""\bimport\s*['"]([^'"]+)['"]""", text))
    return sorted(set(n for n in names if n))


def _resolve_import(path: str, spec: str, candidates: set[str]) -> str | None:
    """Find only unambiguous paths whose existence is demonstrated by Git."""
    current = PurePosixPath(path)
    if spec.startswith("."):
        if spec.startswith("./") or spec.startswith("../"):
            parts = list(current.parent.parts)
            for segment in spec.split("/"):
                if segment == "..":
                    if parts:
                        parts.pop()
                elif segment not in {"", "."}:
                    parts.append(segment)
        else:
            dots = len(spec) - len(spec.lstrip("."))
            parts = list(current.parent.parts)
            for _ in range(max(0, dots - 1)):
                if parts:
                    parts.pop()
            parts.extend(p for p in spec.lstrip(".").split(".") if p)
        stem = "/".join(parts)
    else:
        stem = spec.replace(".", "/") if "/" not in spec else spec
    matches = [
        name
        for name in candidates
        if name == stem
        or name.rsplit(".", 1)[0] == stem
        or name.rsplit(".", 1)[0] == stem + "/index"
        or name.rsplit(".", 1)[0] == stem + "/__init__"
        or name.endswith("/" + stem + ".py")
        or name.endswith("/" + stem + "/__init__.py")
    ]
    return matches[0] if len(matches) == 1 else None


def build_forest(root: Path) -> dict[str, Any]:
    """Preserve the complete tracked source and concrete syntax tree of each file."""
    if not (root / "repo.dfconfig").is_file():
        raise FileNotFoundError("The authoritative repo.dfconfig is required")
    from tree_sitter_language_pack import get_parser

    files: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    dependencies: set[tuple[str, str]] = set()
    paths = tracked_paths(root)
    candidates = {p.relative_to(root).as_posix() for p in paths}

    for source_path in paths:
        path = source_path.relative_to(root).as_posix()
        is_link = source_path.is_symlink()
        source = os.readlink(source_path).encode("utf-8") if is_link else source_path.read_bytes()
        language = None if is_link else parse_language(source_path)
        record: dict[str, Any] = {
            "path": path,
            "kind": "symlink" if is_link else "file",
            "language": language,
            "sha256": hashlib.sha256(source).hexdigest(),
            "size": len(source),
            "source_base64": base64.b64encode(source).decode("ascii"),
            "root": None,
            "parse_error": False,
        }
        if language is not None:
            parser = get_parser(language)
            tree = parser.parse(source)
            record["parse_error"] = tree.root_node.has_error
            # Preorder over ALL syntax children, not named_children, so punctuation,
            # comments and anonymous grammar tokens are not discarded.
            stack = [(tree.root_node, None, None)]
            while stack:
                node, parent, field = stack.pop()
                index = len(nodes)
                nodes.append(
                    {
                        "id": index,
                        "file": len(files),
                        "parent": parent,
                        "field": field,
                        "type": node.type,
                        "named": node.is_named,
                        "start": node.start_byte,
                        "end": node.end_byte,
                        "start_point": list(node.start_point),
                        "end_point": list(node.end_point),
                        "children": [],
                    }
                )
                if parent is not None:
                    nodes[parent]["children"].append(index)
                elif record["root"] is None:
                    record["root"] = index
                for child_index in range(node.child_count - 1, -1, -1):
                    stack.append(
                        (
                            node.children[child_index],
                            index,
                            node.field_name_for_child(child_index),
                        )
                    )
        for spec in _source_dependencies(path, language, source):
            resolved = _resolve_import(path, spec, candidates)
            if resolved and resolved != path:
                dependencies.add((path, resolved))
        files.append(record)
    return {
        "schema": 1,
        "files": files,
        "nodes": nodes,
        "dependencies": [list(edge) for edge in sorted(dependencies)],
    }


def mermaid(forest: dict[str, Any]) -> str:
    """Emit one complete Mermaid tree: paths, cross-package imports and every AST node."""

    def label(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", " ")
        )

    lines = ["flowchart TD", '  repository["Repository"]']
    directories = set()
    file_numbers = {item["path"]: i for i, item in enumerate(forest["files"])}
    for i, file in enumerate(forest["files"]):
        path = PurePosixPath(file["path"])
        parent = "repository"
        acc: list[str] = []
        for part in path.parts[:-1]:
            acc.append(part)
            key = "/".join(acc)
            node_id = "d" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
            if key not in directories:
                lines.append(f'  {node_id}["{label(part)}/"]')
                lines.append(f"  {parent} --> {node_id}")
                directories.add(key)
            parent = node_id
        lines.append(f'  f{i}["{label(path.name)} ({label(file["language"] or "asset")})"]')
        lines.append(f"  {parent} --> f{i}")
        if file["root"] is not None:
            lines.append(f"  f{i} --> n{file['root']}")
    for node in forest["nodes"]:
        descriptor = node["type"]
        if node["field"]:
            descriptor = f'{node["field"]}: {descriptor}'
        lines.append(f'  n{node["id"]}["{label(descriptor)}"]')
        for child in node["children"]:
            lines.append(f'  n{node["id"]} --> n{child}')
    for source, dest in forest["dependencies"]:
        lines.append(f"  f{file_numbers[source]} -. import .-> f{file_numbers[dest]}")
    return "\n".join(lines) + "\n"


def viewer() -> str:
    """Render every node on demand; expanding a branch never discards its children."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Repository AST Explorer</title>
<style>
body{font:14px system-ui,sans-serif;margin:2rem;max-width:1000px}
details{padding:.15rem 0 .15rem 1rem;border-left:1px solid #bbb}
summary{cursor:pointer;white-space:pre-wrap}
small{color:#566}
</style></head><body>
<h1>Repository AST</h1>
<p>Every tracked file and every concrete parser node, including anonymous tokens.
Expand nodes to inspect the full hierarchy. The JSON contains exact original bytes;
the Mermaid file contains a single source tree with cross-file import edges.</p>
<p><a href="./repository.json">Complete AST JSON</a> |
<a href="./repository.mmd">Single Mermaid graph</a></p>
<div id="tree" role="tree">Loading…</div>
<script>
(async () => {
 const response=await fetch("./repository.json");
 if(!response.ok) throw Error("AST JSON unavailable");
 const model=await response.json();
 const root=document.getElementById("tree");root.textContent="";
 const grouped=new Map();
 model.files.forEach((file,i)=>{
   const parts=file.path.split("/");let prefix="";
   parts.slice(0,-1).forEach((part,j)=>{
     const current=prefix;prefix+=(j?"/":"")+part;
     const group=grouped.get(current)||[];
     if(!group.some(x=>x.kind==="folder"&&x.path===prefix))
       group.push({kind:"folder",path:prefix,label:part+"/"});
     grouped.set(current,group);
   });
   const group=grouped.get(prefix)||[];
   group.push({kind:"file",index:i,label:parts.at(-1)});
   grouped.set(prefix,group);
 });
 function branch(title,load){
   const box=document.createElement("details"),heading=document.createElement("summary");
   heading.textContent=title;box.append(heading);
   box.addEventListener("toggle",()=>{
     if(box.open&&!box.dataset.loaded){box.dataset.loaded="1";load(box);}
   });return box;
 }
 function addNode(parent,id){
   const node=model.nodes[id];
   const label=(node.field?node.field+": ":"")+node.type+" ["+node.start+".."+node.end+"]";
   if(!node.children.length){
     const span=document.createElement("div");span.textContent=label;
     span.style.paddingLeft="1rem";parent.append(span);return;
   }
   parent.append(branch(label,box=>node.children.forEach(child=>addNode(box,child))));
 }
 function addGroup(parent,path){
   (grouped.get(path)||[]).forEach(item=>{
     if(item.kind==="folder"){parent.append(branch(item.label,box=>addGroup(box,item.path)));return;}
     const file=model.files[item.index];
     parent.append(branch(item.label+" • "+(file.language||"asset")+", "+file.size+" bytes",box=>{
       if(file.root===null){box.append("Binary or unparsed file: source bytes in JSON.");return;}
       addNode(box,file.root);
     }));
   });
 }
 addGroup(root,"");
 const stats=document.createElement("small");
 stats.textContent=model.files.length+" files · "+model.nodes.length+" AST nodes · "+
   model.dependencies.length+" resolved cross-file imports";
 root.before(stats);
})().catch(err=>{document.getElementById("tree").textContent=String(err)});
</script></body></html>
"""


def generated_assets(root: Path) -> dict[str, str]:
    """Create renderable and machine-reconstructable data from one traversal."""
    forest = build_forest(root)
    return {
        "architecture/ast/repository.json": json.dumps(
            forest, ensure_ascii=False, separators=(",", ":")
        ),
        "architecture/ast/repository.mmd": mermaid(forest),
        "architecture/ast/viewer.html": viewer(),
    }


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[2]
    output = repository / "site"
    for name, data in generated_assets(repository).items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
        print(f"{name}: {len(data):,} bytes")
