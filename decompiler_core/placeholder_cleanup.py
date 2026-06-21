from __future__ import annotations

import re
from typing import List, Tuple

FOREACH_OVER_RE = re.compile(r'^\s*/\*\s*foreach\s+over\s+(.+?)\s*\*/\s*$')
FOREACH_VALUE_RE = re.compile(r'^\s*/\*\s*foreach\s+value\s+(\$[A-Za-z_][A-Za-z0-9_]*)\s*\*/\s*$')
END_FOREACH_RE = re.compile(r'^\s*/\*\s*endforeach\s*\*/\s*$')
PLACEHOLDER_COMMENT_RE = re.compile(r'^\s*/\*\s*(switch on|synthetic labels|endforeach|foreach over|foreach value)\b.*\*/\s*$')
KEY_ASSIGN_RE = re.compile(r'^\s*(\$[A-Za-z_][A-Za-z0-9_]*)\s*=\s*\$_t\d+;\s*$')


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def cleanup_placeholder_comments(source: str) -> str:
    """Convert decompiler placeholder comments into real PHP where possible.

    In particular converts:
      /* foreach over $items */
      /* foreach value $item */
      ...
      /* endforeach */

    into:
      foreach ($items as $item) { ... }

    If the first body line assigns a hidden iterator key temp, such as
      $id = $_t1234;
    it becomes:
      foreach ($items as $id => $item) { ... }
    and the temp assignment is dropped.
    """
    lines = source.splitlines()
    out: List[str] = []
    stack: List[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m_over = FOREACH_OVER_RE.match(line)
        if m_over and i + 1 < len(lines):
            m_val = FOREACH_VALUE_RE.match(lines[i + 1])
            if m_val:
                indent = _indent_of(line)
                iterable = m_over.group(1).strip()
                value = m_val.group(1).strip()
                # Header is emitted lazily so we can inspect the first body line
                # for a hidden key-temp assignment.
                stack.append({"indent": indent, "iterable": iterable, "value": value, "header_emitted": False})
                i += 2
                continue
        if END_FOREACH_RE.match(line) and stack:
            ctx = stack.pop()
            if not ctx.get("header_emitted"):
                out.append(f"{ctx['indent']}foreach ({ctx['iterable']} as {ctx['value']}) {{")
            out.append(f"{ctx['indent']}}}")
            i += 1
            continue
        if stack and not stack[-1].get("header_emitted"):
            ctx = stack[-1]
            key_match = KEY_ASSIGN_RE.match(line)
            if key_match:
                key = key_match.group(1)
                out.append(f"{ctx['indent']}foreach ({ctx['iterable']} as {key} => {ctx['value']}) {{")
                ctx["header_emitted"] = True
                i += 1
                continue
            else:
                out.append(f"{ctx['indent']}foreach ({ctx['iterable']} as {ctx['value']}) {{")
                ctx["header_emitted"] = True
        # Remove remaining placeholder comments, e.g. switch diagnostics and
        # synthetic-boundary notes. They are not valid clean decompiled source.
        if PLACEHOLDER_COMMENT_RE.match(line):
            i += 1
            continue
        out.append(line)
        i += 1
    # Close any malformed/unclosed foreach markers conservatively.
    while stack:
        ctx = stack.pop()
        if not ctx.get("header_emitted"):
            out.append(f"{ctx['indent']}foreach ({ctx['iterable']} as {ctx['value']}) {{")
        out.append(f"{ctx['indent']}}}")
    trailing = "\n" if source.endswith("\n") else ""
    return "\n".join(out) + trailing
