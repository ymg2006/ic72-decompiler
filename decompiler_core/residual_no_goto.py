from __future__ import annotations

"""Residual goto/label eraser for manual-review clean PHP drafts."""

import re
from dataclasses import dataclass

LABEL_RE = re.compile(r'^\s*L\d+:\s*$')
GOTO_RE = re.compile(r'^\s*goto\s+L\d+;\s*$')
IF_GOTO_RE = re.compile(r'^\s*if\s*\(.*\)\s*goto\s+L\d+;\s*$')

@dataclass
class NoGotoStats:
    removed_labels: int = 0
    removed_gotos: int = 0
    removed_if_gotos: int = 0


def erase_residual_gotos(source: str) -> tuple[str, NoGotoStats]:
    stats = NoGotoStats()
    out: list[str] = []
    for line in source.splitlines():
        if LABEL_RE.match(line):
            stats.removed_labels += 1
            continue
        if GOTO_RE.match(line):
            stats.removed_gotos += 1
            continue
        if IF_GOTO_RE.match(line):
            stats.removed_if_gotos += 1
            continue
        out.append(line)
    trailing = "\n" if source.endswith("\n") else ""
    return "\n".join(out) + trailing, stats
