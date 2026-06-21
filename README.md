# PHP ionCube 7.2 Opcode Decompiler

This is a runnable, self-contained repair build for `dawwinci/ic72-decompiler` style opcode JSON dumps.

## What changed

- Added a complete PHP 7.2.34 Zend VM opcode table from `Zend/zend_vm_opcodes.h` / `zend_vm_opcodes.c`.
- Added explicit best-effort handling or safe fallback comments for every PHP 7.2 opcode ID/name from 0 through `ZEND_VM_LAST_OPCODE` 197.
- Added handlers for commonly missing PHP 7.2 opcodes such as static property fetches, class constants, coalesce, spaceship, pow, yield/yield-from, dynamic calls, isset/empty variants, foreach helpers, switch helpers, closure/bind helpers, generator helpers, and object/dim assignment helpers.
- Fixed the CLI indentation/write path so `-o` works.
- Replaced the weak formatter path with a Python-side formatter pipeline:
  - default `--formatter phply` uses the `phply` Python lexer first, then the bundled formatter
  - `--formatter python` uses only the bundled pure-Python formatter
  - `--formatter none` or `--no-format` keeps raw renderer output
- Added smoke tests that prove all official PHP 7.2 opcodes are known by the decompiler.

## Install optional Python formatter dependency

The project includes a fallback formatter, but the default formatter path expects `phply`, the main Python PHP lexer/parser package:

```bash
python -m pip install -r requirements.txt
```

No PHP, Composer, Node, or Prettier dependency is required for the Python formatter path.


## Windows portable bundle

This package includes `decompile.bat`, `setup_embedded_python.bat`, and vendored Python dependencies under `vendor/`:

- `phply` 1.2.6
- `ply` 3.11

Run on Windows with:

```bat
decompile.bat accessdenied.opcodes.json -o accessdenied.php
```

The launcher uses `python\python.exe` first if present, then falls back to `py -3` or `python` on PATH. See `PORTABLE_WINDOWS_README.md` for making the bundle fully portable with the official Windows embeddable Python runtime.

## Usage

```bash
python cfg_decompiler.py contacts.opcodes.json -o contacts_decoded.php
python cfg_decompiler.py contacts.opcodes.json -o contacts_decoded.php --formatter phply
python cfg_decompiler.py contacts.opcodes.json -o contacts_decoded.php --formatter python
python cfg_decompiler.py contacts.opcodes.json --focus Contacts --mode labels
python cfg_decompiler.py contacts.opcodes.json --main-as-function
python cfg_decompiler.py contacts.opcodes.json --no-format  # keep raw decompiler output
```

The output is best-effort PHP and is formatted by default. Complex jumps, obfuscated expressions, and ionCube-specific dump quirks may still need manual review. Use `--no-format` to preserve the raw renderer output.

## Validation

```bash
python -m compileall .
python tests/smoke_test.py
python cfg_decompiler.py accessdenied.opcodes.json -o accessdenied_formatted_phply.php --formatter phply
```

### PHP 7.2 calendar opcode fixes

This build includes reconstruction for PHP 7.2 closure opcodes (`ZEND_DECLARE_LAMBDA_FUNCTION`, `ZEND_BIND_LEXICAL`, and `ZEND_BIND_STATIC`) and array append writes. These are needed for files such as `admin/calendar.php` that compile anonymous functions with `use (...)` variables.

### Foreach reconstruction update

This build reconstructs common PHP 7.2 `ZEND_FE_RESET_R` / `ZEND_FE_FETCH_R` / `ZEND_FE_FREE` loops as source-level `foreach (...) { ... }` blocks, including the closing brace. It also suppresses the VM loop-back jump before `ZEND_FE_FREE`, so generated output no longer contains `foreach helper` / `endforeach` comments for supported foreach patterns.

### Latest opcode/goto recovery update

This build adds handlers for additional PHP 7.x opcodes that previously appeared as
`/* unsupported ZEND_* */` comments in generated output:

- `ZEND_CATCH`
- `ZEND_FETCH_LIST`
- `ZEND_BEGIN_SILENCE` / `ZEND_END_SILENCE`
- `ZEND_BIND_GLOBAL`
- `ZEND_FETCH_CLASS_NAME`
- `ZEND_SEPARATE`
- `ZEND_IN_ARRAY`
- `ZEND_GENERATOR_CREATE`
- `ZEND_MAKE_REF`

