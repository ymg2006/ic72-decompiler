from __future__ import annotations

import re
from typing import Any, Optional


IDENT_RE = re.compile(r"^[A-Za-z_\x80-\xff][A-Za-z0-9_\x80-\xff]*$")


def unwrap(v: Any) -> Any:
    if not isinstance(v, dict) or "type" not in v:
        return v
    t = v.get("type")
    if t == "string":
        if v.get("value") is not None:
            return v.get("value")
        hx = str(v.get("hex", ""))
        try:
            decoded = bytes.fromhex(hx).decode("utf-8")
            if all(ord(ch) >= 32 or ch in "\r\n\t" for ch in decoded):
                return decoded
        except Exception:
            pass
        return "_obf_" + hx
    if t in ("int", "float", "bool", "null"):
        return v.get("value")
    if t == "array":
        val = v.get("value")
        if isinstance(val, list):
            return [unwrap(x) for x in val]
        if isinstance(val, dict):
            return {k: unwrap(x) for k, x in val.items()}
    return v.get("value")


def php_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r") + '"'


def php_literal(v: Any) -> str:
    v = unwrap(v)
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return php_string(v)
    if isinstance(v, list):
        return "[" + ", ".join(php_literal(x) for x in v) + "]"
    if isinstance(v, dict):
        parts = [php_literal(k) + " => " + php_literal(x) for k, x in v.items()]
        return "[" + ", ".join(parts) + "]"
    return php_string(str(v))


def safe_name(v: Any, fallback: str) -> str:
    v = unwrap(v)
    if isinstance(v, str) and IDENT_RE.match(v):
        return v
    return fallback


def decode_hex_name_from_id(prefix: str, key: str) -> Optional[str]:
    if prefix not in key:
        return None
    tail = key.split(prefix, 1)[1].split(":", 1)[0]
    try:
        return bytes.fromhex(tail).decode("utf-8", "replace")
    except ValueError:
        return None


def strip_redundant_parens(expr: str) -> str:
    expr = expr.strip()

    def balanced(s: str) -> bool:
        depth = 0
        quote = ""
        escape = False
        for ch in s:
            if quote:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    quote = ""
                continue
            if ch in ("'", '"'):
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    return False
        return depth == 0 and not quote

    changed = True
    while changed:
        changed = False
        while expr.startswith("(") and expr.endswith(")") and balanced(expr[1:-1]):
            expr = expr[1:-1].strip()
            changed = True
        # Flatten left-associative logical chains: ((a && b) && c) -> a && b && c.
        for op in ("&&", "||"):
            marker = f") {op} "
            if expr.startswith("(") and marker in expr:
                idx = expr.find(marker)
                left = expr[1:idx]
                right = expr[idx + len(marker):]
                # Never flatten (a || b) && c: PHP gives && higher
                # precedence than ||, so removing those parens changes meaning.
                if op == "&&" and "||" in left:
                    continue
                if balanced(left) and op in left and ("&&" not in right if op == "||" else "||" not in right):
                    expr = f"{left} {op} {right}".strip()
                    changed = True
                    break
        if expr.startswith("!(") and expr.endswith(")") and balanced(expr[2:-1]):
            inner = expr[2:-1].strip()
            if re.match(r"^(empty|isset|is_[A-Za-z0-9_]+)\(.+\)$", inner):
                expr = "!" + inner
                changed = True
        cleaned = re.sub(r"!\(([A-Za-z_][A-Za-z0-9_]*\([^()]*\))\)", r"!\1", expr)
        if cleaned != expr:
            expr = cleaned
            changed = True
    return expr
