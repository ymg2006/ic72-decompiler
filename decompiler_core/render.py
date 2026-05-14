from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .engine import Decompiler
from .utils import decode_hex_name_from_id, php_literal, safe_name, unwrap


def _argument_defaults(oa: Dict[str, Any]) -> Dict[int, str]:
    defaults: Dict[int, str] = {}
    for op in oa.get("opcodes") or []:
        if op.get("opcode_name") != "ZEND_RECV_INIT":
            continue
        arg_num = op.get("op1", {}).get("constant")
        if not isinstance(arg_num, int) or arg_num <= 0:
            continue
        defaults[arg_num - 1] = php_literal(op.get("op2", {}).get("literal"))
    return defaults


def method_signature(oa: Dict[str, Any], fallback: str) -> str:
    args = []
    required = int(oa.get("required_num_args") or 0)
    defaults = _argument_defaults(oa)
    for idx, arg in enumerate(oa.get("arg_info") or []):
        name = safe_name(arg.get("name"), "_arg%d" % idx)
        prefix = "&" if arg.get("pass_by_reference") else ""
        variadic = "..." if arg.get("is_variadic") else ""
        s = variadic + prefix + "$" + name
        if idx in defaults:
            s += " = " + defaults[idx]
        elif idx >= required:
            s += " = null"
        args.append(s)
    return fallback + "(" + ", ".join(args) + ")"


def argument_list(oa: Dict[str, Any]) -> List[str]:
    args = []
    required = int(oa.get("required_num_args") or 0)
    defaults = _argument_defaults(oa)
    for idx, arg in enumerate(oa.get("arg_info") or []):
        name = safe_name(arg.get("name"), "_arg%d" % idx)
        prefix = "&" if arg.get("pass_by_reference") else ""
        variadic = "..." if arg.get("is_variadic") else ""
        s = variadic + prefix + "$" + name
        if idx in defaults:
            s += " = " + defaults[idx]
        elif idx >= required:
            s += " = null"
        args.append(s)
    return args


def method_modifiers(oa: Dict[str, Any]) -> str:
    flags = oa.get("fn_flags_decoded") if isinstance(oa.get("fn_flags_decoded"), dict) else {}
    visibility = flags.get("visibility") or "public"
    parts = [visibility]
    if flags.get("is_abstract"):
        parts.append("abstract")
    if flags.get("is_final"):
        parts.append("final")
    if flags.get("is_static"):
        parts.append("static")
    return " ".join(parts)


def class_name_from_id(class_id: str) -> str:
    name = decode_hex_name_from_id("class:", class_id)
    return name or "RecoveredClass"


def _class_meta(ir: Dict[str, Any], cls_id: str) -> Dict[str, Any]:
    meta = (ir.get("class_index") or {}).get(cls_id)
    return meta if isinstance(meta, dict) else {}


def class_header(ir: Dict[str, Any], cls_id: str, cls: str) -> str:
    meta = _class_meta(ir, cls_id)
    parent = unwrap(meta.get("parent"))
    if not parent:
        parent = class_parent_from_declare_ops(ir, cls)
    if isinstance(parent, str) and parent:
        return f"class {cls} extends {parent}"
    return f"class {cls}"


def class_parent_from_declare_ops(ir: Dict[str, Any], cls: str) -> Optional[str]:
    main = (ir.get("op_arrays") or {}).get("main") or {}
    temps: Dict[int, str] = {}
    for op in main.get("opcodes") or []:
        name = op.get("opcode_name")
        result = op.get("result") or {}
        if name == "ZEND_FETCH_CLASS":
            parent = unwrap((op.get("op2") or {}).get("literal"))
            if isinstance(parent, str) and result.get("type_name") in ("IS_VAR", "IS_TMP_VAR"):
                temps[int(result.get("var") or result.get("constant") or 0)] = parent
            continue
        if name != "ZEND_DECLARE_INHERITED_CLASS":
            continue
        declared = unwrap((op.get("op1") or {}).get("literal"))
        if not isinstance(declared, str) or declared.lower() != cls.lower():
            continue
        parent_op = op.get("op2") or {}
        if parent_op.get("type_name") in ("IS_VAR", "IS_TMP_VAR"):
            parent = temps.get(int(parent_op.get("var") or parent_op.get("constant") or 0))
            if parent:
                return parent
        parent = unwrap(parent_op.get("literal"))
        if isinstance(parent, str) and parent:
            return parent
    return None


