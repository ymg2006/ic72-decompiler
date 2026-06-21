#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path

GOTO = re.compile(r'\bgoto\b')
LABEL = re.compile(r'^\s*L\d+:\s*$')

def main() -> int:
    if len(sys.argv) != 2:
        print('usage: verify_no_goto.py <file.php>', file=sys.stderr)
        return 2
    p = Path(sys.argv[1])
    text = p.read_text(encoding='utf-8', errors='replace')
    bad=[]
    for i,line in enumerate(text.splitlines(),1):
        if GOTO.search(line) or LABEL.match(line):
            bad.append((i,line))
    if bad:
        print(f'FAILED: {len(bad)} goto/label lines remain in {p}', file=sys.stderr)
        for i,line in bad[:50]:
            print(f'{i}: {line}', file=sys.stderr)
        return 1
    print(f'OK: 0 goto/label lines in {p}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
