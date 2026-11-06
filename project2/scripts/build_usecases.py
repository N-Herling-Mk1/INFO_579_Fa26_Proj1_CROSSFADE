"""Build the Use cases page data for the Project 2 site.

Inputs
    project1/source/requirements_analysis/requirements_analysis.tex   the graded RA, as written
    project2/data/use_cases.json                                       use cases, their RA evidence, columns
    project1/data_export/csv/<table>.csv                               row counts (the Project 1 sample data)
Output
    project2/data/usecases.js     window.UC = { ra: [...], useCases: [...], schema: {...}, coverage: {...} }

Checks (the build fails if any is broken)
    - every evidence phrase occurs, word for word, in the RA block it cites
    - every column a use case lists exists in the physical model
    - every RA block id cited exists

Run from the repository root:
    python project2/scripts/build_usecases.py
"""
import csv, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "project1", "source", "requirements_analysis", "requirements_analysis.tex")
UCS = os.path.join(ROOT, "project2", "data", "use_cases.json")
CSV_DIR = os.path.join(ROOT, "project1", "data_export", "csv")
OUT = os.path.join(ROOT, "project2", "data", "usecases.js")

# physical model column order (matches database_implementation.sql)
SCHEMA = {
    "artist": ["artist_id", "stage_name", "country", "joined_date", "payout_rate", "verified"],
    "track": ["track_id", "artist_id", "title", "duration", "release_date", "audio_checksum", "ingest_status"],
    "genre": ["genre_id", "name", "description"],
    "listener": ["listener_id", "email", "display_name", "plan_tier", "signup_date"],
    "scoring_model": ["model_id", "version_label", "fusion_type", "embedding_dimension", "segment_length",
                      "training_corpus", "holdout_accuracy", "deployed_on"],
    "station": ["station_id", "listener_id", "model_id", "name", "minimum_ambiguity", "maximum_ambiguity", "created_on"],
    "track_score": ["track_id", "model_id", "genre_id", "top_probability", "posterior_entropy", "model_divergence",
                    "segment_variance", "scored_on"],
    "genre_probability": ["track_id", "model_id", "genre_id", "probability"],
    "station_blend": ["station_id", "genre_id", "weight"],
    "play": ["listener_id", "track_id", "played_at", "station_id", "seconds_played", "completed", "reaction",
             "royalty_amount"],
}
ASSOCIATIVE = {"track_score", "genre_probability", "station_blend", "play"}


def step(n, total, msg):
    print(f"[{n}/{total}] {msg}", flush=True)


