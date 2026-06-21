from __future__ import annotations

import re
from typing import List, Tuple

from .cfg_structurer import (
    LABEL_RE as _LABEL_RE,
    GOTO_RE as _GOTO_RE,
    IF_GOTO_RE as _IF_GOTO_RE,
    build_source_cfg,
    dominators,
    post_dominators,
    invert_condition as _invert_condition,
    goto_refs as _goto_refs,
)


def _label_positions(lines: List[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = _LABEL_RE.match(line)
        if m:
            out[m.group('label')] = i
    return out


def _has_internal_label(block: List[str]) -> bool:
    return any(_LABEL_RE.match(line) for line in block)


def _has_raw_goto(block: List[str]) -> bool:
    return any(_GOTO_RE.match(line) or _IF_GOTO_RE.match(line) for line in block)


def _indent_block(block: List[str], indent: str) -> List[str]:
    out: List[str] = []
    for line in block:
        if not line.strip():
            out.append(line)
        elif line.startswith(indent):
            out.append(indent + '    ' + line[len(indent):])
        else:
            out.append(indent + '    ' + line)
    return out


def _rewrite_if_else_once(lines: List[str], max_block_lines: int, allow_nested_else: bool = True) -> Tuple[List[str], bool]:
    labels = _label_positions(lines)
    i = 0
    while i < len(lines):
        m = _IF_GOTO_RE.match(lines[i])
        if not m:
            i += 1
            continue
        indent = m.group('indent')
        else_label = m.group('label')
        else_pos = labels.get(else_label)
        if else_pos is None or else_pos <= i + 1 or else_pos - i > max_block_lines:
            i += 1
            continue
        gm = _GOTO_RE.match(lines[else_pos - 1]) if else_pos - 1 > i else None
        if not gm:
            i += 1
            continue
        end_label = gm.group('label')
        end_pos = labels.get(end_label)
        if end_pos is None or end_pos <= else_pos or end_pos - i > max_block_lines * 3:
            i += 1
            continue
        then_body = lines[i + 1:else_pos - 1]
        else_body = lines[else_pos + 1:end_pos]
        if not then_body or not else_body:
            i += 1
            continue
        if _has_internal_label(then_body) or _has_internal_label(else_body):
            i += 1
            continue
        # Allow an else body that is itself an if/else chain. This lets us print elseif.
        if _has_raw_goto(then_body):
            i += 1
            continue
        if _has_raw_goto(else_body):
            nested, changed = _rewrite_if_else_once(else_body, max_block_lines, allow_nested_else=False)
            if changed:
                else_body = nested
            elif not allow_nested_else:
                i += 1
                continue
            elif _has_raw_goto(else_body):
                i += 1
                continue
        cond = _invert_condition(m.group('cond'))
        # If else body is a single if block, render as elseif.
        if else_body and else_body[0].lstrip().startswith('if ') and else_body[-1].strip() == '}':
            first = else_body[0].strip()
            repl = [f'{indent}if ({cond}) {{'] + _indent_block(then_body, indent) + [f'{indent}}} else{first[2:]}']
            repl += _indent_block(else_body[1:], indent)
        else:
            repl = [f'{indent}if ({cond}) {{'] + _indent_block(then_body, indent) + [f'{indent}}} else {{'] + _indent_block(else_body, indent) + [f'{indent}}}']
        return lines[:i] + repl + lines[end_pos + 1:], True
    return lines, False


def _rewrite_simple_if_once(lines: List[str], max_block_lines: int) -> Tuple[List[str], bool]:
    labels = _label_positions(lines)
    refs = _goto_refs(lines)
    i = 0
    while i < len(lines):
        m = _IF_GOTO_RE.match(lines[i])
        if not m:
            i += 1
            continue
        indent = m.group('indent')
        label = m.group('label')
        target = labels.get(label)
        if target is None or target <= i + 1 or target - i > max_block_lines:
            i += 1
            continue
        body = lines[i + 1:target]
        if not body or _has_internal_label(body) or _has_raw_goto(body):
            i += 1
            continue
        cond = _invert_condition(m.group('cond'))
        repl = [f'{indent}if ({cond}) {{'] + _indent_block(body, indent) + [f'{indent}}}']
        keep_target = refs.get(label, 0) > 1
        return lines[:i] + repl + (lines[target:] if keep_target else lines[target + 1:]), True
    return lines, False


def _rewrite_do_while_once(lines: List[str], max_block_lines: int) -> Tuple[List[str], bool]:
    labels = _label_positions(lines)
    i = 0
    while i < len(lines):
        lm = _LABEL_RE.match(lines[i])
        if not lm:
            i += 1
            continue
        label = lm.group('label')
        for j in range(i + 1, min(len(lines), i + max_block_lines + 1)):
            m = _IF_GOTO_RE.match(lines[j])
            if not m or m.group('label') != label:
                continue
            body = lines[i + 1:j]
            if not body or _has_internal_label(body) or _has_raw_goto(body):
                continue
            cond = m.group('cond').strip()
            indent = lm.group('indent')
            repl = [f'{indent}do {{'] + _indent_block(body, indent) + [f'{indent}}} while ({cond});']
            return lines[:i] + repl + lines[j + 1:], True
        i += 1
    return lines, False


def _cleanup_noop_gotos(lines: List[str]) -> Tuple[List[str], bool]:
    out: List[str] = []
    changed = False
    i = 0
    while i < len(lines):
        g = _GOTO_RE.match(lines[i])
        if g and i + 1 < len(lines):
            lm = _LABEL_RE.match(lines[i + 1])
            if lm and lm.group('label') == g.group('label'):
                changed = True
                i += 1
                continue
        out.append(lines[i])
        i += 1
    return out, changed


def _cleanup_label_runs(lines: List[str]) -> Tuple[List[str], bool]:
    # Consecutive labels are equivalent. Keep only labels that are still referenced.
    refs = _goto_refs(lines)
    out: List[str] = []
    changed = False
    i = 0
    while i < len(lines):
        if not _LABEL_RE.match(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        run = []
        while i < len(lines) and _LABEL_RE.match(lines[i]):
            run.append(lines[i])
            i += 1
        kept = [line for line in run if refs.get(_LABEL_RE.match(line).group('label'), 0) > 0]  # type: ignore[union-attr]
        if not kept:
            changed = True
        elif len(kept) != len(run):
            changed = True
        out.extend(kept)
    return out, changed


def _cleanup_unreferenced_labels(lines: List[str]) -> Tuple[List[str], bool]:
    refs = _goto_refs(lines)
    out: List[str] = []
    changed = False
    for line in lines:
        lm = _LABEL_RE.match(line)
        if lm and refs.get(lm.group('label'), 0) == 0:
            changed = True
            continue
        out.append(line)
    return out, changed


def _rewrite_break_continue_once(lines: List[str]) -> Tuple[List[str], bool]:
    # This is intentionally conservative: it only acts inside already-rendered foreach blocks.
    stack: List[Tuple[int, int]] = []  # (indent width, line index of foreach)
    changed = False
    out = list(lines)
    labels = _label_positions(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(' '))
        if stripped.startswith('foreach ') and stripped.endswith('{'):
            stack.append((indent, i))
            continue
        if stripped == '}':
            while stack and stack[-1][0] >= indent:
                stack.pop()
            continue
        if not stack:
            continue
        gm = _GOTO_RE.match(line)
        im = _IF_GOTO_RE.match(line)
        m = gm or im
        if not m:
            continue
        target = labels.get(m.group('label'))
        if target is None:
            continue
        # Jump to just after current foreach is break; jump to a label before/at foreach is continue.
        foreach_indent, foreach_line = stack[-1]
        # Find foreach closing brace.
        depth = 0
        close = None
        for j in range(foreach_line, len(lines)):
            txt = lines[j].strip()
            if txt.endswith('{'):
                depth += 1
            if txt == '}':
                depth -= 1
                if depth == 0:
                    close = j
                    break
        if close is None:
            continue
        repl = None
        if target >= close:
            repl = 'break;'
        elif target <= foreach_line + 1:
            repl = 'continue;'
        if not repl:
            continue
        if im:
            cond = im.group('cond')
            out[i] = f"{im.group('indent')}if ({cond}) {{ {repl} }}"
        else:
            out[i] = f"{gm.group('indent')}{repl}"
        changed = True
        return out, changed
    return lines, False



def _assignment_lhs(line: str) -> str | None:
    txt = line.strip()
    if '=' not in txt or txt.startswith(('if ', 'return ', 'echo ')):
        return None
    if '==' in txt or '!=' in txt or '<=' in txt or '>=' in txt:
        # Still allow assignment lines with comparisons on RHS by only looking before first =.
        pass
    lhs = txt.split('=', 1)[0].strip()
    if not lhs or lhs.endswith(('+', '-', '*', '/', '.', '%', '&', '|', '^')):
        return None
    return lhs



def _rewrite_prechecked_while_once(lines: List[str], max_span: int = 160) -> Tuple[List[str], bool]:
    # Pattern:
    #   goto Lcond;
    #   Lbody:
    #      body
    #   Lcond:
    #      $x = next(...);
    #      if ($x) goto Lbody;
    # -> while ($x = next(...)) { body }
    labels = _label_positions(lines)
    for i in range(len(lines) - 4):
        gm = _GOTO_RE.match(lines[i])
        if not gm:
            continue
        cond_label = gm.group('label')
        if i + 1 >= len(lines):
            continue
        lm_body = _LABEL_RE.match(lines[i + 1])
        if not lm_body:
            continue
        body_label = lm_body.group('label')
        cond_pos = labels.get(cond_label)
        if cond_pos is None or cond_pos <= i + 1 or cond_pos - i > max_span:
            continue
        # Find terminal if at condition block.
        if cond_pos + 1 >= len(lines):
            continue
        assign = lines[cond_pos + 1].strip()
        im = _IF_GOTO_RE.match(lines[cond_pos + 2]) if cond_pos + 2 < len(lines) else None
        if not im or im.group('label') != body_label:
            continue
        lhs = _assignment_lhs(assign)
        if not lhs:
            continue
        cond = im.group('cond').strip()
        # Accept if condition is the assigned variable or !!variable.
        norm = cond.replace('!!', '').strip()
        if norm != lhs:
            continue
        rhs = assign.split('=', 1)[1].rstrip(';').strip()
        indent = gm.group('indent')
        body = lines[i + 2:cond_pos]
        if not body:
            continue
        # Do not absorb code containing jumps outside the loop, except local structured code already printed.
        if _has_internal_label(body) or _has_raw_goto(body):
            continue
        repl = [f'{indent}while ({lhs} = {rhs}) {{'] + _indent_block(body, indent) + [f'{indent}}}']
        return lines[:i] + repl + lines[cond_pos + 3:], True
    return lines, False

def _rewrite_temp_if_else_once(lines: List[str], max_span: int = 12) -> Tuple[List[str], bool]:
    # Pattern produced by PHP ternaries and short if/else lowering when the dump has
    # unreliable raw target labels:
    #   if (cond) goto Lfar;
    #   $tmp = A;
    #   goto Ljoin;
    #   $tmp = B;
    #   ... optional local labels ...
    #   Ljoin:
    # becomes:
    #   if (!cond) { $tmp = A; } else { $tmp = B; }
    for i in range(len(lines) - 4):
        im = _IF_GOTO_RE.match(lines[i])
        if not im:
            continue
        indent = im.group('indent')
        lhs1 = _assignment_lhs(lines[i + 1])
        gm = _GOTO_RE.match(lines[i + 2])
        if not lhs1 or not gm:
            continue
        join_label = gm.group('label')
        # Find matching else assignment before local join label.
        for j in range(i + 3, min(len(lines), i + max_span)):
            if _LABEL_RE.match(lines[j]):
                continue
            lhs2 = _assignment_lhs(lines[j])
            if lhs2 != lhs1:
                continue
            # Find join label after j.
            join_pos = None
            for k in range(j + 1, min(len(lines), i + max_span + 4)):
                lm = _LABEL_RE.match(lines[k])
                if lm and lm.group('label') == join_label:
                    join_pos = k
                    break
            if join_pos is None:
                continue
            then_stmt = lines[i + 1].strip()
            else_stmt = lines[j].strip()
            cond = _invert_condition(im.group('cond'))
            repl = [
                f'{indent}if ({cond}) {{',
                f'{indent}    {then_stmt}',
                f'{indent}}} else {{',
                f'{indent}    {else_stmt}',
                f'{indent}}}',
            ]
            return lines[:i] + repl + lines[j + 1:join_pos] + lines[join_pos + 1:], True
    return lines, False



def _rewrite_immediate_label_if_else_once(lines: List[str], max_span: int = 80) -> Tuple[List[str], bool]:
    """Recover diamonds where the false label was emitted immediately after the condition.

    Some ionCube/runtime dumps produce source like:
        if (!cond) goto Lelse;
        Lelse:
        A;
        goto Ljoin;
        B;
        Ljoin:

    The label position is not useful as a source boundary, but the shape is still
    an if/else diamond: A is the fallthrough arm, B is the jumped-over arm.
    We only rewrite when both arms are local, contain no labels/raw gotos, and the
    immediate label is referenced only by this conditional jump.
    """
    labels = _label_positions(lines)
    refs = _goto_refs(lines)
    for i in range(len(lines) - 5):
        im = _IF_GOTO_RE.match(lines[i])
        if not im:
            continue
        indent = im.group('indent')
        else_label = im.group('label')
        if refs.get(else_label, 0) != 1:
            continue
        lm = _LABEL_RE.match(lines[i + 1])
        if not lm or lm.group('label') != else_label:
            continue

        # Find the unconditional jump that skips the alternate arm.
        skip_pos = None
        skip_match = None
        for j in range(i + 2, min(len(lines), i + max_span)):
            if _LABEL_RE.match(lines[j]):
                break
            gm = _GOTO_RE.match(lines[j])
            if gm:
                skip_pos = j
                skip_match = gm
                break
            if _IF_GOTO_RE.match(lines[j]):
                break
        if skip_pos is None or skip_match is None:
            continue

        join_label = skip_match.group('label')
        join_pos = labels.get(join_label)
        if join_pos is None or join_pos <= skip_pos + 1 or join_pos - i > max_span:
            continue

        then_body = lines[i + 2:skip_pos]
        else_body = lines[skip_pos + 1:join_pos]
        if not then_body or not else_body:
            continue
        if _has_internal_label(then_body) or _has_internal_label(else_body):
            continue
        if _has_raw_goto(then_body) or _has_raw_goto(else_body):
            continue

        cond = _invert_condition(im.group('cond'))
        repl = [f'{indent}if ({cond}) {{'] + _indent_block(then_body, indent) + [f'{indent}}} else {{'] + _indent_block(else_body, indent) + [f'{indent}}}']
        # Preserve the join label if other jumps still target it.
        if refs.get(join_label, 0) > 1:
            repl.append(lines[join_pos])
        return lines[:i] + repl + lines[join_pos + 1:], True
    return lines, False

def cfg_diagnostics(lines: List[str]) -> str:
    cfg = build_source_cfg(lines)
    dom = dominators(cfg.blocks)
    pdom = post_dominators(cfg.blocks)
    return f"blocks={len(cfg.blocks)} labels={len(cfg.label_to_line)} dom={len(dom)} pdom={len(pdom)}"


def structure_gotos(lines: List[str], max_block_lines: int = 160) -> List[str]:
    # Build a CFG first. The current pass is still source-preserving, but CFG
    # construction gives us block boundaries, dom/post-dom diagnostics, and a
    # safe base for future region rewriting. Regex-only replacements are kept
    # conservative and run after the graph is valid.
    _ = build_source_cfg(lines)
    out = list(lines)
    for _round in range(40):
        changed = False
        for fn in (
            _rewrite_immediate_label_if_else_once,
            _cleanup_noop_gotos,
            _rewrite_prechecked_while_once,
            _rewrite_temp_if_else_once,
            _rewrite_if_else_once,
            _rewrite_simple_if_once,
            _rewrite_do_while_once,
            _cleanup_label_runs,
            _cleanup_unreferenced_labels,
        ):
            if fn in (_rewrite_if_else_once, _rewrite_simple_if_once, _rewrite_do_while_once):
                out, ch = fn(out, max_block_lines)  # type: ignore[misc]
            else:
                out, ch = fn(out)  # type: ignore[misc]
            if ch:
                changed = True
                break
        if not changed:
            break
    return out


def structure_goto_source(source: str) -> str:
    trailing = '\n' if source.endswith('\n') else ''
    return '\n'.join(structure_gotos(source.splitlines())) + trailing
