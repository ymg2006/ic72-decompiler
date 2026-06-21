from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence

JUMP_NAMES = {
    'ZEND_JMP', 'ZEND_JMPZ', 'ZEND_JMPNZ', 'ZEND_JMPZNZ', 'ZEND_JMPZ_EX', 'ZEND_JMPNZ_EX',
    'ZEND_JMP_SET', 'ZEND_COALESCE', 'ZEND_ASSERT_CHECK', 'ZEND_FE_RESET_R', 'ZEND_FE_RESET_RW',
    'ZEND_FE_FETCH_R', 'ZEND_FE_FETCH_RW', 'ZEND_FAST_CALL', 'ZEND_FAST_RET', 'ZEND_CATCH',
}

# Fields produced by the fixed dumper. These are real opcode-array indexes and
# should always win over legacy overloaded operand values.
EXPLICIT_TARGET_KEYS = (
    'jump_target_index',
    'false_target_index',
    'true_target_index',
    'fe_reset_done_target_index',
    'fe_fetch_done_target_index',
    'jmpznz_true_target_index',
    'catch_target_index',
    'finally_target_index',
)

NESTED_TARGET_KEYS = (
    'jump_target_index',
    'target_index',
    'opline_index',
    'opcode_index',
    'index',
)

LEGACY_TARGET_KEYS = (
    'jmp_addr',
    'opline_num',
    'num',
    'var',
    'constant',
)

TERMINATORS = {
    'ZEND_JMP', 'ZEND_RETURN', 'ZEND_THROW', 'ZEND_EXIT', 'ZEND_FAST_RET'
}

CONDITIONAL_JUMPS = {
    'ZEND_JMPZ', 'ZEND_JMPNZ', 'ZEND_JMPZNZ', 'ZEND_JMPZ_EX', 'ZEND_JMPNZ_EX',
    'ZEND_JMP_SET', 'ZEND_COALESCE', 'ZEND_ASSERT_CHECK', 'ZEND_CATCH'
}

@dataclass(frozen=True)
class ResolvedTarget:
    index: int
    source: str
    confidence: str  # exact, legacy-index, heuristic

