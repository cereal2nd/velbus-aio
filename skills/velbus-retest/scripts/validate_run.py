#!/usr/bin/env python
"""Monitor a read_bus.py retest log for problems and verify the cache.

Usage:
    validate_run.py <run.log> [--cache-dir DIR]

Checks:
  * tracebacks         - "Traceback (most recent call last)" blocks
  * errors             - ERROR / CRITICAL log lines
  * exceptions         - lines that mention a raised/logged exception
  * cache correctness  - every "Module found:" address has a valid
                         {address}.json in the cache dir

Exit code 0 when clean, 1 when any issue is found, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Log format is "{asctime} {levelname:<9} {message}".
LEVEL_RE = re.compile(r"^\S+\s+(ERROR|CRITICAL)\b")
MODULE_FOUND_RE = re.compile(r"Module found:.*?address:(\d+)")
MODULE_NAME_RE = re.compile(r"Module found:\s*<([^ ]*)\s")
EXCEPTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b")


def read_lines(path: Path) -> list[str]:
    return path.read_text(errors="replace").splitlines()


def find_tracebacks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    i = 0
    while i < len(lines):
        if "Traceback (most recent call last)" in lines[i]:
            block = [lines[i]]
            i += 1
            # Traceback body lines are indented; the final line is the exception.
            while i < len(lines) and (
                lines[i].startswith((" ", "\t")) or lines[i].strip() == ""
            ):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])  # exception summary line
                i += 1
            blocks.append([b for b in block if b.strip()])
        else:
            i += 1
    return blocks


def find_errors(lines: list[str]) -> list[str]:
    return [ln for ln in lines if LEVEL_RE.match(ln)]


def find_exceptions(lines: list[str], error_lines: set[str]) -> list[str]:
    out = []
    for ln in lines:
        if ln in error_lines:
            continue
        if "Traceback (most recent call last)" in ln:
            continue
        if EXCEPTION_RE.search(ln) and (
            "raise" in ln.lower()
            or "exception" in ln.lower()
            or "Error" in ln
        ):
            out.append(ln)
    return out


def find_modules(lines: list[str]) -> dict[int, str]:
    """Map found module address -> name (from the 'Module found:' repr)."""
    found: dict[int, str] = {}
    for ln in lines:
        m = MODULE_FOUND_RE.search(ln)
        if not m:
            continue
        addr = int(m.group(1))
        name_m = MODULE_NAME_RE.search(ln)
        found[addr] = name_m.group(1) if name_m else "?"
    return found


def check_cache(addr: int, cache_dir: Path) -> str | None:
    """Return an error string if the cache file is missing/incorrect, else None."""
    cfile = cache_dir / f"{addr}.json"
    if not cfile.exists():
        return f"missing cache file {cfile}"
    try:
        data = json.loads(cfile.read_text())
    except (json.JSONDecodeError, ValueError) as exc:
        return f"corrupt json in {cfile}: {exc}"
    if not isinstance(data, dict):
        return f"cache {cfile} is not a dict"
    if "channels" not in data:
        return f"cache {cfile} missing 'channels' key"
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return f"cache {cfile} has empty/invalid 'name'"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(os.path.expanduser("~")) / ".velbuscache",
    )
    args = ap.parse_args()

    if not args.log.exists():
        print(f"ERROR: log not found: {args.log}", file=sys.stderr)
        return 2

    lines = read_lines(args.log)
    tracebacks = find_tracebacks(lines)
    errors = find_errors(lines)
    exceptions = find_exceptions(lines, set(errors))
    modules = find_modules(lines)

    cache_problems: list[str] = []
    for addr in sorted(modules):
        problem = check_cache(addr, args.cache_dir)
        if problem:
            cache_problems.append(f"[{addr}] {modules[addr]}: {problem}")

    print(f"=== validate: {args.log} ===")
    print(f"cache dir       : {args.cache_dir}")
    print(f"modules found   : {len(modules)}")
    print(f"tracebacks      : {len(tracebacks)}")
    print(f"error lines     : {len(errors)}")
    print(f"exception lines : {len(exceptions)}")
    print(f"cache problems  : {len(cache_problems)}")

    if tracebacks:
        print("\n--- TRACEBACKS ---")
        for i, blk in enumerate(tracebacks, 1):
            print(f"[traceback {i}]")
            print("\n".join(blk))
            print()

    if errors:
        print("\n--- ERROR / CRITICAL LINES ---")
        for ln in errors:
            print(ln)

    if exceptions:
        print("\n--- EXCEPTION LINES ---")
        for ln in exceptions:
            print(ln)

    if cache_problems:
        print("\n--- CACHE PROBLEMS ---")
        for p in cache_problems:
            print(p)

    clean = not (tracebacks or errors or exceptions or cache_problems)
    print("\nRESULT:", "CLEAN" if clean else "ISSUES FOUND")
    if clean and modules:
        print(f"All {len(modules)} found modules have a correct cache file.")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
