from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

LABEL_RE = re.compile(r'^(?P<indent>\s*)L(?P<label>\d+):\s*$')
GOTO_RE = re.compile(r'^(?P<indent>\s*)goto L(?P<label>\d+);\s*$')
IF_GOTO_RE = re.compile(r'^(?P<indent>\s*)if \((?P<cond>.*)\) goto L(?P<label>\d+);\s*$')
TERM_RE = re.compile(r'^\s*(return|throw|exit\b)')

@dataclass
class BasicBlock:
    id: int
    start: int
    end: int
    labels: List[str] = field(default_factory=list)
    successors: Set[int] = field(default_factory=set)
    predecessors: Set[int] = field(default_factory=set)

    def contains(self, line_no: int) -> bool:
        return self.start <= line_no < self.end

@dataclass
class SourceCFG:
    lines: List[str]
    blocks: List[BasicBlock]
    label_to_line: Dict[str, int]
    label_to_block: Dict[str, int]


def invert_condition(cond: str) -> str:
    cond = cond.strip()
    if cond.startswith('!!'):
        return '!' + cond[2:].strip()
    if cond.startswith('!') and not cond.startswith('!='):
        rest = cond[1:].strip()
        if rest.startswith('(') and rest.endswith(')'):
            return rest[1:-1].strip()
        return rest
    return f'!({cond})'


def label_positions(lines: List[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for i, line in enumerate(lines):
        m = LABEL_RE.match(line)
        if m:
            out[m.group('label')] = i
    return out


def goto_refs(lines: List[str]) -> Dict[str, int]:
    refs: Dict[str, int] = {}
    for line in lines:
        for rx in (GOTO_RE, IF_GOTO_RE):
            m = rx.match(line)
            if m:
                refs[m.group('label')] = refs.get(m.group('label'), 0) + 1
    return refs


def is_jump_line(line: str) -> bool:
    return bool(GOTO_RE.match(line) or IF_GOTO_RE.match(line) or TERM_RE.match(line))


def build_source_cfg(lines: List[str]) -> SourceCFG:
    labels = label_positions(lines)
    leaders: Set[int] = {0}
    leaders.update(labels.values())
    for i, line in enumerate(lines):
        if is_jump_line(line) and i + 1 < len(lines):
            leaders.add(i + 1)
        for rx in (GOTO_RE, IF_GOTO_RE):
            m = rx.match(line)
            if m and m.group('label') in labels:
                leaders.add(labels[m.group('label')])
    leader_list = sorted(x for x in leaders if 0 <= x < len(lines))
    blocks: List[BasicBlock] = []
    line_to_block: Dict[int, int] = {}
    for bid, start in enumerate(leader_list):
        end = leader_list[bid + 1] if bid + 1 < len(leader_list) else len(lines)
        blabels = []
        for i in range(start, end):
            m = LABEL_RE.match(lines[i])
            if m:
                blabels.append(m.group('label'))
        block = BasicBlock(bid, start, end, blabels)
        blocks.append(block)
        for i in range(start, end):
            line_to_block[i] = bid
    label_to_block = {lab: line_to_block[pos] for lab, pos in labels.items() if pos in line_to_block}
    for block in blocks:
        last = ''
        for i in range(block.end - 1, block.start - 1, -1):
            if lines[i].strip() and not LABEL_RE.match(lines[i]):
                last = lines[i]
                break
        gm = GOTO_RE.match(last)
        im = IF_GOTO_RE.match(last)
        if gm:
            target = label_to_block.get(gm.group('label'))
            if target is not None:
                block.successors.add(target)
        elif im:
            target = label_to_block.get(im.group('label'))
            if target is not None:
                block.successors.add(target)
            if block.id + 1 < len(blocks):
                block.successors.add(block.id + 1)
        elif TERM_RE.match(last):
            pass
        elif block.id + 1 < len(blocks):
            block.successors.add(block.id + 1)
    for b in blocks:
        for s in b.successors:
            blocks[s].predecessors.add(b.id)
    return SourceCFG(lines, blocks, labels, label_to_block)


def dominators(blocks: List[BasicBlock], entry: int = 0) -> Dict[int, Set[int]]:
    all_ids = {b.id for b in blocks}
    dom: Dict[int, Set[int]] = {b.id: set(all_ids) for b in blocks}
    if entry in dom:
        dom[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for b in blocks:
            if b.id == entry:
                continue
            if b.predecessors:
                new = set.intersection(*(dom[p] for p in b.predecessors))
            else:
                new = set()
            new.add(b.id)
            if new != dom[b.id]:
                dom[b.id] = new
                changed = True
    return dom


def post_dominators(blocks: List[BasicBlock]) -> Dict[int, Set[int]]:
    all_ids = {b.id for b in blocks}
    exits = [b.id for b in blocks if not b.successors]
    pdom: Dict[int, Set[int]] = {b.id: set(all_ids) for b in blocks}
    for e in exits:
        pdom[e] = {e}
    changed = True
    while changed:
        changed = False
        for b in reversed(blocks):
            if b.id in exits:
                continue
            if b.successors:
                new = set.intersection(*(pdom[s] for s in b.successors))
            else:
                new = set()
            new.add(b.id)
            if new != pdom[b.id]:
                pdom[b.id] = new
                changed = True
    return pdom


def nearest_common_postdom(pdom: Dict[int, Set[int]], candidates: Iterable[int], order: List[int]) -> Optional[int]:
    common: Optional[Set[int]] = None
    for c in candidates:
        common = set(pdom.get(c, set())) if common is None else common & pdom.get(c, set())
    if not common:
        return None
    for b in order:
        if b in common:
            return b
    return None
