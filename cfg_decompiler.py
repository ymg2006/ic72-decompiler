#!/usr/bin/env python3
"""CLI wrapper for the PHP 7.2 opcode JSON decompiler."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
if VENDOR.is_dir():
    sys.path.insert(0, str(VENDOR))

from decompiler_core import decompile_file
from decompiler_core.cfg_targets import target_quality_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Decompile PHP 7.2/ionCube opcode dump JSON to best-effort PHP")
    parser.add_argument("dump", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--focus", help="only decompile units whose name contains this text")
    parser.add_argument("--mode", choices=("structured", "dream", "labels", "ast", "ast-labels", "ast-clean-draft", "ast-zero-goto-verified"), default="dream", help="decompilation mode; ast/ast-labels build opcode CFG first; ast-zero-goto-verified emits no gotos and converts supported placeholders into PHP")
    parser.add_argument("--main-as-function", action="store_true", help="wrap main into __decompiled_main__()")
    parser.add_argument("--no-format", action="store_true", help="disable output formatter")
    parser.add_argument("--formatter", choices=("phply", "python", "none"), default="phply", help="output formatter: phply uses the Python phply lexer plus bundled formatter; python uses only the bundled formatter; none disables formatting")
    parser.add_argument("--max-line-length", type=int, default=120, help="formatter target line length")
    parser.add_argument("--cfg-report", action="store_true", help="print CFG target quality report to stderr")
    args = parser.parse_args()

    ir = json.loads(args.dump.read_text(encoding="utf-8"))
    if args.cfg_report:
        print(target_quality_report(ir), file=sys.stderr)
    php = decompile_file(
        ir,
        args.focus,
        args.mode,
        main_as_function=args.main_as_function,
        format_output=not args.no_format,
        max_line_length=args.max_line_length,
        formatter=("none" if args.no_format else args.formatter),
    )
    if args.output:
        args.output.write_text(php, encoding="utf-8", newline="\n")
    else:
        print(php, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
