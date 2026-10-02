"""Checks converter.html's JavaScript (run in Node) matches notes2ti.py."""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "converter"))
import notes2ti  # noqa: E402
import sync_html  # noqa: E402

HTML = os.path.join(ROOT, "converter", "converter.html")

NOTES = [
    ["Chem Unit 2", "Moles\n\n- 1 mol = 6.022e23 particles and some more words "
     "to wrap around\n  1. indented item with a fairly long description\n"
     "“quoted” → arrow, café, x², πr²\n"
     "it's \"both\" \\ back\n" + "W" * 80 + "\n\n\n"],
    ["Empty", ""],
    ["Long", "\n".join("row %d of the long note" % i for i in range(260))],
]

JS = r"""
const fs = require("fs");
const html = fs.readFileSync(process.argv[1], "utf8");
eval(html.match(/<script id="core">([\s\S]*?)<\/script>/)[1]);
const notes = JSON.parse(fs.readFileSync(0, "utf8"));
const files = build(notes);
zip(files).arrayBuffer().then(b => {
  fs.writeFileSync(process.argv[2], Buffer.from(b));
  console.log(JSON.stringify(files));
});
"""


@unittest.skipUnless(shutil.which("node"), "node not installed")
class HtmlTest(unittest.TestCase):
    def test_html_has_current_viewer(self):
        with open(HTML, encoding="utf-8") as f:
            self.assertEqual(f.read(), sync_html.synced_html(),
                             "run converter/sync_html.py")

    def test_js_matches_python_and_zip_opens(self):
        with tempfile.TemporaryDirectory() as d:
            zpath = os.path.join(d, "out.zip")
            res = subprocess.run(["node", "-e", JS, HTML, zpath],
                                 input=json.dumps(NOTES), capture_output=True,
                                 text=True, check=True)
            js_files = json.loads(res.stdout)
            py_files = notes2ti.build([tuple(n) for n in NOTES])
            self.assertEqual(js_files, py_files)
            with zipfile.ZipFile(zpath) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(
                    {n: z.read(n).decode() for n in z.namelist()}, py_files)


if __name__ == "__main__":
    unittest.main()
