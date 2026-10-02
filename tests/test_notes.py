"""Runs the converter, then drives NOTEVIEW.py with a fake ti_system module.

    python3 -m unittest discover tests
"""

import io
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "converter"))
import notes2ti  # noqa: E402

VIEWER = os.path.join(ROOT, "calculator", "NOTEVIEW.py")
RIGHT, LEFT, UP, DOWN, ENTER, CLEAR = 1, 2, 3, 4, 5, 9


def run_viewer(folder, keys):
    """Run NOTEVIEW on the files in folder, pressing keys.

    Returns the screens drawn, before the final clear-screen on exit."""
    presses = iter(keys + [CLEAR] * 5)
    ti = types.ModuleType("ti_system")
    ti.wait_key = lambda: next(presses)
    ti.disp_clr = lambda: print("\f", end="")
    sys.modules["ti_system"] = ti
    for name in list(sys.modules):
        if name == "NOTEIDX" or (name.startswith("N0") and len(name) == 6):
            del sys.modules[name]
    sys.path.insert(0, folder)
    with open(VIEWER) as f:
        code = compile(f.read(), VIEWER, "exec")
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            exec(code,
                 {"__name__": "__main__"})
    finally:
        sys.path.remove(folder)
        del sys.modules["ti_system"]
    return [x for x in out.getvalue().split("\f") if x]


def last_page(screens):
    """The last screen drawn by the note reader (not the menu)."""
    return [x for x in screens if not x.startswith("NOTES (")][-1]


def write(folder, notes, **kw):
    for name, body in notes2ti.build(notes, **kw).items():
        with open(os.path.join(folder, name), "w") as f:
            f.write(body)


class ConverterTest(unittest.TestCase):
    def test_wrap_width_and_blank_lines(self):
        lines = notes2ti.wrap("word " * 40 + "\n\n- item " + "x" * 50)
        self.assertTrue(all(len(s) <= notes2ti.WIDTH for s in lines))
        self.assertIn("", lines)
        self.assertTrue(lines[-1].startswith("  "))  # hanging indent

    def test_unicode_to_ascii(self):
        self.assertEqual(notes2ti.to_ascii("“pi” ≈ 3.14 → café"),
                         '"pi" ~= 3.14 -> cafe')

    def test_files_are_valid_python(self):
        files = notes2ti.build([("A", "x\n" * 300), ("B", "it's \"q\" \\")],
                               chunk=120)
        self.assertEqual(sorted(files), ["N00100.py", "N00101.py", "N00102.py",
                                         "N00200.py", "NOTEIDX.py"])
        for body in files.values():
            body.encode("ascii")
            compile(body, "f", "exec")
        g = {}
        exec(files["NOTEIDX.py"], g)
        self.assertEqual(g["N"], (("A", 1, 300), ("B", 2, 1)))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "in")
            os.mkdir(src)
            with open(os.path.join(src, "Bio_Ch1.txt"), "w") as f:
                f.write("cells")
            out = os.path.join(d, "out")
            with redirect_stdout(io.StringIO()):
                notes2ti.main([src, "-o", out])
            self.assertEqual(sorted(os.listdir(out)),
                             ["N00100.py", "NOTEIDX.py", "NOTEVIEW.py"])


class ViewerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        body = "\n".join("line %d" % i for i in range(1, 301))
        write(self.dir, [("Alpha", "hello world"), ("Beta", body)], chunk=50)

    def tearDown(self):
        self.tmp.cleanup()

    def test_menu_lists_notes(self):
        screen = run_viewer(self.dir, [])[0]
        self.assertEqual(screen.splitlines()[:3],
                         ["NOTES (2)", "> Alpha", "  Beta"])

    def test_open_and_scroll_across_chunks(self):
        # select Beta, open, page down 6 times (crosses 50-line parts)
        screens = run_viewer(self.dir, [DOWN, ENTER] + [RIGHT] * 6
                             + [DOWN, UP, UP])
        self.assertEqual(last_page(screens).splitlines(),
                         ["Beta"] + ["line %d" % i for i in range(48, 56)]
                         + ["48-55/300  clear:back"])
        self.assertFalse(any("missing" in x for x in screens))

    def test_scroll_clamps_at_ends(self):
        screens = run_viewer(self.dir, [DOWN, ENTER] + [RIGHT] * 100)
        self.assertEqual(last_page(screens).splitlines()[1], "line 293")
        screens = run_viewer(self.dir, [DOWN, ENTER, UP, LEFT])
        self.assertTrue(last_page(screens).endswith("1-8/300  clear:back"))

    def test_back_to_menu_then_open_other(self):
        screens = run_viewer(self.dir, [DOWN, ENTER, CLEAR, UP, RIGHT])
        self.assertTrue(last_page(screens).startswith("Alpha\nhello world\n"))

    def test_every_screen_fits(self):
        screens = run_viewer(self.dir, [ENTER, CLEAR, DOWN, ENTER, RIGHT])
        for screen in screens:
            lines = screen.split("\n")
            self.assertEqual(len(lines), 10)  # title, 8 rows, footer
            self.assertTrue(all(len(x) <= 31 for x in lines))

    def test_missing_index(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("No notes found", run_viewer(d, [])[0])


if __name__ == "__main__":
    unittest.main()
