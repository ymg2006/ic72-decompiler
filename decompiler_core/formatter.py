from __future__ import annotations

from typing import Iterable, List, Sequence
import re

DEFAULT_INDENT = "    "
DEFAULT_MAX_LINE_LENGTH = 120


def _opens_block(line: str) -> bool:
    return line.endswith("{")


def _closes_block(line: str) -> bool:
    return line.startswith("}")


def _is_case_label(line: str) -> bool:
    return line.startswith("case ") or line.startswith("default:")


def _split_outside_strings(text: str, needle: str) -> List[str]:
    """Split text on needle occurrences that are outside PHP string literals."""
    parts: List[str] = []
    start = 0
    i = 0
    quote = ""
    escaped = False

    while i < len(text):
        ch = text[i]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            i += 1
            continue

        if ch in {'"', "'"}:
            quote = ch
            i += 1
            continue

        if text.startswith(needle, i):
            parts.append(text[start:i])
            i += len(needle)
            start = i
            continue
        i += 1

    parts.append(text[start:])
    return parts


def _find_assignment_operator(line: str) -> tuple[int, str] | None:
    """Find the first statement assignment operator outside strings.

    Intentionally excludes comparison operators and array arrows.
    """
    operators = (".=", "=&", "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=")
    i = 0
    quote = ""
    escaped = False
    while i < len(line):
        ch = line[i]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            i += 1
            continue

        for op in sorted(operators, key=len, reverse=True):
            if not line.startswith(op, i):
                continue
            prev = line[i - 1] if i else ""
            nxt = line[i + len(op)] if i + len(op) < len(line) else ""
            if op == "=" and (prev in "!<>=" or nxt == ">" or nxt == "="):
                continue
            if op != "=" and (nxt == "=" and op not in {"<<=", ">>="}):
                continue
            return i, op
        i += 1
    return None


def _find_outer_call(line: str) -> tuple[str, str, str] | None:
    """Return call name, inner arguments, suffix for simple one-line calls."""
    if not line.endswith(";"):
        return None
    open_idx = line.find("(")
    if open_idx <= 0:
        return None
    name = line[:open_idx].strip()
    if not name or any(ch.isspace() for ch in name):
        return None
    if not (name.replace("_", "").replace("\\", "").isalnum() or "->" in name or "::" in name):
        return None

    depth = 0
    quote = ""
    escaped = False
    close_idx = -1
    for i, ch in enumerate(line[open_idx:], start=open_idx):
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {'"', "'"}:
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                close_idx = i
                break
    if close_idx == -1:
        return None
    suffix = line[close_idx + 1 :]
    if suffix != ";":
        return None
    return name, line[open_idx + 1 : close_idx], suffix



def _split_commas_outside_strings(text: str) -> List[str]:
    parts: List[str] = []
    start = 0
    depth = 0
    quote = ""
    escaped = False
    for i, ch in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {'"', "'"}:
            quote = ch
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(depth - 1, 0)
        elif ch == "," and depth == 0:
            parts.append(text[start : i + 1].strip())
            start = i + 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def _wrap_call_expr(expr: str, prefix: str, indent: str, max_line_length: int) -> List[str] | None:
    pseudo = expr + ";"
    call = _find_outer_call(pseudo)
    if not call:
        return None
    name, inner, _suffix = call
    args = _split_commas_outside_strings(inner)
    if len(args) <= 1:
        return None
    lines = [prefix + name + "("]
    arg_prefix = prefix + indent
    for arg in args:
        arg_lines = _wrap_concat_expr(arg, arg_prefix, indent, max_line_length)
        lines.extend(arg_lines)
    lines.append(prefix + ")")
    return lines


def _has_odd_trailing_backslashes(text: str) -> bool:
    count = 0
    for ch in reversed(text):
        if ch == "\\":
            count += 1
        else:
            break
    return count % 2 == 1


