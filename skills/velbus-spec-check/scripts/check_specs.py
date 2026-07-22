#!/usr/bin/env python
"""Cross-check velbusaio/module_spec/*.json against the published Velbus protocol.

Reads the extracted protocol produced by fetch_protocol.sh (default
/tmp/velbus_proto) and compares it against the repo's module specs and
command_registry.MODULE_DIRECTORY. It reports:

  ERRORS (authoritative from the protocol binary):
    * a MODULE_DIRECTORY module has no spec file
    * module-type byte in the PDF ("COMMAND_MODULE_TYPE") does not match the
      spec's hex id -- only when the PDF documents a single module

  REVIEW (candidate bugs; confirm against the PDF, some are protocol/README
  quirks rather than real spec bugs):
    * spec name (Type) differs from the README module table
    * a byte the module *transmits* ("... databytes to send") is absent from the
      merged CommandToClass (global.json + module spec) -- an undecodable frame
    * module-type / transmit checks on PDFs shared by several modules (the text
      cannot always be attributed to one module)

Only frames the module TRANSMITS need a CommandToClass mapping; commands it
RECEIVES ("... databytes received") are sent by the library and are ignored.

Usage:
    check_specs.py [--proto DIR] [--repo DIR] [--module HEX]

Exit code 0 when no ERRORS, 1 when any ERROR is found, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_MAX_UP_LEVELS = 6

# H'NN' command notation used throughout the manuals (quotes already normalised).
# Each command byte is preceded by a "DLC ... = N databytes to send/received" line
# that tells us whether the module transmits (must decode) or receives the frame.
COMMAND_RE = re.compile(
    r"databytes?\s+(to send|received)[^\n]*\n\s*"
    r"DATABYTE1\s*=\s*COMMAND_[A-Z0-9_]*\s*\(H'([0-9A-Fa-f]{2})'\)"
)
MODULE_TYPE_RE = re.compile(r"COMMAND_MODULE_TYPE\s*\(H'[0-9A-Fa-f]{2}'\)")
DATABYTE2_HEX_RE = re.compile(r"DATABYTE2\s*=\s*[^\n(]*\(H'([0-9A-Fa-f]{2})'\)")

# Command bytes handled outside CommandToClass (module-type frame is decoded by
# the scanner itself), so their absence from a spec is never a bug.
IGNORED_PDF_BYTES = {"FF"}


def locate(start: Path, *parts: str) -> Path | None:
    p = start
    for _ in range(_MAX_UP_LEVELS):
        candidate = p.joinpath(*parts)
        if candidate.exists():
            return candidate
        p = p.parent
    return None


def norm_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def parse_readme(readme: Path) -> tuple[dict[str, tuple[str, str | None]], list[str]]:
    """Return {hex: (name, pdf_filename)} and a list of duplicate hex ids."""
    rows: dict[str, tuple[str, str | None]] = {}
    dups: list[str] = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = re.search(r"\|\s*0x([0-9A-Fa-f]{2})\s*\|\s*([A-Za-z0-9\-/ ]+?)\s*\|", line)
        if not m:
            continue
        hex_id = m.group(1).upper()
        name = m.group(2).strip()
        pm = re.search(r"protocol[_%A-Za-z0-9]*\.pdf", line)
        pdf = pm.group(0).replace("%5F", "_") if pm else None
        if hex_id in rows:
            dups.append(hex_id)
        rows[hex_id] = (name, pdf)
    return rows, dups


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proto", type=Path, default=Path("/tmp/velbus_proto"))
    ap.add_argument("--repo", type=Path, default=None)
    ap.add_argument("--module", help="limit to one module (hex id, e.g. 1D)")
    args = ap.parse_args(argv)

    here = Path(__file__).resolve().parent
    repo = args.repo.resolve() if args.repo else None
    spec_dir = (
        (repo / "velbusaio" / "module_spec") if repo else locate(here, "velbusaio", "module_spec")
    )
    if not spec_dir or not spec_dir.is_dir():
        print("ERROR: could not find velbusaio/module_spec (use --repo)", file=sys.stderr)
        return 2
    repo_root = spec_dir.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from velbusaio.command_registry import MODULE_DIRECTORY  # noqa: E402
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot import MODULE_DIRECTORY: {exc}", file=sys.stderr)
        return 2

    readme = args.proto / "README.md"
    text_dir = args.proto / "text"
    if not readme.exists() or not text_dir.is_dir():
        print(
            f"ERROR: protocol not found in {args.proto}. Run fetch_protocol.sh first.",
            file=sys.stderr,
        )
        return 2

    readme_rows, dups = parse_readme(readme)
    global_ctc = set(load_json(spec_dir / "global.json").get("CommandToClass", {}))

    # How many modules share each PDF (combined manuals cover several modules).
    pdf_users: dict[str, int] = {}
    for _name, pdf in readme_rows.values():
        if pdf:
            pdf_users[pdf] = pdf_users.get(pdf, 0) + 1

    only = args.module.upper() if args.module else None

    errors: list[str] = []
    review: list[str] = []

    for mtype, mname in sorted(MODULE_DIRECTORY.items()):
        hex_id = f"{mtype:02X}"
        if only and hex_id != only:
            continue

        spec_path = spec_dir / f"{hex_id}.json"
        if not spec_path.exists():
            errors.append(f"[{hex_id}] {mname}: no spec file {hex_id}.json")
            continue
        spec = load_json(spec_path)
        spec_type = spec.get("Type", mname)

        readme_name = readme_rows.get(hex_id, (None, None))[0]
        pdf_name = readme_rows.get(hex_id, (None, None))[1]

        # Name cross-check against README (review: README has known typos).
        if readme_name and norm_name(readme_name) != norm_name(spec_type):
            review.append(
                f"[{hex_id}] name: spec Type={spec_type!r} vs README={readme_name!r}"
            )

        # Command / module-type checks need the extracted PDF text.
        if not pdf_name:
            review.append(f"[{hex_id}] {mname}: not listed in README (no PDF to check)")
            continue
        txt_path = text_dir / f"{Path(pdf_name).stem}.txt"
        if not txt_path.exists():
            review.append(f"[{hex_id}] {mname}: extracted text missing ({txt_path.name})")
            continue
        text = txt_path.read_text(encoding="utf-8")
        shared = pdf_users.get(pdf_name, 0) > 1

        # Module-type byte(s) declared in the protocol frame (authoritative for a
        # single-module PDF; ambiguous when the manual covers several modules).
        type_bytes: set[str] = set()
        for m in MODULE_TYPE_RE.finditer(text):
            tail = text[m.end() : m.end() + 200]
            b2 = DATABYTE2_HEX_RE.search(tail)
            if b2:
                type_bytes.add(b2.group(1).upper())
        if type_bytes and hex_id not in type_bytes:
            msg = (
                f"[{hex_id}] {mname}: protocol module-type byte(s) "
                f"{sorted(type_bytes)} do not include {hex_id}"
            )
            (review if shared else errors).append(
                msg + (" (shared PDF)" if shared else "")
            )

        # Transmit-command cross-check: every frame the module *sends* must be
        # decodable via the merged CommandToClass.
        transmit = {
            byte.upper()
            for direction, byte in COMMAND_RE.findall(text)
            if direction == "to send"
        } - IGNORED_PDF_BYTES
        merged = global_ctc | set(spec.get("CommandToClass", {}))
        missing = sorted(transmit - merged)
        if missing:
            tag = " (shared PDF; may belong to a sibling module)" if shared else ""
            review.append(
                f"[{hex_id}] {mname}: transmits but not in CommandToClass: "
                + ", ".join(missing)
                + tag
            )

    print("=== Velbus module_spec vs published protocol ===")
    print(f"proto dir  : {args.proto}")
    print(f"spec dir   : {spec_dir}")
    print(f"modules    : {len(MODULE_DIRECTORY)}")
    if dups:
        print(f"README duplicate ids (repo quirk): {sorted(set(dups))}")
    print(f"errors     : {len(errors)}")
    print(f"review     : {len(review)}")

    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(e)
    if review:
        print("\n--- REVIEW (confirm against the PDF) ---")
        for r in review:
            print(r)

    print("\nRESULT:", "ERRORS FOUND" if errors else "no hard errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
