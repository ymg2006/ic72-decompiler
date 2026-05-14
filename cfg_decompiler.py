#!/usr/bin/env python3
"""CLI wrapper for the CFG-first PHP decompiler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from decompiler_core import decompile_file


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--focus", help="only decompile units whose name contains this text")
    ap.add_argument("--mode", choices=("structured", "labels"), default="structured")
    ap.add_argument("--main-as-function", action="store_true", help="wrap main into __decompiled_main__()")
    args = ap.parse_args()

    ir = json.loads(args.dump.read_text(encoding="utf-8"))
    php = decompile_file(ir, args.focus, args.mode, main_as_function=args.main_as_function)
    if args.output:
        args.output.write_text(php, encoding="utf-8", newline="\n")
    else:
        print(php)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