def class_properties(ir: Dict[str, Any], cls_id: str, cls: str) -> List[str]:
    meta = _class_meta(ir, cls_id)
    props = meta.get("properties_info") or meta.get("properties_merged") or {}
    if not isinstance(props, dict):
        return []

    rows = []
    seen = set()
    for key, info in props.items():
        if not isinstance(info, dict):
            continue
        name = unwrap(info.get("name"))
        if not isinstance(name, str) or not name:
            name = str(key)
        if name.startswith(cls):
            name = name[len(cls):]
        name = safe_name(name, "")
        if not name or name in seen:
            continue
        seen.add(name)
        flags = info.get("flags_decoded") if isinstance(info.get("flags_decoded"), dict) else {}
        visibility = flags.get("visibility") or "public"
        static = " static" if flags.get("is_static") or info.get("is_static") else ""
        default = ""
        if info.get("has_default_value") or info.get("default_value") is not None:
            default = " = " + php_literal(info.get("default_value"))
        rows.append((int(info.get("offset") or len(rows)), f"    {visibility}{static} ${name}{default};"))
    return [line for _offset, line in sorted(rows, key=lambda row: row[0])]


def _op_array_name(oa: Dict[str, Any]) -> Optional[str]:
    fn = oa.get("function_name")
    if isinstance(fn, dict):
        return fn.get("value")
    if isinstance(fn, str):
        return fn
    return None


def _display_name(oa: Dict[str, Any], id_prefix: str, oid: str, fallback: str) -> str:
    # function_table keys are case-insensitive in PHP and may be normalized by
    # the dump. The op_array function_name keeps the source spelling.
    return safe_name(_op_array_name(oa), "") or decode_hex_name_from_id(id_prefix, oid) or fallback


def group_classes(ir: Dict[str, Any]) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
    classes: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for oid, oa in ir.get("op_arrays", {}).items():
        if ":method:" not in oid:
            continue
        cls_id = oid.split(":method:", 1)[0]
        method = _display_name(oa, ":method:", oid, "method")
        classes.setdefault(cls_id, []).append((method, oa))
    return classes


