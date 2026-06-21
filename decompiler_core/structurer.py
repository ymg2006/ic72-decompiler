from __future__ import annotations

from typing import Any, Mapping
import re

from .ast_nodes import RawPHP
from .engine import Decompiler
from .ir import build_ir
from .op_cfg import build_cfg, compute_dominators, compute_postdominators, find_back_edges
from .php_renderer import render
from .cfg_targets import TargetResolver
from .exception_regions import recover_exception_regions


def cfg_summary(op_array: Mapping[str, Any]) -> str:
    d = Decompiler(op_array)
    ir = build_ir(op_array, expr_resolver=d.expr)
    cfg = build_cfg(ir)
    dom = compute_dominators(cfg)
    pdom = compute_postdominators(cfg)
    back_edges = find_back_edges(cfg, dom)
    resolver = TargetResolver(list(op_array.get("opcodes") or []))
    exceptions = recover_exception_regions(op_array, resolver)
    return (
        f"CFG/AST summary: blocks={len(cfg.blocks)}; edges={sum(len(b.successors) for b in cfg.blocks.values())}; "
        f"exits={len(cfg.exit_blocks())}; back_edges={len(back_edges)}; exception_regions={len(exceptions)}; "
        f"postdom_sets={len(pdom)}."
    )


def ensure_defined_goto_labels(lines: list[str]) -> list[str]:
    gotos: set[str] = set()
    labels: set[str] = set()
    for line in lines:
        for m in re.finditer(r"\bgoto\s+L(\d+)\b", line):
            gotos.add(m.group(1))
        m = re.match(r"\s*L(\d+):", line)
        if m:
            labels.add(m.group(1))
    missing = sorted(gotos - labels, key=int)
    if not missing:
        return lines
    out = list(lines)
    out.append("/* synthetic labels for exception boundary targets that were outside a recovered region */")
    for label in missing:
        out.append(f"L{label}:")
    return out


def decompile_ast_fallback(op_array: Mapping[str, Any], closure_map=None, *, mode: str = "labels") -> list[str]:
    """Opcode-level entry point.

    This builds IR + CFG first, then currently renders with the reliable labels
    fallback. The fallback is intentional: regions are only emitted as structured
    PHP after they are proven safe. This is the bridge for gradually replacing
    labels with AST nodes.
    """
    d = Decompiler(op_array, closure_map=closure_map or {})
    # Build these now so bad target data is found before rendering.
    ir = build_ir(op_array, expr_resolver=d.expr)
    _cfg = build_cfg(ir)
    lines = ensure_defined_goto_labels(d.decompile(mode=mode))
    # Apply conservative source-level cleanups as a fallback until every region
    # has a proven opcode-level AST form. This catches local diamonds such as
    # immediate-label if/else without crossing exception boundaries.
    from .goto_structurer import structure_gotos
    lines = structure_gotos(lines)
    return render([RawPHP(lines)])
