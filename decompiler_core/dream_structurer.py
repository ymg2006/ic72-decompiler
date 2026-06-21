from __future__ import annotations

import re
from typing import Dict, Iterable, List, Set, Tuple

LABEL_RE = re.compile(r'^(?P<indent>\s*)L(?P<label>\d+):\s*$')
GOTO_RE = re.compile(r'^(?P<indent>\s*)goto L(?P<label>\d+);\s*$')
IF_GOTO_RE = re.compile(r'^(?P<indent>\s*)if \((?P<cond>.*)\) goto L(?P<label>\d+);\s*$')
TERM_RE = re.compile(r'^\s*(return|throw|exit\b|break\b|continue\b)')


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


def refs(lines: List[str]) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    for i, line in enumerate(lines):
        for rx in (GOTO_RE, IF_GOTO_RE):
            m = rx.match(line)
            if m:
                out.setdefault(m.group('label'), []).append(i)
    return out


def line_goto_labels(line: str) -> Set[str]:
    out: Set[str] = set()
    for rx in (GOTO_RE, IF_GOTO_RE):
        m = rx.match(line)
        if m:
            out.add(m.group('label'))
    return out


def goto_labels(lines: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for line in lines:
        out |= line_goto_labels(line)
    return out


def labels_in(lines: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for line in lines:
        m = LABEL_RE.match(line)
        if m:
            out.add(m.group('label'))
    return out


def indent_block(block: List[str], indent: str) -> List[str]:
    return [indent + '    ' + line if line.strip() else line for line in block]


def strip_unreferenced_labels(lines: List[str]) -> Tuple[List[str], bool]:
    r = refs(lines)
    out: List[str] = []
    changed = False
    for line in lines:
        m = LABEL_RE.match(line)
        if m and not r.get(m.group('label')):
            changed = True
            continue
        out.append(line)
    return out, changed


def remove_noop_gotos(lines: List[str]) -> Tuple[List[str], bool]:
    out: List[str] = []
    changed = False
    i = 0
    while i < len(lines):
        gm = GOTO_RE.match(lines[i])
        if gm and i + 1 < len(lines):
            lm = LABEL_RE.match(lines[i + 1])
            if lm and lm.group('label') == gm.group('label'):
                changed = True
                i += 1
                continue
        out.append(lines[i])
        i += 1
    return out, changed


def label_owned_by_region(label: str, start: int, end: int, all_refs: Dict[str, List[int]]) -> bool:
    # A label inside a region is safe to absorb only if every reference to it is
    # also inside the same region. This prevents jumping into generated braces.
    for pos in all_refs.get(label, []):
        if pos < start or pos >= end:
            return False
    return True


def region_is_safe(start: int, end: int, lines: List[str], all_refs: Dict[str, List[int]]) -> bool:
    for lab in labels_in(lines[start:end]):
        if not label_owned_by_region(lab, start, end, all_refs):
            return False
    return True


def rewrite_if_else_permissive(lines: List[str], max_span: int) -> Tuple[List[str], bool]:
    pos = label_positions(lines)
    all_refs = refs(lines)
    for i, line in enumerate(lines):
        im = IF_GOTO_RE.match(line)
        if not im:
            continue
        indent = im.group('indent')
        else_label = im.group('label')
        else_pos = pos.get(else_label)
        if else_pos is None or else_pos <= i + 1 or else_pos - i > max_span:
            continue
        # then body must end with a goto to the join label.
        if else_pos - 1 <= i:
            continue
        gm = GOTO_RE.match(lines[else_pos - 1])
        if not gm:
            continue
        join_label = gm.group('label')
        join_pos = pos.get(join_label)
        if join_pos is None or join_pos <= else_pos or join_pos - i > max_span:
            continue
        # Do not absorb labels that are referenced from outside this whole if/else region.
        if not region_is_safe(i + 1, else_pos - 1, lines, all_refs):
            continue
        if not region_is_safe(else_pos + 1, join_pos, lines, all_refs):
            continue
        then_body = dream_structure_lines(lines[i + 1:else_pos - 1], max_span=max_span, _depth=1)
        else_body = dream_structure_lines(lines[else_pos + 1:join_pos], max_span=max_span, _depth=1)
        cond = invert_condition(im.group('cond'))
        repl: List[str]
        # elseif cleanup: else body rendered as a single if block.
        stripped_else = [x for x in else_body if x.strip()]
        if stripped_else and stripped_else[0].lstrip().startswith('if ') and stripped_else[-1].strip() == '}':
            first = stripped_else[0].strip()
            repl = [f'{indent}if ({cond}) {{']
            repl += indent_block(then_body, indent)
            repl.append(f'{indent}}} else{first[2:]}')
            repl += indent_block(stripped_else[1:], indent)
        else:
            repl = [f'{indent}if ({cond}) {{']
            repl += indent_block(then_body or ['/* empty */'], indent)
            repl.append(f'{indent}}} else {{')
            repl += indent_block(else_body or ['/* empty */'], indent)
            repl.append(f'{indent}}}')
        return lines[:i] + repl + lines[join_pos + 1:], True
    return lines, False


def rewrite_simple_if_permissive(lines: List[str], max_span: int) -> Tuple[List[str], bool]:
    pos = label_positions(lines)
    all_refs = refs(lines)
    for i, line in enumerate(lines):
        im = IF_GOTO_RE.match(line)
        if not im:
            continue
        label = im.group('label')
        target = pos.get(label)
        if target is None or target <= i + 1 or target - i > max_span:
            continue
        # If the target label is referenced by more than this conditional, keep it after the block.
        if not region_is_safe(i + 1, target, lines, all_refs):
            continue
        body = dream_structure_lines(lines[i + 1:target], max_span=max_span, _depth=1)
        if not body:
            continue
        indent = im.group('indent')
        cond = invert_condition(im.group('cond'))
        repl = [f'{indent}if ({cond}) {{'] + indent_block(body, indent) + [f'{indent}}}']
        keep_label = len(all_refs.get(label, [])) > 1
        return lines[:i] + repl + (lines[target:] if keep_label else lines[target + 1:]), True
    return lines, False


def rewrite_do_while_permissive(lines: List[str], max_span: int) -> Tuple[List[str], bool]:
    for i, line in enumerate(lines):
        lm = LABEL_RE.match(line)
        if not lm:
            continue
        label = lm.group('label')
        for j in range(i + 1, min(len(lines), i + max_span + 1)):
            im = IF_GOTO_RE.match(lines[j])
            if not im or im.group('label') != label:
                continue
            body = lines[i + 1:j]
            if not body:
                continue
            # Only do this when the body labels are local.
            all_refs = refs(lines)
            if not region_is_safe(i + 1, j, lines, all_refs):
                continue
            indent = lm.group('indent')
            cond = im.group('cond')
            structured = dream_structure_lines(body, max_span=max_span, _depth=1)
            repl = [f'{indent}do {{'] + indent_block(structured, indent) + [f'{indent}}} while ({cond});']
            return lines[:i] + repl + lines[j + 1:], True
    return lines, False


def rewrite_break_continue(lines: List[str]) -> Tuple[List[str], bool]:
    # Convert obvious goto-to-current-structured-loop-end/header after earlier
    # foreach rendering. Conservative: do not infer multi-level jumps here.
    out = list(lines)
    changed = False
    stack: List[Tuple[int, int]] = []
    pos = label_positions(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(' '))
        if (stripped.startswith('foreach ') or stripped.startswith('while ') or stripped.startswith('do ')) and stripped.endswith('{'):
            stack.append((indent, i))
            continue
        if stripped == '}':
            while stack and stack[-1][0] >= indent:
                stack.pop()
            continue
        if not stack:
            continue
        gm = GOTO_RE.match(line)
        im = IF_GOTO_RE.match(line)
        m = gm or im
        if not m:
            continue
        target = pos.get(m.group('label'))
        if target is None:
            continue
        loop_indent, loop_start = stack[-1]
        depth = 0
        close = None
        for j in range(loop_start, len(lines)):
            s = lines[j].strip()
            if s.endswith('{'):
                depth += 1
            elif s == '}':
                depth -= 1
                if depth == 0:
                    close = j
                    break
        if close is None:
            continue
        repl = None
        if target >= close:
            repl = 'break;'
        elif target <= loop_start + 1:
            repl = 'continue;'
        if repl is None:
            continue
        if im:
            out[i] = f"{im.group('indent')}if ({im.group('cond')}) {{ {repl} }}"
        else:
            out[i] = f"{gm.group('indent')}{repl}"
        return out, True
    return out, changed


def dream_structure_lines(lines: List[str], max_span: int = 10000, _depth: int = 0) -> List[str]:
    out = list(lines)
    max_rounds = 80 if _depth == 0 else 25
    for _ in range(max_rounds):
        changed = False
        for fn in (remove_noop_gotos, rewrite_break_continue, rewrite_if_else_permissive, rewrite_simple_if_permissive, rewrite_do_while_permissive, strip_unreferenced_labels):
            if fn in (rewrite_if_else_permissive, rewrite_simple_if_permissive, rewrite_do_while_permissive):
                out, changed = fn(out, max_span)  # type: ignore[misc]
            else:
                out, changed = fn(out)  # type: ignore[misc]
            if changed:
                break
        if not changed:
            break
    return out


def dream_structure_source(source: str, max_span: int = 10000) -> str:
    trailing = '\n' if source.endswith('\n') else ''
    return '\n'.join(dream_structure_lines(source.splitlines(), max_span=max_span)) + trailing
