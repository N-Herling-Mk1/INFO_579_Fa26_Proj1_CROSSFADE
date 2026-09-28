"""Write the shared top banner into every top-level page of the site.

Each page gets the same markup between BANNER:BEGIN and BANNER:END markers, with
relative paths and the current page's button marked. Replaces an old
<header class="masthead"> block on first run. Run from the repository root:
    python tools/build_banner.py
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEGIN, END = "<!-- BANNER:BEGIN -->", "<!-- BANNER:END -->"
REPO = "https://github.com/N-Herling-Mk1/INFO_579_Fa26_Proj1_CROSSFADE"

# page file, path prefix back to the root, active button, context line
PAGES = [
    ("index.html",          "",    "home", "INFO 579 · SQL/NoSQL Databases · Fall 2026"),
    ("design/index.html",   "../", None,   "Top-level design"),
    ("project1/index.html", "../", "p1",   "Project 1 · Database Design"),
    ("project2/index.html", "../", "p2",   "Project 2 · SQL Database"),
    ("project3/index.html", "../", "p3",   "Project 3 · NoSQL Database"),
]
BUTTONS = [("home", "", "Home", None), ("p1", "project1/", "Project 1", "Database Design"),
           ("p2", "project2/", "Project 2", "SQL Database"), ("p3", "project3/", "Project 3", "NoSQL Database")]

def banner(prefix, active, context):
    home = prefix or "./"
    links = []
    for key, path, label, sub in BUTTONS:
        cur = ' aria-current="page"' if key == active else ""
        href = (prefix + path) if path else home
        subtext = f'<span class="nav-sub">{sub}</span>' if sub else ""
        links.append(f'      <a class="nav-btn" href="{href}"{cur}><span class="nav-label">{label}</span>{subtext}</a>')
    return f"""{BEGIN}
<header class="banner">
  <a class="brand" href="{home}" aria-label="CROSSFADE home">
    <span class="brand-wave" style="background-image:url('{prefix}assets/images/crossfade_wave.jpg')" aria-hidden="true"></span>
    <span class="brand-text">
      <img class="brand-mark" src="{prefix}assets/images/crossfade_wordmark.png" width="441" height="72" alt="crossfade">
      <span class="brand-context">{context}</span>
    </span>
  </a>
  <nav class="banner-nav" aria-label="Projects">
{chr(10).join(links)}
  </nav>
  <a class="banner-repo" href="{REPO}" aria-label="GitHub repository" title="GitHub repository">
    <svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
  </a>
</header>
{END}"""

for i, (page, prefix, active, context) in enumerate(PAGES, 1):
    path = os.path.join(ROOT, page)
    html = open(path, encoding="utf-8").read()
    block = banner(prefix, active, context)
    if BEGIN in html:
        html = html[:html.index(BEGIN)] + block + html[html.index(END) + len(END):]
        how = "refreshed"
    else:
        html, n = re.subn(r"[ \t]*<header class=\"masthead\">.*?</header>", block, html, count=1, flags=re.S)
        if n != 1: sys.exit(f"{page}: no masthead or banner markers found")
        how = "replaced masthead"
    open(path, "w", encoding="utf-8", newline="").write(html)
    print(f"[{i}/{len(PAGES)}] {page}: {how}", flush=True)
