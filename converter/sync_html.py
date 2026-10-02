#!/usr/bin/env python3
"""Embed the current calculator/NOTEVIEW.py into converter.html.

Run this after editing NOTEVIEW.py.
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "converter.html")
VIEWER = os.path.join(HERE, "..", "calculator", "NOTEVIEW.py")


def synced_html():
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    with open(VIEWER, encoding="utf-8") as f:
        src = json.dumps(f.read()).replace("</", "<\\/")
    return re.sub(r"var VIEWER_SRC = .*?;\n",
                  lambda m: "var VIEWER_SRC = " + src + ";\n", html, count=1)


if __name__ == "__main__":
    html = synced_html()
    with open(HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("updated", HTML)
