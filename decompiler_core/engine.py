from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from .utils import php_literal, safe_name, strip_redundant_parens, unwrap

SUPERGLOBALS = {
    "_GET",
    "_POST",
    "_COOKIE",
    "_REQUEST",
    "_SERVER",
    "_SESSION",
    "_FILES",
    "_ENV",
    "GLOBALS",
}


class State:
    def __init__(self) -> None:
        self.temps: Dict[int, str] = {}
        self.arrays: Dict[int, List[str]] = {}
        self.call_stack: List[Dict[str, Any]] = []
        self.pending_bool: Dict[int, Tuple[str, str]] = {}

    def clone(self) -> "State":
        return copy.deepcopy(self)


class Decompiler:
    def __init__(
        self,
        oa: Dict[str, Any],
        lambda_names: Optional[Dict[str, str]] = None,
        lambda_exprs: Optional[Dict[str, str]] = None,
        function_names: Optional[Dict[str, str]] = None,
    ) -> None:
        self.oa = oa
        self.lambda_names = lambda_names or {}
        self.lambda_exprs = lambda_exprs or {}
        self.function_names = function_names or {}
        self.function_name = unwrap(oa.get("function_name"))
        self.is_main = not isinstance(self.function_name, str) or self.function_name == ""
        self.ops: List[Dict[str, Any]] = oa.get("opcodes") or []
        self.n = len(self.ops)
        self.target_overrides = self._compute_target_overrides()
        self.incoming: Dict[int, List[int]] = {}
        for src, op in enumerate(self.ops):
            dst = self.target(op, src)
            if dst is not None:
                self.incoming.setdefault(dst, []).append(src)

    def key(self, operand: Dict[str, Any]) -> int:
        return int(operand.get("var") or operand.get("constant") or 0)

    def op_lit(self, operand: Dict[str, Any]) -> str:
        if "literal" in operand:
            return php_literal(operand["literal"])
        idx = operand.get("constant")
        literals = self.oa.get("literals") or []
        if isinstance(idx, int) and 0 <= idx < len(literals):
            return php_literal(literals[idx])
        return php_literal(operand.get("constant"))

    def _const_string(self, operand: Dict[str, Any]) -> Optional[str]:
        if operand.get("type_name") != "IS_CONST":
            return None
        lit = unwrap(operand.get("literal"))
        if isinstance(lit, str):
            return lit
        idx = operand.get("constant")
        literals = self.oa.get("literals") or []
        if isinstance(idx, int) and 0 <= idx < len(literals):
            lv = unwrap(literals[idx])
            if isinstance(lv, str):
                return lv
        return None

    def _superglobal_var(self, operand: Dict[str, Any]) -> Optional[str]:
        name = self._const_string(operand)
        if name in SUPERGLOBALS:
            return "$" + name
        return None

    def canonical_function_name(self, name: Any) -> str:
        text = str(name)
        return self.function_names.get(text.lower(), text)

    def _literal_value(self, operand: Dict[str, Any]) -> Optional[object]:
        if "literal" in operand:
            return unwrap(operand.get("literal"))
        idx = operand.get("constant")
        literals = self.oa.get("literals") or []
        if isinstance(idx, int) and 0 <= idx < len(literals):
            return unwrap(literals[idx])
        return None

    def is_submit_superglobal_guard(self, index: int) -> bool:
        if index < 2 or index >= self.n:
            return False
        if self.ops[index - 1].get("opcode_name") != "ZEND_ISSET_ISEMPTY_DIM_OBJ":
            return False
        fetch = self.ops[index - 2]
        if fetch.get("opcode_name") not in ("ZEND_FETCH_IS", "ZEND_FETCH_R"):
            return False
        if self._literal_value(fetch.get("op1", {})) not in ("_POST", "_REQUEST"):
            return False
        key = self._literal_value(self.ops[index - 1].get("op2", {}))
        return isinstance(key, str) and "submit" in key.lower()

    def expr(self, operand: Dict[str, Any], st: State) -> str:
        typ = operand.get("type_name")
        if typ == "IS_CV":
            return "$" + safe_name(operand.get("cv_name"), "_cv")
        if typ == "IS_CONST":
            superg = self._superglobal_var(operand)
            if superg is not None:
                return superg
            return self.op_lit(operand)
        if typ in ("IS_TMP_VAR", "IS_VAR"):
            k = self.key(operand)
            return st.temps.get(k, "$_tmp%d" % k)
        if typ == "IS_UNUSED":
            return ""
        return "$_unk"

    def set_tmp(self, operand: Dict[str, Any], value: str, st: State) -> None:
        typ = operand.get("type_name")
        if typ in ("IS_TMP_VAR", "IS_VAR"):
            st.temps[self.key(operand)] = value

    def unresolved_tmp(self, expr: str) -> bool:
        return expr.startswith("$_tmp") and expr[5:].isdigit()

    def recent_result_expr(self, i: int, st: State) -> Optional[str]:
        j = i - 1
        while j >= 0 and self.ops[j].get("opcode_name") in ("ZEND_NOP", "ZEND_FREE", "ZEND_FE_FREE"):
            j -= 1
        if j < 0:
            return None
        result = self.ops[j].get("result", {})
        if result.get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
            return None
        return st.temps.get(self.key(result))

    def expr_or_recent(self, operand: Dict[str, Any], st: State, i: int) -> str:
        expr = self.expr(operand, st)
        if self.unresolved_tmp(expr):
            recent = self.recent_result_expr(i, st)
            if recent is not None:
                return recent
        return expr

    def raw_target(self, op: Dict[str, Any]) -> Optional[int]:
        targets = op.get("jump_targets") or []
        for raw in targets:
            try:
                t = int(raw)
            except Exception:
                continue
            if 0 <= t < self.n:
                return t
        return None

    def target(self, op: Dict[str, Any], index: Optional[int] = None) -> Optional[int]:
        if index is not None and index in self.target_overrides:
            return self.target_overrides[index]
        return self.raw_target(op)

    def _compute_target_overrides(self) -> Dict[int, int]:
        overrides: Dict[int, int] = {}
        branch_names = {"ZEND_JMPZ", "ZEND_JMPNZ"}
        barrier_names = {"ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_JMPZ_EX", "ZEND_JMPNZ_EX", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"}
        call_done_names = {"ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"}
        simple_statement_names = {
            "ZEND_ASSIGN",
            "ZEND_ASSIGN_CONCAT",
            "ZEND_ASSIGN_ADD",
            "ZEND_ASSIGN_SUB",
            "ZEND_ASSIGN_MUL",
            "ZEND_ASSIGN_DIV",
            "ZEND_ASSIGN_MOD",
            "ZEND_ASSIGN_BW_OR",
            "ZEND_ASSIGN_BW_AND",
            "ZEND_ASSIGN_BW_XOR",
            "ZEND_DO_FCALL",
            "ZEND_DO_FCALL_BY_NAME",
            "ZEND_DO_ICALL",
            "ZEND_DO_UCALL",
            "ZEND_ECHO",
            "ZEND_INCLUDE_OR_EVAL",
            "ZEND_QM_ASSIGN",
        }
        condition_prep_names = {
            "ZEND_FETCH_DIM_R",
            "ZEND_FETCH_OBJ_R",
            "ZEND_FETCH_R",
            "ZEND_FETCH_IS",
            "ZEND_ISSET_ISEMPTY_DIM_OBJ",
            "ZEND_ISSET_ISEMPTY_CV",
            "ZEND_BOOL",
            "ZEND_BOOL_NOT",
            "ZEND_IS_EQUAL",
            "ZEND_IS_NOT_EQUAL",
            "ZEND_IS_SMALLER",
            "ZEND_IS_SMALLER_OR_EQUAL",
            "ZEND_IS_IDENTICAL",
            "ZEND_IS_NOT_IDENTICAL",
            "ZEND_INIT_FCALL",
            "ZEND_INIT_FCALL_BY_NAME",
            "ZEND_INIT_DYNAMIC_CALL",
            "ZEND_DO_FCALL",
            "ZEND_DO_FCALL_BY_NAME",
            "ZEND_SEND_VAR",
            "ZEND_SEND_VAR_EX",
            "ZEND_SEND_VAL",
            "ZEND_SEND_VAL_EX",
            "ZEND_JMPZ_EX",
            "ZEND_JMPNZ_EX",
        }

        def local_statement_end(start: int) -> Optional[int]:
            if start >= self.n:
                return None
            name = self.ops[start].get("opcode_name")
            unused_call_end = self.unused_call_statement_end(start, min(start + 24, self.n))
            if unused_call_end is not None:
                return unused_call_end
            call_assign_end = self.call_assignment_statement_end(start, min(start + 24, self.n))
            if call_assign_end is not None:
                return call_assign_end
            expr_assign_end = self.expression_assignment_statement_end(start, min(start + 24, self.n))
            if expr_assign_end is not None:
                return expr_assign_end
            if name == "ZEND_BEGIN_SILENCE":
                saw_statement = False
                for j in range(start + 1, min(start + 16, self.n)):
                    inner_name = self.ops[j].get("opcode_name")
                    if inner_name in call_done_names:
                        if self.ops[j].get("result", {}).get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
                            saw_statement = True
                    elif inner_name in simple_statement_names or inner_name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ"):
                        saw_statement = True
                    if inner_name == "ZEND_END_SILENCE":
                        return j + 1 if saw_statement else None
                    if inner_name in barrier_names or inner_name in ("ZEND_RETURN", "ZEND_EXIT"):
                        return None
            if name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ"):
                if start + 1 < self.n and self.ops[start + 1].get("opcode_name") == "ZEND_OP_DATA":
                    return start + 2
                return start + 1
            if name == "ZEND_FETCH_UNSET":
                if start + 1 < self.n and self.ops[start + 1].get("opcode_name") in ("ZEND_UNSET_DIM", "ZEND_UNSET_OBJ"):
                    return start + 2
                return None
            if name in ("ZEND_UNSET_CV", "ZEND_UNSET_DIM", "ZEND_UNSET_OBJ"):
                return start + 1
            if name in simple_statement_names:
                return start + 1
            return None

        def has_effective_ops(start: int, end: int) -> bool:
            for idx in range(start, min(end, self.n)):
                name = self.ops[idx].get("opcode_name")
                if name in ("ZEND_NOP", "ZEND_FREE", "ZEND_FE_FREE"):
                    continue
                if self.is_null_return(idx) or self.is_implicit_main_return(idx):
                    continue
                return True
            return False

        def is_terminal_return(index: int) -> bool:
            return 0 <= index < self.n and self.ops[index].get("opcode_name") == "ZEND_RETURN"

        def starts_loop_latch(target: int, branch_index: int) -> bool:
            if target <= branch_index or target >= self.n:
                return False
            for scan in range(target, min(target + 8, self.n)):
                name = self.ops[scan].get("opcode_name")
                if name not in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ"):
                    continue
                back = self.raw_target(self.ops[scan])
                if back is not None and back <= branch_index:
                    return True
            return False

        def starts_at_foreach_cleanup(index: int) -> bool:
            return 0 <= index < self.n and self.ops[index].get("opcode_name") == "ZEND_FE_FREE"

        def false_branch_reaches_jump_target(jmp_index: int, false_end: int) -> bool:
            jump_target = self.raw_target(self.ops[jmp_index])
            if jump_target is None or jump_target <= false_end:
                return True
            if false_end < self.n and self.ops[false_end].get("opcode_name") == "ZEND_NOP":
                return True
            return not has_effective_ops(false_end, jump_target)

        def unused_call_info(start: int, limit: int) -> Optional[Tuple[int, int]]:
            if start >= min(limit, self.n):
                return None
            init_names = {
                "ZEND_INIT_FCALL",
                "ZEND_INIT_FCALL_BY_NAME",
                "ZEND_INIT_NS_FCALL_BY_NAME",
                "ZEND_INIT_METHOD_CALL",
                "ZEND_INIT_STATIC_METHOD_CALL",
                "ZEND_INIT_DYNAMIC_CALL",
            }
            if self.ops[start].get("opcode_name") not in init_names:
                return None
            send_count = 0
            idx = start + 1
            limit = min(limit, self.n)
            while idx < limit:
                name = self.ops[idx].get("opcode_name", "")
                if name in call_done_names:
                    if self.ops[idx].get("result", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                        return None
                    return idx + 1, send_count
                if name.startswith("ZEND_SEND_"):
                    send_count += 1
                    idx += 1
                    continue
                if name in barrier_names or name in ("ZEND_RETURN", "ZEND_EXIT", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"):
                    return None
                idx += 1
            return None

        def guarded_unused_call_sequence_end(branch_index: int, raw_end: int) -> Optional[int]:
            if branch_index + 1 >= min(raw_end, self.n):
                return None
            if self.ops[branch_index].get("op1", {}).get("type_name") == "IS_CV":
                return None
            scan_limit = min(raw_end, branch_index + 48, self.n)
            for probe in range(branch_index + 1, scan_limit):
                probe_name = self.ops[probe].get("opcode_name")
                if probe_name == "ZEND_JMP":
                    return None
                if probe_name in branch_names or probe_name in ("ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"):
                    break
            info = unused_call_info(branch_index + 1, scan_limit)
            if info is None:
                return None
            cursor, send_count = info
            if raw_end < self.n and is_terminal_return(raw_end):
                if has_effective_ops(cursor, raw_end):
                    return None
            if cursor < scan_limit and self.ops[cursor].get("opcode_name") == "ZEND_EXIT":
                return cursor + 1
            if send_count:
                while cursor < scan_limit:
                    next_info = unused_call_info(cursor, scan_limit)
                    if next_info is None:
                        break
                    next_cursor, _next_send_count = next_info
                    cursor = next_cursor
                return cursor
            while cursor < scan_limit:
                next_info = unused_call_info(cursor, scan_limit)
                if next_info is None:
                    break
                next_cursor, next_send_count = next_info
                if next_send_count:
                    break
                cursor = next_cursor
            return cursor

        def guarded_call_then_guard_end(branch_index: int, raw_end: int) -> Optional[int]:
            if self.ops[branch_index].get("op1", {}).get("type_name") == "IS_CV":
                return None
            first = unused_call_info(branch_index + 1, min(raw_end, branch_index + 32, self.n))
            if first is None:
                return None
            cursor, _send_count = first
            nested_branch = None
            for idx in range(cursor, min(raw_end, cursor + 16, self.n)):
                name = self.ops[idx].get("opcode_name")
                if name in branch_names:
                    nested_branch = idx
                    break
                if name in call_done_names and self.ops[idx].get("result", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                    continue
                if name in simple_statement_names or name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ", "ZEND_JMP", "ZEND_RETURN", "ZEND_EXIT", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"):
                    return None
            if nested_branch is None:
                return None
            nested_end = guarded_unused_call_sequence_end(nested_branch, raw_end)
            if nested_end is None or nested_end <= nested_branch + 1:
                return None
            return nested_end

        def single_dim_assignment_guard_end(branch_index: int, raw_end: int) -> Optional[int]:
            body_start = branch_index + 1
            if body_start + 1 >= min(raw_end, self.n):
                return None
            if self.ops[body_start].get("opcode_name") not in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ"):
                return None
            cursor = body_start
            while cursor + 1 < min(raw_end, self.n):
                if self.ops[cursor].get("opcode_name") not in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ"):
                    break
                if self.ops[cursor + 1].get("opcode_name") != "ZEND_OP_DATA":
                    break
                cursor += 2
            return cursor if cursor > body_start else None

        def local_if_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            true_start = branch_index + 1
            true_end = local_block_end_before_jump(true_start, raw_end, max_statements=4)
            if true_end is None:
                return None
            jmp_index = true_end
            if jmp_index >= min(raw_end, self.n) or self.ops[jmp_index].get("opcode_name") != "ZEND_JMP":
                return None
            false_start = jmp_index + 1
            false_end = local_block_end_before_jump(false_start, raw_end, max_statements=4)
            if false_end is None:
                false_end = local_block_end_at_nop(false_start, raw_end, max_statements=4)
            if false_end is None:
                false_end = local_statement_end(false_start)
            if false_end is None:
                return None
            jmp_target = self.raw_target(self.ops[jmp_index])
            if jmp_target is not None and false_start < jmp_target < raw_end:
                for probe in range(jmp_target, min(raw_end, self.n)):
                    probe_name = self.ops[probe].get("opcode_name")
                    if probe_name not in branch_names:
                        continue
                    back_target = self.raw_target(self.ops[probe])
                    if back_target is not None and back_target <= false_start:
                        return None
            return false_start, false_end, jmp_index

        def local_block_end_at_nop(start: int, raw_end: int, max_statements: int = 4) -> Optional[int]:
            cursor = start
            statements = 0
            limit = min(raw_end, self.n)
            while cursor < limit and statements < max_statements:
                if self.ops[cursor].get("opcode_name") == "ZEND_NOP":
                    return cursor if statements else None
                stmt_end = local_statement_end(cursor)
                if stmt_end is None or stmt_end <= cursor or stmt_end > limit:
                    return None
                cursor = stmt_end
                statements += 1
                if cursor < limit and self.ops[cursor].get("opcode_name") == "ZEND_NOP":
                    return cursor
            return None

        def local_block_end_before_jump(start: int, raw_end: int, max_statements: int = 4) -> Optional[int]:
            cursor = start
            statements = 0
            limit = min(raw_end, self.n)
            while cursor < limit and statements < max_statements:
                if self.ops[cursor].get("opcode_name") == "ZEND_JMP":
                    return cursor if statements else None
                stmt_end = local_statement_end(cursor)
                if stmt_end is None or stmt_end <= cursor or stmt_end > limit:
                    return None
                cursor = stmt_end
                statements += 1
                if cursor < limit and self.ops[cursor].get("opcode_name") == "ZEND_JMP":
                    return cursor
            return None

        def local_include_if_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            true_start = branch_index + 1
            if true_start >= self.n or self.ops[true_start].get("opcode_name") != "ZEND_INCLUDE_OR_EVAL":
                return None
            true_end = local_statement_end(true_start)
            if true_end is None:
                return None
            jmp_index = true_end
            if jmp_index >= min(raw_end, self.n) or self.ops[jmp_index].get("opcode_name") != "ZEND_JMP":
                return None
            false_start = jmp_index + 1
            if false_start >= self.n or self.ops[false_start].get("opcode_name") != "ZEND_INCLUDE_OR_EVAL":
                return None
            false_end = local_statement_end(false_start)
            if false_end is None:
                return None
            return false_start, false_end, jmp_index

        def local_multi_if_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            for jmp_index in range(branch_index + 2, min(raw_end, branch_index + 64, self.n)):
                if self.ops[jmp_index].get("opcode_name") in ("ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT", "ZEND_JMPZ", "ZEND_JMPNZ"):
                    return None
                if self.ops[jmp_index].get("opcode_name") != "ZEND_JMP":
                    continue
                false_start = jmp_index + 1
                false_end = local_statement_end(false_start)
                if false_end is None:
                    return None
                return false_start, false_end, jmp_index
            return None

        def local_outer_if_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            for jmp_index in range(branch_index + 2, min(raw_end, branch_index + 64, self.n)):
                name = self.ops[jmp_index].get("opcode_name")
                if name in ("ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"):
                    return None
                if name != "ZEND_JMP":
                    continue
                if self.raw_target(self.ops[jmp_index]) != jmp_index + 1:
                    continue
                false_start = jmp_index + 1
                false_end = local_statement_end(false_start)
                if false_end is None:
                    return None
                return false_start, false_end, jmp_index
            return None

        def local_guarded_region_end(branch_index: int, raw_end: int) -> Optional[int]:
            scan_end = min(raw_end, branch_index + 16, self.n)
            for nested in range(branch_index + 1, scan_end):
                name = self.ops[nested].get("opcode_name")
                if name in ("ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"):
                    return None
                if name not in branch_names:
                    continue
                nested_body_end = local_statement_end(nested + 1)
                if nested_body_end is None or nested_body_end <= nested + 1 or nested_body_end >= raw_end:
                    return None
                if self.ops[nested + 1].get("opcode_name") != "ZEND_ECHO":
                    return None
                if nested_body_end < self.n and self.ops[nested_body_end].get("opcode_name") == "ZEND_JMP":
                    local_else_start = nested_body_end + 1
                    local_else_end = local_statement_end(local_else_start)
                    if local_else_end is None or local_else_end <= local_else_start:
                        return None
                    if self.ops[local_else_start].get("opcode_name") != "ZEND_ECHO":
                        return None
                    return local_else_start
                return nested_body_end
            return None

        def echo_block_end(start: int, limit: int, max_echo: Optional[int] = None) -> Optional[int]:
            idx = start
            echo_count = 0
            limit = min(limit, self.n)
            allowed = {
                "ZEND_ECHO",
                "ZEND_FETCH_DIM_R",
                "ZEND_FETCH_OBJ_R",
                "ZEND_FETCH_R",
                "ZEND_INIT_FCALL",
                "ZEND_INIT_FCALL_BY_NAME",
                "ZEND_INIT_NS_FCALL_BY_NAME",
                "ZEND_SEND_VAR",
                "ZEND_SEND_VAR_EX",
                "ZEND_SEND_VAL",
                "ZEND_SEND_VAL_EX",
                "ZEND_DO_FCALL",
                "ZEND_DO_FCALL_BY_NAME",
                "ZEND_DO_ICALL",
                "ZEND_DO_UCALL",
                "ZEND_CONCAT",
                "ZEND_FAST_CONCAT",
            }
            while idx < limit:
                name = self.ops[idx].get("opcode_name")
                if name == "ZEND_ECHO":
                    echo_count += 1
                    idx += 1
                    if max_echo is not None and echo_count >= max_echo:
                        return idx
                    continue
                if name in allowed:
                    idx += 1
                    continue
                break
            return idx if echo_count and idx > start else None

        def echo_count(start: int, end: int) -> int:
            return sum(1 for idx in range(start, min(end, self.n)) if self.ops[idx].get("opcode_name") == "ZEND_ECHO")

        def template_condition_block_end(start: int, limit: int, max_echo: Optional[int] = None) -> Optional[int]:
            limit = min(limit, self.n)
            branch_index = None
            for idx in range(start, min(start + 16, limit)):
                name = self.ops[idx].get("opcode_name")
                if name in branch_names:
                    branch_index = idx
                    break
                if name in ("ZEND_JMP", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"):
                    return None
            if branch_index is None:
                return None
            body_end = echo_block_end(branch_index + 1, limit, max_echo)
            if body_end is None:
                return None
            return body_end

        def local_template_echo_if(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            for jmp_index in range(branch_index + 2, min(raw_end, branch_index + 40, self.n)):
                if self.ops[jmp_index].get("opcode_name") != "ZEND_JMP":
                    continue
                true_end = echo_block_end(branch_index + 1, jmp_index)
                if true_end != jmp_index:
                    continue
                false_start = jmp_index + 1
                true_echo_count = echo_count(branch_index + 1, jmp_index)
                false_end = echo_block_end(false_start, raw_end, true_echo_count)
                if false_end is None:
                    false_end = template_condition_block_end(false_start, raw_end, true_echo_count)
                if false_end is None or false_end <= false_start:
                    return None
                return false_start, false_end, jmp_index
            return None

        def local_template_echo_guard(branch_index: int, raw_end: int) -> Optional[int]:
            if branch_index + 1 >= self.n or self.ops[branch_index + 1].get("opcode_name") != "ZEND_ECHO":
                return None
            body_end = local_statement_end(branch_index + 1)
            if body_end is None or body_end <= branch_index + 1 or body_end >= raw_end:
                return None
            return body_end

        def optional_foreach_join(branch_index: int, raw_end: int) -> Optional[int]:
            for idx in range(branch_index + 1, min(raw_end, branch_index + 24, self.n)):
                if self.ops[idx].get("opcode_name") not in ("ZEND_FE_RESET_R", "ZEND_FE_RESET_RW"):
                    continue
                if idx - branch_index > 6:
                    continue
                blocked = False
                for pre_idx in range(branch_index + 1, idx):
                    pre_name = self.ops[pre_idx].get("opcode_name")
                    if (
                        pre_name in simple_statement_names
                        or pre_name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ", "ZEND_ECHO", "ZEND_EXIT", "ZEND_RETURN")
                        or pre_name in barrier_names
                    ):
                        blocked = True
                        break
                if blocked:
                    continue
                done = self.raw_target(self.ops[idx])
                if done is None or done <= idx or done >= raw_end:
                    continue
                if done < self.n and self.ops[done].get("opcode_name") == "ZEND_FE_FREE":
                    after = done + 1
                    stmt_end = local_statement_end(after)
                    if stmt_end is not None and stmt_end < raw_end:
                        return stmt_end
                    return after
            return None

        def guarded_collection_block_end(branch_index: int, raw_end: int) -> Optional[int]:
            if branch_index + 1 >= self.n or self.ops[branch_index + 1].get("opcode_name") != "ZEND_ASSIGN_DIM":
                return None

            def expression_dim_assignment_end(start: int, limit: int) -> Optional[int]:
                produced_tmps = set()
                cursor = start
                while cursor < min(limit, self.n):
                    current = self.ops[cursor]
                    name = current.get("opcode_name")
                    if name in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"):
                        return None
                    if name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ") and cursor + 1 < min(limit, self.n):
                        op_data = self.ops[cursor + 1]
                        if op_data.get("opcode_name") != "ZEND_OP_DATA":
                            return None
                        if self.op_uses_tmps(current, produced_tmps) or self.operand_uses_tmp(op_data.get("op1", {}), produced_tmps):
                            return cursor + 2
                        return None
                    result = current.get("result", {})
                    if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                        produced_tmps.add(self.key(result))
                    cursor += 1
                return None

            for idx in range(branch_index + 1, min(raw_end, branch_index + 16, self.n)):
                if self.ops[idx].get("opcode_name") not in ("ZEND_FE_RESET_R", "ZEND_FE_RESET_RW"):
                    continue
                done = self.raw_target(self.ops[idx])
                if done is None or done <= idx or done >= raw_end:
                    continue
                if done >= self.n or self.ops[done].get("opcode_name") != "ZEND_FE_FREE":
                    continue
                cursor = done + 1
                while cursor < min(raw_end, self.n):
                    if cursor + 1 < raw_end and self.ops[cursor].get("opcode_name") == "ZEND_FETCH_UNSET" and self.ops[cursor + 1].get("opcode_name") == "ZEND_UNSET_DIM":
                        return cursor + 2
                    expr_dim_end = expression_dim_assignment_end(cursor, raw_end)
                    if expr_dim_end is not None and cursor < expr_dim_end < raw_end:
                        cursor = expr_dim_end
                        continue
                    stmt_end = local_statement_end(cursor)
                    if stmt_end is None or stmt_end <= cursor or stmt_end >= raw_end:
                        break
                    cursor = stmt_end
                return cursor if cursor > done + 1 else done + 1
            return None

        def operand_literal_value(index: int, operand: str) -> Optional[object]:
            if index < 0 or index >= self.n:
                return None
            value = self.ops[index].get(operand, {}).get("literal")
            if isinstance(value, dict):
                return value.get("value")
            return value

        def superglobal_isset_key(branch_index: int) -> Optional[object]:
            if branch_index < 2:
                return None
            if self.ops[branch_index - 1].get("opcode_name") != "ZEND_ISSET_ISEMPTY_DIM_OBJ":
                return None
            fetch = self.ops[branch_index - 2]
            if fetch.get("opcode_name") not in ("ZEND_FETCH_IS", "ZEND_FETCH_R"):
                return None
            if operand_literal_value(branch_index - 2, "op1") not in ("_POST", "_GET", "_REQUEST"):
                return None
            return operand_literal_value(branch_index - 1, "op2")

        def terminal_redirect_status_end(branch_index: int, raw_end: int) -> Optional[int]:
            scan_end = min(raw_end, branch_index + 320, self.n - 2)
            for term_idx in range(branch_index + 1, scan_end):
                if self.ops[term_idx].get("opcode_name") != "ZEND_EXIT":
                    continue
                if self.ops[term_idx + 1].get("opcode_name") != "ZEND_JMP":
                    continue
                follow = term_idx + 2
                if follow >= raw_end or follow >= self.n:
                    continue
                if self.ops[follow].get("opcode_name") == "ZEND_ASSIGN" and self.ops[follow].get("op1", {}).get("type_name") == "IS_CV":
                    return follow + 1
            return None

        def negated_isset_cv_guard(branch_index: int) -> bool:
            if branch_index < 2:
                return False
            bool_not = self.ops[branch_index - 1]
            isset_op = self.ops[branch_index - 2]
            if bool_not.get("opcode_name") != "ZEND_BOOL_NOT":
                return False
            if isset_op.get("opcode_name") != "ZEND_ISSET_ISEMPTY_CV":
                return False
            if bool_not.get("op1", {}).get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
                return False
            if isset_op.get("result", {}).get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
                return False
            return self.key(bool_not["op1"]) == self.key(isset_op["result"])

        def range_uses_literal(start: int, end: int, literal: object) -> bool:
            for idx in range(start, min(end, self.n)):
                op = self.ops[idx]
                for operand_name in ("op1", "op2"):
                    if operand_literal_value(idx, operand_name) == literal:
                        return True
                    operand = op.get(operand_name, {})
                    if unwrap(operand.get("literal")) == literal:
                        return True
            return False

        def superglobal_key_foreach_end(start: int, raw_end: int, key: object) -> Optional[int]:
            if start + 3 >= min(raw_end, self.n):
                return None
            if self.ops[start].get("opcode_name") not in ("ZEND_FETCH_R", "ZEND_FETCH_IS"):
                return None
            if operand_literal_value(start, "op1") not in ("_POST", "_GET", "_REQUEST"):
                return None
            if self.ops[start + 1].get("opcode_name") != "ZEND_FETCH_DIM_R":
                return None
            if operand_literal_value(start + 1, "op2") != key:
                return None
            if self.ops[start + 2].get("opcode_name") not in ("ZEND_FE_RESET_R", "ZEND_FE_RESET_RW"):
                return None
            if self.ops[start + 3].get("opcode_name") not in ("ZEND_FE_FETCH_R", "ZEND_FE_FETCH_RW"):
                return None
            done = self.raw_target(self.ops[start + 3]) or self.raw_target(self.ops[start + 2])
            if done is None or done <= start + 3 or done > min(raw_end, self.n):
                return None
            if done < self.n and self.ops[done].get("opcode_name") == "ZEND_FE_FREE":
                return done + 1
            return done

        def superglobal_key_unset_end(start: int, end: int, key: object) -> Optional[int]:
            for idx in range(start, min(end, self.n - 1)):
                if self.ops[idx].get("opcode_name") != "ZEND_FETCH_UNSET":
                    continue
                if self.ops[idx + 1].get("opcode_name") != "ZEND_UNSET_DIM":
                    continue
                if operand_literal_value(idx, "op1") not in ("_POST", "_GET", "_REQUEST"):
                    continue
                if operand_literal_value(idx + 1, "op2") == key:
                    return idx + 2
            return None

        def literal_key_dependent_branch_end(branch_index: int, raw_end: int) -> Optional[int]:
            key = superglobal_isset_key(branch_index)
            if not isinstance(key, str) or "submit" in key.lower():
                return None
            cursor = branch_index + 1
            consumed = False
            while cursor < min(raw_end, self.n):
                if (
                    cursor + 1 < raw_end
                    and self.ops[cursor].get("opcode_name") == "ZEND_FETCH_UNSET"
                    and self.ops[cursor + 1].get("opcode_name") == "ZEND_UNSET_DIM"
                    and operand_literal_value(cursor, "op1") in ("_POST", "_GET", "_REQUEST")
                    and operand_literal_value(cursor + 1, "op2") == key
                ):
                    return cursor + 2 if consumed else None
                stmt_end = self.expression_assignment_statement_end(cursor, min(raw_end, cursor + 32, self.n))
                if stmt_end is None:
                    stmt_end = local_statement_end(cursor)
                if stmt_end is None or stmt_end <= cursor or stmt_end >= raw_end:
                    unset_end = superglobal_key_unset_end(cursor, min(raw_end, cursor + 32, self.n), key)
                    if unset_end is not None and (consumed or range_uses_literal(cursor, unset_end, key)):
                        return unset_end
                    foreach_end = superglobal_key_foreach_end(cursor, raw_end, key)
                    if foreach_end is not None and cursor < foreach_end < raw_end:
                        cursor = foreach_end
                        consumed = True
                        continue
                    break
                unset_end = superglobal_key_unset_end(cursor, stmt_end, key)
                if unset_end is not None and (consumed or range_uses_literal(cursor, unset_end, key)):
                    return unset_end
                uses_key = range_uses_literal(cursor, stmt_end, key)
                next_end = self.expression_assignment_statement_end(stmt_end, min(raw_end, stmt_end + 32, self.n))
                if next_end is None:
                    next_end = local_statement_end(stmt_end)
                next_uses_key = next_end is not None and next_end > stmt_end and range_uses_literal(stmt_end, next_end, key)
                if uses_key or (not consumed and next_uses_key):
                    cursor = stmt_end
                    consumed = True
                    continue
                break
            return cursor if consumed and cursor > branch_index + 1 else None

        def loop_body_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            scan_end = min(max(raw_end, branch_index + 128), self.n)
            for pre_jmp in range(branch_index + 1, min(scan_end, branch_index + 16, self.n)):
                if self.ops[pre_jmp].get("opcode_name") != "ZEND_JMP":
                    continue
                if pre_jmp - branch_index > 4:
                    continue
                if not any(self.ops[k].get("opcode_name") == "ZEND_ASSIGN" for k in range(branch_index + 1, pre_jmp)):
                    continue
                loop_branch = None
                for idx in range(pre_jmp + 1, scan_end):
                    if self.ops[idx].get("opcode_name") in ("ZEND_JMPNZ", "ZEND_JMPZ"):
                        target = self.raw_target(self.ops[idx])
                        if target is not None and target <= idx:
                            loop_branch = idx
                            break
                if loop_branch is None:
                    continue
                after_loop = loop_branch + 1
                for jmp_after_true in range(after_loop, min(scan_end, after_loop + 12, self.n)):
                    if self.ops[jmp_after_true].get("opcode_name") != "ZEND_JMP":
                        continue
                    false_start = jmp_after_true + 1
                    false_end = local_statement_end(false_start)
                    if false_end is None:
                        return None
                    after_false = false_end
                    if after_false < self.n and self.ops[after_false].get("opcode_name") == "ZEND_JMP":
                        skipped_end = local_statement_end(after_false + 1)
                        if skipped_end is not None:
                            overrides[after_false] = skipped_end
                            after_false = skipped_end
                    return false_start, after_false, jmp_after_true
            return None

        def independent_silenced_terminal_tail(start: int, first_end: int, raw_end: int) -> bool:
            if raw_end >= self.n or not is_terminal_return(raw_end):
                return False
            if self.ops[start].get("opcode_name") != "ZEND_BEGIN_SILENCE":
                return False
            cursor = first_end
            saw_tail = False
            while cursor < raw_end:
                name = self.ops[cursor].get("opcode_name")
                if name in ("ZEND_NOP", "ZEND_FREE"):
                    cursor += 1
                    continue
                if name != "ZEND_BEGIN_SILENCE":
                    return False
                tail_end = local_statement_end(cursor)
                if tail_end is None or tail_end <= cursor or tail_end > raw_end:
                    return False
                if any(self.ops[idx].get("opcode_name") in barrier_names for idx in range(cursor, tail_end)):
                    return False
                saw_tail = True
                cursor = tail_end
            return saw_tail

        def short_statement_join(branch_index: int, raw_end: int) -> Optional[int]:
            if raw_end <= branch_index + 1:
                return None
            idx = branch_index + 1
            allowed = {
                "ZEND_ECHO",
                "ZEND_INCLUDE_OR_EVAL",
                "ZEND_DO_FCALL",
                "ZEND_DO_FCALL_BY_NAME",
                "ZEND_DO_ICALL",
                "ZEND_DO_UCALL",
                "ZEND_INIT_FCALL",
                "ZEND_INIT_FCALL_BY_NAME",
                "ZEND_INIT_METHOD_CALL",
                "ZEND_INIT_STATIC_METHOD_CALL",
                "ZEND_INIT_DYNAMIC_CALL",
                "ZEND_BEGIN_SILENCE",
            }
            first_end = local_statement_end(idx)
            if first_end is None or first_end <= idx:
                return None
            if raw_end < self.n and is_terminal_return(raw_end):
                if has_effective_ops(first_end, raw_end) and not independent_silenced_terminal_tail(idx, first_end, raw_end):
                    return None
            first_stmt_cvs = self.assigned_cvs_in_range(idx, first_end)
            if first_stmt_cvs and any(self.op_uses_cvs(self.ops[probe], first_stmt_cvs) for probe in range(first_end, min(raw_end, self.n))):
                return None
            if self.ops[idx].get("opcode_name") not in allowed and self.ops[idx].get("opcode_name") not in simple_statement_names:
                return None
            if first_end >= min(raw_end, self.n):
                return None
            next_name = self.ops[first_end].get("opcode_name")
            if next_name == "ZEND_BEGIN_SILENCE":
                next_end = local_statement_end(first_end)
                if next_end is None:
                    return first_end
                if (
                    self.ops[idx].get("opcode_name") == "ZEND_BEGIN_SILENCE"
                    and raw_end < self.n
                    and (
                        self.is_implicit_main_return(raw_end)
                        or self.ops[raw_end].get("opcode_name") in ("ZEND_RETURN", "ZEND_NOP")
                    )
                ):
                    return first_end
                return None
            if next_name in simple_statement_names or next_name in condition_prep_names or next_name in branch_names | {"ZEND_JMP", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"}:
                return first_end
            return None

        def terminated_body_end(start: int, raw_end: int) -> Optional[int]:
            saw_statement = False
            j = start
            while j < min(raw_end, self.n):
                name = self.ops[j].get("opcode_name")
                if name in ("ZEND_EXIT", "ZEND_RETURN"):
                    return j + 1 if saw_statement else None
                if name in simple_statement_names or name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ", "ZEND_INIT_ARRAY", "ZEND_ADD_ARRAY_ELEMENT"):
                    saw_statement = True
                    j += 1
                    continue
                if name in condition_prep_names or name.startswith("ZEND_SEND_"):
                    j += 1
                    continue
                if name in barrier_names:
                    return None
                j += 1
            return None

        def terminated_condition_chain_end(start: int, raw_end: int) -> Optional[int]:
            cursor = start
            count = 0
            while cursor < min(raw_end, self.n):
                branch_index = None
                j = cursor
                while j < min(raw_end, cursor + 12, self.n):
                    name = self.ops[j].get("opcode_name")
                    if name in branch_names:
                        branch_index = j
                        break
                    if name not in condition_prep_names and not name.startswith("ZEND_SEND_"):
                        return cursor if count else None
                    j += 1
                if branch_index is None:
                    return cursor if count else None
                body_end = terminated_body_end(branch_index + 1, raw_end)
                if body_end is None or body_end <= branch_index + 1:
                    return cursor if count else None
                cursor = body_end
                count += 1
            return cursor if count else None

        def guarded_statement_end(start: int, raw_end: int) -> Optional[int]:
            direct = local_statement_end(start)
            if direct is not None:
                return direct
            chain = terminated_condition_chain_end(start, raw_end)
            if chain is None or chain <= start:
                cursor = start
                used_exit_guard = False
                while cursor < min(raw_end, self.n):
                    branch_index = None
                    j = cursor
                    while j < min(raw_end, cursor + 12, self.n):
                        name = self.ops[j].get("opcode_name")
                        if name in branch_names:
                            branch_index = j
                            break
                        if name not in condition_prep_names and not name.startswith("ZEND_SEND_"):
                            branch_index = None
                            break
                        j += 1
                    if branch_index is None or branch_index + 1 >= raw_end:
                        break
                    if self.ops[branch_index + 1].get("opcode_name") != "ZEND_EXIT":
                        break
                    cursor = branch_index + 2
                    used_exit_guard = True
                if not used_exit_guard:
                    return None
                tail = local_statement_end(cursor)
                if tail is not None and tail <= raw_end:
                    return tail
                return cursor if cursor > start else None
            tail = local_statement_end(chain)
            if tail is not None and tail <= raw_end:
                return tail
            return chain

        def guarded_block_if_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            if branch_index + 1 < self.n and self.ops[branch_index + 1].get("opcode_name") in ("ZEND_EXIT", "ZEND_RETURN"):
                return None
            for jmp_index in range(branch_index + 2, min(raw_end, branch_index + 64, self.n)):
                name = self.ops[jmp_index].get("opcode_name")
                if name in ("ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN"):
                    return None
                if name != "ZEND_JMP":
                    continue
                bad_nested = False
                for nested in range(branch_index + 1, jmp_index):
                    if self.ops[nested].get("opcode_name") not in branch_names:
                        continue
                    if nested + 1 >= jmp_index or self.ops[nested + 1].get("opcode_name") != "ZEND_EXIT":
                        bad_nested = True
                        break
                if bad_nested:
                    return None
                if not any(
                    self.ops[k].get("opcode_name") in simple_statement_names or self.ops[k].get("opcode_name") in ("ZEND_UNSET_DIM", "ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ")
                    for k in range(branch_index + 1, jmp_index)
                ):
                    continue
                false_start = jmp_index + 1
                false_end = guarded_statement_end(false_start, raw_end)
                if false_end is None or false_end <= false_start or false_end >= raw_end:
                    continue
                return false_start, false_end, jmp_index
            return None

        def guarded_assignment_if_else(branch_index: int, raw_end: int) -> Optional[Tuple[int, int, int]]:
            body_start = branch_index + 1
            first_stmt_end = self.call_assignment_statement_end(body_start, min(raw_end, body_start + 16, self.n))
            if first_stmt_end is None:
                first_stmt_end = local_statement_end(body_start)
            if first_stmt_end is None or first_stmt_end <= body_start or first_stmt_end >= raw_end:
                return None
            guard_end = terminated_condition_chain_end(first_stmt_end, raw_end)
            if guard_end is None or guard_end <= first_stmt_end or guard_end >= raw_end:
                guard_end = None
                for candidate in range(first_stmt_end + 1, min(raw_end, first_stmt_end + 48, self.n)):
                    if self.ops[candidate].get("opcode_name") != "ZEND_JMP":
                        continue
                    prev = candidate - 1
                    while prev > first_stmt_end and self.ops[prev].get("opcode_name") in ("ZEND_FREE", "ZEND_NOP", "ZEND_FE_FREE"):
                        prev -= 1
                    if self.ops[prev].get("opcode_name") in ("ZEND_EXIT", "ZEND_RETURN"):
                        guard_end = candidate
                        break
                if guard_end is None:
                    return None
            if self.ops[guard_end].get("opcode_name") != "ZEND_JMP":
                return None
            false_start = guard_end + 1
            false_end = guarded_statement_end(false_start, raw_end)
            if false_end is None or false_end <= false_start or false_end >= raw_end:
                return None
            return false_start, false_end, guard_end

        def short_main_branch_join(branch_index: int) -> Optional[int]:
            branch_raw = self.raw_target(self.ops[branch_index])
            if branch_raw is None or branch_raw <= branch_index + 1:
                return None
            saw_statement = False
            statement_count = 0
            last_statement_end = branch_index + 1
            j = branch_index + 1
            while j < min(branch_raw, branch_index + 20, self.n):
                name = self.ops[j].get("opcode_name")
                if name in call_done_names and self.ops[j].get("result", {}).get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
                    statement_count += 1
                    saw_statement = True
                    last_statement_end = j + 1
                    j += 1
                    continue
                if name in ("ZEND_ASSIGN", "ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ", "ZEND_ECHO"):
                    statement_count += 1
                    saw_statement = True
                    last_statement_end = j + 1
                    j += 1
                    continue
                if saw_statement and name in branch_names:
                    if statement_count <= 4:
                        return last_statement_end
                    return None
                if saw_statement and name in condition_prep_names:
                    j += 1
                    continue
                if name in barrier_names or name in ("ZEND_EXIT", "ZEND_RETURN"):
                    return None
                j += 1
            return None

        for i, op in enumerate(self.ops):
            if op.get("opcode_name") not in branch_names:
                continue
            raw = self.raw_target(op)
            if raw is None or raw <= i + 1:
                continue
            if raw - 1 > i and self.ops[raw - 1].get("opcode_name") == "ZEND_JMP":
                explicit_join = self.raw_target(self.ops[raw - 1])
                if explicit_join is not None and explicit_join > raw:
                    continue
            condition_cvs = set()
            if op.get("op1", {}).get("type_name") == "IS_CV":
                condition_cvs.add(self.key(op["op1"]))
            large_cv_guard = bool(condition_cvs) and raw - i > 16
            terminal_return_guard = False
            if raw < self.n and is_terminal_return(raw):
                first_guard_stmt_end = local_statement_end(i + 1)
                terminal_return_guard = (
                    first_guard_stmt_end is not None
                    and i + 1 < first_guard_stmt_end < raw
                    and has_effective_ops(first_guard_stmt_end, raw)
                )
            if terminal_return_guard:
                if not independent_silenced_terminal_tail(i + 1, first_guard_stmt_end, raw):
                    continue
            if starts_loop_latch(raw, i):
                continue

            submit_key = superglobal_isset_key(i)
            if raw - i > 96 and isinstance(submit_key, str) and "submit" in submit_key.lower():
                form_end = terminal_redirect_status_end(i, raw)
                if form_end is not None and i + 1 < form_end < raw:
                    overrides[i] = form_end
                    continue

            long_form_end = terminal_redirect_status_end(i, raw) if negated_isset_cv_guard(i) else None
            if raw - i > 96 and long_form_end is not None and i + 1 < long_form_end < raw:
                overrides[i] = long_form_end
                continue

            nested_guard_end = guarded_call_then_guard_end(i, raw)
            if nested_guard_end is not None and i + 1 < nested_guard_end < raw:
                overrides[i] = nested_guard_end
                continue

            call_guard_end = guarded_unused_call_sequence_end(i, raw)
            if call_guard_end is not None and i + 1 < call_guard_end < raw:
                overrides[i] = call_guard_end
                continue

            local_else = local_if_else(i, raw)
            if local_else is not None:
                false_start, false_end, jmp_index = local_else
                if starts_at_foreach_cleanup(false_start):
                    pass
                elif not false_branch_reaches_jump_target(jmp_index, false_end):
                    pass
                else:
                    overrides[i] = false_start
                    overrides[jmp_index] = false_end
                    continue

            guarded_assignment_else = guarded_assignment_if_else(i, raw)
            if guarded_assignment_else is not None:
                false_start, false_end, jmp_index = guarded_assignment_else
                if starts_at_foreach_cleanup(false_start):
                    pass
                elif not false_branch_reaches_jump_target(jmp_index, false_end):
                    pass
                else:
                    overrides[i] = false_start
                    overrides[jmp_index] = false_end
                    continue

            key_dependent_end = literal_key_dependent_branch_end(i, raw)
            if key_dependent_end is not None and i + 1 < key_dependent_end < raw:
                overrides[i] = key_dependent_end
                continue

            dim_guard_end = single_dim_assignment_guard_end(i, raw)
            if dim_guard_end is not None and i + 1 < dim_guard_end < raw:
                overrides[i] = dim_guard_end
                continue

            if not large_cv_guard:
                first_stmt_end = local_statement_end(i + 1)
                if first_stmt_end is not None and i + 1 < first_stmt_end < raw:
                    first_call_assignment_end = self.call_assignment_statement_end(i + 1, min(raw, i + 32, self.n))
                    if first_call_assignment_end == first_stmt_end:
                        first_stmt_cvs = self.assigned_cvs_in_range(i + 1, first_stmt_end)
                        dependent_end = self.dependent_tail_end(first_stmt_end, raw, first_stmt_cvs) if first_stmt_cvs else first_stmt_end
                        if first_stmt_end < dependent_end <= first_stmt_end + 32:
                            overrides[i] = dependent_end
                            continue

            include_else = local_include_if_else(i, raw)
            if include_else is not None:
                false_start, false_end, jmp_index = include_else
                if starts_at_foreach_cleanup(false_start):
                    pass
                elif not false_branch_reaches_jump_target(jmp_index, false_end):
                    pass
                else:
                    overrides[i] = false_start
                    overrides[jmp_index] = false_end
                    continue

            template_echo = local_template_echo_if(i, raw)
            if template_echo is not None:
                false_start, false_end, jmp_index = template_echo
                if starts_at_foreach_cleanup(false_start):
                    pass
                elif not false_branch_reaches_jump_target(jmp_index, false_end):
                    pass
                else:
                    overrides[i] = false_start
                    overrides[jmp_index] = false_end
                    continue

            template_guard_end = local_template_echo_guard(i, raw)
            if template_guard_end is not None and i + 1 < template_guard_end < raw:
                overrides[i] = template_guard_end
                continue

            guarded_end = local_guarded_region_end(i, raw)
            if guarded_end is not None and i + 1 < guarded_end < raw:
                overrides[i] = guarded_end
                continue

            collection_end = guarded_collection_block_end(i, raw)
            if collection_end is not None and i + 1 < collection_end < raw:
                overrides[i] = collection_end
                continue

            if not large_cv_guard:
                expr_stmt_end = self.expression_assignment_statement_end(i + 1, min(raw, i + 32, self.n))
                if expr_stmt_end is not None and i + 1 < expr_stmt_end < raw:
                    stmt_cvs = self.assigned_cvs_in_range(i + 1, expr_stmt_end)
                    dependent_end = self.dependent_tail_end(expr_stmt_end, raw, stmt_cvs) if stmt_cvs else expr_stmt_end
                    if expr_stmt_end < dependent_end <= expr_stmt_end + 32:
                        overrides[i] = dependent_end
                        continue
                    if dependent_end <= expr_stmt_end or dependent_end > expr_stmt_end + 32:
                        overrides[i] = expr_stmt_end
                        continue

            assigned_cvs = self.assigned_cvs_in_range(i + 1, raw)
            dependent_target_end = self.terminated_dependent_target_end(raw, assigned_cvs)
            if dependent_target_end is not None and dependent_target_end > raw:
                overrides[i] = dependent_target_end
                continue

            if op.get("op1", {}).get("type_name") == "IS_VAR":
                for term_idx in range(i + 1, min(raw, i + 128, self.n - 1)):
                    if self.ops[term_idx].get("opcode_name") != "ZEND_EXIT":
                        continue
                    if self.ops[term_idx + 1].get("opcode_name") != "ZEND_JMP":
                        continue
                    skip_target = self.raw_target(self.ops[term_idx + 1])
                    if skip_target is not None and skip_target > raw and term_idx + 2 < raw:
                        overrides[i] = term_idx + 2
                        break
            if i in overrides:
                continue

            guarded_else = guarded_block_if_else(i, raw)
            if guarded_else is not None:
                false_start, false_end, jmp_index = guarded_else
                if not false_branch_reaches_jump_target(jmp_index, false_end):
                    continue
                overrides[i] = false_start
                overrides[jmp_index] = false_end
                continue

            chain_end = terminated_condition_chain_end(i + 1, raw)
            if chain_end is not None and chain_end > i + 1 and chain_end < raw:
                overrides[i] = chain_end
                continue

            body_end = terminated_body_end(i + 1, raw)
            if body_end is not None and i + 1 < body_end < raw:
                overrides[i] = body_end
                continue

            loop_else = loop_body_else(i, raw)
            if loop_else is not None:
                false_start, after_false, jmp_index = loop_else
                if not false_branch_reaches_jump_target(jmp_index, after_false):
                    continue
                overrides[i] = false_start
                overrides[jmp_index] = after_false
                continue

            if not large_cv_guard:
                short_join = short_statement_join(i, raw)
                if short_join is not None and i + 1 < short_join < raw:
                    overrides[i] = short_join
                    continue

            multi_else = local_multi_if_else(i, raw)
            if multi_else is not None:
                false_start, false_end, jmp_index = multi_else
                if not false_branch_reaches_jump_target(jmp_index, false_end):
                    continue
                overrides[i] = false_start
                overrides[jmp_index] = false_end
                continue

            outer_else = local_outer_if_else(i, raw)
            if outer_else is not None:
                false_start, false_end, jmp_index = outer_else
                if not false_branch_reaches_jump_target(jmp_index, false_end):
                    continue
                overrides[i] = false_start
                overrides[jmp_index] = false_end
                continue

            foreach_join = optional_foreach_join(i, raw)
            if foreach_join is not None and i + 1 < foreach_join < raw:
                overrides[i] = foreach_join
                continue
            if i in overrides:
                continue

            j = i + 1
            while j < min(raw, i + 32, self.n):
                name = self.ops[j].get("opcode_name")
                if name in ("ZEND_EXIT", "ZEND_RETURN"):
                    if j + 1 < raw:
                        overrides[i] = j + 1
                    break
                if name in barrier_names:
                    break
                j += 1
            if i in overrides:
                continue

            has_intervening_control = any(
                self.ops[k].get("opcode_name") in barrier_names
                for k in range(i + 1, min(raw, self.n))
            )
            if not has_intervening_control and self.is_expression_midpoint(raw):
                repaired = self.next_control_boundary(raw, min(raw + 48, self.n))
                if repaired is not None and repaired > i + 1:
                    overrides[i] = repaired
                    continue

            scan_limit = min(raw, i + 14, self.n)
            j = i + 1
            while j < scan_limit:
                name = self.ops[j].get("opcode_name")
                if name in ("ZEND_EXIT", "ZEND_RETURN"):
                    if j + 1 < raw:
                        overrides[i] = j + 1
                    break
                if name in barrier_names:
                    break
                j += 1

        for i, op in enumerate(self.ops):
            if op.get("opcode_name") != "ZEND_JMP" or i in overrides:
                continue
            raw = self.raw_target(op)
            if raw is None or raw <= i + 1 or raw >= self.n:
                continue
            if raw - i <= 48:
                continue
            local_after = local_statement_end(i + 1)
            prev_name = self.ops[i - 1].get("opcode_name") if i > 0 else None
            if local_after is not None and i + 1 < local_after < raw and prev_name in (simple_statement_names | {"ZEND_OP_DATA"}):
                if has_effective_ops(local_after, raw) and self.ops[local_after].get("opcode_name") != "ZEND_NOP":
                    continue
                overrides[i] = local_after
                continue
            produced_tmps = set()
            for idx in range(i + 1, raw):
                result = self.ops[idx].get("result", {})
                if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                    produced_tmps.add(self.key(result))
            if produced_tmps and self.op_uses_tmps(self.ops[raw], produced_tmps):
                repaired = self.statement_end(raw)
                if repaired > raw:
                    overrides[i] = repaired
        return overrides

    def _recover_call_from_ops(self, i: int, st: State) -> Optional[Tuple[str, List[str]]]:
        if i <= 0:
            return None
        do_name = self.ops[i].get("opcode_name")
        if do_name not in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"):
            return None
        init_names = {
            "ZEND_INIT_FCALL",
            "ZEND_INIT_FCALL_BY_NAME",
            "ZEND_INIT_NS_FCALL_BY_NAME",
            "ZEND_INIT_METHOD_CALL",
            "ZEND_INIT_STATIC_METHOD_CALL",
            "ZEND_INIT_DYNAMIC_CALL",
        }
        barrier_prefix = ("ZEND_JMP", "ZEND_FE_", "ZEND_RETURN", "ZEND_EXIT")
        barrier_exact = {"ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"}

        j = i - 1
        init_idx = None
        steps = 0
        while j >= 0 and steps < 32:
            nm = self.ops[j].get("opcode_name", "")
            if nm in init_names:
                init_idx = j
                break
            if nm in barrier_exact or nm.startswith(barrier_prefix):
                break
            j -= 1
            steps += 1
        if init_idx is None:
            return None

        init = self.ops[init_idx]
        init_name = init.get("opcode_name")
        expr: Optional[str] = None
        if init_name in ("ZEND_INIT_FCALL", "ZEND_INIT_FCALL_BY_NAME", "ZEND_INIT_NS_FCALL_BY_NAME"):
            expr = self.canonical_function_name(unwrap(init["op2"].get("literal")))
        elif init_name == "ZEND_INIT_METHOD_CALL":
            recv = self.expr(init["op1"], st) or "$this"
            method = unwrap(init["op2"].get("literal"))
            expr = f"{recv}->{method}"
        elif init_name == "ZEND_INIT_STATIC_METHOD_CALL":
            cls = self.expr(init["op1"], st) or str(unwrap(init["op1"].get("literal")))
            method = unwrap(init["op2"].get("literal"))
            expr = f"{cls}::{method}"
        elif init_name == "ZEND_INIT_DYNAMIC_CALL":
            expr = self.dynamic_callee_expr(init, st)
        if not expr:
            return None
        send_ops = [self.ops[k] for k in range(init_idx + 1, i) if self.ops[k].get("opcode_name", "").startswith("ZEND_SEND_")]
        args = [self.expr(op["op1"], st) for op in send_ops]
        return expr, args

    def fixed_false_target(self, i: int) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        t = self.target(self.ops[i], i)
        if t is None:
            return None, None, None
        if t < self.n and self.ops[t].get("opcode_name") == "ZEND_JMP":
            for probe in range(t + 1, min(self.n, t + 96)):
                probe_name = self.ops[probe].get("opcode_name")
                if probe_name in ("ZEND_JMPNZ", "ZEND_JMPZ") and self.raw_target(self.ops[probe]) == t + 1:
                    return t, None, None
                if probe_name in ("ZEND_RETURN", "ZEND_EXIT"):
                    break
            jt = self.target(self.ops[t], t)
            if jt is not None and jt > t + 1:
                return t + 1, jt, t
        if t > i + 1 and t - 1 < self.n and self.ops[t - 1].get("opcode_name") == "ZEND_JMP":
            jt = self.target(self.ops[t - 1], t - 1)
            if jt is not None and jt > t:
                return t, jt, t - 1
        if i + 2 < t < self.n and self.ops[t - 1].get("opcode_name") == "ZEND_JMP":
            terminal = t - 2
            while terminal > i and self.ops[terminal].get("opcode_name") in ("ZEND_FREE", "ZEND_NOP", "ZEND_FE_FREE"):
                terminal -= 1
            if self.ops[terminal].get("opcode_name") in ("ZEND_EXIT", "ZEND_RETURN"):
                false_end = self.statement_end(t)
                if t < false_end <= self.n:
                    return t, false_end, t - 1
        return t, None, None

    def first_external_entry(self, start: int, end: int, branch_index: int) -> Optional[int]:
        """Return first index in (start, end) that has incoming jump from outside [start, end), excluding branch_index."""
        if end - start <= 1:
            return None
        branch_op = self.ops[branch_index]
        branch_key = None
        if branch_op.get("op1", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
            branch_key = self.key(branch_op["op1"])
        for idx in range(start + 1, end):
            if self.ops[idx].get("opcode_name") == "ZEND_JMP":
                continue
            for src in self.incoming.get(idx, []):
                if src == branch_index:
                    continue
                src_op = self.ops[src]
                if src > idx and src_op.get("opcode_name") in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ"):
                    # Back edges from later loop/foreach bodies are not real
                    # alternate entries into the current structured block. Some
                    # ionCube dumps leave these pointing into nearby expression
                    # temporaries, which must not truncate an if body.
                    continue
                if src_op.get("opcode_name") == "ZEND_JMP" and self.is_expression_midpoint(idx):
                    continue
                if src_op.get("opcode_name") in ("ZEND_JMPZ_EX", "ZEND_JMPNZ_EX"):
                    if self.is_expression_midpoint(idx):
                        continue
                    if branch_key is None or src_op.get("result", {}).get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
                        continue
                    if self.key(src_op["result"]) != branch_key:
                        continue
                if not (start <= src < end):
                    return idx
        return None

    def is_expression_midpoint(self, index: int) -> bool:
        if not (0 <= index < self.n):
            return False
        name = self.ops[index].get("opcode_name")
        if name.startswith("ZEND_SEND_"):
            return True
        if name in (
            "ZEND_CONCAT",
            "ZEND_FAST_CONCAT",
            "ZEND_ADD",
            "ZEND_SUB",
            "ZEND_MUL",
            "ZEND_DIV",
            "ZEND_MOD",
            "ZEND_BW_XOR",
            "ZEND_BW_OR",
            "ZEND_SPACESHIP",
        ):
            op = self.ops[index]
            # A binary op with only CV/CONST inputs can begin a fresh expression
            # at a block target. It is only a true midpoint when it consumes a
            # temporary value produced by earlier opcodes.
            return op.get("op1", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR") or op.get("op2", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR")
        if name in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"):
            prev = self.ops[index - 1].get("opcode_name") if index > 0 else ""
            if prev not in (
                "ZEND_INIT_FCALL",
                "ZEND_INIT_FCALL_BY_NAME",
                "ZEND_INIT_NS_FCALL_BY_NAME",
                "ZEND_INIT_METHOD_CALL",
                "ZEND_INIT_STATIC_METHOD_CALL",
                "ZEND_INIT_DYNAMIC_CALL",
                "ZEND_NEW",
            ):
                return True
        return False

    def next_control_boundary(self, start: int, limit: int) -> Optional[int]:
        idx = start
        limit = min(limit, self.n)
        while idx < limit:
            name = self.ops[idx].get("opcode_name")
            if name in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R", "ZEND_RETURN", "ZEND_EXIT"):
                return idx
            idx += 1
        return None

    def first_forward_jump(self, start: int, end: int) -> Optional[int]:
        idx = start
        limit = min(end, self.n)
        branch_names = {"ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_JMPZ_EX", "ZEND_JMPNZ_EX"}
        while idx < limit:
            name = self.ops[idx].get("opcode_name")
            if name in branch_names:
                target = self.target(self.ops[idx], idx)
                if target is not None and target > idx + 1:
                    idx = min(target, limit)
                    continue
            if name != "ZEND_JMP":
                idx += 1
                continue
            prev = idx - 1
            while prev >= start and self.ops[prev].get("opcode_name") in ("ZEND_NOP", "ZEND_FREE", "ZEND_FE_FREE"):
                prev -= 1
            if prev >= start and self.ops[prev].get("opcode_name") in ("ZEND_RETURN", "ZEND_EXIT"):
                idx += 1
                continue
            target = self.target(self.ops[idx], idx)
            if target is not None and target > idx:
                tail_branch = None
                for probe in range(idx + 1, limit):
                    probe_name = self.ops[probe].get("opcode_name")
                    if probe_name in ("ZEND_JMPNZ", "ZEND_JMPZ"):
                        probe_target = self.raw_target(self.ops[probe])
                        if probe_target is not None and probe_target <= probe:
                            tail_branch = probe
                            break
                if tail_branch is not None:
                    idx = tail_branch + 1
                    continue
                return idx
            idx += 1
        return None

    def repaired_after_target(self, false_start: int, raw_after: int) -> int:
        """Trim stale far after-targets when an else arm ends with an ionCube NOP pad."""
        produced_tmps = set()
        for idx in range(false_start, min(raw_after, self.n)):
            result = self.ops[idx].get("result", {})
            if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                produced_tmps.add(self.key(result))
        if raw_after < self.n and produced_tmps and self.op_uses_tmps(self.ops[raw_after], produced_tmps):
            return self.statement_end(raw_after)

        saw_statement = False
        idx = false_start
        limit = min(raw_after, false_start + 96, self.n)
        statement_names = {
            "ZEND_ASSIGN",
            "ZEND_ASSIGN_DIM",
            "ZEND_ASSIGN_OBJ",
            "ZEND_DO_FCALL",
            "ZEND_DO_FCALL_BY_NAME",
            "ZEND_DO_ICALL",
            "ZEND_DO_UCALL",
            "ZEND_ECHO",
            "ZEND_INCLUDE_OR_EVAL",
        }
        while idx < limit:
            name = self.ops[idx].get("opcode_name")
            if name in statement_names:
                saw_statement = True
                idx += 1
                continue
            if saw_statement and name == "ZEND_NOP":
                pad_start = idx
                while idx < limit and self.ops[idx].get("opcode_name") == "ZEND_NOP":
                    idx += 1
                if idx - pad_start >= 2 and idx < raw_after:
                    return idx
                continue
            idx += 1
        return raw_after

    def simple_assignment_statement_end(self, index: int) -> Optional[int]:
        if index >= self.n:
            return None
        name = self.ops[index].get("opcode_name")
        if name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ") and index + 1 < self.n:
            if self.ops[index + 1].get("opcode_name") == "ZEND_OP_DATA":
                return index + 2
        return None

    def statement_end(self, index: int) -> int:
        if index >= self.n:
            return index
        name = self.ops[index].get("opcode_name")
        if name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ") and index + 1 < self.n:
            if self.ops[index + 1].get("opcode_name") == "ZEND_OP_DATA":
                return index + 2
        return index + 1

    def unused_call_statement_end(self, index: int, limit: int) -> Optional[int]:
        if index >= min(limit, self.n):
            return None
        init_names = {
            "ZEND_INIT_FCALL",
            "ZEND_INIT_FCALL_BY_NAME",
            "ZEND_INIT_NS_FCALL_BY_NAME",
            "ZEND_INIT_METHOD_CALL",
            "ZEND_INIT_STATIC_METHOD_CALL",
            "ZEND_INIT_DYNAMIC_CALL",
        }
        if self.ops[index].get("opcode_name") == "ZEND_BEGIN_SILENCE":
            inner_limit = min(limit, self.n, index + 16)
            idx = index + 1
            while idx < inner_limit and self.ops[idx].get("opcode_name") != "ZEND_END_SILENCE":
                end = self.unused_call_statement_end(idx, inner_limit)
                if end is not None:
                    while end < inner_limit:
                        if self.ops[end].get("opcode_name") == "ZEND_END_SILENCE":
                            return end + 1
                        end += 1
                    return None
                idx += 1
            return None
        if self.ops[index].get("opcode_name") not in init_names:
            return None
        idx = index + 1
        limit = min(limit, self.n)
        while idx < limit and self.ops[idx].get("opcode_name", "").startswith("ZEND_SEND_"):
            idx += 1
        if idx >= limit:
            return None
        if self.ops[idx].get("opcode_name") not in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"):
            return None
        if self.ops[idx].get("result", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
            return None
        return idx + 1

    def call_assignment_statement_end(self, index: int, limit: int) -> Optional[int]:
        if index >= min(limit, self.n):
            return None
        init_names = {
            "ZEND_INIT_FCALL",
            "ZEND_INIT_FCALL_BY_NAME",
            "ZEND_INIT_NS_FCALL_BY_NAME",
            "ZEND_INIT_METHOD_CALL",
            "ZEND_INIT_STATIC_METHOD_CALL",
            "ZEND_INIT_DYNAMIC_CALL",
        }
        if self.ops[index].get("opcode_name") not in init_names:
            return None
        idx = index + 1
        limit = min(limit, self.n)
        while idx < limit:
            name = self.ops[idx].get("opcode_name")
            if name in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"):
                result = self.ops[idx].get("result", {})
                if result.get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
                    return None
                assign_idx = idx + 1
                if assign_idx < limit and self.ops[assign_idx].get("opcode_name") == "ZEND_ASSIGN":
                    src = self.ops[assign_idx].get("op2", {})
                    if src.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and self.key(src) == self.key(result):
                        return assign_idx + 1
                return None
            if name.startswith("ZEND_SEND_") or name in (
                "ZEND_FETCH_FUNC_ARG",
                "ZEND_FETCH_DIM_FUNC_ARG",
                "ZEND_FETCH_OBJ_FUNC_ARG",
                "ZEND_DECLARE_LAMBDA_FUNCTION",
                "ZEND_BIND_LEXICAL",
            ):
                idx += 1
                continue
            return None
        return None

    def expression_assignment_statement_end(self, index: int, limit: int) -> Optional[int]:
        if index >= min(limit, self.n):
            return None
        produced_tmps = set()
        limit = min(limit, self.n)
        idx = index
        while idx < limit:
            op = self.ops[idx]
            name = op.get("opcode_name")
            if name in (
                "ZEND_ASSIGN",
                "ZEND_ASSIGN_CONCAT",
                "ZEND_ASSIGN_ADD",
                "ZEND_ASSIGN_SUB",
                "ZEND_ASSIGN_MUL",
                "ZEND_ASSIGN_DIV",
                "ZEND_ASSIGN_MOD",
                "ZEND_ASSIGN_BW_OR",
                "ZEND_ASSIGN_BW_AND",
                "ZEND_ASSIGN_BW_XOR",
                "ZEND_ASSIGN_SL",
                "ZEND_ASSIGN_SR",
            ):
                src = op.get("op2", {})
                if self.operand_uses_tmp(src, produced_tmps):
                    return idx + 1
                return None
            if name in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_RETURN", "ZEND_EXIT", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"):
                return None
            result = op.get("result", {})
            if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                produced_tmps.add(self.key(result))
            idx += 1
        return None

    def repaired_loop_guard_end(self, branch_index: int, raw_end: int, st: State) -> Optional[int]:
        body_start = branch_index + 1
        if body_start >= min(raw_end, self.n):
            return None
        if self.ops[body_start].get("opcode_name") != "ZEND_JMP":
            return None
        if raw_end - body_start < 64:
            return None
        loop = self.find_tail_condition_loop(body_start, min(raw_end, body_start + 128, self.n), st)
        if loop is None:
            return None
        _body_end, after_loop, _cond = loop
        end = after_loop
        cleanup_end = self.unused_call_statement_end(end, min(raw_end, end + 16, self.n))
        if cleanup_end is not None:
            end = cleanup_end
        return end if end > body_start else None

    def assigned_cvs_in_range(self, start: int, end: int) -> set:
        cvs = set()
        for idx in range(start, min(end, self.n)):
            op = self.ops[idx]
            name = op.get("opcode_name")
            if name == "ZEND_ASSIGN" and op.get("op1", {}).get("type_name") == "IS_CV":
                cvs.add(self.key(op["op1"]))
        return cvs

    def operand_uses_cv(self, operand: Dict[str, Any], cvs: set) -> bool:
        return operand.get("type_name") == "IS_CV" and self.key(operand) in cvs

    def operand_uses_tmp(self, operand: Dict[str, Any], tmps: set) -> bool:
        return operand.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and self.key(operand) in tmps

    def op_uses_cvs(self, op: Dict[str, Any], cvs: set) -> bool:
        return self.operand_uses_cv(op.get("op1", {}), cvs) or self.operand_uses_cv(op.get("op2", {}), cvs)

    def op_uses_tmps(self, op: Dict[str, Any], tmps: set) -> bool:
        if self.operand_uses_tmp(op.get("op1", {}), tmps) or self.operand_uses_tmp(op.get("op2", {}), tmps):
            return True
        if op.get("opcode_name") in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ") and op.get("index", -1) + 1 < self.n:
            next_op = self.ops[op["index"] + 1]
            if next_op.get("opcode_name") == "ZEND_OP_DATA":
                return self.operand_uses_tmp(next_op.get("op1", {}), tmps)
        return False

    def dependent_statement_end(self, start: int, limit: int, cvs: set) -> Optional[int]:
        uses = False
        idx = start
        limit = min(limit, self.n)
        init_names = {
            "ZEND_INIT_FCALL",
            "ZEND_INIT_FCALL_BY_NAME",
            "ZEND_INIT_NS_FCALL_BY_NAME",
            "ZEND_INIT_METHOD_CALL",
            "ZEND_INIT_STATIC_METHOD_CALL",
            "ZEND_INIT_DYNAMIC_CALL",
        }
        if idx < limit and self.ops[idx].get("opcode_name") in init_names:
            call_idx = idx + 1
            call_uses = self.op_uses_cvs(self.ops[idx], cvs)
            while call_idx < limit:
                op = self.ops[call_idx]
                name = op.get("opcode_name")
                call_uses = call_uses or self.op_uses_cvs(op, cvs)
                if name in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"):
                    return call_idx + 1 if call_uses else None
                if name in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_RETURN", "ZEND_EXIT", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"):
                    return None
                call_idx += 1

        while idx < limit:
            op = self.ops[idx]
            name = op.get("opcode_name")
            uses = uses or self.op_uses_cvs(op, cvs)
            if name == "ZEND_ASSIGN" and uses:
                return idx + 1
            if name in ("ZEND_ASSIGN_DIM", "ZEND_ASSIGN_OBJ") and idx + 1 < limit and self.ops[idx + 1].get("opcode_name") == "ZEND_OP_DATA":
                if uses or self.op_uses_cvs(self.ops[idx + 1], cvs):
                    return idx + 2
            if name.startswith("ZEND_JMP") or name in ("ZEND_RETURN", "ZEND_EXIT", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"):
                return None
            idx += 1
        return None

    def dependent_tail_end(self, start: int, raw_end: int, cvs: set) -> int:
        if not cvs:
            return raw_end
        idx = raw_end
        limit = min(raw_end + 48, self.n)
        while idx < limit:
            op = self.ops[idx]
            name = op.get("opcode_name")

            # If a dependent tail reaches an auth/guard expression over values
            # initialized by the protected branch, keep the guarded continuation
            # in the same region. This preserves top-level session/bootstrap
            # blocks where later calls rely on globals initialized inside the
            # guarded setup.
            if name == "ZEND_BOOL_NOT" and self.operand_uses_cv(op.get("op1", {}), cvs):
                return self.protected_region_end(idx)

            # Pattern: FETCH_DIM_R $definedCv[...] ; JMPZ ; one simple assignment.
            if (
                name in ("ZEND_FETCH_DIM_R", "ZEND_FETCH_DIM_IS", "ZEND_FETCH_OBJ_R")
                and self.operand_uses_cv(op.get("op1", {}), cvs)
                and idx + 1 < self.n
                and self.ops[idx + 1].get("opcode_name") in ("ZEND_JMPZ", "ZEND_JMPNZ")
            ):
                branch = self.ops[idx + 1]
                if branch.get("op1", {}).get("type_name") in ("IS_VAR", "IS_TMP_VAR") and self.key(branch["op1"]) == self.key(op["result"]):
                    simple_end = self.simple_assignment_statement_end(idx + 2)
                    if simple_end is not None:
                        idx = simple_end
                        continue

            stmt_end = self.dependent_statement_end(idx, limit, cvs)
            if stmt_end is not None and stmt_end > idx:
                idx = stmt_end
                continue
            break
        return idx if idx > raw_end else raw_end

    def terminated_dependent_target_end(self, start: int, cvs: set) -> Optional[int]:
        if not cvs or start >= self.n:
            return None
        dep_end = self.dependent_statement_end(start, min(start + 32, self.n), cvs)
        if dep_end is None or dep_end <= start:
            return None
        idx = dep_end
        while idx < self.n and self.ops[idx].get("opcode_name") in ("ZEND_FREE", "ZEND_NOP", "ZEND_END_SILENCE"):
            idx += 1
        if idx < self.n and self.ops[idx].get("opcode_name") == "ZEND_EXIT":
            idx += 1
            if idx < self.n and self.ops[idx].get("opcode_name") == "ZEND_JMP":
                return idx + 1
            return idx
        return None

    def protected_region_end(self, start: int) -> int:
        idx = start
        while idx < self.n:
            name = self.ops[idx].get("opcode_name")
            if name in ("ZEND_RETURN", "ZEND_EXIT"):
                return idx
            idx += 1
        return self.n

    def first_nested_join_after_statement(self, start: int, end: int) -> Optional[int]:
        statement_names = {
            "ZEND_ASSIGN",
            "ZEND_ASSIGN_DIM",
            "ZEND_ASSIGN_OBJ",
            "ZEND_DO_FCALL",
            "ZEND_DO_FCALL_BY_NAME",
            "ZEND_DO_ICALL",
            "ZEND_DO_UCALL",
            "ZEND_ECHO",
            "ZEND_INCLUDE_OR_EVAL",
        }
        branch_names = {"ZEND_JMPZ", "ZEND_JMPNZ"}
        saw_statement = False
        idx = start
        while idx < min(end, self.n):
            name = self.ops[idx].get("opcode_name")
            if name in statement_names:
                saw_statement = True
            elif saw_statement and name in branch_names:
                target = self.target(self.ops[idx], idx)
                if target is not None and idx < target < end:
                    return target
            idx += 1
        return None

    def condition_expr(self, op: Dict[str, Any], st: State) -> str:
        cond = self.expr(op["op1"], st)
        if op.get("opcode_name") in ("ZEND_JMPNZ",):
            cond = "!(" + cond + ")"
        return strip_redundant_parens(cond)

    def loop_condition_expr(self, op: Dict[str, Any], st: State, assignment_expr: Optional[str] = None) -> str:
        cond = assignment_expr or self.expr(op["op1"], st)
        if op.get("opcode_name") == "ZEND_JMPZ":
            cond = "!(" + cond + ")"
        return strip_redundant_parens(cond)

    def is_null_return(self, index: int) -> bool:
        if not (0 <= index < self.n):
            return False
        op = self.ops[index]
        if op.get("opcode_name") != "ZEND_RETURN":
            return False
        operand = op.get("op1", {})
        if operand.get("type_name") in ("IS_UNUSED",):
            return True
        if operand.get("type_name") != "IS_CONST":
            return False
        return unwrap(operand.get("literal")) is None

    def is_implicit_main_return(self, index: int) -> bool:
        if not self.is_main or not (0 <= index < self.n):
            return False
        op = self.ops[index]
        if op.get("opcode_name") != "ZEND_RETURN":
            return False
        operand = op.get("op1", {})
        if operand.get("type_name") != "IS_CONST":
            return False
        return unwrap(operand.get("literal")) == 1

    def only_trailing_noise(self, start: int, end: int) -> bool:
        for idx in range(start, min(end, self.n)):
            if self.ops[idx].get("opcode_name") in ("ZEND_NOP", "ZEND_FREE", "ZEND_FE_FREE"):
                continue
            if self.is_null_return(idx):
                continue
            if self.is_implicit_main_return(idx):
                continue
            else:
                return False
        return True

    def jump_statement_for_target(
        self,
        index: int,
        break_target: Optional[int],
        continue_target: Optional[int],
    ) -> Optional[str]:
        if not (0 <= index < self.n):
            return None
        op = self.ops[index]
        if op.get("opcode_name") != "ZEND_JMP":
            return None
        jump_target = self.target(op, index)
        if break_target is not None and jump_target is not None and jump_target >= break_target:
            return "break;"
        if continue_target is not None and jump_target is not None and jump_target <= continue_target:
            return "continue;"
        return None

    def return_statement_for_jump(self, index: int, st: State) -> Optional[str]:
        if not (0 <= index < self.n):
            return None
        op = self.ops[index]
        if op.get("opcode_name") != "ZEND_JMP":
            return None
        target = self.target(op, index)
        if target is None or not (0 <= target < self.n):
            return None
        ret = self.ops[target]
        if ret.get("opcode_name") != "ZEND_RETURN":
            return None
        if self.is_implicit_main_return(target):
            return None
        if self.is_null_return(target):
            return "return;"
        return f"return {self.expr(ret.get('op1', {}), st)};"

    def find_forward_jump_loop(self, i: int, end: int, st: State) -> Optional[Tuple[int, int, str]]:
        op = self.ops[i]
        if op.get("opcode_name") != "ZEND_JMP":
            return None
        cond_start = self.target(op, i)
        body_start = i + 1
        if cond_start is None or cond_start <= body_start or cond_start >= min(end, self.n):
            fallback = self.find_tail_condition_loop(i, end, st)
            if fallback is not None:
                return fallback
            return None

        branch_idx = None
        scan_limit = min(cond_start + 12, end, self.n)
        for j in range(cond_start, scan_limit):
            name = self.ops[j].get("opcode_name")
            if name in ("ZEND_JMPNZ", "ZEND_JMPZ") and self.target(self.ops[j], j) == body_start:
                branch_idx = j
                break
            if name in ("ZEND_JMP", "ZEND_RETURN", "ZEND_EXIT"):
                break
        if branch_idx is None:
            fallback = self.find_tail_condition_loop(i, end, st)
            if fallback is not None:
                return fallback
            return None

        cond_state = st.clone()
        assignment_expr = None
        assigned_tmp_exprs: Dict[int, str] = {}
        branch = self.ops[branch_idx]
        branch_key = self.key(branch.get("op1", {})) if branch.get("op1", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR") else None
        for k in range(cond_start, branch_idx):
            cond_op = self.ops[k]
            if cond_op.get("opcode_name") == "ZEND_ASSIGN" and branch_key is not None:
                result = cond_op.get("result", {})
                expr = f"({self.expr(cond_op['op1'], cond_state)} = {self.expr(cond_op['op2'], cond_state)})"
                if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and self.key(result) == branch_key:
                    assignment_expr = expr
                if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                    assigned_tmp_exprs[self.key(result)] = expr
            if cond_op.get("opcode_name") in ("ZEND_IS_NOT_IDENTICAL", "ZEND_IS_IDENTICAL") and branch_key is not None:
                result = cond_op.get("result", {})
                left = cond_op.get("op1", {})
                if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and self.key(result) == branch_key and left.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                    left_expr = assigned_tmp_exprs.get(self.key(left))
                    if left_expr is not None:
                        symbol = "!==" if cond_op.get("opcode_name") == "ZEND_IS_NOT_IDENTICAL" else "==="
                        assignment_expr = f"{left_expr} {symbol} {self.expr(cond_op['op2'], cond_state)}"
            self.handle_op(k, cond_state)
        return cond_start, branch_idx + 1, self.loop_condition_expr(branch, cond_state, assignment_expr)

    def find_tail_condition_loop(self, i: int, end: int, st: State) -> Optional[Tuple[int, int, str]]:
        body_start = i + 1
        limit = min(end, self.n)
        for branch_idx in range(body_start + 1, limit):
            branch = self.ops[branch_idx]
            if branch.get("opcode_name") not in ("ZEND_JMPNZ", "ZEND_JMPZ"):
                continue
            raw = self.raw_target(branch)
            if raw is None or raw > branch_idx:
                continue
            cond_start = branch_idx - 1
            while cond_start > body_start and self.ops[cond_start - 1].get("opcode_name") in (
                "ZEND_INIT_FCALL",
                "ZEND_INIT_FCALL_BY_NAME",
                "ZEND_INIT_NS_FCALL_BY_NAME",
                "ZEND_INIT_METHOD_CALL",
                "ZEND_INIT_STATIC_METHOD_CALL",
                "ZEND_INIT_DYNAMIC_CALL",
                "ZEND_SEND_VAR",
                "ZEND_SEND_VAR_EX",
                "ZEND_SEND_VAL",
                "ZEND_SEND_VAL_EX",
                "ZEND_DO_FCALL",
                "ZEND_DO_FCALL_BY_NAME",
                "ZEND_ASSIGN",
                "ZEND_IS_NOT_IDENTICAL",
                "ZEND_IS_IDENTICAL",
            ):
                cond_start -= 1
            if cond_start <= body_start:
                continue

            branch_key = self.key(branch.get("op1", {})) if branch.get("op1", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR") else None
            if branch_key is not None:
                prev = self.ops[branch_idx - 1]
                prev_result = prev.get("result", {})
                if (
                    prev.get("opcode_name") == "ZEND_ASSIGN"
                    and prev_result.get("type_name") in ("IS_TMP_VAR", "IS_VAR")
                    and self.key(prev_result) == branch_key
                ):
                    cond_start = branch_idx - 1
                    rhs = prev.get("op2", {})
                    if rhs.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and cond_start - 1 > body_start:
                        rhs_key = self.key(rhs)
                        producer_idx = cond_start - 1
                        producer = self.ops[producer_idx]
                        if (
                            producer.get("opcode_name") in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL")
                            and producer.get("result", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR")
                            and self.key(producer["result"]) == rhs_key
                        ):
                            init_idx = producer_idx - 1
                            while init_idx > body_start and self.ops[init_idx].get("opcode_name", "").startswith("ZEND_SEND_"):
                                init_idx -= 1
                            if self.ops[init_idx].get("opcode_name") in (
                                "ZEND_INIT_FCALL",
                                "ZEND_INIT_FCALL_BY_NAME",
                                "ZEND_INIT_NS_FCALL_BY_NAME",
                                "ZEND_INIT_METHOD_CALL",
                                "ZEND_INIT_STATIC_METHOD_CALL",
                                "ZEND_INIT_DYNAMIC_CALL",
                            ):
                                cond_start = init_idx

            assignment_expr = None
            assigned_tmp_exprs: Dict[int, str] = {}
            assigned_cv = None
            cond_state = st.clone()
            for k in range(cond_start, branch_idx):
                cond_op = self.ops[k]
                if cond_op.get("opcode_name") == "ZEND_ASSIGN":
                    expr = f"({self.expr(cond_op['op1'], cond_state)} = {self.expr(cond_op['op2'], cond_state)})"
                    if cond_op.get("op1", {}).get("type_name") == "IS_CV":
                        assigned_cv = self.key(cond_op["op1"])
                    result = cond_op.get("result", {})
                    if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                        # Use the assignment as the visible loop condition when
                        # the following compare branches on the assignment temp.
                        assignment_expr = expr
                        assigned_tmp_exprs[self.key(result)] = expr
                if cond_op.get("opcode_name") in ("ZEND_IS_NOT_IDENTICAL", "ZEND_IS_IDENTICAL") and branch_key is not None:
                    result = cond_op.get("result", {})
                    left = cond_op.get("op1", {})
                    if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and self.key(result) == branch_key and left.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                        left_expr = assigned_tmp_exprs.get(self.key(left))
                        if left_expr is not None:
                            symbol = "!==" if cond_op.get("opcode_name") == "ZEND_IS_NOT_IDENTICAL" else "==="
                            assignment_expr = f"{left_expr} {symbol} {self.expr(cond_op['op2'], cond_state)}"
                self.handle_op(k, cond_state)
            if assigned_cv is None:
                continue
            if not any(self.op_uses_cvs(self.ops[k], {assigned_cv}) for k in range(body_start, cond_start)):
                continue
            after_loop = branch_idx + 1
            for j in range(body_start, cond_start):
                op = self.ops[j]
                if op.get("opcode_name") != "ZEND_JMP":
                    continue
                target = self.raw_target(op)
                if target is not None and target > branch_idx:
                    after_loop = max(after_loop, target)
            return cond_start, after_loop, self.loop_condition_expr(branch, cond_state, assignment_expr if branch_key is not None else None)
        return None

    def conditional_expression(self, i: int, end: int, st: State) -> Optional[Tuple[int, Dict[str, Any], str]]:
        op = self.ops[i]
        if op.get("opcode_name") not in ("ZEND_JMPZ", "ZEND_JMPNZ"):
            return None

        # Common PHP ternary shape after ionCube lazy materialization:
        #   JMPZ cond, <stale target>
        #   QM_ASSIGN true
        #   JMP <stale after>
        #   QM_ASSIGN false
        # The raw targets can point into a later concat/echo chain, so trust the
        # local opcode shape when both arms write the same temp.
        if i + 3 < min(end, self.n):
            true_op = self.ops[i + 1]
            jmp_op = self.ops[i + 2]
            false_op = self.ops[i + 3]
            if (
                true_op.get("opcode_name") == "ZEND_QM_ASSIGN"
                and jmp_op.get("opcode_name") == "ZEND_JMP"
                and false_op.get("opcode_name") == "ZEND_QM_ASSIGN"
            ):
                true_result = true_op.get("result", {})
                false_result = false_op.get("result", {})
                if (
                    true_result.get("type_name") in ("IS_TMP_VAR", "IS_VAR")
                    and false_result.get("type_name") in ("IS_TMP_VAR", "IS_VAR")
                    and self.key(true_result) == self.key(false_result)
                ):
                    true_state = st.clone()
                    self.handle_op(i + 1, true_state)
                    false_state = st.clone()
                    self.handle_op(i + 3, false_state)
                    true_expr = true_state.temps.get(self.key(true_result))
                    false_expr = false_state.temps.get(self.key(false_result))
                    if true_expr is not None and false_expr is not None:
                        cond = self.condition_expr(op, st)
                        return i + 4, true_result, f"({cond} ? {true_expr} : {false_expr})"

        false_start = self.target(op, i)
        if false_start is None or false_start <= i + 1 or false_start >= min(end, self.n):
            return None
        jmp_index = false_start - 1
        if jmp_index <= i or self.ops[jmp_index].get("opcode_name") != "ZEND_JMP":
            return None
        after = self.target(self.ops[jmp_index], jmp_index)
        if after is None or after <= false_start or after > end:
            return None
        if false_start >= after:
            return None

        true_last = self.ops[jmp_index - 1] if jmp_index - 1 >= i + 1 else None
        false_last = self.ops[after - 1]
        if not true_last or true_last.get("opcode_name") != "ZEND_QM_ASSIGN" or false_last.get("opcode_name") != "ZEND_QM_ASSIGN":
            return None
        true_result = true_last.get("result", {})
        false_result = false_last.get("result", {})
        if true_result.get("type_name") not in ("IS_TMP_VAR", "IS_VAR") or false_result.get("type_name") not in ("IS_TMP_VAR", "IS_VAR"):
            return None
        if self.key(true_result) != self.key(false_result):
            return None

        true_state = st.clone()
        for k in range(i + 1, jmp_index):
            self.handle_op(k, true_state)
        false_state = st.clone()
        for k in range(false_start, after):
            self.handle_op(k, false_state)

        true_expr = true_state.temps.get(self.key(true_result))
        false_expr = false_state.temps.get(self.key(false_result))
        if true_expr is None or false_expr is None:
            return None
        cond = self.condition_expr(op, st)
        return after, true_result, f"({cond} ? {true_expr} : {false_expr})"

    def case_dispatch_chain(self, start: int, end: int, st: State) -> Optional[Tuple[int, List[Tuple[str, int]]]]:
        cases: List[Tuple[str, int]] = []
        idx = start
        limit = min(end, self.n)
        while idx + 2 < limit:
            if self.ops[idx].get("opcode_name") == "ZEND_JMP":
                break
            case_idx = None
            scan = idx
            scan_limit = min(idx + 16, limit - 1)
            while scan < scan_limit:
                name = self.ops[scan].get("opcode_name")
                if name in ("ZEND_SWITCH_STRING", "ZEND_SWITCH_LONG"):
                    return None
                if name == "ZEND_CASE" and self.ops[scan + 1].get("opcode_name") == "ZEND_JMPNZ":
                    case_idx = scan
                    break
                if name in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_RETURN", "ZEND_EXIT", "ZEND_FE_RESET_R", "ZEND_FE_FETCH_R"):
                    return None
                scan += 1
            if case_idx is None:
                break

            jump_idx = case_idx + 1
            target = self.target(self.ops[jump_idx], jump_idx)
            if target is None or target <= jump_idx or target >= limit:
                return None

            local = st.clone()
            probe = idx
            while probe < case_idx:
                _stmt, adv = self.handle_op(probe, local)
                probe += max(adv, 1)
            cond = self.expr(self.ops[case_idx].get("op2", {}), local)
            if self.unresolved_tmp(cond):
                self.handle_op(case_idx, local)
                cond = self.expr(self.ops[case_idx].get("result", {}), local)
            cases.append((strip_redundant_parens(cond), target))
            idx = jump_idx + 1

        if not cases or idx >= limit or self.ops[idx].get("opcode_name") != "ZEND_JMP":
            return None
        join = self.target(self.ops[idx], idx)
        if join is None or join <= idx or join > end:
            return None
        targets = [target for _cond, target in cases]
        if any(target <= idx or target >= join for target in targets):
            return None
        if targets != sorted(targets):
            return None
        return join, cases

    def emit_case_dispatch_chain(
        self,
        cases: List[Tuple[str, int]],
        join: int,
        st: State,
        indent: int,
        seen: set,
        break_target: Optional[int],
        continue_target: Optional[int],
    ) -> List[str]:
        lines: List[str] = []
        targets = sorted({target for _cond, target in cases})
        for case_pos, (cond, target) in enumerate(cases):
            keyword = "if" if case_pos == 0 else "elseif"
            body_end = next((candidate for candidate in targets if candidate > target), join)
            if body_end > target and self.ops[body_end - 1].get("opcode_name") == "ZEND_JMP":
                jump_target = self.target(self.ops[body_end - 1], body_end - 1)
                if jump_target == join:
                    body_end -= 1
            lines.append("    " * indent + f"{keyword} ({cond}) {{")
            lines += self.emit_range(target, body_end, st.clone(), indent + 1, seen, break_target, continue_target)
            lines.append("    " * indent + "}")
        return lines

    def switch_statement(
        self,
        i: int,
        end: int,
        st: State,
        indent: int,
        seen: set,
        break_target: Optional[int],
        continue_target: Optional[int],
    ) -> Optional[Tuple[int, List[str]]]:
        op = self.ops[i]
        if op.get("opcode_name") not in ("ZEND_SWITCH_STRING", "ZEND_SWITCH_LONG"):
            return None

        limit = min(end, self.n)
        cases: List[Tuple[str, int]] = []
        j = i + 1
        while (
            j + 1 < limit
            and self.ops[j].get("opcode_name") == "ZEND_CASE"
            and self.ops[j + 1].get("opcode_name") == "ZEND_JMPNZ"
        ):
            target = self.target(self.ops[j + 1], j + 1)
            if target is None or target <= j + 1 or target > limit:
                return None
            cases.append((self.expr(self.ops[j].get("op2", {}), st), target))
            j += 2
        if not cases:
            return None

        default_target = None
        if j < limit and self.ops[j].get("opcode_name") == "ZEND_JMP":
            default_target = self.target(self.ops[j], j)
            if default_target is None or default_target <= j or default_target > limit:
                return None
            j += 1

        starts = sorted({target for _case, target in cases} | ({default_target} if default_target is not None else set()))
        if not starts:
            return None

        jump_targets: List[int] = []
        for pos, start in enumerate(starts):
            scan_end = starts[pos + 1] if pos + 1 < len(starts) else limit
            for scan in range(start, scan_end):
                if self.ops[scan].get("opcode_name") != "ZEND_JMP":
                    continue
                target = self.target(self.ops[scan], scan)
                if target is not None and target > scan and target <= limit:
                    jump_targets.append(target)
                    break

        join = None
        if jump_targets:
            counts: Dict[int, int] = {}
            for target in jump_targets:
                counts[target] = counts.get(target, 0) + 1
            join = sorted(counts, key=lambda target: (-counts[target], target))[0]
        elif default_target is not None:
            join = starts[-1]

        case_targets = [target for _case, target in cases]
        if join is None or join > limit:
            return None
        if case_targets and join <= max(case_targets):
            return None

        lines: List[str] = []
        lines.append("    " * indent + f"switch ({self.expr(op['op1'], st)}) {{")
        arm_starts = sorted(starts)

        def arm_end(target: int) -> Tuple[int, bool]:
            next_start = next((candidate for candidate in arm_starts if candidate > target and candidate < join), join)
            end_idx = next_start
            has_break = False
            if end_idx > target and self.ops[end_idx - 1].get("opcode_name") == "ZEND_JMP":
                jump_target = self.target(self.ops[end_idx - 1], end_idx - 1)
                if jump_target == join:
                    end_idx -= 1
                    has_break = True
            return end_idx, has_break

        def append_break_if_needed(body_lines: List[str], has_break: bool) -> None:
            if not has_break:
                return
            last = body_lines[-1].strip() if body_lines else ""
            if last == "break;" or last == "return;" or last.startswith("return ") or last == "exit;" or last.startswith("exit("):
                return
            lines.append("    " * (indent + 2) + "break;")

        for case_expr, target in cases:
            if target >= join:
                return None
            body_end, has_break = arm_end(target)
            lines.append("    " * (indent + 1) + f"case {case_expr}:")
            body_lines = self.emit_range(target, body_end, st.clone(), indent + 2, seen, break_target, continue_target)
            lines += body_lines
            append_break_if_needed(body_lines, has_break)

        if default_target is not None and default_target < join:
            body_end, has_break = arm_end(default_target)
            lines.append("    " * (indent + 1) + "default:")
            body_lines = self.emit_range(default_target, body_end, st.clone(), indent + 2, seen, break_target, continue_target)
            lines += body_lines
            append_break_if_needed(body_lines, has_break)

        lines.append("    " * indent + "}")
        return join, lines

    def emit_range(
        self,
        start: int,
        end: int,
        st: State,
        indent: int = 0,
        seen: Optional[set] = None,
        break_target: Optional[int] = None,
        continue_target: Optional[int] = None,
    ) -> List[str]:
        lines: List[str] = []
        i = start
        seen = seen or set()
        while i < end and i < self.n:
            if (i, end, indent) in seen:
                lines.append("    " * indent + "/* recursion guard at opcode %d */" % i)
                break
            seen.add((i, end, indent))
            op = self.ops[i]
            name = op.get("opcode_name")

            if end == self.n and self.is_null_return(i) and self.only_trailing_noise(i + 1, end):
                break
            if end == self.n and self.is_implicit_main_return(i) and self.only_trailing_noise(i + 1, end):
                break

            switch_stmt = self.switch_statement(i, end, st, indent, seen, break_target, continue_target)
            if switch_stmt is not None:
                switch_end, switch_lines = switch_stmt
                lines += switch_lines
                i = switch_end
                continue

            case_chain = self.case_dispatch_chain(i, end, st)
            if case_chain is not None:
                join, cases = case_chain
                lines += self.emit_case_dispatch_chain(cases, join, st, indent, seen, break_target, continue_target)
                i = join
                continue

            if name in ("ZEND_JMPZ", "ZEND_JMPNZ"):
                guarded_end = self.target(op, i)
                if guarded_end is not None and guarded_end > i + 1 and guarded_end <= end:
                    guarded_case_chain = self.case_dispatch_chain(i + 1, guarded_end, st)
                    if guarded_case_chain is not None:
                        join, cases = guarded_case_chain
                        if join < guarded_end:
                            cond = self.condition_expr(op, st)
                            lines.append("    " * indent + f"if ({cond}) {{")
                            lines += self.emit_case_dispatch_chain(cases, join, st.clone(), indent + 1, seen, break_target, continue_target)
                            lines += self.emit_range(join, guarded_end, st.clone(), indent + 1, seen, break_target, continue_target)
                            lines.append("    " * indent + "}")
                            i = guarded_end
                            continue

            ternary = self.conditional_expression(i, end, st)
            if ternary is not None:
                after, result, expr = ternary
                self.set_tmp(result, expr, st)
                i = after
                continue

            loop = self.find_forward_jump_loop(i, end, st)
            if loop is not None:
                body_end, after_loop, cond = loop
                lines.append("    " * indent + f"while ({cond}) {{")
                lines += self.emit_range(i + 1, body_end, st.clone(), indent + 1, seen, after_loop, body_end)
                lines.append("    " * indent + "}")
                i = after_loop
                continue

            if name in ("ZEND_FE_RESET_R", "ZEND_FE_RESET_RW") and i + 1 < end:
                fetch = self.ops[i + 1]
                if fetch.get("opcode_name") in ("ZEND_FE_FETCH_R", "ZEND_FE_FETCH_RW"):
                    done = self.target(fetch, i + 1) or self.target(op, i)
                    if done is not None and done > i + 1 and done <= end:
                        src = self.expr(op["op1"], st)
                        var = self.expr(fetch["op2"], st)
                        body_start = i + 2
                        key_var = None
                        if (
                            body_start < done
                            and self.ops[body_start].get("opcode_name") == "ZEND_ASSIGN"
                            and self.ops[body_start].get("op2", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR")
                            and fetch.get("result", {}).get("type_name") in ("IS_TMP_VAR", "IS_VAR")
                            and self.key(self.ops[body_start]["op2"]) == self.key(fetch["result"])
                        ):
                            key_var = self.expr(self.ops[body_start]["op1"], st)
                            body_start += 1
                        each = f"{key_var} => {var}" if key_var else var
                        lines.append("    " * indent + f"foreach ({src} as {each}) {{")
                        body_end = done - 1 if self.ops[done - 1].get("opcode_name") == "ZEND_FE_FREE" else done
                        if body_end > i + 2 and self.ops[body_end - 1].get("opcode_name") == "ZEND_JMP":
                            jump_back = self.target(self.ops[body_end - 1], body_end - 1)
                            if jump_back is not None and jump_back < body_end:
                                body_end -= 1
                        lines += self.emit_range(body_start, body_end, st.clone(), indent + 1, seen, done, i + 1)
                        lines.append("    " * indent + "}")
                        i = done
                        continue

            if name in ("ZEND_JMPZ", "ZEND_JMPNZ"):
                false_start, after, jmp_index = self.fixed_false_target(i)
                cond = self.condition_expr(op, st)
                if false_start is not None and false_start <= i:
                    raw_cond = self.expr(op["op1"], st)
                    loop_cond = raw_cond if name == "ZEND_JMPNZ" else "!(" + raw_cond + ")"
                    lines.append("    " * indent + f"/* loop back while ({loop_cond}) to opcode {false_start} */")
                    i += 1
                    continue
                if false_start is not None and false_start > i:
                    body_start = i + 1
                    protected_extended = False
                    if self.is_submit_superglobal_guard(i):
                        protected_extended = True
                    repaired_guard_end = self.repaired_loop_guard_end(i, false_start, st)
                    if repaired_guard_end is not None and repaired_guard_end > body_start:
                        false_start = repaired_guard_end
                    if after is None and false_start > end:
                        forward_jmp = self.first_forward_jump(body_start, end)
                        if forward_jmp is not None:
                            maybe_after = self.target(self.ops[forward_jmp], forward_jmp)
                            if maybe_after is not None:
                                maybe_after = self.repaired_after_target(forward_jmp + 1, maybe_after)
                            if maybe_after is not None and maybe_after > forward_jmp + 1 and maybe_after <= end:
                                has_nested_branch = any(self.ops[k].get("opcode_name") in ("ZEND_JMPZ", "ZEND_JMPNZ") for k in range(body_start, forward_jmp))
                                if not has_nested_branch and self.find_forward_jump_loop(forward_jmp, end, st) is None:
                                    false_start = forward_jmp + 1
                                    after = maybe_after
                                    jmp_index = forward_jmp
                    if false_start > end:
                        simple_end = self.simple_assignment_statement_end(body_start)
                        if simple_end is not None and simple_end <= end:
                            false_start = simple_end
                        else:
                            false_start = end
                            protected_extended = True
                    if self.is_main and self.raw_target(op) == false_start:
                        dependent_end = self.dependent_tail_end(body_start, false_start, self.assigned_cvs_in_range(body_start, false_start))
                        if dependent_end > false_start:
                            protected_extended = True
                            false_start = dependent_end
                    body_end = false_start
                    cut = None
                    if after is None and false_start - 1 > i and self.ops[false_start - 1].get("opcode_name") == "ZEND_JMP":
                        prev = false_start - 2
                        while prev >= body_start and self.ops[prev].get("opcode_name") in ("ZEND_NOP", "ZEND_FREE", "ZEND_FE_FREE"):
                            prev -= 1
                        if prev < body_start or self.ops[prev].get("opcode_name") not in ("ZEND_RETURN", "ZEND_EXIT"):
                            maybe_after = self.target(self.ops[false_start - 1], false_start - 1)
                            if maybe_after is not None and maybe_after > false_start and maybe_after <= end:
                                after = maybe_after
                                jmp_index = false_start - 1
                    if after is None:
                        cut = None if protected_extended else self.first_external_entry(body_start, body_end, i)
                        if cut is not None:
                            body_end = cut
                            simple_end = self.simple_assignment_statement_end(body_start)
                            if simple_end is not None and simple_end < body_end:
                                body_end = simple_end
                            else:
                                nested_join = self.first_nested_join_after_statement(body_start, body_end)
                                if nested_join is not None and nested_join < body_end:
                                    body_end = nested_join
                    if body_end <= body_start:
                        i = false_start
                        continue

                    if after is None and not protected_extended:
                        forward_jmp = self.first_forward_jump(body_start, body_end)
                        if forward_jmp is not None:
                            maybe_after = self.target(self.ops[forward_jmp], forward_jmp)
                            if maybe_after is not None:
                                maybe_after = self.repaired_after_target(forward_jmp + 1, maybe_after)
                            if maybe_after is not None and maybe_after > forward_jmp + 1 and maybe_after <= self.n:
                                has_nested_branch = any(self.ops[k].get("opcode_name") in ("ZEND_JMPZ", "ZEND_JMPNZ") for k in range(body_start, forward_jmp))
                                if not has_nested_branch and self.find_forward_jump_loop(forward_jmp, body_end, st) is None:
                                    false_start = forward_jmp + 1
                                    after = maybe_after
                                    jmp_index = forward_jmp

                    # else-formation is only safe when both ranges are single-entry.
                    if after is not None and after <= end and cut is None:
                        else_cut = self.first_external_entry(false_start, after, i)
                        if else_cut is not None:
                            after = None

                    if after is not None and after > end and false_start < end:
                        lines.append("    " * indent + f"if ({cond}) {{")
                        true_start = i + 1
                        true_end = jmp_index or false_start
                        true_jump_stmt = self.jump_statement_for_target(true_start, break_target, continue_target) if true_end == true_start else None
                        if (
                            true_jump_stmt is not None
                        ):
                            lines.append("    " * (indent + 1) + true_jump_stmt)
                        else:
                            lines += self.emit_range(true_start, true_end, st.clone(), indent + 1, seen, break_target, continue_target)
                            if jmp_index is not None:
                                jump_stmt = self.jump_statement_for_target(jmp_index, break_target, continue_target)
                                if jump_stmt is not None:
                                    lines.append("    " * (indent + 1) + jump_stmt)
                                else:
                                    return_stmt = self.return_statement_for_jump(jmp_index, st)
                                    if return_stmt is not None:
                                        lines.append("    " * (indent + 1) + return_stmt)
                        lines.append("    " * indent + "}")
                        trailing_jump_stmt = self.jump_statement_for_target(jmp_index, break_target, continue_target) if jmp_index is not None else None
                        if true_jump_stmt is not None or trailing_jump_stmt is not None:
                            lines += self.emit_range(false_start, end, st.clone(), indent, seen, break_target, continue_target)
                        else:
                            lines[-1] = "    " * indent + "} else {"
                            lines += self.emit_range(false_start, end, st.clone(), indent + 1, seen, break_target, continue_target)
                            lines.append("    " * indent + "}")
                        i = end
                        continue

                    if after is not None and after <= end:
                        lines.append("    " * indent + f"if ({cond}) {{")
                        true_start = i + 1
                        true_end = jmp_index or false_start
                        true_jump_stmt = self.jump_statement_for_target(true_start, break_target, continue_target) if true_end == true_start else None
                        if (
                            true_jump_stmt is not None
                        ):
                            lines.append("    " * (indent + 1) + true_jump_stmt)
                        else:
                            lines += self.emit_range(true_start, true_end, st.clone(), indent + 1, seen, break_target, continue_target)
                        lines.append("    " * indent + "}")
                        if true_jump_stmt is not None:
                            lines += self.emit_range(false_start, after, st.clone(), indent, seen, break_target, continue_target)
                        else:
                            lines[-1] = "    " * indent + "} else {"
                            lines += self.emit_range(false_start, after, st.clone(), indent + 1, seen, break_target, continue_target)
                            lines.append("    " * indent + "}")
                        i = after
                        continue
                    lines.append("    " * indent + f"if ({cond}) {{")
                    true_end = jmp_index if jmp_index is not None and jmp_index > body_start else body_end
                    lines += self.emit_range(body_start, true_end, st.clone(), indent + 1, seen, break_target, continue_target)
                    if jmp_index is not None:
                        jmp_target = self.target(self.ops[jmp_index], jmp_index)
                        if break_target is not None and jmp_target is not None and jmp_target >= break_target:
                            lines.append("    " * (indent + 1) + "break;")
                        elif continue_target is not None and jmp_target is not None and jmp_target <= continue_target:
                            lines.append("    " * (indent + 1) + "continue;")
                    lines.append("    " * indent + "}")
                    i = false_start if jmp_index is not None and false_start < end else body_end
                    continue

            if name == "ZEND_JMP":
                t = self.target(op, i)
                if break_target is not None and t is not None and t >= break_target:
                    lines.append("    " * indent + "break;")
                elif continue_target is not None and t is not None and t <= continue_target:
                    lines.append("    " * indent + "continue;")
                elif t is not None and t <= i:
                    lines.append("    " * indent + "/* loop back to opcode %d */" % t)
                elif t is not None and t < end:
                    lines.append("    " * indent + "/* jump to opcode %d */" % t)
                i += 1
                continue

            stmt, advance = self.handle_op(i, st)
            if stmt:
                for line in stmt:
                    for physical_line in line.splitlines() or [""]:
                        lines.append("    " * indent + physical_line)
                # Keep blocks sane: stop linear emission after hard terminators.
                last = stmt[-1].strip()
                if last == "exit;" or last.startswith("exit(") or last == "return;" or last.startswith("return "):
                    break
            i += advance
        return lines

    def _binop(self, op: Dict[str, Any], st: State, symbol: str) -> None:
        self.set_tmp(op["result"], strip_redundant_parens(self.expr(op["op1"], st) + f" {symbol} " + self.expr(op["op2"], st)), st)

    def propagate_call_to_next_assign(self, i: int, expr: str, st: State) -> bool:
        j = i + 1
        while j < self.n and self.ops[j].get("opcode_name") in ("ZEND_END_SILENCE", "ZEND_FREE", "ZEND_NOP"):
            j += 1
        if j >= self.n:
            return False
        next_op = self.ops[j]
        if next_op.get("opcode_name") != "ZEND_ASSIGN":
            return False
        src = next_op.get("op2", {})
        if src.get("type_name") in ("IS_VAR", "IS_TMP_VAR"):
            self.set_tmp(src, expr, st)
            return True
        return False

    def format_call_args(self, callee: str, args: List[str]) -> List[str]:
        mode_arg_indexes = {
            "chmod": (1,),
            "fchmod": (1,),
            "mkdir": (1,),
            "umask": (0,),
        }
        indexes = mode_arg_indexes.get(callee.lower())
        if not indexes:
            return args

        formatted = list(args)
        for idx in indexes:
            if idx >= len(formatted):
                continue
            value = formatted[idx]
            if not value.isdigit():
                continue
            numeric = int(value, 10)
            if 0 < numeric <= 0o7777:
                formatted[idx] = "0" + format(numeric, "o")
        return formatted

    def call_is_silenced(self, i: int) -> bool:
        init_names = {
            "ZEND_INIT_FCALL",
            "ZEND_INIT_FCALL_BY_NAME",
            "ZEND_INIT_NS_FCALL_BY_NAME",
            "ZEND_INIT_METHOD_CALL",
            "ZEND_INIT_STATIC_METHOD_CALL",
            "ZEND_INIT_DYNAMIC_CALL",
            "ZEND_NEW",
        }
        j = i - 1
        init_idx = None
        while j >= 0:
            name = self.ops[j].get("opcode_name")
            if name in init_names:
                init_idx = j
                break
            if name in ("ZEND_JMP", "ZEND_JMPZ", "ZEND_JMPNZ", "ZEND_RETURN", "ZEND_EXIT"):
                return False
            j -= 1
        if init_idx is None:
            return False
        j = init_idx - 1
        while j >= 0 and self.ops[j].get("opcode_name") in ("ZEND_NOP", "ZEND_FREE"):
            j -= 1
        return j >= 0 and self.ops[j].get("opcode_name") == "ZEND_BEGIN_SILENCE"

    def apply_silence(self, i: int, expr: str) -> str:
        if not self.call_is_silenced(i):
            return expr
        if expr.startswith("@"):
            return expr
        return "@" + expr

    def dynamic_callee_expr(self, op: Dict[str, Any], st: State) -> str:
        operand = op.get("op2", {})
        if operand.get("type_name") == "IS_UNUSED":
            operand = op.get("op1", {})
        if operand.get("type_name") == "IS_CONST":
            lit = unwrap(operand.get("literal"))
            if isinstance(lit, str):
                return lit
        expr = self.expr(operand, st)
        if expr.startswith("$") or expr.startswith("_") or expr.replace("\\", "").replace("_", "").isalnum():
            return expr
        return "(" + expr + ")"

    def expression_range_result(self, start: int, end: int, result_key: int, st: State) -> Optional[str]:
        local = st.clone()
        idx = start
        limit = min(end, self.n)
        while idx < limit:
            _lines, adv = self.handle_op(idx, local)
            idx += max(adv, 1)
        return local.temps.get(result_key)

    def handle_op(self, i: int, st: State) -> Tuple[List[str], int]:
        op = self.ops[i]
        name = op.get("opcode_name")
        out: List[str] = []

        if name in (
            "ZEND_RECV",
            "ZEND_RECV_INIT",
            "ZEND_FREE",
            "ZEND_FE_FREE",
            "ZEND_NOP",
            "ZEND_SEPARATE",
            "ZEND_BEGIN_SILENCE",
            "ZEND_END_SILENCE",
        ):
            return out, 1

        if name == "ZEND_FETCH_CONSTANT":
            val = unwrap(op["op2"].get("literal"))
            self.set_tmp(op["result"], str(val), st)
        elif name in ("ZEND_FETCH_DIM_R", "ZEND_FETCH_DIM_FUNC_ARG", "ZEND_FETCH_DIM_W", "ZEND_FETCH_DIM_IS"):
            dim = self.op_lit(op["op2"]) if op["op2"].get("type_name") in ("IS_CONST", "IS_UNUSED") else self.expr(op["op2"], st)
            self.set_tmp(op["result"], self.expr(op["op1"], st) + "[" + dim + "]", st)
        elif name in ("ZEND_FETCH_OBJ_R", "ZEND_FETCH_OBJ_FUNC_ARG", "ZEND_FETCH_OBJ_W", "ZEND_FETCH_OBJ_IS"):
            base = self.expr(op["op1"], st) or "$this"
            prop = unwrap(op["op2"].get("literal"))
            self.set_tmp(op["result"], f"{base}->{prop}", st)
        elif name == "ZEND_FETCH_THIS":
            self.set_tmp(op["result"], "$this", st)
        elif name in ("ZEND_FETCH_R", "ZEND_FETCH_W", "ZEND_FETCH_IS", "ZEND_FETCH_FUNC_ARG", "ZEND_FETCH_UNSET"):
            superg = self._superglobal_var(op["op1"])
            self.set_tmp(op["result"], superg if superg is not None else self.expr(op["op1"], st), st)
        elif name in ("ZEND_CONCAT", "ZEND_FAST_CONCAT"):
            self._binop(op, st, ".")
        elif name in ("ZEND_BW_XOR", "ZEND_BW_OR", "ZEND_SPACESHIP"):
            m = {
                "ZEND_BW_XOR": "^",
                "ZEND_BW_OR": "|",
                "ZEND_SPACESHIP": "<=>",
            }[name]
            self._binop(op, st, m)
        elif name == "ZEND_CAST":
            cast = op.get("extended_value_decoded") or "int"
            if isinstance(cast, dict):
                cast = "int"
            self.set_tmp(op["result"], f"({cast}) " + self.expr(op["op1"], st), st)
        elif name in ("ZEND_BOOL", "ZEND_QM_ASSIGN"):
            k = self.key(op["result"])
            val = self.expr(op["op1"], st)
            if k in st.pending_bool:
                join, join_op = st.pending_bool.pop(k)
                if join_op == "&&" and "||" in join:
                    join = f"({join})"
                val = f"({join} {join_op} {val})"
            self.set_tmp(op["result"], strip_redundant_parens(val), st)
        elif name == "ZEND_BOOL_NOT":
            self.set_tmp(op["result"], "!(" + self.expr(op["op1"], st) + ")", st)
        elif name in (
            "ZEND_IS_EQUAL",
            "ZEND_IS_NOT_EQUAL",
            "ZEND_IS_SMALLER",
            "ZEND_IS_SMALLER_OR_EQUAL",
            "ZEND_IS_IDENTICAL",
            "ZEND_IS_NOT_IDENTICAL",
            "ZEND_CASE",
        ):
            m = {
                "ZEND_IS_EQUAL": "==",
                "ZEND_IS_NOT_EQUAL": "!=",
                "ZEND_IS_SMALLER": "<",
                "ZEND_IS_SMALLER_OR_EQUAL": "<=",
                "ZEND_IS_IDENTICAL": "===",
                "ZEND_IS_NOT_IDENTICAL": "!==",
                "ZEND_CASE": "==",
            }[name]
            self._binop(op, st, m)
        elif name in ("ZEND_SUB", "ZEND_DIV", "ZEND_ADD", "ZEND_MUL", "ZEND_MOD"):
            m = {
                "ZEND_SUB": "-",
                "ZEND_DIV": "/",
                "ZEND_ADD": "+",
                "ZEND_MUL": "*",
                "ZEND_MOD": "%",
            }[name]
            self._binop(op, st, m)
        elif name == "ZEND_ISSET_ISEMPTY_DIM_OBJ":
            fn = "empty" if (int(op.get("extended_value") or 0) & 0x01000000) else "isset"
            dim = self.op_lit(op["op2"]) if op["op2"].get("type_name") in ("IS_CONST", "IS_UNUSED") else self.expr(op["op2"], st)
            self.set_tmp(op["result"], fn + "(" + self.expr(op["op1"], st) + "[" + dim + "])", st)
        elif name == "ZEND_ISSET_ISEMPTY_CV":
            fn = "empty" if (int(op.get("extended_value") or 0) & 0x01000000) else "isset"
            self.set_tmp(op["result"], fn + "(" + self.expr(op["op1"], st) + ")", st)
        elif name in ("ZEND_JMPZ_EX", "ZEND_JMPNZ_EX"):
            val = self.expr(op["op1"], st)
            k = self.key(op["result"])
            if name == "ZEND_JMPNZ_EX":
                st.pending_bool[k] = (val, "||")
                st.temps[k] = val
            else:
                st.pending_bool[k] = (val, "&&")
                st.temps[k] = val
        elif name == "ZEND_JMP_SET":
            result = op.get("result", {})
            left = self.expr(op["op1"], st)
            target = self.target(op, i)
            if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR") and target is not None and target > i + 1:
                fallback = self.expression_range_result(i + 1, target, self.key(result), st)
                if fallback is not None:
                    self.set_tmp(result, strip_redundant_parens(f"({left} ?: {fallback})"), st)
                    return out, target - i
            self.set_tmp(result, left, st)
        elif name == "ZEND_ASSIGN":
            left = self.expr(op["op1"], st)
            right = self.expr_or_recent(op["op2"], st, i)
            out.append(f"{left} = {right};")
            self.set_tmp(op["result"], left, st)
        elif name == "ZEND_ASSIGN_CONCAT":
            out.append(f"{self.expr(op['op1'], st)} .= {self.expr_or_recent(op['op2'], st, i)};")
        elif name in ("ZEND_ASSIGN_ADD", "ZEND_ASSIGN_SUB", "ZEND_ASSIGN_MUL", "ZEND_ASSIGN_DIV", "ZEND_ASSIGN_MOD", "ZEND_ASSIGN_BW_OR", "ZEND_ASSIGN_BW_AND", "ZEND_ASSIGN_BW_XOR"):
            m = {
                "ZEND_ASSIGN_ADD": "+=",
                "ZEND_ASSIGN_SUB": "-=",
                "ZEND_ASSIGN_MUL": "*=",
                "ZEND_ASSIGN_DIV": "/=",
                "ZEND_ASSIGN_MOD": "%=",
                "ZEND_ASSIGN_BW_OR": "|=",
                "ZEND_ASSIGN_BW_AND": "&=",
                "ZEND_ASSIGN_BW_XOR": "^=",
            }[name]
            out.append(f"{self.expr(op['op1'], st)} {m} {self.expr_or_recent(op['op2'], st, i)};")
        elif name == "ZEND_BIND_GLOBAL":
            var = self.expr(op["op1"], st)
            if not var or var == "$_unk":
                global_name = self._const_string(op["op2"])
                if global_name:
                    var = "$" + safe_name(global_name, "_global")
            if var and var != "$_unk":
                out.append(f"global {var};")
        elif name == "ZEND_UNSET_CV":
            out.append(f"unset({self.expr(op['op1'], st)});")
        elif name == "ZEND_UNSET_DIM":
            dim = self.op_lit(op["op2"]) if op["op2"].get("type_name") in ("IS_CONST", "IS_UNUSED") else self.expr(op["op2"], st)
            out.append(f"unset({self.expr(op['op1'], st)}[{dim}]);")
        elif name == "ZEND_ROPE_INIT":
            self.set_tmp(op["result"], self.expr(op["op2"], st), st)
        elif name == "ZEND_ROPE_ADD":
            self.set_tmp(op["result"], self.expr(op["op1"], st) + " . " + self.expr(op["op2"], st), st)
        elif name == "ZEND_ROPE_END":
            self.set_tmp(op["result"], self.expr(op["op1"], st) + " . " + self.expr(op["op2"], st), st)
        elif name == "ZEND_ASSIGN_DIM":
            dim = ""
            if op["op2"].get("type_name") != "IS_UNUSED":
                dim = self.op_lit(op["op2"]) if op["op2"].get("type_name") == "IS_CONST" else self.expr(op["op2"], st)
            left = self.expr(op["op1"], st) + "[" + dim + "]"
            val = "null"
            adv = 1
            if i + 1 < self.n and self.ops[i + 1].get("opcode_name") == "ZEND_OP_DATA":
                val = self.expr(self.ops[i + 1]["op1"], st)
                adv = 2
            out.append(f"{left} = {val};")
            return out, adv
        elif name == "ZEND_ASSIGN_OBJ":
            recv = self.expr(op["op1"], st) or "$this"
            left = recv + "->" + str(unwrap(op["op2"].get("literal")))
            val = "null"
            adv = 1
            if i + 1 < self.n and self.ops[i + 1].get("opcode_name") == "ZEND_OP_DATA":
                val = self.expr(self.ops[i + 1]["op1"], st)
                adv = 2
            out.append(f"{left} = {val};")
            return out, adv
        elif name == "ZEND_INIT_ARRAY":
            k = self.key(op["result"])
            st.arrays[k] = []
            if op["op1"].get("type_name") != "IS_UNUSED":
                val = self.expr(op["op1"], st)
                key = self.op_lit(op["op2"]) if op["op2"].get("type_name") != "IS_UNUSED" else ""
                st.arrays[k].append(f"{key} => {val}" if key else val)
            st.temps[k] = "[" + ", ".join(st.arrays[k]) + "]"
        elif name == "ZEND_ADD_ARRAY_ELEMENT":
            k = self.key(op["result"])
            val = self.expr(op["op1"], st)
            key = self.op_lit(op["op2"]) if op["op2"].get("type_name") != "IS_UNUSED" else ""
            st.arrays.setdefault(k, []).append(f"{key} => {val}" if key else val)
            st.temps[k] = "[" + ", ".join(st.arrays[k]) + "]"
        elif name in ("ZEND_INIT_FCALL", "ZEND_INIT_FCALL_BY_NAME", "ZEND_INIT_NS_FCALL_BY_NAME"):
            st.call_stack.append({"expr": self.canonical_function_name(unwrap(op["op2"].get("literal"))), "args": []})
        elif name == "ZEND_DECLARE_LAMBDA_FUNCTION":
            lit = op.get("op1", {}).get("literal") or {}
            closure_id = "closure:" + str(lit.get("hex", ""))
            label = self.lambda_exprs.get(closure_id) or self.lambda_names.get(closure_id, "function () { /* closure */ }")
            self.set_tmp(op["result"], php_literal(label) if label.startswith("_closure_") else label, st)
        elif name in ("ZEND_BIND_LEXICAL", "ZEND_BIND_STATIC", "ZEND_SWITCH_STRING"):
            pass
        elif name == "ZEND_NEW":
            cls = str(unwrap(op["op1"].get("literal")))
            st.call_stack.append({"expr": f"new {cls}", "args": []})
        elif name == "ZEND_INIT_METHOD_CALL":
            recv = self.expr(op["op1"], st) or "$this"
            method = unwrap(op["op2"].get("literal"))
            st.call_stack.append({"expr": f"{recv}->{method}", "args": []})
        elif name == "ZEND_INIT_STATIC_METHOD_CALL":
            cls = self._const_string(op["op1"]) or self.expr(op["op1"], st) or str(unwrap(op["op1"].get("literal")))
            method = unwrap(op["op2"].get("literal"))
            st.call_stack.append({"expr": f"{cls}::{method}", "args": []})
        elif name == "ZEND_INIT_DYNAMIC_CALL":
            st.call_stack.append({"expr": self.dynamic_callee_expr(op, st), "args": []})
        elif name.startswith("ZEND_SEND_"):
            if st.call_stack:
                st.call_stack[-1]["args"].append(self.expr(op["op1"], st))
        elif name in ("ZEND_DO_FCALL", "ZEND_DO_FCALL_BY_NAME", "ZEND_DO_ICALL", "ZEND_DO_UCALL"):
            call = st.call_stack.pop() if st.call_stack else None
            if call is None:
                recovered = self._recover_call_from_ops(i, st)
                if recovered is None:
                    out.append("/* unresolved call */;")
                    return out, 1
                recovered_args = self.format_call_args(recovered[0], recovered[1])
                expr = self.apply_silence(i, recovered[0] + "(" + ", ".join(recovered_args) + ")")
                if op["result"].get("type_name") in ("IS_VAR", "IS_TMP_VAR"):
                    self.set_tmp(op["result"], expr, st)
                    self.propagate_call_to_next_assign(i, expr, st)
                else:
                    out.append(expr + ";")
                return out, 1
            call_args = self.format_call_args(call["expr"], call["args"])
            expr = call["expr"] + "(" + ", ".join(call_args) + ")"
            expr = self.apply_silence(i, expr)
            if op["result"].get("type_name") in ("IS_VAR", "IS_TMP_VAR"):
                self.set_tmp(op["result"], expr, st)
                self.propagate_call_to_next_assign(i, expr, st)
            else:
                if not (expr.startswith("new ") and self.propagate_call_to_next_assign(i, expr, st)):
                    out.append(expr + ";")
        elif name in ("ZEND_PRE_INC", "ZEND_POST_INC"):
            var = self.expr(op["op1"], st)
            result = op.get("result", {})
            if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                if i + 1 < self.n and self.ops[i + 1].get("opcode_name") == "ZEND_FREE" and self.key(self.ops[i + 1].get("op1", {})) == self.key(result):
                    out.append(("++" + var if name == "ZEND_PRE_INC" else var + "++") + ";")
                    return out, 2
                self.set_tmp(op["result"], f"++{var}" if name == "ZEND_PRE_INC" else f"{var}++", st)
            else:
                out.append(("++" + var if name == "ZEND_PRE_INC" else var + "++") + ";")
        elif name in ("ZEND_PRE_DEC", "ZEND_POST_DEC"):
            var = self.expr(op["op1"], st)
            result = op.get("result", {})
            if result.get("type_name") in ("IS_TMP_VAR", "IS_VAR"):
                if i + 1 < self.n and self.ops[i + 1].get("opcode_name") == "ZEND_FREE" and self.key(self.ops[i + 1].get("op1", {})) == self.key(result):
                    out.append(("--" + var if name == "ZEND_PRE_DEC" else var + "--") + ";")
                    return out, 2
                self.set_tmp(op["result"], f"--{var}" if name == "ZEND_PRE_DEC" else f"{var}--", st)
            else:
                out.append(("--" + var if name == "ZEND_PRE_DEC" else var + "--") + ";")
        elif name == "ZEND_ECHO":
            out.append("echo " + self.expr(op["op1"], st) + ";")
        elif name == "ZEND_EXIT":
            expr = self.expr(op["op1"], st)
            out.append("exit;" if expr in ("", "null") else "exit(" + expr + ");")
        elif name == "ZEND_INCLUDE_OR_EVAL":
            expr = self.expr(op["op1"], st)
            mode = op.get("extended_value_decoded")
            if isinstance(mode, str):
                mode_s = mode.upper()
                if "REQUIRE_ONCE" in mode_s:
                    out.append("require_once " + expr + ";")
                elif "REQUIRE" in mode_s:
                    out.append("require " + expr + ";")
                elif "INCLUDE_ONCE" in mode_s:
                    out.append("include_once " + expr + ";")
                elif "INCLUDE" in mode_s:
                    out.append("include " + expr + ";")
                elif "EVAL" in mode_s:
                    out.append("eval(" + expr + ");")
                else:
                    out.append("/* include/eval */ " + expr + ";")
            else:
                out.append("/* include/eval */ " + expr + ";")
        elif name == "ZEND_RETURN":
            expr = self.expr(op["op1"], st)
            out.append("return;" if expr in ("", "null") else "return " + expr + ";")
        elif name in ("ZEND_FETCH_CLASS", "ZEND_DECLARE_INHERITED_CLASS", "ZEND_OP_DATA"):
            pass
        else:
            out.append(f"/* TODO {name} at opcode {i} */")
        return out, 1

    def decompile_structured(self) -> List[str]:
        return self.emit_range(0, self.n, State(), 0)

    def decompile_labels(self) -> List[str]:
        st = State()
        labels = {int(t) for op in self.ops for t in (op.get("jump_targets") or []) if isinstance(t, int) and 0 <= t < self.n}
        lines: List[str] = []
        i = 0
        while i < self.n:
            if i in labels:
                lines.append(f"L{i}:")
            op = self.ops[i]
            name = op.get("opcode_name")
            if name in ("ZEND_JMPZ", "ZEND_JMPNZ"):
                cond = self.condition_expr(op, st)
                t = self.target(op, i)
                if t is not None:
                    if name == "ZEND_JMPZ":
                        lines.append(f"if (!({cond})) goto L{t};")
                    else:
                        lines.append(f"if ({cond}) goto L{t};")
                i += 1
                continue
            if name in ("ZEND_JMPZ_EX", "ZEND_JMPNZ_EX"):
                self.handle_op(i, st)
                cond = self.expr(op["op1"], st)
                t = self.target(op, i)
                if t is not None:
                    if name == "ZEND_JMPZ_EX":
                        lines.append(f"if (!({cond})) goto L{t};")
                    else:
                        lines.append(f"if ({cond}) goto L{t};")
                i += 1
                continue
            if name == "ZEND_JMP":
                t = self.target(op, i)
                if t is not None:
                    lines.append(f"goto L{t};")
                i += 1
                continue
            if self.is_implicit_main_return(i) and self.only_trailing_noise(i + 1, self.n):
                i += 1
                continue
            stmt, advance = self.handle_op(i, st)
            lines.extend(stmt)
            for skipped in range(i + 1, min(i + advance, self.n)):
                if skipped in labels:
                    lines.append(f"L{skipped}:")
            i += advance
        return lines

    def decompile(self, mode: str = "structured") -> List[str]:
        if mode == "labels":
            return self.decompile_labels()
        return self.decompile_structured()