@dataclass
class TargetResolver:
    ops: Sequence[Mapping[str, Any]]
    index_to_pos: dict[int, int] = field(init=False, default_factory=dict)
    line_to_pos: dict[int, int] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.index_to_pos = {}
        self.line_to_pos = {}
        for pos, op in enumerate(self.ops):
            for key in ('index', 'op_index', 'opcode_index'):
                val = _as_int(op.get(key))
                if val is not None and val not in self.index_to_pos:
                    self.index_to_pos[val] = pos
            line = _as_int(op.get('line', op.get('lineno')))
            if line is not None and line not in self.line_to_pos:
                self.line_to_pos[line] = pos

    def normalize_index(self, value: Any, *, explicit: bool = False, source: str = '') -> Optional[ResolvedTarget]:
        iv = _as_int(value)
        if iv is None:
            return None
        if 0 <= iv < len(self.ops):
            # Explicit fixed-dumper fields are exact. For legacy values, this is
            # still the best available interpretation when it is in range.
            return ResolvedTarget(iv, source or 'direct', 'exact' if explicit else 'legacy-index')
        if iv in self.index_to_pos:
            return ResolvedTarget(self.index_to_pos[iv], source or 'opcode-index-map', 'exact' if explicit else 'legacy-index')
        # Last-resort support for very old dumps that stored source/opline line
        # numbers instead of indexes. This is deliberately marked heuristic and
        # is not used when a precise index exists.
        if iv in self.line_to_pos:
            return ResolvedTarget(self.line_to_pos[iv], source or 'line-map', 'heuristic')
        return None

    def _scan_mapping_keys(self, mapping: Mapping[str, Any], keys: Iterable[str], *, explicit: bool, prefix: str) -> Optional[ResolvedTarget]:
        for key in keys:
            if key not in mapping:
                continue
            rt = self.normalize_index(mapping.get(key), explicit=explicit, source=f'{prefix}{key}')
            if rt is not None:
                return rt
        return None

    def explicit_target(self, op: Mapping[str, Any], preferred_keys: Iterable[str] = EXPLICIT_TARGET_KEYS) -> Optional[ResolvedTarget]:
        rt = self._scan_mapping_keys(op, preferred_keys, explicit=True, prefix='op.')
        if rt is not None:
            return rt
        for slot in ('op1', 'op2', 'result', 'extended'):
            node = op.get(slot) or {}
            if isinstance(node, Mapping):
                rt = self._scan_mapping_keys(node, NESTED_TARGET_KEYS, explicit=True, prefix=f'{slot}.')
                if rt is not None:
                    return rt
        for entry in op.get('jump_targets') or []:
            if isinstance(entry, Mapping):
                rt = self._scan_mapping_keys(entry, NESTED_TARGET_KEYS, explicit=True, prefix='jump_targets[].')
            else:
                rt = self.normalize_index(entry, explicit=False, source='jump_targets[]')
            if rt is not None and (rt.confidence == 'exact' or isinstance(entry, Mapping)):
                return rt
        return None

    def legacy_target(self, op: Mapping[str, Any], slots: Iterable[str] = ('op2', 'op1', 'result')) -> Optional[ResolvedTarget]:
        # jump_targets is the best legacy field. In old dumps it can be either
        # an actual opcode index or an overloaded line-like number.
        for entry in op.get('jump_targets') or []:
            if isinstance(entry, Mapping):
                rt = self._scan_mapping_keys(entry, NESTED_TARGET_KEYS + LEGACY_TARGET_KEYS, explicit=False, prefix='jump_targets[].')
            else:
                rt = self.normalize_index(entry, explicit=False, source='jump_targets[]')
            if rt is not None:
                return rt
        for slot in slots:
            node = op.get(slot) or {}
            if isinstance(node, Mapping):
                rt = self._scan_mapping_keys(node, LEGACY_TARGET_KEYS, explicit=False, prefix=f'{slot}.')
                if rt is not None:
                    return rt
        return self.normalize_index(op.get('jmp_addr'), explicit=False, source='op.jmp_addr')

    def target(self, op: Mapping[str, Any], preferred_keys: Iterable[str] = EXPLICIT_TARGET_KEYS, slots: Iterable[str] = ('op2', 'op1', 'result')) -> Optional[ResolvedTarget]:
        return self.explicit_target(op, preferred_keys=preferred_keys) or self.legacy_target(op, slots=slots)

    def all_targets(self, op: Mapping[str, Any]) -> list[ResolvedTarget]:
        out: list[ResolvedTarget] = []
        seen: set[int] = set()

        def add(rt: Optional[ResolvedTarget]) -> None:
            if rt is not None and rt.index not in seen:
                seen.add(rt.index)
                out.append(rt)

        for key in EXPLICIT_TARGET_KEYS:
            add(self.normalize_index(op.get(key), explicit=True, source=f'op.{key}'))
        for slot in ('op1', 'op2', 'result', 'extended'):
            node = op.get(slot) or {}
            if isinstance(node, Mapping):
                for key in NESTED_TARGET_KEYS:
                    add(self.normalize_index(node.get(key), explicit=True, source=f'{slot}.{key}'))
        for entry in op.get('jump_targets') or []:
            if isinstance(entry, Mapping):
                for key in NESTED_TARGET_KEYS + LEGACY_TARGET_KEYS:
                    add(self.normalize_index(entry.get(key), explicit=('target_index' in key or key.endswith('_index')), source=f'jump_targets[].{key}'))
            else:
                add(self.normalize_index(entry, explicit=False, source='jump_targets[]'))
        # Opcode-specific legacy fallbacks.
        name = op.get('opcode_name')
        if name == 'ZEND_JMP':
            add(self.legacy_target(op, slots=('op1',)))
        elif name in CONDITIONAL_JUMPS or name in {'ZEND_FE_RESET_R', 'ZEND_FE_RESET_RW'}:
            add(self.legacy_target(op, slots=('op2',)))
        elif name in {'ZEND_FE_FETCH_R', 'ZEND_FE_FETCH_RW', 'ZEND_JMPZNZ'}:
            add(self.extended_target(op))
        else:
            add(self.legacy_target(op))
        return out

    def extended_target(self, op: Mapping[str, Any]) -> Optional[ResolvedTarget]:
        node = op.get('extended') or {}
        if isinstance(node, Mapping):
            rt = self._scan_mapping_keys(node, NESTED_TARGET_KEYS + LEGACY_TARGET_KEYS, explicit=True, prefix='extended.')
            if rt is not None:
                return rt
        for key in ('extended.jump_target_index', 'extended_target_index', 'extended_value_decoded', 'extended_value'):
            explicit = key.endswith('_index') or key == 'extended.jump_target_index'
            rt = self.normalize_index(op.get(key), explicit=explicit, source=f'op.{key}')
            if rt is not None:
                return rt
        return None

    def fallthrough(self, pos: int) -> Optional[ResolvedTarget]:
        if pos + 1 < len(self.ops):
            return ResolvedTarget(pos + 1, 'fallthrough', 'exact')
        return None

    def edge_targets(self, pos: int) -> list[ResolvedTarget]:
        op = self.ops[pos]
        name = str(op.get('opcode_name') or '')
        out: list[ResolvedTarget] = []
        seen: set[int] = set()

        def add(rt: Optional[ResolvedTarget]) -> None:
            if rt is not None and rt.index not in seen:
                seen.add(rt.index)
                out.append(rt)

        if name == 'ZEND_JMP':
            add(self.target(op, preferred_keys=('jump_target_index',), slots=('op1',)))
            return out
        if name in CONDITIONAL_JUMPS:
            add(self.target(op, slots=('op2',)))
            add(self.fallthrough(pos))
            return out
        if name in {'ZEND_FE_RESET_R', 'ZEND_FE_RESET_RW'}:
            add(self.target(op, preferred_keys=('fe_reset_done_target_index', 'jump_target_index'), slots=('op2',)))
            add(self.fallthrough(pos))
            return out
        if name in {'ZEND_FE_FETCH_R', 'ZEND_FE_FETCH_RW'}:
            add(self.target(op, preferred_keys=('fe_fetch_done_target_index', 'jump_target_index'), slots=()))
            add(self.extended_target(op))
            add(self.fallthrough(pos))
            return out
        if name == 'ZEND_JMPZNZ':
            add(self.target(op, preferred_keys=('false_target_index', 'jump_target_index'), slots=('op2',)))
            add(self.extended_target(op) or self.target(op, preferred_keys=('true_target_index', 'jmpznz_true_target_index'), slots=()))
            return out
        if name in TERMINATORS:
            return out
        add(self.fallthrough(pos))
        return out


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith('+'):
            text = text[1:]
        if text.startswith('-') and text[1:].isdigit():
            return int(text)
        if text.isdigit():
            return int(text)
    return None


