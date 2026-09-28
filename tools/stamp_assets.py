"""Add a content fingerprint to every link to the shared CSS and JS.

GitHub Pages lets browsers reuse a cached file for up to 10 minutes, so after a push
a page can load new HTML with an old site.css. This rewrites each reference to
assets/site.css and assets/panel.js as, e.g., site.css?v=3f9a1c2b, where the tag is
a hash of the file's contents: when a file changes its links change, and browsers
fetch it fresh. Run from the repository root after editing either file:
    python tools/stamp_assets.py
"""
import glob, hashlib, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = ["site.css", "panel.js"]
tags = {}
for name in ASSETS:
    with open(os.path.join(ROOT, "assets", name), "rb") as f:
        tags[name] = hashlib.sha256(f.read()).hexdigest()[:8]
print("[1/2] fingerprints: " + ", ".join(f"{n}={t}" for n, t in tags.items()), flush=True)

pages = sorted(set(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)))
changed = 0
for path in pages:
    html = open(path, encoding="utf-8").read()
    new = html
    for name, tag in tags.items():
        new = re.sub(r'((?:\.\./)*assets/' + re.escape(name) + r')(\?v=[0-9a-f]+)?"', r'\1?v=' + tag + '"', new)
    if new != html:
        open(path, "w", encoding="utf-8", newline="").write(new)
        changed += 1
print(f"[2/2] {changed} of {len(pages)} pages updated", flush=True)
