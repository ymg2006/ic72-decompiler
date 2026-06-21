from __future__ import annotations

import re
from dataclasses import dataclass, field

@dataclass
class DispatchCase:
    values: list[str]
    start_label: str | None = None
    body: list[str] = field(default_factory=list)

@dataclass
class DispatchRegion:
    variable: str
    cases: list[DispatchCase]

_EQ_RE = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)\s*(?:===|==)\s*((?:"[^"]+")|(?:\'[^\']+\'))')
_IN_ARRAY_RE = re.compile(r'in_array\(\$([A-Za-z_][A-Za-z0-9_]*),\s*\[([^\]]+)\]')
_STR_RE = re.compile(r'("[^"]+"|\'[^\']+\')')


def extract_action_values(condition: str) -> tuple[str, list[str]] | None:
    m = _EQ_RE.search(condition)
    if m:
        return "$" + m.group(1), [m.group(2)]
    m = _IN_ARRAY_RE.search(condition)
    if m:
        return "$" + m.group(1), _STR_RE.findall(m.group(2))
    return None


def detect_dispatch_from_lines(lines: list[str], variable: str = "$action") -> DispatchRegion | None:
    cases: list[DispatchCase] = []
    for line in lines:
        parsed = extract_action_values(line)
        if parsed and parsed[0] == variable:
            cases.append(DispatchCase(parsed[1]))
    if len(cases) < 4:
        return None
    return DispatchRegion(variable, cases)
