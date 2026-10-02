#!/usr/bin/env python3
"""Convert text notes into files the NOTEVIEW calculator app can read.

Usage:
    python3 notes2ti.py NOTES_FOLDER_OR_FILES... [-o OUTPUT_DIR]

Every .txt / .md file becomes one note, titled after its file name.
The output folder gets NOTEIDX.py (the list of notes), one or more
N<note><part>.py files per note, and a copy of NOTEVIEW.py. Send all of
them to the calculator with TI Connect CE.
"""

import argparse
import os
import re
import shutil
import sys
import textwrap
import unicodedata

WIDTH = 31        # characters per line on the calculator screen
CHUNK = 120       # lines per N*.py file (keeps each import small)
MAX_NOTES = 999   # note ids are 3 digits
MAX_CHUNKS = 100  # part ids are 2 digits
EXTS = (".txt", ".md", ".text")

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.join(HERE, "..", "calculator", "NOTEVIEW.py")

# Common non-ASCII characters and their closest ASCII spelling.
REPLACE = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "′": "'", "″": '"',
    "–": "-", "—": "--", "―": "--", "−": "-",
    "…": "...", "•": "*", "·": "*", "●": "*", "◦": "o",
    " ": " ", " ": " ", "​": "",
    "×": "x", "÷": "/", "±": "+/-", "≠": "!=",
    "≤": "<=", "≥": ">=", "≈": "~=", "∞": "inf",
    "→": "->", "←": "<-", "↔": "<->", "⇒": "=>",
    "°": " deg", "²": "^2", "³": "^3", "√": "sqrt",
    "π": "pi", "θ": "theta", "Δ": "delta", "δ": "delta",
    "Σ": "sum", "μ": "u", "α": "alpha", "β": "beta",
    "λ": "lambda", "σ": "sigma", "Ω": "ohm", "ω": "omega",
}


def to_ascii(text):
    out = []
    for ch in text:
        if ch in REPLACE:
            out.append(REPLACE[ch])
        elif ch == "\t":
            out.append("  ")
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            base = unicodedata.normalize("NFKD", ch)
            base = "".join(c for c in base if 32 <= ord(c) < 127)
            out.append(base or "?")
    return "".join(out)


def wrap(text, width=WIDTH):
    """Wrap text to the screen width, keeping blank lines and indents."""
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        raw = to_ascii(raw).rstrip()
        if not raw:
            lines.append("")
            continue
        indent = raw[: len(raw) - len(raw.lstrip())][: width // 3]
        # Hanging indent for list items so wrapped lines line up.
        m = re.match(r"\s*([-*+]|\d+[.)])\s+", raw)
        hang = " " * min(len(m.group(0)), width // 3) if m else indent
        lines.extend(
            textwrap.wrap(
                raw.strip(),
                width=width,
                initial_indent=indent,
                subsequent_indent=hang,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
        )
    while lines and not lines[-1]:
        lines.pop()
    return lines


def title_for(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return to_ascii(name.replace("_", " ")).strip() or "untitled"


def collect(inputs):
    files = []
    for p in inputs:
        if os.path.isdir(p):
            for name in sorted(os.listdir(p), key=str.lower):
                full = os.path.join(p, name)
                if os.path.isfile(full) and name.lower().endswith(EXTS):
                    files.append(full)
        elif os.path.isfile(p):
            files.append(p)
        else:
            sys.exit("not found: " + p)
    return files


def py_tuple(items):
    if not items:
        return "()"
    return "(\n" + "".join(repr(s) + ",\n" for s in items) + ")"


def build(notes, width=WIDTH, chunk=CHUNK):
    """notes: list of (title, text). Returns {filename: file contents}."""
    if len(notes) > MAX_NOTES:
        raise ValueError("too many notes (max %d)" % MAX_NOTES)
    files = {}
    index = []
    for nid, (title, text) in enumerate(notes, 1):
        lines = wrap(text, width)
        parts = [lines[i:i + chunk] for i in range(0, len(lines), chunk)]
        if len(parts) > MAX_CHUNKS:
            raise ValueError("note %r is too long (max %d lines)"
                             % (title, MAX_CHUNKS * chunk))
        for c, part in enumerate(parts):
            files["N%03d%02d.py" % (nid, c)] = "L=" + py_tuple(part) + "\n"
        index.append((title[:40], nid, len(lines)))
    files["NOTEIDX.py"] = "C=%d\nN=%s\n" % (chunk, py_tuple(index))
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("inputs", nargs="+", help="note files or folders")
    ap.add_argument("-o", "--out", default="ti_notes", help="output folder")
    ap.add_argument("--width", type=int, default=WIDTH)
    ap.add_argument("--chunk", type=int, default=CHUNK,
                    help="lines per calculator file")
    args = ap.parse_args(argv)

    paths = collect(args.inputs)
    if not paths:
        sys.exit("no .txt or .md notes found")
    notes = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            notes.append((title_for(p), f.read()))

    try:
        files = build(notes, args.width, args.chunk)
    except ValueError as e:
        sys.exit(str(e))

    os.makedirs(args.out, exist_ok=True)
    for old in os.listdir(args.out):
        if re.fullmatch(r"N\d{5}\.py|NOTEIDX\.py", old):
            os.remove(os.path.join(args.out, old))
    for name, body in files.items():
        with open(os.path.join(args.out, name), "w", encoding="ascii",
                  newline="\n") as f:
            f.write(body)
    if os.path.exists(VIEWER):
        shutil.copy(VIEWER, os.path.join(args.out, "NOTEVIEW.py"))

    for title, _ in notes:
        print("  " + title)
    print("%d notes -> %d files in %s/" % (len(notes), len(files), args.out))
    print("Send every .py file in that folder with TI Connect CE,")
    print("then run NOTEVIEW from the calculator's Python app.")


if __name__ == "__main__":
    main()