def iter_op_arrays(ir: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    op_arrays = ir.get('op_arrays')
    if isinstance(op_arrays, Mapping):
        for oa in op_arrays.values():
            if isinstance(oa, Mapping):
                yield oa
    # Very old/print_r-converted style sometimes has op_array singular.
    oa = ir.get('op_array') or ir.get('main')
    if isinstance(oa, Mapping):
        yield oa


def opcodes_of(oa: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    ops = oa.get('opcodes')
    if isinstance(ops, list):
        return [op for op in ops if isinstance(op, Mapping)]
    return []


def has_explicit_cfg_targets(op: Mapping[str, Any]) -> bool:
    if any(k in op for k in EXPLICIT_TARGET_KEYS):
        return True
    for slot in ('op1', 'op2', 'result', 'extended'):
        node = op.get(slot) or {}
        if isinstance(node, Mapping) and any(k in node for k in NESTED_TARGET_KEYS):
            return True
    for entry in op.get('jump_targets') or []:
        if isinstance(entry, Mapping) and any(k in entry for k in NESTED_TARGET_KEYS):
            return True
    return False


def op_arrays_have_explicit_cfg_targets(ir: Mapping[str, Any]) -> bool:
    return any(has_explicit_cfg_targets(op) for oa in iter_op_arrays(ir) for op in opcodes_of(oa))


def target_quality_report(ir: Mapping[str, Any]) -> str:
    total_jumps = explicit = legacy = heuristic = unresolved = 0
    arrays = 0
    for oa in iter_op_arrays(ir):
        ops = opcodes_of(oa)
        if not ops:
            continue
        arrays += 1
        resolver = TargetResolver(ops)
        for pos, op in enumerate(ops):
            if op.get('opcode_name') not in JUMP_NAMES:
                continue
            total_jumps += 1
            if has_explicit_cfg_targets(op):
                explicit += 1
            rt = resolver.target(op)
            if rt is None:
                # FE_FETCH/JMPZNZ may use extended target only.
                rt = resolver.extended_target(op)
            if rt is None:
                unresolved += 1
            elif rt.confidence == 'heuristic':
                heuristic += 1
            elif not has_explicit_cfg_targets(op):
                legacy += 1
    if total_jumps == 0:
        return f'CFG target report: {arrays} op arrays; no jump-like opcodes found.'
    parts = [
        f'CFG target report: {arrays} op arrays; {total_jumps} jump-like opcodes',
        f'explicit={explicit}',
        f'legacy-index={legacy}',
        f'heuristic={heuristic}',
        f'unresolved={unresolved}',
    ]
    if explicit == total_jumps and unresolved == 0:
        parts.append('quality=exact')
    elif explicit > 0 and unresolved == 0:
        parts.append('quality=mixed')
    elif unresolved == 0:
        parts.append('quality=legacy-compatible')
    else:
        parts.append('quality=best-effort')
    return '; '.join(parts) + '.'
