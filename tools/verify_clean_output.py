#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8', errors='replace')
checks = {
    'goto': re.findall(r'^\s*(?:if\s*\(.+\)\s*)?goto\s+L\d+;', s, flags=re.M),
    'labels': re.findall(r'^\s*L\d+:\s*$', s, flags=re.M),
    'foreach_placeholders': re.findall(r'/\*\s*(?:foreach over|foreach value|endforeach)\b.*?\*/', s),
    'switch_placeholders': re.findall(r'/\*\s*switch on\b.*?\*/', s),
    'synthetic_placeholders': re.findall(r'/\*\s*synthetic labels\b.*?\*/', s),
}
bad = {k:v for k,v in checks.items() if v}
if bad:
    for k,v in bad.items():
        print(f'FAIL {k}: {len(v)}')
    sys.exit(1)
print(f'OK clean: no goto, no labels, no foreach/switch placeholder comments in {p}')
