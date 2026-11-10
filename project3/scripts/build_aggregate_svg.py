"""Build the CROSSFADE Project 3 aggregate-boundary diagram (SVG).

Tables, columns, keys and row counts are taken from the Project 1 schema
(project1/source/physical_model/crossfade_schema.sql) and sample data (data.xlsx).

From the repository root:
    python project3/scripts/build_aggregate_svg.py            # both themes into project3/design/
    python project3/scripts/build_aggregate_svg.py out.svg    # dark theme to a chosen path
    python project3/scripts/build_aggregate_svg.py out.svg --light
"""
import sys
from pathlib import Path

ARGS = [x for x in sys.argv[1:] if not x.startswith("--")]
LIGHT = "--light" in sys.argv          # white background, black primary text
DESIGN = Path(__file__).resolve().parent.parent / "design"
if not ARGS:                                   # no path given: build both themes into project3/design/
    import subprocess
    for i, extra in enumerate(([], ["--light"]), 1):
        name = "crossfade_p3_aggregate" + ("_light" if extra else "") + ".svg"
        print(f"[{i}/2] {name}", flush=True)
        subprocess.run([sys.executable, __file__, str(DESIGN / name)] + extra, check=True)
    sys.exit(0)
OUT = Path(ARGS[0])

W, H = 1500, 1000
X = [40, 420, 800, 1180]          # four table columns, 140 px gaps
G = 140
TW, HDR, RH = 240, 34, 22          # table width, header height, row height
CORE, REF, EXC = "#22e5ff", "#ffb43c", "#5d6b7c"
if LIGHT:
    BG, INK, DIM = "#ffffff", "#000000", "#4a5560"
    BODY, ALT, GRIDC = "#ffffff", "#000000", "#eef2f5"
    PANEL, PANEL_STROKE = "#f7f9fa", "#c9d3da"
    KEYC = {"PK": "#000000", "FK": "#000000", "PK·FK": "#000000"}
    STRUCK, STRIKE, NOTE = "#8a949c", "#d6249f", "#4a5560"
    HDR_OP, NAME_C, TARGET_C, GLOW, ALT_OP = (.85, .45), "#000000", "#000000", False, .035
else:
    BG, INK, DIM = "#05080d", "#d8f6ff", "#6f8796"
    BODY, ALT, GRIDC = "#08111a", "#ffffff", "#0e1a24"
    PANEL, PANEL_STROKE = "#08111a", "#16303f"
    KEYC = {"PK": "#ffe27a", "FK": "#ff6ad5", "PK·FK": "#ffb3f0"}
    STRUCK, STRIKE, NOTE = "#56707f", "#ff6ad5", "#8a97a6"
    HDR_OP, NAME_C, TARGET_C, GLOW, ALT_OP = (.30, .06), None, None, True, .025
FONT = "JetBrains Mono, Consolas, 'DejaVu Sans Mono', monospace"