def group_functions(ir: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    funcs: List[Tuple[str, Dict[str, Any]]] = []
    for oid, oa in ir.get("op_arrays", {}).items():
        if not oid.startswith("function:"):
            continue
        name = _display_name(oa, "function:", oid, "recovered_function")
        funcs.append((name, oa))
    return funcs


def function_name_map(ir: Dict[str, Any]) -> Dict[str, str]:
    names: Dict[str, str] = {}
    for name, _oa in group_functions(ir):
        names.setdefault(name.lower(), name)
    return names


def group_closures(ir: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    closures: List[Tuple[str, Dict[str, Any]]] = []
    for oid, oa in ir.get("op_arrays", {}).items():
        if not oid.startswith("closure:"):
            continue
        closures.append((oid, oa))
    return sorted(closures, key=lambda x: x[0].lower())


def _focus_match(focus: Optional[str], name: str) -> bool:
    if not focus:
        return True
    return focus.lower() in name.lower()


def closure_names(ir: Dict[str, Any]) -> Dict[str, str]:
    names: Dict[str, str] = {}
    for idx, (closure_id, _oa) in enumerate(group_closures(ir), start=1):
        names[closure_id] = f"_closure_{idx}"
    return names


def closure_use_vars(oa: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    static_vars = unwrap(oa.get("static_variables"))
    if isinstance(static_vars, dict):
        names.extend(str(name) for name in static_vars.keys())
    for op in oa.get("opcodes") or []:
        if op.get("opcode_name") != "ZEND_BIND_STATIC":
            continue
        operand = op.get("op1") or {}
        name = operand.get("cv_name")
        if isinstance(name, str) and name:
            names.append(name)
    seen = set()
    result = []
    for name in names:
        safe = safe_name(name, "")
        if not safe or safe in seen:
            continue
        seen.add(safe)
        result.append("$" + safe)
    return result


def closure_expressions(ir: Dict[str, Any], mode: str, lambda_names: Dict[str, str], function_names: Dict[str, str]) -> Dict[str, str]:
    exprs: Dict[str, str] = {}
    for closure_id, oa in group_closures(ir):
        args = ", ".join(argument_list(oa))
        use_vars = closure_use_vars(oa)
        use_clause = " use (" + ", ".join(use_vars) + ")" if use_vars else ""
        body = Decompiler(oa, lambda_names=lambda_names, lambda_exprs=exprs, function_names=function_names).decompile(mode)
        if not body:
            body = ["/* empty */"]
        body_text = "\n".join("    " + line.strip() for line in body)
        exprs[closure_id] = f"function ({args}){use_clause} {{\n{body_text}\n}}"
    return exprs


def _emit_body(
    oa: Dict[str, Any],
    mode: str,
    indent: str,
    lambda_names: Optional[Dict[str, str]] = None,
    lambda_exprs: Optional[Dict[str, str]] = None,
    function_names: Optional[Dict[str, str]] = None,
) -> List[str]:
    body = Decompiler(oa, lambda_names=lambda_names, lambda_exprs=lambda_exprs, function_names=function_names).decompile(mode)
    if not body:
        body = ["/* empty */"]
    return [indent + line for line in body]


def decompile_file(
    ir: Dict[str, Any],
    focus: Optional[str] = None,
    mode: str = "structured",
    main_as_function: bool = False,
) -> str:
    lines = ["<?php", ""]
    lambda_names = closure_names(ir)
    function_names = function_name_map(ir)
    lambda_exprs = closure_expressions(ir, mode, lambda_names, function_names)

    main = ir.get("op_arrays", {}).get("main")
    if main and _focus_match(focus, "main"):
        main_body = Decompiler(main, lambda_names=lambda_names, lambda_exprs=lambda_exprs, function_names=function_names).decompile(mode)
        if main_body:
            if main_as_function:
                lines.append("function __decompiled_main__()")
                lines.append("{")
                lines.extend("    " + line for line in main_body)
                lines.append("}")
                lines.append("")
                lines.append("__decompiled_main__();")
            else:
                lines.append("/* main */")
                lines.extend(main_body)
            lines.append("")

    for func, oa in group_functions(ir):
        if not _focus_match(focus, func):
            continue
        sig = method_signature(oa, func)
        lines.append(f"function {sig}")
        lines.append("{")
        lines.extend(_emit_body(oa, mode, "    ", lambda_names, lambda_exprs, function_names))
        lines.append("}")
        lines.append("")

    closure_index = 1
    for closure_id, oa in group_closures(ir):
        closure_label = f"_closure_{closure_index}"
        if closure_id in lambda_exprs and not (focus and (_focus_match(focus, "closure") or _focus_match(focus, closure_id))):
            closure_index += 1
            continue
        if not _focus_match(focus, "closure") and not _focus_match(focus, closure_id):
            continue
        lines.append(f"/* closure {closure_index}: {closure_id} */")
        lines.append(f"function {closure_label}()")
        lines.append("{")
        lines.extend(_emit_body(oa, mode, "    ", lambda_names, lambda_exprs, function_names))
        lines.append("}")
        lines.append("")
        closure_index += 1

    for cls_id, methods in sorted(group_classes(ir).items(), key=lambda x: x[0].lower()):
        cls = class_name_from_id(cls_id)
        class_lines = [class_header(ir, cls_id, cls), "{"]
        props = class_properties(ir, cls_id, cls)
        if props:
            class_lines.extend(props)
            class_lines.append("")
        method_count = 0
        for method, oa in methods:
            if not _focus_match(focus, method):
                continue
            method_count += 1
            sig = method_signature(oa, method)
            class_lines.append(f"    {method_modifiers(oa)} function {sig}")
            class_lines.append("    {")
            class_lines.extend(_emit_body(oa, mode, "        ", lambda_names, lambda_exprs, function_names))
            class_lines.append("    }")
            class_lines.append("")
        if method_count == 0:
            continue
        class_lines.append("}")
        lines.extend(class_lines)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
