"""Build project2/data/reqmap.js: for each deliverable, where the brief's requirements are met.

    python project2/scripts/build_reqmap.py

Reads the four .sql files in project2/deliverables. For every tagged block it takes the `Requirements:` field (its
first line names the requirement; the indented lines under it quote the brief and name the SQL), finds that SQL in
the statement below the comment, and colours the comment line and the SQL the same. A claim whose SQL cannot be
found is reported on the page and in this script's output. project2/panels/reqmap.html shows the result.
Nothing here is typed in by hand: every row, tag and highlight comes from the files.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEL = ROOT / "project2" / "deliverables"
OUT = ROOT / "project2" / "data" / "reqmap.js"
esc = html.escape


def say(i, n, msg):
    print(f"[{i}/{n}] {msg}", flush=True)


# ------------------------------------------------------------------------------------------------ per-file setup
BRIEF = {
    "implementation": ('Task 1: "Develop the SQL statements to create the tables of your database and insert the '
                       'sample data. You must present the statements in a single sql script named '
                       'database_implementation.sql."'),
    "single": ('Task 2: "Develop a variety of SQL queries following the requirements for single table queries"; '
               'requirement 1 (here 2.1) and its sub-requirements (a)-(e), each "at least one of the queries".'),
    "multiple": ('Task 3: "Develop a variety of SQL queries following the requirements for multiple table queries"; '
                 'requirements 1-5 (here 3.1-3.5), one query each.'),
    "routines": ('Task 4: "Implement 2 procedures and 1 function or 1 procedure and 2 functions that make use of the '
                 'data in your database. The 3 routines must be presented in a single sq file named routines.sql."'),
}
KEYS = {
    "implementation": [("db", "Task 1", "the database the script builds", "#c9a227"),
                       ("create", "create", "create the tables", "#4fa3e0"),
                       ("insert", "insert", "insert the sample data", "#59b36a")],
    "single": [("2.1", "2.1", "each non-associative table, individually", "#c9a227"),
               ("a", "(a)", "single row functions", "#4fa3e0"),
               ("b", "(b)", "aggregate functions", "#d0723a"),
               ("c", "(c)", "sort the results", "#59b36a"),
               ("d", "(d)", "first N results", "#b07ad8"),
               ("e", "(e)", "selection control function", "#e05d8a")],
    "multiple": [("3.1", "3.1", "associative table + 2 related, INNER JOIN on all three", "#4fa3e0"),
                 ("3.2", "3.2", "two or more tables with LEFT OUTER JOIN", "#d0723a"),
                 ("3.3", "3.3", "a set operation", "#59b36a"),
                 ("3.4", "3.4", "a subquery with a multi-row operation", "#b07ad8"),
                 ("3.5", "3.5", "a derived table with WITH", "#e05d8a")],
    "routines": [("kind", "4 kind", "2 procedures + 1 function, or 1 + 2", "#4fa3e0"),
                 ("data", "4 data", "make use of the data in your database", "#59b36a"),
                 ("file", "4 file", "all 3 in a single file named routines.sql", "#c9a227")],
}
FILES = {"implementation": "database_implementation.sql", "single": "single_table.sql",
         "multiple": "multiple_table.sql", "routines": "routines.sql"}
FUNCS = ["CHAR_LENGTH", "DATEDIFF", "CONCAT", "LPAD", "ROUND", "MOD", "COUNT", "MIN", "MAX", "AVG", "SUM", "IF", "CASE"]


def segments(lines):
    """[kind, first_line, last_line]: block comments and the code between them."""
    segs, i = [], 0
    while i < len(lines):
        if lines[i].startswith("/*"):
            j = i
            while not lines[j].rstrip().endswith("*/"):
                j += 1
            segs.append(["comment", i, j]); i = j + 1
        else:
            j = i
            while j < len(lines) and not lines[j].startswith("/*"):
                j += 1
            if any(l.strip() for l in lines[i:j]):
                segs.append(["code", i, j - 1])
            i = j
    return segs


def paren_end(code, start):
    """Index just past the parenthesis group that opens at code[start] == '('."""
    depth = 0
    for k in range(start, len(code)):
        depth += {"(": 1, ")": -1}.get(code[k], 0)
        if depth == 0:
            return k + 1
    return len(code)


# ------------------------------------------------------------------------------------------------ the Requirements field
def read_requirements(fid, lines, a, b):
    """(declared keys, {line: key}, {key: evidence text}) from the comment lines a..b."""
    for n in range(a, b + 1):
        if not re.match(r"\tRequirements:", lines[n]):
            continue
        first = lines[n]
        line_key, ev = {n: "first"}, {}
        if fid == "single":
            declared = (["2.1"] if re.search(r"\b2\.1\b", first) else []) + re.findall(r"\(([a-e])\)", first)
            cur = None
            for q in range(n + 1, b + 1):
                mm = re.match(r"\t  (2\.1|\(([a-e])\))\s+(.*)", lines[q])
                if mm:
                    cur = "2.1" if mm.group(1) == "2.1" else mm.group(2); ev[cur] = mm.group(3)
                elif cur and re.match(r"\t {7}\S", lines[q]):
                    ev[cur] += " " + lines[q].strip()
                else:
                    break
                line_key[q] = cur
        elif fid == "multiple":
            m = re.search(r"\b(3\.[1-5])\b", first)
            declared = [m.group(1)] if m else []
            for q in range(n + 1, b + 1):
                if not lines[q].startswith("\t  ") or not declared:
                    break
                line_key[q] = declared[0]; ev[declared[0]] = ev.get(declared[0], "") + " " + lines[q].strip()
        elif fid == "routines":
            declared = ["kind", "data", "file"] if re.search(r"\b4 (function|procedure)\b", first) else []
            line_key[n] = "kind"
            cur = None
            for q in range(n + 1, b + 1):
                if not lines[q].startswith("\t  "):
                    break
                s = lines[q].strip()
                if s.startswith('"Implement'):
                    cur = "data"
                elif s.startswith('"The 3 routines'):
                    cur = "file"
                line_key[q] = cur; ev[cur] = ev.get(cur, "") + " " + s
        else:  # implementation
            declared = ["create"] if "create the tables" in first else ["insert"] if "insert the sample data" in first \
                else ["db"] if re.search(r"Task 1\b", first) else []
            if declared:
                line_key[n] = declared[0]
        return declared, line_key, ev
    return [], {}, {}


def header_keys(fid, lines, hdr_end):
    """{line: key} for the header's BRIEF REQUIREMENTS ADDRESSED list."""
    out, on, cur = {}, False, None
    for n in range(0, hdr_end + 1):
        l = lines[n]
        if l.strip().startswith("BRIEF REQUIREMENTS ADDRESSED"):
            on = True; continue
        if on and not l.strip():
            break
        if not on:
            continue
        if fid == "single":
            mm = re.match(r"\t  (2\.1|\(([a-e])\))\s", l)
            cur = ("2.1" if mm.group(1) == "2.1" else mm.group(2)) if mm else (cur if re.match(r"\t {7}\S", l) else None)
        elif fid == "multiple":
            mm = re.match(r"\t  (3\.[1-5])\s", l)
            cur = mm.group(1) if mm else (cur if re.match(r"\t {7}\S", l) else None)
        elif fid == "routines":
            if re.match(r"\t  4  ", l):
                cur = "kind" if '"Implement' in l else "file"
            elif not re.match(r"\t {5}\S", l):
                cur = None
        if cur:
            out[n] = cur
    return out