# name: (x, y, role, rows, mongo target, [(col, key, type, discarded)])
T = {
    "artist": (X[0], 170, "ref", 8, "→ artist{}  (embedded)", [
        ("artist_id", "PK", "MEDIUMINT", False), ("stage_name", "", "VARCHAR(64)", False),
        ("country", "", "CHAR(2)", False), ("joined_date", "", "DATE", False),
        ("payout_rate", "", "DEC(5,5)", False), ("verified", "", "BIT(1)", False)]),
    "track": (X[1], 170, "core", 15, "→ document root  (_id = track_id)", [
        ("track_id", "PK", "INT", False), ("artist_id", "FK", "MEDIUMINT", True),
        ("title", "", "VARCHAR(128)", False), ("duration", "", "SMALLINT", False),
        ("release_date", "", "DATE", False), ("audio_checksum", "", "BINARY(32)", False),
        ("ingest_status", "", "ENUM", False)]),
    "track_score": (X[2], 170, "core", 27, "→ scores[]", [
        ("track_id", "PK·FK", "INT", True), ("model_id", "PK·FK", "TINYINT", True),
        ("genre_id", "FK", "TINYINT", True), ("top_probability", "", "DEC(5,4)", False),
        ("posterior_entropy", "", "DEC(5,4)", False), ("model_divergence", "", "DEC(5,4)", False),
        ("segment_variance", "", "DEC(4,4)", False), ("scored_on", "", "DATETIME", False)]),
    "genre_probability": (X[3], 170, "core", 270, "→ scores[].probabilities[]", [
        ("track_id", "PK·FK", "INT", True), ("model_id", "PK·FK", "TINYINT", True),
        ("genre_id", "PK·FK", "TINYINT", True), ("probability", "", "DEC(5,4)", False)]),
    "scoring_model": (X[2], 500, "ref", 5, "→ scores[].model{}", [
        ("model_id", "PK", "TINYINT", False), ("version_label", "", "VARCHAR(32)", False),
        ("fusion_type", "", "ENUM", False), ("embedding_dimension", "", "SMALLINT", False),
        ("segment_length", "", "TINYINT", False), ("training_corpus", "", "VARCHAR(16)", False),
        ("holdout_accuracy", "", "DEC(5,4)", False), ("deployed_on", "", "DATE", False)]),
    "genre": (X[3], 500, "ref", 10, "→ scores[].top_genre{}|→ scores[].probabilities[].genre{}", [
        ("genre_id", "PK", "TINYINT", False), ("name", "", "VARCHAR(9)", False),
        ("description", "", "VARCHAR(80)", False)]),
    # outside the boundary (keys only)
    "listener": (X[0], 800, "exc", 8, "", [("listener_id", "PK", "INT", False)]),
    "play": (X[1], 800, "exc", 31, "", [
        ("listener_id", "PK·FK", "INT", False), ("track_id", "PK·FK", "INT", False),
        ("played_at", "PK", "DATETIME", False), ("station_id", "FK", "INT", False)]),
    "station": (X[2], 800, "exc", 8, "", [
        ("station_id", "PK", "INT", False), ("listener_id", "FK", "INT", False),
        ("model_id", "FK", "TINYINT", False)]),
    "station_blend": (X[3], 800, "exc", 19, "", [
        ("station_id", "PK·FK", "INT", False), ("genre_id", "PK·FK", "TINYINT", False)]),
}
COLOR = {"core": CORE, "ref": REF, "exc": EXC}


def height(name):
    return HDR + RH * len(T[name][5]) + 10


def row_y(name, i):
    return T[name][1] + HDR + RH / 2 + 5 + RH * i


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


out = []
a = out.append

a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
  f'font-family="{FONT}">')
a(f'''<defs>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
    <path d="M24 0H0V24" fill="none" stroke="{GRIDC}" stroke-width="1"/>
  </pattern>
  <linearGradient id="hc" x1="0" x2="1"><stop offset="0" stop-color="{CORE}" stop-opacity="{HDR_OP[0]}"/><stop offset="1" stop-color="{CORE}" stop-opacity="{HDR_OP[1]}"/></linearGradient>
  <linearGradient id="hr" x1="0" x2="1"><stop offset="0" stop-color="{REF}" stop-opacity="{HDR_OP[0]}"/><stop offset="1" stop-color="{REF}" stop-opacity="{HDR_OP[1]}"/></linearGradient>
  <linearGradient id="he" x1="0" x2="1"><stop offset="0" stop-color="{EXC}" stop-opacity="{HDR_OP[0]}"/><stop offset="1" stop-color="{EXC}" stop-opacity="{HDR_OP[1]}"/></linearGradient>
</defs>''')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#grid)"/>')

