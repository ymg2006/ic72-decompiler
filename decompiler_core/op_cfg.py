from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .ir import IRInstruction


@dataclass
class BasicBlock:
    id: int
    start: int
    end: int
    instructions: list[IRInstruction]
    successors: set[int] = field(default_factory=set)
    predecessors: set[int] = field(default_factory=set)


@dataclass
class CFG:
    blocks: dict[int, BasicBlock]
    entry: int
    index_to_block: dict[int, int]

    def exit_blocks(self) -> list[int]:
        return [bid for bid, b in self.blocks.items() if not b.successors]


def _targets(ins: IRInstruction) -> Iterable[int]:
    for t in (ins.jump_target, ins.true_target, ins.false_target, ins.fallthrough):
        if isinstance(t, int) and t >= 0:
            yield t


def build_cfg(ir: list[IRInstruction]) -> CFG:
    if not ir:
        return CFG(blocks={}, entry=0, index_to_block={})
    valid = {ins.index for ins in ir}
    leaders = {ir[0].index}
    for ins in ir:
        for t in _targets(ins):
            if t in valid:
                leaders.add(t)
        # Instruction after a branch starts a block even when it is not the branch target.
        if ins.opcode.startswith("ZEND_JMP") and ins.pos + 1 < len(ir):
            leaders.add(ir[ins.pos + 1].index)
    sorted_leaders = sorted(leaders)
    blocks: dict[int, BasicBlock] = {}
    index_to_block: dict[int, int] = {}
    for bid, start in enumerate(sorted_leaders):
        next_start = sorted_leaders[bid + 1] if bid + 1 < len(sorted_leaders) else (ir[-1].index + 1)
        body = [ins for ins in ir if start <= ins.index < next_start]
        if not body:
            continue
        block = BasicBlock(id=bid, start=body[0].index, end=body[-1].index, instructions=body)
        blocks[bid] = block
        for ins in body:
            index_to_block[ins.index] = bid
    for block in blocks.values():
        last = block.instructions[-1]
        for t in _targets(last):
            tb = index_to_block.get(t)
            if tb is not None and tb != block.id:
                block.successors.add(tb)
    for block in blocks.values():
        for succ in block.successors:
            blocks[succ].predecessors.add(block.id)
    return CFG(blocks=blocks, entry=index_to_block.get(ir[0].index, 0), index_to_block=index_to_block)


def compute_dominators(cfg: CFG) -> dict[int, set[int]]:
    all_blocks = set(cfg.blocks)
    dom = {b: set(all_blocks) for b in cfg.blocks}
    if cfg.entry in dom:
        dom[cfg.entry] = {cfg.entry}
    changed = True
    while changed:
        changed = False
        for bid, block in cfg.blocks.items():
            if bid == cfg.entry:
                continue
            if block.predecessors:
                new = set.intersection(*(dom[p] for p in block.predecessors))
            else:
                new = set()
            new.add(bid)
            if new != dom[bid]:
                dom[bid] = new
                changed = True
    return dom


def compute_postdominators(cfg: CFG) -> dict[int, set[int]]:
    all_blocks = set(cfg.blocks)
    post = {b: set(all_blocks) for b in cfg.blocks}
    exits = cfg.exit_blocks()
    for e in exits:
        post[e] = {e}
    changed = True
    while changed:
        changed = False
        for bid, block in cfg.blocks.items():
            if bid in exits:
                continue
            if block.successors:
                new = set.intersection(*(post[s] for s in block.successors))
            else:
                new = {bid}
            new.add(bid)
            if new != post[bid]:
                post[bid] = new
                changed = True
    return post


def nearest_common_postdominator(a: int, b: int, post: dict[int, set[int]]) -> int | None:
    common = post.get(a, set()) & post.get(b, set())
    if not common:
        return None
    # Prefer the smallest block id among common postdominators as the nearest in linear opcode order.
    return min(common)


def find_back_edges(cfg: CFG, dominators: dict[int, set[int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for bid, block in cfg.blocks.items():
        for succ in block.successors:
            if succ in dominators.get(bid, set()):
                out.append((bid, succ))
    return out
