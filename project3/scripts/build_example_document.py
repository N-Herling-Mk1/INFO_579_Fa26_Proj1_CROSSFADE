"""Build one example document of the proposed `tracks` collection from the Project 1 sample data.

This is a preview of the aggregate boundary on real rows, not collection.json: it builds a single track
so the site can show what the denormalized document looks like. It reads the per-table CSVs in
project1/data_export/csv/ (written from the graded data.xlsx by tools/export_p1_data.py, which checks
every cell against the workbook) and takes column types from the Project 1 schema, so DECIMAL keeps its
scale and DATE/DATETIME/BINARY/BIT become BSON Date, Binary and boolean.

From the repository root:
    python project3/scripts/build_example_document.py          # track 4818 (two models that disagree)
    python project3/scripts/build_example_document.py 4817     # any track_id
Writes project3/design/example_document_<track_id>.json (MongoDB Extended JSON, relaxed mode).
"""
import base64
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_DIR = ROOT / "project1" / "data_export" / "csv"
SCHEMA = ROOT / "project1" / "source" / "physical_model" / "crossfade_schema.sql"
OUT_DIR = ROOT / "project3" / "design"
TRACK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 4818

# which columns are foreign keys and therefore dropped (the link survives as nesting or an embedded PK)
DROP = {
    "track": {"artist_id"},
    "track_score": {"track_id", "model_id", "genre_id"},
    "genre_probability": {"track_id", "model_id", "genre_id"},
}


def step(i, n, msg):
    print(f"[{i}/{n}] {msg}", flush=True)


def column_types():
    """{table: {column: sql_type}} from CREATE TABLE statements."""
    types, table = {}, None
    for line in SCHEMA.read_text(encoding="utf-8").splitlines():
        m = re.match(r"CREATE TABLE (\w+)", line)
        if m:
            table = m.group(1); types[table] = {}; continue
        m = re.match(r"\s+(\w+) ([A-Z]+(?:\([\d,]+\))?)", line)
        if table and m and m.group(1) not in ("PRIMARY", "UNIQUE", "CONSTRAINT"):
            types[table][m.group(1)] = m.group(2)
    return types


def read(table):
    with open(CSV_DIR / f"{table}.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    # CSV headers are display names ("Track ID"); schema names are snake_case
    return [{k.strip().lower().replace(" ", "_"): v for k, v in r.items()} for r in rows]


def bson(value, sql_type):
    """CSV text -> Extended JSON value for the column's SQL type. Empty field = NULL."""
    if value == "":
        return None
    t = sql_type.upper()
    if t.startswith("DECIMAL"):
        scale = int(re.search(r",(\d+)\)", t).group(1))
        return {"$numberDecimal": f"{float(value):.{scale}f}"}
    if t in ("TINYINT", "SMALLINT", "MEDIUMINT", "INT"):
        return int(value)
    if t == "DATE":
        return {"$date": f"{value}T00:00:00Z"}
    if t == "DATETIME":
        return {"$date": datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%SZ")}
    if t.startswith("BINARY"):
        raw = bytes.fromhex(value[2:] if value.lower().startswith("0x") else value)
        return {"$binary": {"base64": base64.b64encode(raw).decode(), "subType": "00"}}
    if t.startswith("BIT"):
        return value == "1"
    return value


def convert(table, row, types):
    return {c: bson(row[c], types[table][c]) for c in types[table] if c not in DROP.get(table, ())}


def main():
    n = 5
    step(1, n, f"schema types from {SCHEMA.relative_to(ROOT)}")
    types = column_types()
    step(2, n, f"reading 6 tables from {CSV_DIR.relative_to(ROOT)}")
    T = {t: read(t) for t in ("track", "artist", "track_score", "genre_probability", "scoring_model", "genre")}
    by = lambda t, col: {r[col]: r for r in T[t]}
    artist, model, genre = by("artist", "artist_id"), by("scoring_model", "model_id"), by("genre", "genre_id")

    track = next((r for r in T["track"] if int(r["track_id"]) == TRACK_ID), None)
    if track is None:
        sys.exit(f"track_id {TRACK_ID} is not in track.csv")
    step(3, n, f"denormalizing track {TRACK_ID} ({track['title']})")
    doc = {"_id": int(track["track_id"])}
    doc.update({k: v for k, v in convert("track", track, types).items() if k != "track_id"})
    doc["artist"] = convert("artist", artist[track["artist_id"]], types)
    scores = []
    for s in sorted((r for r in T["track_score"] if r["track_id"] == track["track_id"]), key=lambda r: int(r["model_id"])):
        sc = {"model": convert("scoring_model", model[s["model_id"]], types),
              "top_genre": convert("genre", genre[s["genre_id"]], types)}
        sc.update(convert("track_score", s, types))
        probs = [r for r in T["genre_probability"] if r["track_id"] == s["track_id"] and r["model_id"] == s["model_id"]]
        sc["probabilities"] = [{"genre": convert("genre", genre[p["genre_id"]], types), **convert("genre_probability", p, types)}
                               for p in sorted(probs, key=lambda r: int(r["genre_id"]))]
        scores.append(sc)
    doc["scores"] = scores

    step(4, n, "checking the document")
    flat = json.dumps(doc)
    for fk in ("artist_id\": " + track["artist_id"],):          # artist_id may only appear inside artist{}
        assert flat.count(fk) == 1, "artist_id leaked outside the embedded artist"
    assert all(len(s["probabilities"]) == 10 for s in scores), "every score needs 10 genre probabilities"
    total = sum(float(p["probability"]["$numberDecimal"]) for s in scores for p in s["probabilities"])
    print(f"      {len(scores)} score(s), {sum(len(s['probabilities']) for s in scores)} probabilities, "
          f"probability sums per score: " + ", ".join(f"{sum(float(p['probability']['$numberDecimal']) for p in s['probabilities']):.4f}" for s in scores), flush=True)
    try:                                                         # optional: parse with the driver's own Extended JSON reader
        from bson import json_util
        json_util.loads(json.dumps(doc))
        print("      bson.json_util.loads: ok", flush=True)
    except ImportError:
        print("      (pymongo not installed: skipped the bson.json_util parse check)", flush=True)

    out = OUT_DIR / f"example_document_{TRACK_ID}.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    step(5, n, f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