It also adds a conservative goto structuring pass. Simple forward conditional
jumps are rewritten to `if (...) { ... }` blocks when the target block is local
and has no nested labels/gotos. Ambiguous VM control-flow is intentionally kept
as labels/gotos so the output stays traceable instead of silently producing wrong
PHP.

### Goto structuring notes

This build adds a stronger safe control-flow structuring pass. It rewrites recognized VM goto idioms into source-level PHP constructs:

- `if (...) goto Lelse; ... goto Lend; Lelse: ... Lend:` becomes `if (...) { ... } else { ... }`
- `if (...) goto Lend; ... Lend:` becomes a guarded `if` block
- simple backward conditional jumps become `do { ... } while (...)`
- no-op gotos and unreferenced labels are removed

The pass is intentionally conservative. It keeps ambiguous jumps when converting them could change behavior, especially obfuscated jumps, exception edges, switch dispatch, or jumps crossing foreach/try boundaries. Use `--mode labels --formatter none` when you need the raw VM trace.

### CFG/goto structuring notes

This build includes `decompiler_core/cfg_structurer.py` and an enhanced `goto_structurer.py` pass. The pass builds a source-level CFG with basic blocks, successor/predecessor edges, dominators, and post-dominators before applying safe rewrites. It also normalizes loop-control jumps inside recovered foreach blocks into `break`/`continue` where the target matches the loop exit or fetch/header.

The decompiler still preserves any jump that is irreducible or whose target is unsafe/ambiguous in the ionCube dump. This is intentional: a remaining `goto` is preferable to silently changing behavior.


### DREAM-style readable structuring mode

This build adds a best-readable `dream` mode and makes it the CLI default. It is a conservative region-structuring pass inspired by DREAM-style decompilers: it structures provable `if`, `else`, `elseif`, local loops, and obvious `break`/`continue`, while preserving labels/gotos only when a jump cannot safely be proven as structured source.

The decompiler now prefers the fixed dumper CFG fields when present:

- `jump_target_index`
- `jump_targets[].target_index`
- `false_target_index` / `true_target_index`
- `fe_reset_done_target_index` / `fe_fetch_done_target_index`
- `jmpznz_true_target_index` / `extended.jump_target_index`

Usage:

```bash
python cfg_decompiler.py input.opcodes.json -o output.php --mode dream --formatter python
```

For old dumps that only contain overloaded `opline_num` / integer `jump_targets`, the decompiler still falls back to the legacy labels. Those dumps can be structurally ambiguous because the numbers may not be real opcode indexes. For best output, generate fresh dumps with the fixed opcodedump extension that exports explicit `*_target_index` fields.

## Opcode-level AST/CFG project mode

This build includes the first opcode-level CFG/AST implementation layer. It does **not** pretend every ionCube control-flow graph can already be rendered as clean `if/else` PHP. Instead it does the reliable architecture first and keeps labels/gotos only for unresolved regions.

New modules:

```text
Decompiler pipeline modules:
  decompiler_core/ir.py                 opcode -> IRInstruction
  decompiler_core/op_cfg.py             IR -> basic blocks + CFG edges
  decompiler_core/ast_nodes.py          PHP AST node data classes
  decompiler_core/exception_regions.py  try/catch table recovery helpers
  decompiler_core/action_dispatch.py    $action dispatcher detection helpers
  decompiler_core/php_renderer.py       AST node renderer
  decompiler_core/structurer.py         CFG/AST bridge + reliable fallback
```

Recommended reliable command:

```bat
python cfg_decompiler.py supporttickets.opcodes.json -o supporttickets.php --mode ast-labels --formatter none --cfg-report
```

Readable experimental command:

```bat
python cfg_decompiler.py supporttickets.opcodes.json -o supporttickets_readable.php --mode ast --formatter python --cfg-report
```

For large WHMCS controller files, `ast-labels` is the safe mode. It builds opcode IR and CFG, recovers exception regions, and then renders a conservative fallback that keeps ambiguous branches as labels/gotos. The `ast` mode tries old local structuring too, but it can still create illegal PHP if a jump crosses a loop/switch boundary.

The next intended work is to replace fallback regions one at a time:

```text
exact JSON -> IR -> CFG -> exception regions -> action dispatcher -> if/else regions -> loop regions -> fallback labels only for unresolved regions
```

Do not remove the fallback renderer. A decompiler must keep a valid representation for irreducible or obfuscated control flow.
