---
name: velbus-spec-check
description: Cross-check velbusaio/module_spec/*.json against the published Velbus protocol manuals from github.com/velbus/moduleprotocol. Fetches the protocol PDFs, extracts their text, and reports module-id/name mismatches and transmitted command bytes that are missing from a module's CommandToClass. Use when asked to verify the module specs against the Velbus module protocol, check for bugs in module_spec, or build/compare specs from the moduleprotocol repo.
disable-model-invocation: true
---

# Velbus module_spec protocol check

Compares the repo's `velbusaio/module_spec/*.json` against the module protocol
Velbus publishes at https://github.com/velbus/moduleprotocol, to surface likely
bugs in the specs.

## What it checks

The ground truth is the protocol repo: its `README.md` (module id -> name table,
one PDF per module) and the command tables inside each PDF. Command bytes are
written as `H'NN'`, and each is preceded by a `DLC ... = N databytes to send`
(module transmits -> must be decodable) or `... received` (module receives ->
the library sends it, no decoding needed) line.

- **module-id byte**: the `COMMAND_MODULE_TYPE` frame in the PDF must include the
  spec's hex id. Authoritative for single-module PDFs; ambiguous (review only)
  for manuals that cover several modules.
- **transmit coverage**: every byte the module _transmits_ must appear in the
  merged `CommandToClass` (`global.json` + the module spec). A transmitted frame
  with no mapping is an undecodable message.
- **name**: spec `Type` vs the README name (the README has known typos, so this
  is review-only).

Only transmitted frames need a `CommandToClass` entry. Received/config frames
(clock, memory, sensor-settings such as `AB`, `AE`, `C0`-`C8`, ...) are commonly
absent by design and are not bugs.

## Workflow

```
- [ ] Step 0: Choose the Python venv (VELBUS_VENV)
- [ ] Step 1: Fetch + extract the protocol (scripts/fetch_protocol.sh)
- [ ] Step 2: Run the checker (scripts/check_specs.py)
- [ ] Step 3: Confirm each finding against the PDF before changing a spec
```

### Step 0: Choose the Python venv

The venv is **not hardcoded**. Ask the user for it (or reuse an already-activated
one) and pass its root via the `VELBUS_VENV` environment variable. `fetch_protocol.sh` resolves the interpreter
in this order: `VELBUS_VENV/bin/python` → `VELBUS_PY` → `VIRTUAL_ENV/bin/python` →
`python3`. The `check_specs.py` / `extract_pdf.py` commands below run with
`"$VELBUS_VENV/bin/python"`, so export it once for the session.

### Step 1: Fetch and extract

```bash
VELBUS_VENV="/path/to/venv" skills/velbus-spec-check/scripts/fetch_protocol.sh
```

This shallow-clones (or refreshes) the repo into `/tmp/velbus_proto`, ensures
`pypdf` is in the chosen venv, and extracts every PDF to
`/tmp/velbus_proto/text/<stem>.txt`. Extracting ~80 PDFs is slow on this host
(~15 min) — background it with a generous `block_until_ms` (e.g. `900000`) or
poll `/tmp/velbus_proto/text`. Re-running reuses the clone; the text files are
cached, so Step 2 is instant afterwards.

### Step 2: Check the specs

```bash
"$VELBUS_VENV/bin/python" skills/velbus-spec-check/scripts/check_specs.py
```

Options: `--module 1D` (one module only), `--proto DIR` (protocol dir, default
`/tmp/velbus_proto`), `--repo DIR` (repo root; auto-detected from the script
location otherwise).

Output has two sections:

- **ERRORS** — a missing spec file, or a single-module PDF whose module-type byte
  does not match the spec id. Exit code is non-zero when any error is present.
- **REVIEW** — candidate bugs to confirm against the PDF: transmitted bytes
  absent from `CommandToClass`, name diffs, shared-PDF ambiguities, and modules
  with no published PDF.

### Step 3: Confirm before editing

REVIEW items are candidates, not confirmed bugs. For each one, read the relevant
PDF text and decide:

```bash
"$VELBUS_VENV/bin/python" skills/velbus-spec-check/scripts/extract_pdf.py \
    /tmp/velbus_proto/protocol_<module>.pdf | less
```

A transmit byte is a real bug only if it is a frame the library should decode
(e.g. a status message) but has no `CommandToClass` entry. Ignore programming,
memory, clock and sensor-configuration frames. When a spec is genuinely wrong,
fix `velbusaio/module_spec/<hex>.json` and re-run Step 2 to confirm it clears.

## Notes

- Combined manuals (e.g. `vmbgp1_2_4.pdf` covers GP1/GP2/GP4) only spell out one
  module's type byte and mix every sibling's commands, so those findings are
  flagged `(shared PDF)` and reported as review, not errors.
- Some modules (e.g. `VMB1RYS-20`, `VMB6PBB`, `VMB1BLE`) have no published PDF;
  they are reported as "not listed in README" and cannot be command-checked.
- The README has real quirks the checker reports verbatim: a duplicated `0x5C`
  row and a `VMBBEL1PIR-20` typo (spec `Type` is `VMBEL1PIR-20`).
