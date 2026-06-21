from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class ExceptionRegion:
    try_start: int
    catch_start: int
    catch_end: int | None = None
    class_name: str = "Exception"
    var_name: str = "$e"


def recover_exception_regions(op_array: Mapping[str, Any], target_resolver=None) -> list[ExceptionRegion]:
    ops = list(op_array.get("opcodes") or [])
    regions: list[ExceptionRegion] = []
    for tc in op_array.get("try_catch") or op_array.get("try_catch_array") or []:
        try:
            try_op = int(tc.get("try_op", tc.get("try_start_index")))
            catch_op = int(tc.get("catch_op", tc.get("catch_start_index")))
        except Exception:
            continue
        if not (0 <= try_op < len(ops) and 0 <= catch_op < len(ops) and try_op < catch_op):
            continue
        catch_end = None
        if target_resolver is not None and catch_op > 0:
            rt = target_resolver.target(ops[catch_op - 1])
            if rt is not None and catch_op < rt.index <= len(ops):
                catch_end = rt.index
        cls = "Exception"
        var = "$e"
        catch_ins = ops[catch_op]
        lit = ((catch_ins.get("op1") or {}).get("literal") or {})
        if isinstance(lit, Mapping) and lit.get("value"):
            cls = str(lit.get("value"))
        cv = (catch_ins.get("op2") or {}).get("cv_name")
        if cv:
            var = "$" + str(cv)
        regions.append(ExceptionRegion(try_op, catch_op, catch_end, cls, var))
    return regions
