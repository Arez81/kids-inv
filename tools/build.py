"""Build the kids' read-only site from the parent app page.

Usage: python3 -I tools/build.py <parent-page.html> <output-dir>

Writes <output-dir>/index.html (the same app in read-only mode, numbers
loaded from data.json) and <output-dir>/data.json (the family ledger,
without the parent code). data.json keeps its old "syncedAt" when the
numbers did not change, so an unchanged run produces no git diff.
"""
import datetime
import json
import os
import re
import sys

src, out = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()

m = re.search(r'(<script id="state" type="application/json">)(.*?)(</script>)', html, re.S)
if not m:
    sys.exit("state block not found")
state = json.loads(m.group(2))
state.setdefault("config", {}).pop("pinHash", None)

page = html[: m.start(2)] + "{}" + html[m.end(2):]
if '<script id="app-script">' not in page:
    sys.exit("app script not found")
page = page.replace('<script id="app-script">', '<script>window.KIDS_PUBLIC=true</script><script id="app-script">', 1)
page = page.replace(
    "<meta charset=utf8>",
    '<meta charset=utf8><meta name="robots" content="noindex,nofollow">'
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-title" content="הקופה">',
    1,
)
page = page.replace("<html>", '<html lang="he" dir="rtl">', 1)

os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
    f.write(page)

data_path = os.path.join(out, "data.json")
old = None
if os.path.exists(data_path):
    try:
        old = json.load(open(data_path, encoding="utf-8"))
    except Exception:
        old = None
old_synced = old.pop("syncedAt", None) if isinstance(old, dict) else None
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
state["syncedAt"] = old_synced if (old == {k: v for k, v in state.items() if k != "syncedAt"} and old_synced) else now
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
print("built", out, "synced", state["syncedAt"])
