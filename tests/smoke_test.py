from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from decompiler_core import ALL_OPCODE_NAMES, OPCODE_ID_TO_NAME, decompile_file, format_php_source, format_php_source_with_phply


def main() -> int:
    assert len(OPCODE_ID_TO_NAME) == 196, len(OPCODE_ID_TO_NAME)
    assert "ZEND_FETCH_STATIC_PROP_FUNC_ARG" in ALL_OPCODE_NAMES
    assert "ZEND_ISSET_ISEMPTY_CV" in ALL_OPCODE_NAMES
    sample = {
        "op_arrays": {
            "main": {
                "opcodes": [
                    {"opcode_name": "ZEND_ASSIGN", "op1": {"type_name": "IS_CV", "var": 0, "cv_name": "a"}, "op2": {"type_name": "IS_CONST", "literal": 1}},
                    {"opcode_name": "ZEND_ASSIGN", "op1": {"type_name": "IS_CV", "var": 1, "cv_name": "b"}, "op2": {"type_name": "IS_CONST", "literal": 2}},
                    {"opcode_name": "ZEND_ADD", "op1": {"type_name": "IS_CV", "var": 0, "cv_name": "a"}, "op2": {"type_name": "IS_CV", "var": 1, "cv_name": "b"}, "result": {"type_name": "IS_TMP_VAR", "var": 2}},
                    {"opcode_name": "ZEND_ECHO", "op1": {"type_name": "IS_TMP_VAR", "var": 2}},
                    {"opcode_name": "ZEND_RETURN", "op1": {"type_name": "IS_CONST", "literal": 1}},
                ]
            }
        }
    }
    out = decompile_file(sample)
    assert "$a = 1;" in out
    assert "echo ($a + $b);" in out
    assert out.endswith("\n")

    messy = "<?php\nfunction demo() {\n$a = 1;\nif ($a) {\necho $a;\n}\n}\n"
    formatted = format_php_source_with_phply(messy)
    assert "function demo() {\n    $a = 1;" in formatted
    assert "    if ($a) {\n        echo $a;\n    }" in formatted
    phply_out = decompile_file(sample, formatter="phply")
    assert "echo ($a + $b);" in phply_out
    print("smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