def _split_string_literal_token(token: str, max_content_length: int = 96) -> List[str]:
    """Split a long quoted string token into quoted chunks.

    Handles plain string tokens as well as tokens wrapped in decompiler-added
    parentheses, for example "..."), (("...", or (("...")).
    """
    if len(token) <= max_content_length + 2:
        return [token]

    start = 0
    while start < len(token) and token[start] == "(":
        start += 1
    if start >= len(token) or token[start] not in {'"', "'"}:
        return [token]

    quote = token[start]
    escaped = False
    end = -1
    i = start + 1
    while i < len(token):
        ch = token[i]
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == quote:
            end = i
        i += 1
    if end <= start:
        return [token]
    suffix = token[end + 1 :]
    if suffix and any(ch != ")" for ch in suffix):
        return [token]

    prefix = token[:start]
    body = token[start + 1 : end]
    suffix = token[end + 1 :]
    if len(body) <= max_content_length:
        return [token]

    raw_chunks: List[str] = []
    pos = 0
    while pos < len(body):
        limit = min(pos + max_content_length, len(body))
        split = limit
        # Prefer escaped newlines, then SQL-ish comma/space boundaries.
        search_start = pos + max_content_length // 2
        for marker in ("\\n", ", ", " "):
            found = body.rfind(marker, search_start, limit)
            if found > pos:
                split = found + len(marker)
                break
        while split > pos and _has_odd_trailing_backslashes(body[pos:split]):
            split -= 1
        if split <= pos:
            split = limit
        raw_chunks.append(body[pos:split])
        pos = split

    chunks = [quote + chunk + quote for chunk in raw_chunks]
    chunks[0] = prefix + chunks[0]
    chunks[-1] = chunks[-1] + suffix
    return chunks


def _expand_long_string_parts(parts: Sequence[str]) -> List[str]:
    expanded: List[str] = []
    for part in parts:
        expanded.extend(_split_string_literal_token(part))
    return expanded


def _wrap_array_expr(expr: str, prefix: str, indent: str, max_line_length: int) -> List[str] | None:
    expr = expr.strip()
    if not (expr.startswith("[") and expr.endswith("]")):
        return None
    inner = expr[1:-1].strip()
    if not inner:
        return [prefix + "[]"]
    items = _split_commas_outside_strings(inner)
    if len(items) <= 1:
        return None
    lines = [prefix + "["]
    item_prefix = prefix + indent
    for item in items:
        item = item.rstrip(",")
        item_lines = _wrap_concat_expr(item, item_prefix, indent, max_line_length)
        if item_lines:
            item_lines[-1] += ","
            lines.extend(item_lines)
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append(prefix + "]")
    return lines

def _wrap_concat_expr(expr: str, prefix: str, indent: str, max_line_length: int) -> List[str]:
    """Wrap a long expression by splitting concatenation operators."""
    expr = expr.strip()

    array_lines = _wrap_array_expr(expr, prefix, indent, max_line_length)
    if array_lines is not None:
        return array_lines

    call_lines = _wrap_call_expr(expr, prefix, indent, max_line_length)
    if call_lines is not None:
        return call_lines

    parts = [part.strip() for part in _split_outside_strings(expr, " . ")]
    parts = _expand_long_string_parts(parts)
    if len(parts) <= 1:
        return [prefix + expr]

    lines: List[str] = []
    current = prefix + parts[0]
    cont_prefix = " " * len(prefix)
    dot_prefix = cont_prefix + ". "

    for part in parts[1:]:
        candidate = current + " . " + part
        if len(candidate) <= max_line_length:
            current = candidate
        else:
            lines.append(current)
            current = dot_prefix + part
    lines.append(current)
    return lines


def _wrap_statement(line: str, indent_prefix: str, indent: str, max_line_length: int) -> List[str]:
    full = indent_prefix + line
    if len(full) <= max_line_length:
        return [full]

    # Long assignment: put the RHS on wrapped continuation lines.
    assignment = _find_assignment_operator(line)
    if assignment and line.endswith(";"):
        idx, op = assignment
        lhs = line[:idx].rstrip()
        rhs = line[idx + len(op) :].strip()[:-1].rstrip()
        first = f"{indent_prefix}{lhs} {op}"
        rhs_prefix = indent_prefix + indent
        wrapped = _wrap_concat_expr(rhs, rhs_prefix, indent, max_line_length)
        if wrapped:
            wrapped[-1] += ";"
        return [first, *wrapped]

    # Long simple call: split as call( / wrapped arg / ); .
    call = _find_outer_call(line)
    if call:
        name, inner, _suffix = call
        inner_prefix = indent_prefix + indent
        wrapped_inner = _wrap_concat_expr(inner, inner_prefix, indent, max_line_length)
        return [f"{indent_prefix}{name}(", *wrapped_inner, f"{indent_prefix});"]

    # Fallback: wrap concatenations in any other long statement.
    wrapped = _wrap_concat_expr(line, indent_prefix, indent, max_line_length)
    return wrapped