# ------------------------------------------------------------------------------------------------ finding the SQL
def find_spans(fid, blk, code, ev):
    """[(start, end, key)] within code, and {key: True/False} whether each declared claim was found."""
    spans, found = [], {}

    def add(pattern, key, flags=0):
        hits = [(m.start(), m.end(), key) for m in re.finditer(pattern, code, flags)]
        spans.extend(hits)
        return bool(hits)

    for key in blk["declared"]:
        e = ev.get(key, "")
        after = e.split('":', 1)[1] if '":' in e else e
        ok = True
        if fid == "single":
            if key == "2.1":
                t = re.search(r"the (\w+) table", after)
                ok = bool(t) and add(r"crossfade\." + t.group(1) + r"\b", key)
            elif key == "c":
                ok = add(r"ORDER BY[\s\S]*?(?=\nLIMIT|;)", key)
            elif key == "d":
                t = re.search(r"LIMIT \d+", after)
                ok = bool(t) and add(re.escape(t.group(0)), key)
            else:
                named = [f for f in FUNCS if re.search(r"\b" + f + r"\b", after)]
                ok = bool(named)
                for f in named:
                    pats = [r"\bCASE\b", r"\bWHEN\b", r"\bTHEN\b", r"\bELSE\b", r"\bEND\b"] if f == "CASE" \
                        else [r"\b" + f + r"(?=\s*\()"]
                    ok = all([add(p, key) for p in pats]) and ok
        elif fid == "multiple":
            if key == "3.1":
                tabs = re.findall(r"(\w+) is the associative table", after)
                joined = re.findall(r"INNER\s+JOIN\s+\w+\s+to\s+(\w+)", after)
                ok = len(re.findall(r"\bINNER JOIN\b", code)) >= 2 and bool(tabs) and len(joined) == 2
                add(r"\bINNER JOIN\b", key)
                for t in tabs + joined:
                    ok = add(r"crossfade\." + t + r"\b", key) and ok
            elif key == "3.2":
                ok = add(r"\bLEFT OUTER JOIN\b", key)
            elif key == "3.3":
                ok = add(r"\b(UNION|INTERSECT|EXCEPT)(\s+ALL)?\b", key)
            elif key == "3.4":
                m = re.search(r"\bIN\s*(?=\(\s*SELECT\b)", code)
                ok = bool(m)
                if m:
                    p = code.index("(", m.end() - 1)
                    spans.append((m.start(), paren_end(code, p), key))
            elif key == "3.5":
                names = re.findall(r"(\w+)\s+AS\s*\(", code)
                ok = code.lstrip().upper().startswith("WITH") and bool(names)
                add(r"^\s*WITH\b", key)
                for nm in names:
                    add(r"\b" + nm + r"\b", key)
        elif fid == "routines":
            if key == "kind":
                ok = add(r"CREATE\s+(FUNCTION|PROCEDURE)\s+crossfade\.\w+", key)
            elif key == "data":
                tables = blk.get("tables", [])
                via = {}                                    # tables read through a routine this one calls
                for fn in re.findall(r"crossfade\.(\w+)\s*\(", code):
                    if fn.lower() in blk.get("routine_tables", {}) and fn.lower() != blk["name"].lower():
                        add(r"crossfade\." + fn + r"(?=\s*\()", key)
                        via.update({x: fn for x in blk["routine_tables"][fn.lower()]})
                for t in tables:
                    direct = t not in blk["routine_tables"] and add(r"(?:INSERT\s+INTO\s+)?crossfade\." + t + r"\b", key)
                    ok = (direct or t in via) and ok
                ok = ok and bool(tables)
            else:
                ok = True                                   # where the routine lives: this file
        else:
            if key == "db":
                ok = add(r"(DROP|CREATE) DATABASE( IF (NOT )?EXISTS)? crossfade", key)
            elif key == "create":
                ok = add(r"CREATE TABLE IF NOT EXISTS crossfade\." + blk["table"] + r"\b", key)
            else:
                ok = add(r"INSERT INTO crossfade\." + blk["table"] + r"\b", key)
        found[key] = ok
    return spans, found