# title
a(f'<text x="40" y="44" fill="{INK}" font-size="22" font-weight="700" letter-spacing="3">CROSSFADE · PROJECT 3 · AGGREGATE BOUNDARY</text>')
a(f'<text x="40" y="68" fill="{DIM}" font-size="12.5">Six tables joined by foreign keys in the Project 1 schema, denormalized into one MongoDB collection: '
  f'<tspan fill="{INK if LIGHT else CORE}" font-weight="700">tracks</tspan> (15 documents, one per track)</text>')

# boundary
a(f'<rect x="18" y="104" width="1470" height="648" rx="14" fill="{CORE}" fill-opacity=".025" '
  f'stroke="{CORE}" stroke-opacity=".75" stroke-width="1.6" stroke-dasharray="10 6"{' filter="url(#glow)"' if GLOW else ""}/>')
a(f'<rect x="36" y="94" width="318" height="20" fill="{BG}"/>')
a(f'<text x="44" y="109" fill="{INK if LIGHT else CORE}" font-size="12.5" font-weight="700" letter-spacing="2">AGGREGATE BOUNDARY · db.tracks</text>')
a(f'<rect x="36" y="742" width="412" height="20" fill="{BG}"/>')
a(f'<text x="44" y="757" fill="{EXC}" font-size="12" letter-spacing="2">OUTSIDE · listener-side tables (keys only)</text>')


# ---------- edges (drawn before tables) ----------
def path(d, color, dash=None, width=1.7, op=1):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-opacity="{op}"{da}/>')


def one(x, y, dirn, color):
    """'1' end: two short bars perpendicular to the line. dirn = direction pointing INTO the table."""
    dx, dy = {"r": (1, 0), "l": (-1, 0), "d": (0, 1), "u": (0, -1)}[dirn]
    for off in (8, 13):
        cx, cy = x - dx * off, y - dy * off
        px, py = dy * 6, dx * 6
        a(f'<line x1="{cx-px}" y1="{cy-py}" x2="{cx+px}" y2="{cy+py}" stroke="{color}" stroke-width="1.8"/>')


def many(x, y, dirn, color):
    """crow's foot, toes touching the table edge at (x, y)."""
    dx, dy = {"r": (1, 0), "l": (-1, 0), "d": (0, 1), "u": (0, -1)}[dirn]
    hx, hy = x - dx * 14, y - dy * 14
    px, py = dy * 7, dx * 7
    for s in (-1, 0, 1):
        a(f'<line x1="{hx}" y1="{hy}" x2="{x+px*s}" y2="{y+py*s}" stroke="{color}" stroke-width="1.8"/>')
    bx, by = x - dx * 20, y - dy * 20
    a(f'<line x1="{bx-px*.85}" y1="{by-py*.85}" x2="{bx+px*.85}" y2="{by+py*.85}" stroke="{color}" stroke-width="1.8"/>')


def label(x, y, text, color, size=11, anchor="middle", bg=True):
    if LIGHT and color in (CORE, REF):
        color = INK
    if bg:
        w = len(text) * size * 0.61 + 8
        x0 = x - w / 2 if anchor == "middle" else (x - 4 if anchor == "start" else x - w + 4)
        a(f'<rect x="{x0}" y="{y-size}" width="{w}" height="{size+5}" rx="3" fill="{BG}" fill-opacity=".92"/>')
    a(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}">{esc(text)}</text>')


R = lambda n: T[n][0] + TW
L = lambda n: T[n][0]
TOP = lambda n: T[n][1]
BOT = lambda n: T[n][1] + height(n)

mid = lambda i: X[i] + TW + G / 2          # centre of the gap right of column i

# 1. track.artist_id -> artist.artist_id   (N : 1)
y1, y2 = row_y("track", 1), row_y("artist", 0)
path(f"M{L('track')},{y1} H{mid(0)} V{y2} H{R('artist')}", REF)
many(L("track"), y1, "r", REF); one(R("artist"), y2, "l", REF)
label(mid(0), 196, "N : 1", REF, 11.5)
label(mid(0), 300, "fk_track_artist", DIM, 10)

