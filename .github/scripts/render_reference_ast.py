#!/usr/bin/env python3
"""Render the supported Mermaid AST flowchart grammar into a deterministic reference SVG.

Every node and every edge in AST.mmd is included. The source file is authoritative;
Graphviz is used only as a layout engine because the graph has thousands of nodes.
The renderer fails closed on unrecognized Mermaid statements instead of silently
omitting architecture declarations or action-expression edges.
"""
from __future__ import annotations
import argparse
import html
import hashlib
import re
import subprocess
from pathlib import Path

SOURCE = Path('.agents/notes/requirements/AST.mmd')
OUTPUT = Path('.agents/notes/requirements/diagrams/reference_AST.svg')
NODE = re.compile(r'^\s*([A-Za-z][A-Za-z0-9_]*)\["((?:[^"\\]|\\.)*)"\]\s*$')
EDGE = re.compile(r'^\s*([A-Za-z][A-Za-z0-9_]*)\s+(?:-->|-\.->)\s*(?:\|"?([^|]*)"?\|\s*)?([A-Za-z][A-Za-z0-9_]*)\s*$')
SUBGRAPH = re.compile(r'^\s*subgraph\s+([A-Za-z0-9_]+)\["([^"]*)"\]\s*$')


def dot_quote(s: str) -> str:
    """Escape a Mermaid label for a quoted DOT string without interpreting markup."""
    return '"' + s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n') + '"'


def parse_mermaid(source: str) -> tuple[dict[str,str],list[tuple[str,str,str]]]:
    """Read the flowchart's complete node/edge declaration set; reject unsupported syntax."""
    nodes: dict[str,str] = {}
    edges: list[tuple[str,str,str]] = []
    stack: list[str] = []
    for index,line in enumerate(source.splitlines(),1):
        item=line.strip()
        if not item or item.startswith('%%') or item=='flowchart TB':continue
        if item=='end':
            if not stack:raise ValueError(f'{index}: unmatched end')
            stack.pop();continue
        match=SUBGRAPH.fullmatch(line)
        if match: stack.append(match.group(1));continue
        match=NODE.fullmatch(line)
        if match:
            name,label=match.groups()
            if name in nodes:raise ValueError(f'{index}: duplicate {name}')
            label=html.unescape(label).replace('<br/>','\n')
            nodes[name]=label
            continue
        match=EDGE.fullmatch(line)
        if match:
            start,label,end=match.groups()
            edges.append((start,end,html.unescape((label or '').strip('" '))))
            continue
        raise ValueError(f'{index}: unrecognized Mermaid syntax {item[:130]!r}')
    if stack:raise ValueError(f'unclosed subgraphs: {stack}')
    for start,end,_ in edges:
        if start not in nodes or end not in nodes:
            raise ValueError(f'edge references undeclared node: {start} -> {end}')
    return nodes,edges


def make_dot(nodes: dict[str,str], edges: list[tuple[str,str,str]]) -> str:
    """Generate a stable DOT layout preserving every Mermaid node and edge."""
    lines=['digraph reference_AST {', 'graph [layout=sfdp, bgcolor="transparent", overlap=prism, outputorder=edgesfirst, start=42, maxiter=200];', 'node [shape=box, style="rounded,filled", fillcolor="#f7f9fc", color="#68778a", fontname="DejaVu Sans", fontsize=9, margin="0.10,0.06"];', 'edge [color="#93a0af", arrowsize=0.4, penwidth=0.7];']
    for name,label in nodes.items():
        # Graphviz's XML text escapes labels; do not allow embedded HTML or SVG scripts.
        lines.append(name+' [label='+dot_quote(label)+'];')
    for start,end,label in edges:
        lines.append(f'{start} -> {end}'+(' [label='+dot_quote(label)+']' if label else '')+';')
    lines.append('}')
    return '\n'.join(lines)+'\n'


def render_reference_ast(source_path: Path=SOURCE, output_path: Path=OUTPUT) -> tuple[int,int]:
    """Regenerate reference_AST.svg from the complete Mermaid graph using Graphviz."""
    nodes,edges=parse_mermaid(source_path.read_text(encoding='utf-8'))
    dot=make_dot(nodes,edges)
    p=subprocess.run(['sfdp','-Tsvg','-Gstart=42'],input=dot.encode('utf-8'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=240)
    if p.returncode:
        raise RuntimeError('Graphviz could not render the AST: '+p.stderr.decode('utf-8',errors='replace')[:2000])
    if b'<svg' not in p.stdout:raise RuntimeError('Renderer produced no SVG')
    output_path.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(source_path.read_bytes()).hexdigest()
    provenance=f'<!-- Mermaid-source-sha256: {digest}; nodes: {len(nodes)}; edges: {len(edges)} -->\n'.encode('ascii')
    data=p.stdout.replace(b'<svg ', provenance+b'<svg ',1)
    output_path.write_bytes(data)
    return len(nodes),len(edges)


def main() -> None:
    """Render or check the committed SVG from its normative .mmd source."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--check',action='store_true',help='Validate the committed SVG provenance without re-rendering')
    args=parser.parse_args()
    if args.check:
        nodes,edges=parse_mermaid(args.source.read_text(encoding='utf-8'))
        expected=f'Mermaid-source-sha256: {hashlib.sha256(args.source.read_bytes()).hexdigest()}; nodes: {len(nodes)}; edges: {len(edges)}'
        if not args.output.exists() or expected not in args.output.read_text(encoding='utf-8'):
            raise SystemExit('reference_AST.svg is missing or stale; regenerate from AST.mmd')
        print(f'AST reference verified: {len(nodes)} nodes / {len(edges)} edges')
        return
    nodes,edges=render_reference_ast(args.source,args.output)
    print(f'AST rendered: {nodes} nodes / {edges} edges / {args.output.stat().st_size} bytes')

if __name__ == '__main__':main()