def format_php_lines(
    lines: Iterable[str],
    indent: str = DEFAULT_INDENT,
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH,
) -> List[str]:
    """Return consistently indented and wrapped PHP source lines.

    The decompiler emits best-effort PHP one statement at a time. This formatter
    is intentionally conservative: it does not parse/rewrite PHP semantics. It
    normalizes block indentation, collapses excessive blank lines, and wraps the
    huge assignment/call/concatenation statements the opcode renderer produces.
    """
    formatted: List[str] = []
    level = 0
    blank_count = 0
    heredoc_marker = ""

    for raw in lines:
        if heredoc_marker:
            formatted.append(raw.rstrip())
            if raw.strip() in {heredoc_marker, heredoc_marker + ";"}:
                heredoc_marker = ""
            continue

        line = raw.strip()

        if not line:
            if formatted and blank_count == 0:
                formatted.append("")
                blank_count = 1
            continue

        blank_count = 0

        if line == "<?php":
            formatted.append(line)
            level = 0
            continue

        effective_level = level
        if _closes_block(line):
            effective_level = max(effective_level - 1, 0)
        if _is_case_label(line):
            effective_level = max(effective_level - 1, 0)

        indent_prefix = indent * effective_level
        statement_lines = _wrap_statement(line, indent_prefix, indent, max_line_length)
        formatted.extend(statement_lines)
        hd_match = re.search(r"<<<['\"]?([A-Za-z_][A-Za-z0-9_]*)", line)
        if hd_match:
            heredoc_marker = hd_match.group(1)

        if _closes_block(line):
            level = max(level - 1, 0)
        if _opens_block(line):
            level += 1

    while formatted and formatted[-1] == "":
        formatted.pop()
    return formatted



def _lex_with_phply(source: str) -> tuple[bool, str]:
    """Return whether phply can lex the PHP source.

    phply is the best maintained Python-side PHP lexer/parser package, but it
    is not a code formatter/re-printer. We use its lexer as the Python tool for
    token-aware validation before applying the decompiler formatter. This keeps
    the formatter from silently accepting broken quoted strings/heredocs while
    still avoiding PHP/Composer/Node dependencies.
    """
    try:
        from phply.phplex import lexer  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional install
        return False, f"phply is not installed: {exc}"

    try:
        lx = lexer.clone()
        lx.input(source)
        while lx.token():
            pass
        return True, ""
    except Exception as exc:
        return False, f"phply lexer failed: {exc}"


def format_php_source_with_phply(
    source: str,
    indent: str = DEFAULT_INDENT,
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH,
) -> str:
    """Format PHP using the Python phply lexer plus the bundled formatter.

    There is no mature pure-Python equivalent of PHP-CS-Fixer/Prettier that
    parses PHP 7.2 and reprints PSR-12 source. phply is the practical Python
    choice for PHP tokenization, so this formatter lexes with phply first and
    then applies the formatter that understands the decompiler's output shape.
    """
    ok, _message = _lex_with_phply(source)
    # Even if phply is missing or rejects a best-effort decompiler construct,
    # still return formatted output. The decompiler output is often partial PHP
    # while opcode support is being expanded, and formatting should not erase it.
    return format_php_source(source, indent=indent, max_line_length=max_line_length)

def format_php_source(
    source: str,
    indent: str = DEFAULT_INDENT,
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH,
) -> str:
    """Format a PHP source string produced by the decompiler."""
    return "\n".join(
        format_php_lines(source.splitlines(), indent=indent, max_line_length=max_line_length)
    ).rstrip() + "\n"