# 2. track_score.track_id -> track.track_id   (1 : N)
y = row_y("track", 0)
path(f"M{R('track')},{y} H{L('track_score')}", CORE)
one(R("track"), y, "l", CORE); many(L("track_score"), y, "r", CORE)
label(mid(1), 196, "1 : N", CORE, 11.5)
label(mid(1), 300, "fk_track_score_track", DIM, 10)

# 3. genre_probability(track_id, model_id) -> track_score(track_id, model_id)   (1 : 10)
ya, yb = row_y("track_score", 0), row_y("track_score", 1)
ym = (ya + yb) / 2
xa, xb = R("track_score") + 30, L("genre_probability") - 30
for yy in (ya, yb):
    path(f"M{R('track_score')},{yy} H{xa}", CORE, width=1.3)
    path(f"M{xb},{yy} H{L('genre_probability')}", CORE, width=1.3)
path(f"M{xa},{ya} V{yb} M{xb},{ya} V{yb} M{xa},{ym} H{xb}", CORE)
one(R("track_score"), ya, "l", CORE); many(L("genre_probability"), yb, "r", CORE)
label(mid(2), 196, "1 : 10", CORE, 11.5)
label(mid(2), 136, "composite FK", DIM, 10)
label(mid(2), 151, "(track_id, model_id)", DIM, 10)

# 4. track_score.model_id -> scoring_model.model_id   (N : 1)
x = X[2] + 175
path(f"M{x},{BOT('track_score')} V{TOP('scoring_model')}", REF)
many(x, BOT("track_score"), "u", REF); one(x, TOP("scoring_model"), "d", REF)
label(x - 10, 430, "N : 1", REF, 11.5, "end")
label(x - 10, 448, "fk_track_score_scoring_model", DIM, 10, "end")

# 5. track_score.genre_id -> genre.genre_id   (N : 1, the derived top genre)
y1, y2 = row_y("track_score", 2), row_y("genre", 0)
xr = R("track_score") + 45
path(f"M{R('track_score')},{y1} H{xr} V{y2} H{L('genre')}", REF)
many(R("track_score"), y1, "l", REF); one(L("genre"), y2, "r", REF)
label(xr + 10, 400, "N : 1", REF, 11.5, "start")
label(xr + 10, 418, "fk_track_score_genre", DIM, 10, "start")
label(xr + 10, 433, "(top genre)", DIM, 10, "start")

# 6. genre_probability.genre_id -> genre.genre_id   (N : 1), routed down the right side
y1, y2 = row_y("genre_probability", 2), row_y("genre", 1)
xr = R("genre_probability") + 34
path(f"M{R('genre_probability')},{y1} H{xr} V{y2} H{R('genre')}", REF)
many(R("genre_probability"), y1, "l", REF); one(R("genre"), y2, "l", REF)
label(xr, 400, "N : 1", REF, 11.5)
a(f'<text transform="translate({xr+8},440) rotate(90)" fill="{DIM}" font-size="10">fk_genre_probability_genre</text>')

