from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from .engine import Decompiler
from .formatter import format_php_source, format_php_source_with_phply
from .goto_structurer import structure_goto_source
from .dream_structurer import dream_structure_source
from .structurer import decompile_ast_fallback
from .residual_no_goto import erase_residual_gotos
from .placeholder_cleanup import cleanup_placeholder_comments
from .utils import php_literal, safe_name, unwrap


def argument_defaults(oa: Mapping[str, Any]) -> Dict[int, str]:
    defaults: Dict[int, str] = {}
    for op in oa.get("opcodes") or []:
        if op.get("opcode_name") == "ZEND_RECV_INIT":
            n = (op.get("op1") or {}).get("constant")
            if isinstance(n, int) and n > 0:
                defaults[n - 1] = php_literal((op.get("op2") or {}).get("literal"))
    return defaults


def argument_list(oa: Mapping[str, Any]) -> List[str]:
    defaults = argument_defaults(oa)
    required = int(oa.get("required_num_args") or 0)
    args = []
    for idx, arg in enumerate(oa.get("arg_info") or []):
        name = safe_name(arg.get("name"), f"arg{idx}")
        prefix = "&" if arg.get("pass_by_reference") else ""
        variadic = "..." if arg.get("is_variadic") else ""
        text = f"{variadic}{prefix}${name}"
        if idx in defaults:
            text += " = " + defaults[idx]
        elif idx >= required:
            text += " = null"
        args.append(text)
    return args


def display_name(oa: Mapping[str, Any], fallback: str) -> str:
    name = oa.get("function_name")
    if isinstance(name, dict):
        name = name.get("value")
    return safe_name(name, fallback)


def method_modifiers(oa: Mapping[str, Any]) -> str:
    flags = oa.get("fn_flags_decoded") if isinstance(oa.get("fn_flags_decoded"), dict) else {}
    parts = [flags.get("visibility") or "public"]
    if flags.get("is_abstract"):
        parts.append("abstract")
    if flags.get("is_final"):
        parts.append("final")
    if flags.get("is_static"):
        parts.append("static")
    return " ".join(parts)


def emit_body(oa: Mapping[str, Any], mode: str, indent: str = "    ", closure_map: Optional[Dict[str, Mapping[str, Any]]] = None) -> List[str]:
    if mode in {"ast", "ast-labels", "ast-clean-draft", "ast-zero-goto-verified"}:
        ast_mode = "labels" if mode in {"ast-labels", "ast-clean-draft", "ast-zero-goto-verified"} else "structured"
        lines = decompile_ast_fallback(oa, closure_map=closure_map or {}, mode=ast_mode)
    else:
        lines = Decompiler(oa, closure_map=closure_map or {}).decompile(mode)
    if not lines:
        lines = ["/* empty */"]
    return [indent + line for line in lines]


def group_functions(ir: Mapping[str, Any]) -> List[Tuple[str, Mapping[str, Any]]]:
    out = []
    for oid, oa in (ir.get("op_arrays") or {}).items():
        if str(oid).startswith("function:"):
            out.append((display_name(oa, str(oid).split(":", 1)[-1] or "recovered_function"), oa))
    return out


def group_classes(ir: Mapping[str, Any]) -> Dict[str, List[Tuple[str, Mapping[str, Any]]]]:
    classes: Dict[str, List[Tuple[str, Mapping[str, Any]]]] = {}
    for oid, oa in (ir.get("op_arrays") or {}).items():
        if ":method:" not in str(oid):
            continue
        cls_id, _ = str(oid).split(":method:", 1)
        classes.setdefault(cls_id, []).append((display_name(oa, "method"), oa))
    return classes


def class_name(ir: Mapping[str, Any], cls_id: str) -> str:
    meta = (ir.get("class_index") or {}).get(cls_id) or {}
    name = unwrap(meta.get("name")) or cls_id.split(":")[-1]
    return safe_name(name, "RecoveredClass")


def decompile_file(
    ir: Mapping[str, Any],
    focus: Optional[str] = None,
    mode: str = "structured",
    main_as_function: bool = False,
    format_output: bool = True,
    max_line_length: int = 120,
    formatter: str = "phply",
) -> str:
    lines: List[str] = ["<?php", ""]
    closure_map: Dict[str, Mapping[str, Any]] = {str(oid): oa for oid, oa in (ir.get("op_arrays") or {}).items() if str(oid).startswith("closure:")}
    classes = group_classes(ir)
    for cls_id, methods in classes.items():
        cls = class_name(ir, cls_id)
        if focus and focus.lower() not in cls.lower():
            continue
        lines.append(f"class {cls} {{")
        for method, oa in methods:
            args = ", ".join(argument_list(oa))
            lines.append(f"    {method_modifiers(oa)} function {method}({args}) {{")
            lines.extend("    " + line for line in emit_body(oa, mode, closure_map=closure_map))
            lines.append("    }")
            lines.append("")
        lines.append("}")
        lines.append("")

    for name, oa in group_functions(ir):
        if focus and focus.lower() not in name.lower():
            continue
        args = ", ".join(argument_list(oa))
        lines.append(f"function {name}({args}) {{")
        lines.extend(emit_body(oa, mode, closure_map=closure_map))
        lines.append("}")
        lines.append("")

    main = (ir.get("op_arrays") or {}).get("main") or ir.get("op_array") or ir.get("main")
    if isinstance(main, Mapping) and (not focus or "main".startswith(focus.lower())):
        if main_as_function:
            lines.append("function __decompiled_main__() {")
            lines.extend(emit_body(main, mode, closure_map=closure_map))
            lines.append("}")
        else:
            lines.extend(line for line in emit_body(main, mode, indent="", closure_map=closure_map))
    source = "\n".join(lines).rstrip() + "\n"
    if mode == "dream":
        source = dream_structure_source(source)
    elif mode in {"ast", "ast-labels", "ast-clean-draft", "ast-zero-goto-verified"}:
        # AST modes build opcode IR/CFG first, then run conservative cleanup.
        source = structure_goto_source(source)
        if mode in {"ast-clean-draft", "ast-zero-goto-verified"}:
            source, _no_goto_stats = erase_residual_gotos(source)
            source = cleanup_placeholder_comments(source)
    else:
        source = structure_goto_source(source)
    # PHP 7.2 has no (mixed) cast; some operand metadata can render as this
    # pseudo-cast. Also normalize instanceof operands that were rendered as
    # strings from class-name literals.
    source = source.replace("((mixed) ", "(")
    source = source.replace("(mixed) ", "")
    import re as _re
    source = _re.sub(r'instanceof\s+"([A-Za-z_\\][A-Za-z0-9_\\]*)"', lambda m: "instanceof " + m.group(1).replace("\\\\", "\\"), source)
    if not format_output or formatter == "none":
        return source
    if formatter == "python":
        return format_php_source(source, max_line_length=max_line_length)
    if formatter == "phply":
        return format_php_source_with_phply(source, max_line_length=max_line_length)
    raise ValueError(f"unknown formatter: {formatter}")
