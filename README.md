# PHP ionCube 7.2 Opcode Decompiler

Small Python decompiler for rebuilding readable PHP source from ionCube/PHP 7.2 opcode dump JSON files.

The tool takes an opcode dump, walks the PHP control flow, and renders a best-effort `.php` file. It is useful for code recovery, migration, auditing, or studying old encoded PHP modules when you have permission to work with the files.

## What It Does

- Reads opcode JSON dumps such as `contacts.opcodes.json`.
- Reconstructs PHP classes, methods, functions, conditionals, loops, calls, arrays, and common expressions.
- Outputs readable PHP such as `contacts_decoded.php`.
- Supports structured output by default, with a label-based fallback mode for harder control-flow cases.

## Requirements

- Python 3.10+ recommended
- Opcode dump produced from a PHP 7.2 / ionCube target

No external Python packages are required for the current scripts.

## Usage

Decode a full opcode dump:

```bash
python cfg_decompiler.py contacts.opcodes.json -o contacts_decoded.php
```

Decode only units whose name contains specific text:

```bash
python cfg_decompiler.py contacts.opcodes.json -o contacts_decoded.php --focus Contacts
```

Use label mode when structured reconstruction is not clean enough:

```bash
python cfg_decompiler.py contacts.opcodes.json -o contacts_decoded.php --mode labels
```

Print the decoded PHP to the terminal instead of writing a file:

```bash
python cfg_decompiler.py contacts.opcodes.json
```

## Project Layout

- `cfg_decompiler.py` - command-line entrypoint
- `decompiler_core/engine.py` - opcode/control-flow reconstruction logic
- `decompiler_core/render.py` - PHP rendering helpers
- `decompiler_core/utils.py` - shared helpers for names, literals, and formatting
- `*.opcodes.json` - input opcode dumps
- `*_decoded.php` - generated PHP output

## Notes

This is a best-effort decompiler, not a perfect source-code restore tool. The generated PHP should always be reviewed manually, especially around complex jumps, obfuscated variables, dynamic calls, and license/protection logic.

Use this only on code you own, maintain, or are authorized to analyze.