# ---- outside-boundary edges (grey, dashed) ----
# play.track_id -> track   (crosses the boundary)
x = X[1] + 120
path(f"M{x},{TOP('play')} V{BOT('track')}", EXC, dash="6 5")
many(x, TOP("play"), "u", EXC); one(x, BOT("track"), "d", EXC)
label(x + 10, 560, "play → track   N : 1", EXC, 11, "start")
label(x + 10, 578, "excluded: one row per listen,", NOTE, 10, "start")
label(x + 10, 593, "unbounded-array anti-pattern", NOTE, 10, "start")
# play.listener_id -> listener
y = row_y("play", 0)
path(f"M{L('play')},{y} H{R('listener')}", EXC, dash="6 5")
many(L("play"), y, "r", EXC); one(R("listener"), row_y("listener", 0), "l", EXC)
# play.station_id -> station
y1, y2 = row_y("play", 3), row_y("station", 0)
path(f"M{R('play')},{y1} H{mid(1)} V{y2} H{L('station')}", EXC, dash="6 5")
many(R("play"), y1, "l", EXC); one(L("station"), y2, "r", EXC)
# station.listener_id -> listener (routed underneath)
path(f"M{X[2]+120},{BOT('station')} V975 H{X[0]+120} V{BOT('listener')}", EXC, dash="6 5")
many(X[2] + 120, BOT("station"), "u", EXC); one(X[0] + 120, BOT("listener"), "u", EXC)
# station.model_id -> scoring_model (crosses the boundary)
x = X[2] + 60
path(f"M{x},{TOP('station')} V{BOT('scoring_model')}", EXC, dash="6 5")
many(x, TOP("station"), "u", EXC); one(x, BOT("scoring_model"), "d", EXC)
# station_blend.station_id -> station
y = row_y("station_blend", 0)
path(f"M{L('station_blend')},{y} H{R('station')}", EXC, dash="6 5")
many(L("station_blend"), y, "r", EXC); one(R("station"), row_y("station", 0), "l", EXC)
# station_blend.genre_id -> genre (crosses the boundary)
x = X[3] + 120
path(f"M{x},{TOP('station_blend')} V{BOT('genre')}", EXC, dash="6 5")
many(x, TOP("station_blend"), "u", EXC); one(x, BOT("genre"), "d", EXC)


# ---------- tables ----------
def table(name):
    x, y, role, nrows, target, cols = T[name]
    c = COLOR[role]
    h = height(name)
    grad = {"core": "hc", "ref": "hr", "exc": "he"}[role]
    op = 1 if role != "exc" else .8
    if target:
        parts = target.split("|")
        for k, t in enumerate(parts):
            ty = y - 9 - 15 * (len(parts) - 1 - k)
            a(f'<text x="{x+2}" y="{ty}" fill="{TARGET_C or c}" font-size="11" font-style="italic" opacity=".95">{esc(t)}</text>')
    a(f'<g opacity="{op}">')
    a(f'<rect x="{x}" y="{y}" width="{TW}" height="{h}" rx="6" fill="{BODY}" stroke="{c}" stroke-width="1.5"'
      f'{" filter=" + chr(34) + "url(#glow)" + chr(34) if role != "exc" and GLOW else ""}/>')
    a(f'<path d="M{x} {y+HDR} V{y+6} Q{x} {y} {x+6} {y} H{x+TW-6} Q{x+TW} {y} {x+TW} {y+6} V{y+HDR} Z" fill="url(#{grad})"/>')
    a(f'<line x1="{x}" y1="{y+HDR}" x2="{x+TW}" y2="{y+HDR}" stroke="{c}" stroke-opacity=".6"/>')
    a(f'<text x="{x+12}" y="{y+22}" fill="{NAME_C or c}" font-size="14" font-weight="700" letter-spacing="1">{name}</text>')
    a(f'<text x="{x+TW-10}" y="{y+22}" fill="{DIM}" font-size="10.5" text-anchor="end">{nrows} rows</text>')
    for i, (col, key, typ, gone) in enumerate(cols):
        ry = row_y(name, i)
        if i % 2:
            a(f'<rect x="{x+1}" y="{ry-RH/2}" width="{TW-2}" height="{RH}" fill="{ALT}" fill-opacity="{ALT_OP}"/>')
        kc = KEYC.get(key, DIM)
        if key:
            a(f'<text x="{x+10}" y="{ry+4}" fill="{kc}" font-size="9.5" font-weight="700">{key}</text>')
        tc = STRUCK if gone else INK
        a(f'<text x="{x+50}" y="{ry+4}" fill="{tc}" font-size="11">{col}</text>')
        if gone:
            tw = len(col) * 11 * 0.6
            a(f'<line x1="{x+48}" y1="{ry}" x2="{x+52+tw}" y2="{ry}" stroke="{STRIKE}" stroke-opacity=".7" stroke-width="1.1"/>')
        a(f'<text x="{x+TW-10}" y="{ry+4}" fill="{DIM}" font-size="9.5" text-anchor="end">{typ}</text>')
    a('</g>')


