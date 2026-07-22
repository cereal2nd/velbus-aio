#!/usr/bin/env python
"""Extract text from Velbus protocol PDFs using pypdf.

Usage:
    extract_pdf.py <file.pdf>                 # print one PDF's text to stdout
    extract_pdf.py --all <pdf_dir> <out_dir>  # extract every *.pdf into out_dir/<stem>.txt

Curly quotes are normalised to straight quotes so downstream regexes can rely on
the H'NN' command-byte notation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pypdf
except ImportError:  # pragma: no cover - surfaced to the user by fetch_protocol.sh
    print(
        "ERROR: pypdf is not installed. Run: pip install pypdf",
        file=sys.stderr,
    )
    raise SystemExit(2)


def extract(pdf: Path) -> str:
    reader = pypdf.PdfReader(str(pdf))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text.replace("\u2019", "'").replace("\u2018", "'")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="batch-extract a directory")
    ap.add_argument("src", type=Path, help="pdf file, or pdf dir with --all")
    ap.add_argument("out", type=Path, nargs="?", help="output dir (with --all)")
    args = ap.parse_args(argv)

    if args.all:
        if args.out is None:
            print("ERROR: --all requires an output dir", file=sys.stderr)
            return 2
        args.out.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(args.src.glob("*.pdf"))
        if not pdfs:
            print(f"ERROR: no PDFs found in {args.src}", file=sys.stderr)
            return 2
        ok = 0
        for pdf in pdfs:
            try:
                (args.out / f"{pdf.stem}.txt").write_text(extract(pdf), encoding="utf-8")
                ok += 1
            except Exception as exc:  # noqa: BLE001 - keep going, report at end
                print(f"WARN: failed to extract {pdf.name}: {exc}", file=sys.stderr)
        print(f"extracted {ok}/{len(pdfs)} PDFs into {args.out}")
        return 0 if ok else 1

    if not args.src.exists():
        print(f"ERROR: not found: {args.src}", file=sys.stderr)
        return 2
    print(extract(args.src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
