from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Mapping

from .cfg_targets import TargetResolver
from .opcodes import opcode_name


@dataclass
class IRInstruction:
    """Opcode-level intermediate instruction.

    This intentionally stores graph facts (targets/fallthrough) separately from
    PHP text. The PHP renderer is allowed to use text only at the final fallback
    stage.
    """
    index: int
    opcode: str
    pos: int
    condition: Optional[str] = None
    jump_target: Optional[int] = None
    true_target: Optional[int] = None
    false_target: Optional[int] = None
    fallthrough: Optional[int] = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class IRStatement:
    index: int
    code: str
    raw: Mapping[str, Any] = field(default_factory=dict)


def build_ir(op_array: Mapping[str, Any], expr_resolver=None) -> list[IRInstruction]:
    ops = list(op_array.get("opcodes") or [])
    resolver = TargetResolver(ops)
    out: list[IRInstruction] = []
    for pos, op in enumerate(ops):
        name = opcode_name(op.get("opcode_name", op.get("opcode", op.get("opcode_id"))))
        edges = resolver.edge_targets(pos)
        fall = resolver.fallthrough(pos)
        fall_i = fall.index if fall is not None else None
        cond = None
        if expr_resolver is not None:
            try:
                cond = expr_resolver(op.get("op1"))
            except Exception:
                cond = None
        ins = IRInstruction(index=pos, opcode=name, pos=pos, fallthrough=fall_i, raw=op)
        if name == "ZEND_JMP":
            ins.jump_target = edges[0].index if edges else None
        elif name in {"ZEND_JMPZ", "ZEND_JMPZ_EX"}:
            ins.condition = cond
            ins.false_target = edges[0].index if edges else None
            ins.true_target = fall_i
        elif name in {"ZEND_JMPNZ", "ZEND_JMPNZ_EX"}:
            ins.condition = cond
            ins.true_target = edges[0].index if edges else None
            ins.false_target = fall_i
        elif name == "ZEND_JMPZNZ":
            ins.condition = cond
            ins.false_target = edges[0].index if len(edges) > 0 else None
            ins.true_target = edges[1].index if len(edges) > 1 else None
        elif len(edges) == 1:
            if edges[0].index != fall_i:
                ins.jump_target = edges[0].index
        elif len(edges) == 2:
            ins.false_target = edges[0].index
            ins.true_target = edges[1].index
        out.append(ins)
    return out
