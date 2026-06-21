from __future__ import annotations

import json
import re
from typing import Any, Mapping

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def unwrap(value: Any) -> Any:
    """Unwrap ic72dump typed value records to their native value.

    The JSON dumper represents constants/literals as dictionaries such as
    {"type": "string", "value": "foo", ...metadata...}.  Older code only
    unwrapped very small records, which caused full metadata dictionaries to be
    emitted into recovered PHP.
    """
    seen = 0
    while isinstance(value, Mapping) and "value" in value and seen < 16:
        # Typed scalar/null/array records from ic72dump.  Do not unwrap arbitrary
        # user dictionaries unless they look like dumper value wrappers.
        if any(k in value for k in ("type", "printable", "preview", "hex", "base64", "sha1", "length", "index")):
            value = value.get("value")
            seen += 1
            continue
        if len(value) <= 3:
            value = value.get("value")
            seen += 1
            continue
        break
    return value

def php_literal(value: Any) -> str:
    value = unwrap(value)
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(php_literal(v) for v in value) + "]"
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            items.append(f"{php_literal(k)} => {php_literal(v)}")
        return "[" + ", ".join(items) + "]"
    return json.dumps(str(value), ensure_ascii=False)

def safe_name(name: Any, fallback: str = "var") -> str:
    name = unwrap(name)
    if not isinstance(name, str) or not name:
        return fallback
    name = name.strip().lstrip("$").replace("\\", "_")
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not name or not re.match(r"^[A-Za-z_]", name):
        name = "_" + name
    return name

def is_identifier(name: str) -> bool:
    return bool(_IDENT.match(name))

def operand_name(op: Mapping[str, Any] | None) -> str:
    if not op:
        return ""
    if op.get("cv_name"):
        return "$" + safe_name(op.get("cv_name"), "var")
    if op.get("name"):
        name = str(op.get("name"))
        return "$" + safe_name(name, "var") if not name.startswith("$") else "$" + safe_name(name, "var")
    if "literal" in op:
        return php_literal(op.get("literal"))
    if "constant" in op and op.get("type_name") not in {"IS_UNUSED", "IS_TMP_VAR", "IS_VAR"}:
        return php_literal(op.get("constant"))
    t = op.get("type_name") or op.get("type") or "op"
    n = op.get("var", op.get("constant", op.get("num", "")))
    if t in {"IS_TMP_VAR", "IS_VAR"}:
        return f"$_t{n}"
    if t == "IS_CV":
        return f"$cv{n}"
    return str(n) if n != "" else ""

def result_key(op: Mapping[str, Any] | None) -> str | None:
    if not op:
        return None
    t = op.get("type_name") or op.get("type")
    if t in {"IS_TMP_VAR", "IS_VAR", "IS_CV"}:
        n = op.get("var", op.get("constant", op.get("num")))
        if n is not None:
            return f"{t}:{n}"
    if op.get("cv_name"):
        return "CV:" + safe_name(op.get("cv_name"), "var")
    return None
