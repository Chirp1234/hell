# NOTEVIEW: notes on the TI-84 Plus CE Python

Read your own notes on a TI-84 Plus CE Python calculator.

- `calculator/NOTEVIEW.py` is the reader app that runs on the calculator.
- `converter/converter.html` turns `.txt` / `.md` files into notes in your browser. It needs no install.
- `converter/notes2ti.py` does the same conversion from the command line.

## How it works

The calculator's Python can't open arbitrary files, but it can `import` other
`.py` files stored on the calculator. The converter word-wraps each note to the
31-column screen and saves it as small Python data files:

| File | Contents |
| --- | --- |
| `NOTEIDX.py` | The list of notes (title, number, line count) |
| `N00100.py`, `N00101.py`, … | Note 1, 120 lines per file |
| `N00200.py`, … | Note 2, and so on |

NOTEVIEW imports only the part of a note that is on screen, so long notes don't
run the calculator out of memory.

## Uploading notes

1. Put each note in its own `.txt` or `.md` file. The file name becomes the
   note title (`Bio_Ch3.txt` shows as "Bio Ch3").
2. Convert them using one of these:
   - **Browser:** open `converter/converter.html`, drop in your files, then click
     **Download ti_notes.zip** and unzip it.
   - **Command line:** `python3 converter/notes2ti.py my_notes/ -o ti_notes`
3. Open **TI Connect CE**, connect the calculator, and drag **every `.py` file**
   from the output folder onto it. That includes NOTEVIEW.py the first time.
4. To add or change notes later, convert the **whole** set again and resend
   `NOTEIDX.py` plus the `N*.py` files. Notes are numbered by file name order,
   so the index must match the note files.

## Reading notes

On the calculator: `[prgm]` → Python App → choose **NOTEVIEW** → Run.

| Key | Note list | Inside a note |
| --- | --- | --- |
| up / down | choose a note | scroll one line |
| left / right | right opens the note | previous / next page |
| enter | open note | next page |
| clear | quit | back to the list |

Non-ASCII characters are converted to ASCII. For example, “quotes” become "quotes",
π becomes `pi`, x² becomes `x^2`, and é becomes `e`.

## Limits

- Up to 999 notes, and 12,000 wrapped lines per note.
- If you delete notes, old `N*.py` files can stay on the calculator. They're
  harmless, but you can delete them in `[2nd][mem]` → Mem Management → AppVars.

## Development

```
python3 -m unittest discover tests     # converter + viewer (fake ti_system)
python3 converter/sync_html.py         # after editing NOTEVIEW.py
```

The tests run NOTEVIEW under desktop Python with a fake `ti_system` module. They
also check that the browser converter's output is byte-identical to `notes2ti.py`.