def snake(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ------------------------------------------------------------------ LaTeX helpers
def braced(s, i):
    """s[i] == '{'; return (content, index after the closing brace)."""
    assert s[i] == "{", s[i:i + 20]
    depth, j = 0, i
    while True:
        c = s[j]
        if c == "\\":
            j += 2; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1


def args(s, i, n):
    """Read n braced arguments starting at s[i], skipping whitespace and %-line breaks between them."""
    out = []
    for _ in range(n):
        while s[i] in " \t\r\n%":
            if s[i] == "%":
                while s[i] != "\n": i += 1
            i += 1
        a, i = braced(s, i)
        out.append(a)
    return out, i


def clean(t):
    t = re.sub(r"\\dictnote\{[^}]*\}\{[^}]*\}", "", t)
    for _ in range(3):  # unwrap nested formatting commands
        t = re.sub(r"\\(?:rae|textbf|emph|textit|texttt|ent|asc|rel|small)\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\q\{([^{}]*)\}", r"'\1'", t)
    t = t.replace("---", "\u2014").replace("--", "\u2013").replace("~", " ")
    t = t.replace("\\%", "%").replace("\\&", "&").replace("\\#", "#").replace("\\_", "_")
    t = t.replace("``", "\u201c").replace("''", "\u201d")
    t = re.sub(r"\\[a-zA-Z]+\*?", "", t)       # anything left: drop the command name
    t = t.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip()


def section(tex, title):
    a = tex.index("\\section{" + title + "}")
    b = tex.find("\\section{", a + 10)
    return tex[a:b if b > 0 else len(tex)]


def table_rows(block):
    """Data rows of a longtable: skip header rows (\\rowcolor / \\endhead)."""
    body = block[block.index("\\endhead") + len("\\endhead"):block.index("\\end{longtable}")]
    rows = []
    for raw in body.split("\\\\"):
        raw = raw.replace("\\hline", "").strip()
        if raw and "&" in raw:
            rows.append([clean(c) for c in raw.split("&")])
    return rows


def parse_ra(tex):
    blocks = []
    ov = section(tex, "Overview")
    para = ov[ov.index("\\label{sec:ra}") + len("\\label{sec:ra}"):ov.index("\\subsection{Entities}")]
    blocks.append({"id": "overview", "kind": "para", "section": "Overview", "title": "Overview", "text": clean(para)})

    for sec_title, kind in (("Entities", "entity"), ("Associative entities", "entity")):
        sec = section(tex, sec_title)
        if sec_title == "Associative entities":
            intro = sec[sec.index("\\label{sec:assoc}") + len("\\label{sec:assoc}"):sec.index("\\begin{entitytable}")]
            for k, p in enumerate([p for p in re.split(r"\n\s*\n", intro) if p.strip()], 1):
                blocks.append({"id": f"assoc:intro{k}", "kind": "para", "section": sec_title,
                               "title": "Associative entities" if k == 1 else "", "text": clean(p)})
        i = 0
        while True:
            i = sec.find("\\entityhead", i)
            if i < 0: break
            (name, desc), i = args(sec, i + len("\\entityhead"), 2)
            ent = snake(clean(name))
            blocks.append({"id": f"ent:{ent}", "kind": "entity", "section": sec_title, "table": ent,
                           "title": clean(name), "text": clean(desc)})
            end = sec.find("\\end{entitytable}", i)
            j = i
            while True:
                j = sec.find("\\attr", j, end)
                if j < 0: break
                (an, atype, anull, auniq, akey, adesc), j = args(sec, j + len("\\attr"), 6)
                col = snake(clean(an))
                blocks.append({"id": f"attr:{ent}.{col}", "kind": "attr", "section": sec_title, "table": ent,
                               "column": col, "title": clean(an), "type": clean(atype), "text": clean(adesc)})
            i = end

    rels = section(tex, "Relationships")
    for parent, child, card, desc in table_rows(rels[:rels.index("\\subsection{Integrity rules}")]):
        blocks.append({"id": f"rel:{snake(parent)}-{snake(child)}", "kind": "rel", "section": "Relationships",
                       "title": f"{parent} {card} {child}", "text": desc})
    integ = rels[rels.index("\\subsection{Integrity rules}"):]
    intro = integ[integ.index("\\label{sec:integ}") + len("\\label{sec:integ}"):integ.index("\\begin{longtable}")]
    blocks.append({"id": "rules:intro", "kind": "para", "section": "Integrity rules", "title": "Integrity rules",
                   "text": clean(intro)})
    for rid, rule, enf in table_rows(integ):
        blocks.append({"id": f"rule:{rid}", "kind": "rule", "section": "Integrity rules", "title": rid,
                       "text": rule, "enforcement": enf})
    return blocks


def main():
    total = 5
    step(1, total, "parsing the requirements analysis LaTeX source")
    tex = open(TEX, encoding="utf-8").read()
    ra = parse_ra(tex)
    kinds = {}
    for b in ra: kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    print("      " + ", ".join(f"{v} {k}" for k, v in kinds.items()), flush=True)
    attrs = {(b["table"], b["column"]) for b in ra if b["kind"] == "attr"}
    keyish = {(t, c) for t, cols in SCHEMA.items() for c in cols} - attrs
    print(f"      {len(attrs)} attribute descriptions; {len(keyish)} key columns described only in their entity's key list",
          flush=True)

    step(2, total, "loading use cases and checking every citation against the RA text")
    spec = json.load(open(UCS, encoding="utf-8"))
    ids = {b["id"]: b for b in ra}
    bad = 0
    for uc in spec["useCases"]:
        for ev in uc["evidence"]:
            b = ids.get(ev["block"])
            if not b:
                print(f"      {uc['id']}: unknown RA block {ev['block']}"); bad += 1; continue
            hay = b["text"] + " " + b.get("enforcement", "")
            if ev.get("phrase") and ev["phrase"] not in hay:
                print(f"      {uc['id']}: phrase not found in {ev['block']}: {ev['phrase']!r}"); bad += 1
        for t, cols in uc["columns"].items():
            for c in cols:
                if c not in SCHEMA.get(t, []):
                    print(f"      {uc['id']}: no column {t}.{c}"); bad += 1
        for t in uc.get("single", {}):
            if t in ASSOCIATIVE or t not in SCHEMA:
                print(f"      {uc['id']}: single-table mapping to {t}, which is not a non-associative table"); bad += 1
    if bad:
        sys.exit(f"      {bad} problems; nothing written")
    print(f"      {len(spec['useCases'])} use cases, all citations found", flush=True)

    step(3, total, "counting rows in the Project 1 sample data")
    rows = {}
    for t in SCHEMA:
        with open(os.path.join(CSV_DIR, t + ".csv"), encoding="utf-8", newline="") as f:
            rows[t] = sum(1 for _ in csv.reader(f)) - 1
    cells_total = sum(rows[t] * len(c) for t, c in SCHEMA.items())
    print(f"      {sum(rows.values())} rows, {sum(len(c) for c in SCHEMA.values())} columns, {cells_total} cells", flush=True)

    step(4, total, "computing data coverage")

    def coverage(selected):
        hit = {}
        for uc in selected:
            for t, cols in uc["columns"].items():
                for c in cols:
                    hit.setdefault((t, c), set()).add(uc["id"])
        cols_hit = len(hit)
        cells_hit = sum(rows[t] for (t, c) in hit)
        per_table = {t: {"columns": sum(1 for c in cs if (t, c) in hit), "of": len(cs),
                         "cells": sum(rows[t] for c in cs if (t, c) in hit), "cellsOf": rows[t] * len(cs)}
                     for t, cs in SCHEMA.items()}
        return {"columns": cols_hit, "columnsOf": sum(len(c) for c in SCHEMA.values()),
                "cells": cells_hit, "cellsOf": cells_total, "perTable": per_table,
                "hits": {f"{t}.{c}": sorted(v) for (t, c), v in hit.items()}}

    ucs = spec["useCases"]
    single_full = [u for u in ucs if any(v == "full" for v in u.get("single", {}).values())]
    single_any = [{**u, "columns": {t: u.get("singleColumns", {}).get(t, u["columns"].get(t, []))
                                    for t in u.get("single", {})}} for u in ucs if u.get("single")]
    cov = {"all": coverage(ucs), "single": coverage(single_any)}
    for k, v in cov.items():
        print(f"      {k:>6}: {v['columns']}/{v['columnsOf']} columns ({100 * v['columns'] / v['columnsOf']:.0f}%), "
              f"{v['cells']}/{v['cellsOf']} cells ({100 * v['cells'] / v['cellsOf']:.0f}%)", flush=True)

    step(5, total, "writing " + os.path.relpath(OUT, ROOT))
    data = {"source": "project1/source/requirements_analysis/requirements_analysis.tex",
            "ra": ra, "useCases": ucs, "schema": SCHEMA, "rows": rows,
            "associative": sorted(ASSOCIATIVE), "coverage": cov}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("/* Generated by project2/scripts/build_usecases.py from use_cases.json and the RA source. Do not edit. */\n")
        f.write("window.UC = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    print(f"      {os.path.getsize(OUT):,} bytes", flush=True)


if __name__ == "__main__":
    main()