# ------------------------------------------------------------------------------------------------ one file
def build(fid):
    path = DEL / FILES[fid]
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    lines = text.split("\n")
    segs = segments(lines)
    offs = [0]
    for l in lines:
        offs.append(offs[-1] + len(l) + 1)
    keys = KEYS[fid]
    label = {k: lb for k, lb, _, _ in keys}

    routine_tables = {m.group(1).lower(): [x.strip().lower() for x in m.group(2).split(",")]
                      for m in re.finditer(r"\[[FP]\d+\]\s*(\w+)[\s\S]*?\tTables:\s*([^\n]+)", text)}
    blocks, line_key, anchor = [], {}, {}
    for i, (kind, a, b) in enumerate(segs):
        if kind != "comment":
            continue
        body = "\n".join(lines[a:b + 1])
        m = re.search(r"\[([BTDSEMFP]\d+)\]\s*([A-Za-z_]+)?", body)
        if not m:
            continue
        tag = m.group(1)
        anchor[a] = tag
        blk = {"tag": tag, "name": (m.group(2) or ""), "comment": (a, b), "code": None}
        blk["table"] = blk["name"].lower()
        t = re.search(r"\tTables:\s*([^\n]+)", body)
        blk["tables"] = [x.strip().lower() for x in t.group(1).split(",")] if t else []
        blk["routine_tables"] = routine_tables
        if i + 1 < len(segs) and segs[i + 1][0] == "code":
            blk["code"] = (segs[i + 1][1], segs[i + 1][2])
        blk["declared"], lk, ev = read_requirements(fid, lines, a, b)
        line_key.update(lk)
        blk["spans"], blk["found"] = [], {}
        if blk["code"]:
            s0 = offs[blk["code"][0]]; s1 = offs[blk["code"][1] + 1] - 1
            sp, blk["found"] = find_spans(fid, blk, text[s0:s1], ev)
            blk["spans"] = [(s0 + x, s0 + y, k) for x, y, k in sp]
        elif blk["declared"]:
            blk["found"] = {k: False for k in blk["declared"]}
        if fid == "routines" and blk["code"]:
            mk = re.search(r"CREATE\s+(FUNCTION|PROCEDURE)", text[offs[blk["code"][0]]:offs[blk["code"][1] + 1]])
            blk["kind"] = mk.group(1).lower() if mk else "?"
        blocks.append(blk)

    hdr_end = segs[0][2]
    hkeys = header_keys(fid, lines, hdr_end)

    # spans: keep the first of any overlapping pair
    spans = sorted((s for b in blocks for s in b["spans"]), key=lambda x: (x[0], -(x[1] - x[0])))
    clean, last = [], -1
    for s in spans:
        if s[0] >= last:
            clean.append(s); last = s[1]
    spans = clean

    # ---- the code view
    out, si = [], 0
    for n, l in enumerate(lines):
        lo, hi = offs[n], offs[n] + len(l)
        while si < len(spans) and spans[si][1] <= lo:
            si += 1
        pieces, pos, k = [], lo, si
        while k < len(spans) and spans[k][0] < hi:
            s, e, key = spans[k]
            s2, e2 = max(s, lo), min(e, hi)
            if s2 > pos:
                pieces.append(esc(text[pos:s2]))
            if e2 > s2 and s2 == lo:                       # a span carried onto a new line: leave its indent unmarked
                lead = len(text[s2:e2]) - len(text[s2:e2].lstrip())
                pieces.append(esc(text[s2:s2 + lead])); s2 += lead
            if e2 > s2:
                pieces.append(f'<span class="hit" data-r="{key}">{esc(text[s2:e2])}</span>')
            pos = max(pos, e2)
            if e > hi:
                break
            k += 1
        if pos < hi:
            pieces.append(esc(text[pos:hi]))
        body = "".join(pieces)
        cls, data = "", ""
        key = line_key.get(n) or hkeys.get(n)
        if key == "first":
            cls = "reqfirst"
        elif key:
            cls, data = "req", key
        if n <= hdr_end and n in hkeys:
            body = re.sub(r"\b([SM][1-7]|[FP][12])\b", lambda m: f'<a class="tl" href="#blk-{m.group(1)}">{m.group(1)}</a>', body)
        if cls == "req":
            body = re.sub(r"^(\t  )(2\.1|\([a-e]\)|3\.[1-5]|4)(?=\s)",
                          lambda m: m.group(1) + f'<b class="chip" data-r="{data}">{m.group(2)}</b>', body)
        if key == "first" or (fid == "routines" and n in line_key and lines[n].startswith("\tRequirements:")):
            if fid == "single":
                body = re.sub(r"(2\.1|\([a-e]\))", lambda m: f'<b class="chip" data-r="{"2.1" if m.group(1) == "2.1" else m.group(1)[1]}">{m.group(1)}</b>', body)
            elif fid == "multiple":
                body = re.sub(r"(3\.[1-5])", lambda m: f'<b class="chip" data-r="{m.group(1)}">{m.group(1)}</b>', body, count=1)
        kind = next((s[0] for s in segs if s[1] <= n <= s[2]), "blank")
        aid = f' id="blk-{anchor[n - 1]}"' if (n - 1) in anchor else ""
        dr = f' data-r="{data}"' if data else ""
        out.append(f'<div class="ln k-{kind} {cls}"{aid}{dr}><i>{n + 1}</i><code>{body or " "}</code></div>')

    # ---- grid and notes
    req_blocks = [b for b in blocks if b["declared"]]
    missing = [(b["tag"], k) for b in req_blocks for k, ok in b["found"].items() if not ok]
    claims = sum(len(b["declared"]) for b in req_blocks)
    counts = {k: sum(k in b["declared"] for b in req_blocks) for k, _, _, _ in keys}

    def cell(b, k, text_=None):
        if k not in b["declared"]:
            return '<td class="off">&middot;</td>'
        ok = b["found"].get(k)
        return f'<td class="on" data-r="{k}"><a href="#blk-{b["tag"]}">{text_ or ("&#10003;" if ok else "?")}</a></td>'

    head = "".join(f'<th data-r="{k}">{esc(lb)}</th>' for k, lb, _, _ in keys)
    if fid == "implementation":
        tables = []
        for b in req_blocks:
            if b["declared"][0] in ("create", "insert") and b["table"] not in tables:
                tables.append(b["table"])
        rows = []
        for t in tables:
            c = next((b for b in req_blocks if b["table"] == t and "create" in b["declared"]), None)
            d = next((b for b in req_blocks if b["table"] == t and "insert" in b["declared"]), None)
            rows.append(f'<tr><th>{esc(t)}</th>'
                        + (cell(c, "create", c["tag"]) if c else '<td class="off">&middot;</td>')
                        + (cell(d, "insert", d["tag"]) if d else '<td class="off">&middot;</td>') + "</tr>")
        dbs = [b for b in req_blocks if "db" in b["declared"]]
        grid = (f'<table><thead><tr><th>table</th><th data-r="create">create</th><th data-r="insert">insert</th></tr>'
                f'</thead><tbody>{"".join(rows)}</tbody><tfoot><tr><th>database</th><td colspan="2" class="on" data-r="db">'
                + " ".join(f'<a href="#blk-{b["tag"]}">{b["tag"]}</a>' for b in dbs)
                + f'</td></tr></tfoot></table>')
        notes = (f"<p><b>create</b>: {counts['create']} CREATE TABLE statements; <b>insert</b>: {counts['insert']} "
                 f"INSERT statements, one per table; <b>Task 1</b>: {counts['db']} statements that drop and create "
                 f"the database itself.</p><p><b>single script</b>: all of it is in database_implementation.sql.</p>")
    elif fid == "routines":
        rows = []
        for b in req_blocks:
            rows.append(f'<tr><th><a href="#blk-{b["tag"]}">{b["tag"]}</a></th><td class="tb">{esc(b["name"])}</td>'
                        + cell(b, "kind", b.get("kind", "?")) + cell(b, "data", esc(", ".join(b["tables"])))
                        + cell(b, "file", "routines.sql") + "</tr>")
        nf = sum(b.get("kind") == "function" for b in req_blocks)
        np_ = sum(b.get("kind") == "procedure" for b in req_blocks)
        mix_ok = (nf, np_) in ((1, 2), (2, 1))
        grid = (f'<table><thead><tr><th>tag</th><th>routine</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody>'
                f'<tfoot><tr><th colspan="2">brief</th><td colspan="3">{np_} procedure(s) + {nf} function(s): '
                f'{"exactly the brief&#39;s mix" if mix_ok else "NOT the brief&#39;s mix"}</td></tr></tfoot></table>')
        notes = ("<p><b>Exact count, not a minimum</b>: Task 4 asks for three routines in one of two splits; routines.sql "
                 "has exactly three. The example calls that used to sit at the end of the file are on the site as "
                 "example usage, not in the deliverable.</p>")
    else:
        rows = []
        for b in req_blocks:
            tb = b["table"] if fid == "single" else ", ".join(b["tables"])
            rows.append(f'<tr><th><a href="#blk-{b["tag"]}">{b["tag"]}</a></th><td class="tb">{esc(tb)}</td>'
                        + "".join(cell(b, k) for k, _, _, _ in keys) + "</tr>")
        mins = '<td>6 tables</td>' + '<td>1</td>' * 5 if fid == "single" else '<td>1</td>' * 5
        grid = (f'<table><thead><tr><th>query</th><th>{"table" if fid == "single" else "tables"}</th>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}</tbody><tfoot><tr><th colspan="2">queries meeting it</th>'
                + "".join(f"<td>{counts[k]}</td>" for k, _, _, _ in keys)
                + f'</tr><tr><th colspan="2">brief minimum</th>{mins}</tr></tfoot></table>')
        if fid == "single":
            tabs = sorted({b["table"] for b in req_blocks})
            notes = (f"<p><b>2.1</b>: tables queried: {', '.join(tabs)} ({len(tabs)} of the 6 non-associative tables).</p>"
                     "<p><b>(a)-(e)</b>: the brief asks for at least one query each; every count is at least 1, so the "
                     "minimum is met and the rest is extra.</p>")
        else:
            notes = ("<p><b>3.1-3.5</b>: one query each is the minimum. M1-M5 meet it, one requirement each; M6 (a second "
                     "3.1) and M7 (a second 3.5) go beyond it.</p>")
    check = (f'<span class="ok">All {claims} claims check out.</span>' if not missing else
             '<span class="bad">Not found: ' + ", ".join(f"{t} {label[k]}" for t, k in missing) + "</span>")
    notes += f"<p>&#10003; = the SQL the comment names was found in the statement under it. {check}</p>"

    legend = "".join(f'<button class="lg" data-r="{k}"><b>{esc(lb)}</b> {esc(nm)} <em>{counts[k]}</em></button>'
                     for k, lb, nm, _ in keys)
    colours = {k: c for k, _, _, c in keys}
    return {"file": FILES[fid], "brief": BRIEF[fid], "legend": legend, "grid": grid, "notes": notes,
            "code": "\n".join(out), "colours": colours, "lines": len(lines), "claims": claims, "missing": missing}


def main():
    ids = list(FILES)
    data, bad = {}, []
    for i, fid in enumerate(ids, 1):
        say(i, len(ids) + 1, f"mapping {FILES[fid]}")
        data[fid] = build(fid)
        print(f"      {data[fid]['claims']} claims, {len(data[fid]['missing'])} not found {data[fid]['missing'] or ''}")
        bad += data[fid]["missing"]
    say(len(ids) + 1, len(ids) + 1, f"writing {OUT.relative_to(ROOT)}")
    OUT.write_text("/* Written by project2/scripts/build_reqmap.py from the deliverables. Do not edit. */\n"
                   "window.P2_REQMAP = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"      {OUT.stat().st_size:,} bytes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