for n in T:
    table(n)

# ---------- legend ----------
lx, ly = 40, 478
a(f'<rect x="{lx-12}" y="{ly-22}" width="440" height="232" rx="8" fill="{PANEL}" fill-opacity=".9" stroke="{PANEL_STROKE}"/>')
a(f'<text x="{lx}" y="{ly}" fill="{INK}" font-size="12" font-weight="700" letter-spacing="2">LEGEND</text>')
items = [
    (CORE, "core chain → nested arrays"),
    (REF, "reference tables → embedded subdocuments"),
    (EXC, "outside the boundary"),
]
for i, (c, t) in enumerate(items):
    yy = ly + 24 + i * 22
    a(f'<rect x="{lx}" y="{yy-10}" width="22" height="12" rx="2" fill="none" stroke="{c}" stroke-width="1.6"/>')
    a(f'<text x="{lx+32}" y="{yy}" fill="{INK}" font-size="11.5">{esc(t)}</text>')
yy = ly + 24 + 3 * 22
a(f'<text x="{lx}" y="{yy}" fill="{KEYC['PK']}" font-size="10" font-weight="700">PK</text>'
  f'<text x="{lx+24}" y="{yy}" fill="{KEYC['FK']}" font-size="10" font-weight="700">FK</text>'
  f'<text x="{lx+48}" y="{yy}" fill="{KEYC['PK·FK']}" font-size="10" font-weight="700">PK·FK</text>'
  f'<text x="{lx+92}" y="{yy}" fill="{INK}" font-size="11.5">key role in Project 1</text>')
yy += 22
a(f'<text x="{lx}" y="{yy}" fill="{STRUCK}" font-size="11.5">fk_col</text>'
  f'<line x1="{lx-2}" y1="{yy-4}" x2="{lx+44}" y2="{yy-4}" stroke="{STRIKE}" stroke-opacity=".7"/>'
  f'<text x="{lx+60}" y="{yy}" fill="{INK}" font-size="11.5">FK dropped in MongoDB; nesting</text>')
a(f'<text x="{lx+60}" y="{yy+16}" fill="{INK}" font-size="11.5">or the embedded PK carries the link</text>')
yy += 38
a(f'<text x="{lx}" y="{yy}" fill="{INK if LIGHT else REF}" font-size="11.5" font-weight="{700 if LIGHT else 400}">genre · scoring_model</text>'
  f'<text x="{lx+150}" y="{yy}" fill="{INK}" font-size="11.5">: static reference data, also</text>')
a(f'<text x="{lx}" y="{yy+16}" fill="{INK}" font-size="11.5">used by station / station_blend — copied in, never</text>')
a(f'<text x="{lx}" y="{yy+32}" fill="{INK}" font-size="11.5">updated, so the duplication is safe</text>')
yy += 58
# cardinality key
many(lx + 30, yy - 4, "r", INK)
path(f"M{lx},{yy-4} H{lx+30}", INK, width=1.4)
a(f'<text x="{lx+42}" y="{yy}" fill="{INK}" font-size="11.5">many</text>')
path(f"M{lx+100},{yy-4} H{lx+130}", INK, width=1.4)
one(lx + 130, yy - 4, "r", INK)
a(f'<text x="{lx+142}" y="{yy}" fill="{INK}" font-size="11.5">one   ·   line = FK → PK join</text>')

a("</svg>")
OUT.write_text("\n".join(out), encoding="utf-8")
print(f"[ok] wrote {OUT}  ({OUT.stat().st_size/1024:.1f} KB, {len(T)} tables)")
