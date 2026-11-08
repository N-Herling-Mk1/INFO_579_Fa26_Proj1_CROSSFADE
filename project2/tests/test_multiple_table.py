"""Unit tests for multiple_table.sql (INFO 579 Project 2, Task 3).

Layers, as in test_single_table.py:
  contract     each query follows the brief and the course: purpose comment with tag, title, use cases, business
               need and question, the Task 3 requirement it meets, the tables it reads, what one result row is and
               its output columns; read-only SELECT (or WITH ... SELECT), no SELECT *; MySQL's own plan (EXPLAIN)
               reads exactly the tables the comment lists; the SQL really meets the requirement it claims; every
               join names its type; every column MySQL reads is one its use cases declare.
  correctness  each result equals an independent answer computed in Python from data.csv (oracle_multiple.py),
               row for row, in order, to the exact decimal; one row per declared grain, the ORDER BY includes the
               grain so no two rows can tie, and two runs agree.
  behaviour    logic the sample data never exercises: rows are added inside a transaction, the query is checked
               against the oracle on the changed data, and everything is rolled back.
  coverage     the file as a whole: each requirement 3.1-3.5 met, every use case with multiple-table columns
               answered, every declared column read by a query answering its use case, tags M1, M2, ... in order.

Run (from the repo root or the test-kit folder):
    python -m pytest project2/tests/test_multiple_table.py -v      (repo)
    python -m pytest test_multiple_table.py -v                      (test kit)
"""
import copy, json, re
from decimal import Decimal

import pytest

from conftest import run, strip_literals, canon
from oracle_multiple import ORACLES

# Associative tables of the physical model: each resolves a many-to-many relationship between two other tables.
ASSOCIATIVE = ["play", "track_score", "station_blend", "genre_probability"]
REQUIREMENTS = {
    "3.1": "an associative table and the two tables it relates, joined with INNER JOIN",
    "3.2": "two or more tables joined with LEFT OUTER JOIN",
    "3.3": "a set operation (UNION, INTERSECT or EXCEPT)",
    "3.4": "a subquery with a multi-row operation (IN, NOT IN, ANY, SOME, ALL or EXISTS)",
    "3.5": "a derived table defined with WITH",
}


def code(q):
    return strip_literals(q.sql).upper()


def alias_map(q):
    """alias -> table for every `crossfade.<table> [AS alias]` in the statement (a table read without an alias maps
    to itself)."""
    out = {}
    for t, a in re.findall(r"\bcrossfade\.(\w+)(?:\s+AS\s+(\w+))?", strip_literals(q.sql), re.I):
        out[t.lower()] = t.lower()
        if a and a.upper() not in ("ON", "WHERE", "INNER", "LEFT", "RIGHT", "GROUP", "ORDER", "UNION"):
            out[a.lower()] = t.lower()
    return out


def plan_reads(q, db):
    """{table: columns} that MySQL's plan (EXPLAIN FORMAT=JSON) reads, with aliases resolved to tables and derived
    tables left out. A column counts only if the statement names it: the plan also lists primary-key columns that
    come along with an index, which the query never asked for."""
    with db.cursor() as cur:
        cur.execute("EXPLAIN FORMAT=JSON " + q.sql)
        plan = json.loads(cur.fetchone()[0])
    names, words = alias_map(q), set(re.findall(r"\b[a-z_][a-z0-9_]*\b", strip_literals(q.sql).lower()))
    out = {}

    def walk(x):
        if isinstance(x, dict):
            t = x.get("table_name")
            if isinstance(t, str) and t.lower() in names:
                out.setdefault(names[t.lower()], set()).update(c.lower() for c in x.get("used_columns", [])
                                                                if c.lower() in words)
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(plan)
    return {t: sorted(c) for t, c in out.items()}


def foreign_keys(db):
    """{child: {parent, ...}} from the live schema."""
    with db.cursor() as cur:
        cur.execute("SELECT TABLE_NAME, REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE "
                    "WHERE TABLE_SCHEMA = 'crossfade' AND REFERENCED_TABLE_NAME IS NOT NULL")
        fk = {}
        for child, parent in cur.fetchall():
            fk.setdefault(child.lower(), set()).add(parent.lower())
    return fk


def meets(req, q, db=None):
    """(met?, reason) for one Task 3 requirement."""
    c = code(q)
    if req == "3.1":
        if re.search(r"\b(LEFT|RIGHT|CROSS|FULL|NATURAL)\b[\w\s]*\bJOIN\b", c):
            return False, "3.1 joins with INNER JOIN only"
        if len(re.findall(r"\bINNER\s+JOIN\b", c)) < 2:
            return False, "3.1 needs two INNER JOINs (three tables)"
        tables = set(alias_map(q).values())
        fk = foreign_keys(db)
        for a in ASSOCIATIVE:
            if a in tables and len(fk.get(a, set()) & (tables - {a})) >= 2:
                return True, f"{a} joined to {sorted(fk[a] & tables)}"
        return False, f"no associative table joined to two of the tables it relates (reads {sorted(tables)})"
    if req == "3.2":
        ok = re.search(r"\bLEFT\s+OUTER\s+JOIN\b", c) and len(set(alias_map(q).values())) >= 2
        return bool(ok), "LEFT OUTER JOIN" if ok else "no LEFT OUTER JOIN across two or more tables"
    if req == "3.3":
        m = re.search(r"\b(UNION|INTERSECT|EXCEPT)\b", c)
        return bool(m), m.group(1) if m else "no UNION, INTERSECT or EXCEPT"
    if req == "3.4":
        m = re.search(r"\b((?:NOT\s+)?IN|ANY|SOME|ALL|EXISTS)\s*\(\s*SELECT\b", c)
        return bool(m), (re.sub(r"\s+", " ", m.group(1)) + " (SELECT ...)") if m else "no multi-row subquery operator"
    if req == "3.5":
        m = re.match(r"\s*WITH\s+(RECURSIVE\s+)?\w+\s+AS\s*\(", c)
        return bool(m), "WITH" if m else "does not start with WITH name AS ("
    return False, f"unknown requirement {req}"


def declared_columns(q, use_cases):
    """{table: columns} the query's use cases declare in use_cases.json (multipleColumns)."""
    out = {}
    for uid in q.use_cases:
        for t, cols in (use_cases.get(uid, {}).get("multipleColumns") or {}).items():
            out.setdefault(t, set()).update(cols)
    return {t: sorted(c) for t, c in out.items()}


# ============================================================================ contract (per query)
def test_comment_contract(mquery, use_cases, data):
    """Preceded by a purpose comment with a tag and title, use cases, the business need, a business question, the
    Task 3 requirement it meets, the tables it reads, what one result row is, and its output columns; every use case
    exists, the grain is among the output columns, and the output columns are the ones the oracle answers with."""
    q = mquery
    assert q.tag and q.tag.startswith("M"), "comment has no [M#] tag"
    assert q.title, "comment has no title after the tag ([M1] short title)"
    assert q.use_cases, "comment names no use case (Use cases: UC-xx)"
    unknown = [u for u in q.use_cases if u not in use_cases]
    assert not unknown, f"use cases not in use_cases.json: {unknown}"
    assert len(q.need) > 20, "comment states no business need (Business need: ...)"
    assert len(q.question) > 20, "comment has no business question"
    assert q.requirement3 in REQUIREMENTS, "comment names no Task 3 requirement (Requirements: 3.1 ... 3.5)"
    assert len(q.tables) >= 2, "comment lists fewer than two tables (Tables: a, b, ...)"
    assert q.grain, "comment does not say what one result row is (One row per: col, ...)"
    assert q.output, "comment lists no output columns (Output: col, col, ...)"
    missing = [g for g in q.grain if g not in q.output]
    assert not missing, f"One row per: {missing} not among the output columns"
    if q.tag in ORACLES:
        want = ORACLES[q.tag](data)[0]
        assert q.output == want, f"Output: lists {q.output}, the oracle answers with {want}"
    from conftest import record
    record(q.tag, title=q.title, tables=q.tables, use_cases=q.use_cases, question=q.question, need=q.need,
           requirement=q.requirement3, requirement_text=REQUIREMENTS.get(q.requirement3), grain=q.grain,
           output=q.output, sql=q.sql)


def test_read_only_select(mquery):
    """A single read-only SELECT (WITH ... SELECT counts), no SELECT *, nothing outside the crossfade database."""
    c = code(mquery)
    assert re.match(r"\s*(SELECT|WITH)\b", c), "not a SELECT or WITH ... SELECT"
    assert not re.search(r"SELECT\s+(DISTINCT\s+)?(\w+\.)?\*", c), "SELECT * is a generic query (brief: avoid trivial and generic)"
    for verb in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE INTO", "CALL"):
        assert not re.search(r"\b" + verb + r"\b", c), f"{verb} in a query file"
    text = strip_literals(mquery.sql).lower()
    names = set(re.findall(r"\bas\s+(\w+)", text)) | set(re.findall(r"(\w+)\s+as\s*\(", text))  # aliases, WITH names
    schemas = set(re.findall(r"\b([a-z_][a-z0-9_]*)\.[a-z_]", text)) - names
    assert schemas <= {"crossfade"}, f"refers to other schemas: {schemas - {'crossfade'}}"


def test_reads_declared_tables(mquery, db):
    """MySQL's own plan (EXPLAIN FORMAT=JSON) reads exactly the tables the comment lists under Tables:."""
    reads = plan_reads(mquery, db)
    assert set(reads) == set(mquery.tables), f"plan reads {sorted(reads)}, comment says {sorted(mquery.tables)}"


def test_meets_its_requirement(mquery, db):
    """The SQL really does what the Task 3 requirement it claims asks for (3.1 INNER JOIN through an associative
    table, 3.2 LEFT OUTER JOIN, 3.3 set operation, 3.4 multi-row subquery, 3.5 WITH)."""
    ok, why = meets(mquery.requirement3, mquery, db)
    from conftest import record
    record(mquery.tag, detected=why if ok else None)
    assert ok, f"claims {mquery.requirement3} ({REQUIREMENTS.get(mquery.requirement3)}): {why}"


def test_join_types_explicit(mquery):
    """Every join names its type (Unit 9): INNER JOIN, LEFT OUTER JOIN or RIGHT OUTER JOIN. No bare JOIN, no LEFT
    JOIN without OUTER, no NATURAL JOIN, no comma join."""
    c = code(mquery)
    for m in re.finditer(r"\bJOIN\b", c):
        before = c[:m.start()].split()[-2:]
        ok = before[-1:] == ["INNER"] or before in (["LEFT", "OUTER"], ["RIGHT", "OUTER"])
        assert ok, f"join type not named in full: '... {' '.join(before)} JOIN' (write INNER JOIN or LEFT OUTER JOIN)"
    assert not re.search(r"\bNATURAL\b", c), "NATURAL JOIN hides the join condition"
    comma = re.search(r"\bFROM\s+(CROSSFADE\.)?\w+(\s+(AS\s+)?\w+)?\s*,", c)
    assert not comma, "comma join in FROM: name the join type and write its ON condition"


def test_columns_match_use_cases(mquery, db, use_cases):
    """Every column MySQL reads from each table is one its use cases declare under multipleColumns in
    use_cases.json, so the use-case heat map never misses what the query reads. (The other direction, every
    declared column read by some query, is checked for the whole file: two queries can answer one use case.)"""
    reads = plan_reads(mquery, db)
    want = declared_columns(mquery, use_cases)
    from conftest import record
    record(mquery.tag, columns=reads)
    assert want, f"{mquery.use_cases} declare no multipleColumns in use_cases.json"
    extra = {t: sorted(set(c) - set(want.get(t, []))) for t, c in reads.items() if set(c) - set(want.get(t, []))}
    assert not extra, f"reads columns {mquery.use_cases} do not declare: {extra}"


# ============================================================================ correctness (per query)
def strs(rows):
    return [[None if v is None else str(v) for v in r] for r in rows]


def shown(want, got):
    """The oracle's rows as text for the site, written the way MySQL writes a value it agrees with (0.0216 and
    0.02160 are the same DECIMAL; MySQL keeps the column's scale), so the page compares like with like."""
    out = []
    for i, w in enumerate(want):
        g = got[i] if i < len(got) else ()
        out.append([None if v is None else str(g[k]) if k < len(g) and g[k] == v and g[k] is not None else str(v)
                    for k, v in enumerate(w)])
    return out


def test_result_matches_oracle(mquery, db, data):
    """Same columns, same rows, same order, exact values as the Python answer from data.csv."""
    assert mquery.tag in ORACLES, f"no oracle for {mquery.tag}"
    cols, rows = run(db, mquery.sql)
    want_cols, want = ORACLES[mquery.tag](data)
    from conftest import record
    record(mquery.tag, columns_out=cols, rows=strs(rows), expected={"columns": want_cols, "rows": shown(want, rows)})
    assert cols == want_cols, f"columns {cols} != {want_cols}"
    assert len(rows) == len(want), f"{len(rows)} rows, oracle has {len(want)}"
    for i, (g, w) in enumerate(zip(rows, want), 1):
        assert g == w, f"row {i}: MySQL {g} != oracle {w}"


def order_keys(c):
    """Bare column names of the final, top-level ORDER BY (`col`, `t.col DESC`); expressions are skipped."""
    hits = [m for m in re.finditer(r"\bORDER\s+BY\b", c) if c[:m.start()].count("(") == c[:m.start()].count(")")]
    if not hits:
        return None
    body = c[hits[-1].end():]
    body = body[:re.search(r"\bLIMIT\b|$", body).start()]
    out, d, cur = [], 0, ""
    for ch in body + ",":
        d += (ch == "(") - (ch == ")")
        if ch == "," and d == 0:
            m = re.fullmatch(r"\s*(?:\w+\.)?(\w+)(?:\s+(?:ASC|DESC))?\s*;?\s*", cur)
            if m: out.append(m.group(1).lower())
            cur = ""
        else:
            cur += ch
    return out


def test_result_is_deterministic(mquery, db):
    """The row order cannot depend on chance: each result row is one value of the declared grain (One row per:),
    and the ORDER BY includes every grain column, so no two rows can tie on all the sort keys. Two runs alone cannot
    prove this (MySQL usually returns tied rows in primary-key order, hiding a missing tie-break). Then two runs must
    agree."""
    keys = order_keys(code(mquery))
    assert keys is not None, "no ORDER BY: the row order is up to the server"
    missing = [g for g in mquery.grain if g not in keys]
    assert not missing, f"ORDER BY {', '.join(keys)} does not include {missing} (One row per: {mquery.grain}): rows can tie"
    cols, rows = run(db, mquery.sql)
    idx = [cols.index(g) for g in mquery.grain]
    seen = [tuple(r[i] for i in idx) for r in rows]
    dup = sorted({s for s in seen if seen.count(s) > 1})
    assert not dup, f"more than one row per {mquery.grain}: {dup}"
    assert run(db, mquery.sql) == (cols, rows)


# ============================================================================ behaviour (targeted)
# One "case" per test, logged for the site like test_single_table.py: inputs (rows added), the oracle's expected
# result on the changed data, and MySQL's actual result. Docstring: first line = title, then "Why:" and "Expect:".
CASE = {}


@pytest.fixture(autouse=True)
def case_log(request):
    m = re.match(r"test_m(\d+)_", request.node.name)
    if m:
        CASE.clear()
        CASE.update(tag="M" + m.group(1), inputs=[])
    yield
    if m:
        from conftest import record_case
        record_case(request.node.name, dict(CASE, doc=(request.node.function.__doc__ or "").strip()))


@pytest.fixture
def tx(db):
    """A cursor inside a transaction that is always rolled back."""
    db.rollback()
    with db.cursor() as cur:
        yield cur
    db.rollback()


class Written(dict):
    def __missing__(self, tag):
        pytest.fail(f"[{tag}] has no statement in multiple_table.sql yet: write the query under its comment")


@pytest.fixture
def q(pytestconfig):
    from conftest import parse_queries, find_file
    return Written({x.tag: x for x in parse_queries(find_file(pytestconfig, "msql")) if x.tag})


def add(cur, tables, table, row):
    """Insert a row in MySQL (inside tx) and the same row into a copy of the oracle's data."""
    cols = list(row)
    vals = [bytes.fromhex(v[2:]) if isinstance(v, str) and v.startswith("0x") else v for v in row.values()]
    cur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", vals)
    as_str = {k: (None if v is None else str(v)) for k, v in row.items()}
    tables[table]["rows"].append(as_str)
    CASE.setdefault("inputs", []).append({"kind": "insert", "table": table, "row": as_str})


def check(cur, query, tables):
    cur.execute(query.sql)
    got = [tuple(canon(v) for v in r) for r in cur.fetchall()]
    want_cols, want = ORACLES[query.tag](tables)
    CASE.update(columns=want_cols, expected=shown(want, got), got=strs(got))
    assert got == want, f"MySQL {got} != oracle {want}"
    return got


def play(listener, track, at, seconds, station=None, completed=0, reaction=None, royalty="0.00350"):
    return {"listener_id": listener, "track_id": track, "played_at": at, "station_id": station,
            "seconds_played": seconds, "completed": completed, "reaction": reaction, "royalty_amount": royalty}


def score(track, model, genre, entropy, divergence="0.0100"):
    return {"track_id": track, "model_id": model, "genre_id": genre, "top_probability": "0.5000",
            "posterior_entropy": entropy, "model_divergence": divergence, "segment_variance": "0.0100",
            "scored_on": "2026-09-01 12:00:00"}


def track(tid, artist, status="scored", duration=200):
    return {"track_id": tid, "artist_id": artist, "title": f"Case Track {tid}", "duration": duration,
            "release_date": "2026-09-01", "audio_checksum": "0x" + f"{tid:064x}", "ingest_status": status}


def row(rows, key):
    return [r for r in rows if r[0] == key]


# ---------------------------------------------------------------------------- M1
def test_m1_listener_with_no_plays_is_absent(tx, q, data):
    """A listener who has played nothing has no taste profile yet.
    Why: every sample listener has plays, so the INNER JOIN never has to drop anyone.
    Expect: listener 20990 (no plays) is not in the result; the 8 sample listeners are."""
    t = copy.deepcopy(data)
    add(tx, t, "listener", {"listener_id": 20990, "email": "quiet@example.com", "display_name": "quiet",
                            "plan_tier": "free", "signup_date": "2026-09-01"})
    rows = check(tx, q["M1"], t)
    assert not row(rows, 20990) and len(rows) == 8


def test_m1_abandoned_skip_lowers_the_share_heard(tx, q, data):
    """An abandoned, skipped play lowers the share of audio heard and counts as a skip, not a completion.
    Why: the sample's top listener (20937) heard all of their one recording; a second, half-heard play must pull the
    share down by duration, not by play count.
    Expect: 20937 has 2 plays, 1 completed, 1 skip, and hears 100 * (189 + 107) / (189 + 214) = 73.4 percent."""
    t = copy.deepcopy(data)
    add(tx, t, "play", play(20937, 4817, "2026-09-01 10:00:00", 107, completed=0, reaction="skipped"))
    rows = check(tx, q["M1"], t)
    r = row(rows, 20937)[0]
    assert r[2:] == (2, 1, 0, 1, Decimal("73.4"))


# ---------------------------------------------------------------------------- M2
def test_m2_artist_with_uploads_but_no_plays_is_owed_zero(tx, q, data):
    """An artist whose recordings nobody has played yet is listed, owed zero.
    Why: the sample's one artist with no plays (1049) has no uploads either, so the second LEFT OUTER JOIN (track to
    play) never has to keep a track with no plays.
    Expect: artist 9002 with track 9401 and no plays: 0 plays, 0 qualifying, 0 owed, listed after every earning artist."""
    t = copy.deepcopy(data)
    add(tx, t, "artist", {"artist_id": 9002, "stage_name": "Silent Upload", "country": "US",
                          "joined_date": "2026-09-01", "payout_rate": "0.0030", "verified": 1})
    add(tx, t, "track", track(9401, 9002))
    rows = check(tx, q["M2"], t)
    assert row(rows, 9002)[0][2:] == (0, 0, 0)


def test_m2_short_play_is_counted_but_does_not_qualify(tx, q, data):
    """A play under 30 seconds counts as a play but not as a qualifying play (RA rule I7).
    Why: checks the 30-second boundary: one play at 29 seconds, one at exactly 30.
    Expect: artist 1048 (track 4829) gains 2 plays and 1 qualifying play; what it is owed grows by the two recorded
    royalties (0.00000 and 0.00350)."""
    t = copy.deepcopy(data)
    before = row(check(tx, q["M2"], copy.deepcopy(data)), 1048)[0]
    add(tx, t, "play", play(20937, 4829, "2026-09-01 10:00:00", 29, royalty="0.00000"))
    add(tx, t, "play", play(20937, 4829, "2026-09-02 10:00:00", 30, royalty="0.00350"))
    after = row(check(tx, q["M2"], t), 1048)[0]
    assert after[2] - before[2] == 2 and after[3] - before[3] == 1 and after[4] - before[4] == Decimal("0.00350")


# ---------------------------------------------------------------------------- M3
def test_m3_listener_playing_anothers_station_shares_it(tx, q, data):
    """A listener playing a station someone else created makes it shared, and equal reach orders by station_id.
    Why: in the sample only two stations are shared; a third at the same reach checks the tie-break.
    Expect: 20937 plays station 7713 (created by 20933): 7713 reaches 2, 'shared', listed between 7710 and 7714."""
    t = copy.deepcopy(data)
    add(tx, t, "play", play(20937, 4827, "2026-09-01 10:00:00", 254, station=7713))
    rows = check(tx, q["M3"], t)
    assert [r[0] for r in rows[:3]] == [7710, 7713, 7714] and rows[1][3:] == (2, "shared")


def test_m3_unplayed_station_still_reaches_its_creator(tx, q, data):
    """A station nobody has played yet still reaches its creator.
    Why: every sample station has been played through, so the creator half of the UNION is never the only source.
    Expect: station 7799 (created by 20938, no plays) is listed with 1 listener, 'creator only', created_by 'hito'."""
    t = copy.deepcopy(data)
    add(tx, t, "station", {"station_id": 7799, "listener_id": 20938, "model_id": 3, "name": "Unplayed",
                           "minimum_ambiguity": "0.20", "maximum_ambiguity": "0.80", "created_on": "2026-09-01"})
    rows = check(tx, q["M3"], t)
    r = row(rows, 7799)[0]
    assert r[2:] == ("hito", 1, "creator only")


# ---------------------------------------------------------------------------- M4
def test_m4_new_disagreeing_score_adds_the_recording(tx, q, data):
    """A second model version that names a different top genre puts the recording on the list; equal divergence
    orders by track_id.
    Why: 4824 is scored by one version only in the sample, so it can never qualify; a disagreeing score with the
    same divergence as 4828 (0.0421) checks the tie-break too.
    Expect: 4824 joins with 2 models scoring, listed just before 4828."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", score(4824, 1, 9, "0.4500", divergence="0.0421"))
    rows = check(tx, q["M4"], t)
    assert [r[0] for r in rows] == [4821, 4824, 4828, 4818] and rows[1][2] == 2


def test_m4_third_version_raises_the_highest_divergence(tx, q, data):
    """With three versions scoring a recording, the highest of their divergences is reported.
    Why: every listed sample recording is scored by exactly two versions, whose divergences from each other are the
    same number, so MAX and MIN agree and a wrong aggregate would go unnoticed.
    Expect: model 4 also scores 4821 (metal, divergence 0.2000): 4821 shows 3 models scoring, highest 0.2000."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", score(4821, 4, 6, "0.5500", divergence="0.2000"))
    rows = check(tx, q["M4"], t)
    assert rows[0][0] == 4821 and rows[0][2:] == (3, Decimal("0.2000"))


def test_m4_agreeing_new_score_adds_nothing(tx, q, data):
    """Another version that agrees on the top genre does not make a disagreement.
    Why: the IN subquery must count distinct top genres, not scores.
    Expect: model 1 scores 4824 as genre 2, like model 4 did: the result is unchanged (3 recordings)."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", score(4824, 1, 2, "0.4500"))
    rows = check(tx, q["M4"], t)
    assert [r[0] for r in rows] == [4821, 4828, 4818]


def test_m4_disagreement_without_divergence_is_listed_last(tx, q, data):
    """A disagreement whose divergence is not recorded is still listed, after every measured one.
    Why: model_divergence may be NULL; MAX of NULLs is NULL, and MySQL sorts NULL last in a DESC order.
    Expect: new recording 9500, scored rock by model 1 and jazz by model 2, both without divergence: listed last,
    highest_divergence NULL."""
    t = copy.deepcopy(data)
    add(tx, t, "track", track(9500, 1042))
    add(tx, t, "track_score", score(9500, 1, 9, "0.6000", divergence=None))
    add(tx, t, "track_score", score(9500, 2, 5, "0.6000", divergence=None))
    rows = check(tx, q["M4"], t)
    assert rows[-1][0] == 9500 and rows[-1][3] is None


# ---------------------------------------------------------------------------- M5
def test_m5_window_edges_are_inside(tx, q, data):
    """A recording whose entropy equals the window's minimum or maximum is on the station; one just outside is not.
    Why: no sample score falls exactly on a window edge, so BETWEEN's inclusive edges are never tested.
    Expect: station 7798 (model 3, window 0.40 to 0.60, blend country 1.00) with four model-3 country scores:
    4818 (0.6000) and 4817 (0.4000) are on it, higher entropy first; 4819 (0.3999) and 4820 (0.6001) are not."""
    t = copy.deepcopy(data)
    add(tx, t, "station", {"station_id": 7798, "listener_id": 20938, "model_id": 3, "name": "Edges",
                           "minimum_ambiguity": "0.40", "maximum_ambiguity": "0.60", "created_on": "2026-09-01"})
    add(tx, t, "station_blend", {"station_id": 7798, "genre_id": 2, "weight": "1.00"})
    for tid, h in ((4817, "0.4000"), (4818, "0.6000"), (4819, "0.3999"), (4820, "0.6001")):
        add(tx, t, "track_score", score(tid, 3, 2, h))
    rows = check(tx, q["M5"], t)
    assert [r[2] for r in rows if r[0] == 7798] == [4818, 4817]


def test_m5_rejected_recording_is_never_streamed(tx, q, data):
    """A rejected recording stays off every station even if a model scored it.
    Why: every scored row in the sample belongs to a scored recording, so the ingest-status rule is never needed.
    Expect: rejected track 4831, scored by model 2 as genre 0 at entropy 0.5000 (inside station 7717's window and
    blend), is not on 7717, which still holds 1 recording."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", score(4831, 2, 0, "0.5000"))
    rows = check(tx, q["M5"], t)
    on = [r for r in rows if r[0] == 7717]
    assert [r[2] for r in on] == [4829] and on[0][7] == 1


def test_m5_only_blend_genres_and_its_own_model_count(tx, q, data):
    """A station holds only recordings whose top genre is in its blend, as placed by its own model version.
    Why: a new station with a one-genre blend and the widest window isolates the blend and model rules.
    Expect: station 7797 (model 4, window 0 to 1, blend genre 8 only) holds just 4825 (model 4 places it in genre 8;
    model 1 also does, but model 1 is not this station's model): 1 recording, 4825's duration in minutes."""
    t = copy.deepcopy(data)
    add(tx, t, "station", {"station_id": 7797, "listener_id": 20938, "model_id": 4, "name": "One Genre",
                           "minimum_ambiguity": "0.00", "maximum_ambiguity": "1.00", "created_on": "2026-09-01"})
    add(tx, t, "station_blend", {"station_id": 7797, "genre_id": 8, "weight": "1.00"})
    rows = check(tx, q["M5"], t)
    on = [r for r in rows if r[0] == 7797]
    assert [r[2] for r in on] == [4825] and on[0][7] == 1


# ---------------------------------------------------------------------------- M6
def dist(track, model, probs):
    """The ten genre_probability rows of one result: probs = {genre_id: probability}, the rest share what is left."""
    rest = [g for g in range(10) if g not in probs]
    left = Decimal(1) - sum(Decimal(v) for v in probs.values())
    each = (left / len(rest)).quantize(Decimal("0.0001")) if rest else Decimal(0)
    return [{"track_id": track, "model_id": model, "genre_id": g,
             "probability": str(Decimal(probs[g]) if g in probs else each)} for g in range(10)]


def test_m6_rescore_by_the_model_in_service_brings_a_recording_up_to_date(tx, q, data):
    """A recording scored since the newest version was deployed no longer needs recomputing, whatever its older results.
    Why: only the newest result matters; the sample's oldest stale recording (4819) is rescored here.
    Expect: beardown_3sec (model 5) scores 4819 on 2026-07-01: 4819 leaves the list, which keeps the other 8."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", dict(score(4819, 5, 1, "0.5000"), scored_on="2026-07-01 09:00:00"))
    rows = check(tx, q["M6"], t)
    assert not row(rows, 4819) and len(rows) == 8


def test_m6_deployment_day_is_the_boundary(tx, q, data):
    """A result scored at midnight on the deployment day is up to date; one second earlier is not.
    Why: deployed_on is a date, scored_on a moment; the comparison puts the deployment at 00:00:00 of that day.
    Expect: 4819 rescored by model 5 at 2026-06-23 00:00:00 leaves the list; 4821 rescored at 2026-06-22 23:59:59
    stays, 1 day out of date, now scored by 3 versions."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", dict(score(4819, 5, 1, "0.5000"), scored_on="2026-06-23 00:00:00"))
    add(tx, t, "track_score", dict(score(4821, 5, 6, "0.5000"), scored_on="2026-06-22 23:59:59"))
    rows = check(tx, q["M6"], t)
    assert not row(rows, 4819) and row(rows, 4821)[0][2] == 3 and row(rows, 4821)[0][5] == 1


def test_m6_new_deployment_makes_every_recording_stale(tx, q, data):
    """Deploying a new version makes every released, scored recording due for recomputing, and equal ages order
    by track_id.
    Why: in the sample the newest version already scored 4 recordings; a version deployed after every result
    leaves none up to date.
    Expect: version 6 deployed 2026-08-01: all 13 scored recordings are listed, the days counted from 2026-08-01."""
    t = copy.deepcopy(data)
    add(tx, t, "scoring_model", {"model_id": 6, "version_label": "beardown_next", "fusion_type": "concat",
                                 "embedding_dimension": 384, "segment_length": 3, "training_corpus": "GTZAN",
                                 "holdout_accuracy": "0.8000", "deployed_on": "2026-08-01"})
    rows = check(tx, q["M6"], t)
    assert len(rows) == 13


def test_m6_rejected_recording_is_never_rescored(tx, q, data):
    """A rejected recording is not queued for recomputing, however old its result.
    Why: none of the sample's scored results belongs to a rejected recording.
    Expect: rejected 4831 scored by model 1 in January: not listed; the 9 sample rows are unchanged."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", dict(score(4831, 1, 0, "0.5000"), scored_on="2026-01-30 12:00:00"))
    rows = check(tx, q["M6"], t)
    assert not row(rows, 4831) and len(rows) == 9


# ---------------------------------------------------------------------------- M7
def test_m7_tie_for_second_place_takes_the_lower_genre_id(tx, q, data):
    """When two genres share the runner-up probability, the lower genre_id is the runner-up, and the result
    appears once.
    Why: no sample distribution has a tie for second place; without the rule the result would appear twice.
    Expect: model 1 scores 4824 as country (2, 0.4000) with disco (3) and jazz (5) both at 0.2000: one row,
    runner-up disco, margin 0.2000."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", dict(score(4824, 1, 2, "0.6000"), top_probability="0.4000"))
    for r in dist(4824, 1, {2: "0.4000", 3: "0.2000", 5: "0.2000"}):
        add(tx, t, "genre_probability", r)
    rows = check(tx, q["M7"], t)
    mine = [r for r in rows if r[0] == 4824 and r[2] == 1]
    assert len(mine) == 1 and mine[0][5] == "disco" and mine[0][7] == Decimal("0.2000")


def test_m7_top_tie_is_exactly_between_genres(tx, q, data):
    """When two genres share the top probability, the other one is the runner-up and the margin is 0: the
    recording sits exactly between them, and is listed first.
    Why: the sample has no tied top genre; margin 0 is the strongest "between genres" case.
    Expect: model 2 scores 4824 with pop (7) and rock (9) both at 0.4000 and pop as its top genre: runner-up rock,
    margin 0.0000, first row."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", dict(score(4824, 2, 7, "0.7000"), top_probability="0.4000"))
    for r in dist(4824, 2, {7: "0.4000", 9: "0.4000"}):
        add(tx, t, "genre_probability", r)
    rows = check(tx, q["M7"], t)
    assert rows[0][0] == 4824 and rows[0][5] == "rock" and rows[0][7] == Decimal("0.0000")


def test_m7_result_without_a_distribution_is_absent(tx, q, data):
    """A scoring result with no probability rows has no runner-up, so it is left out rather than shown half empty.
    Why: rule I2 says every result has its ten probabilities, but the database alone does not stop a result being
    written first; the INNER JOIN to the derived table drops it.
    Expect: model 1 scores 4824 with no genre_probability rows: 4824 is listed only for model 4, as before."""
    t = copy.deepcopy(data)
    add(tx, t, "track_score", score(4824, 1, 2, "0.5000"))
    rows = check(tx, q["M7"], t)
    assert [r[2] for r in rows if r[0] == 4824] == [4]


# ============================================================================ coverage (whole file)
@pytest.fixture(scope="module")
def all_queries(pytestconfig):
    from conftest import parse_queries, find_file
    return [x for x in parse_queries(find_file(pytestconfig, "msql")) if x.tag]


def test_each_requirement_is_met(all_queries, db):
    """Each of the five Task 3 requirements (3.1-3.5) is claimed by a query that really meets it."""
    met = {r: [x.tag for x in all_queries if x.requirement3 == r and meets(r, x, db)[0]] for r in REQUIREMENTS}
    missing = [f"{r} ({REQUIREMENTS[r]})" for r, tags in met.items() if not tags]
    assert not missing, f"requirements not met: {missing}"


def test_every_multiple_table_use_case_is_answered(all_queries, use_cases):
    """Every use case with multipleColumns in use_cases.json is answered by a query, and every use case a query
    names has multipleColumns."""
    claimed = {u for x in all_queries for u in x.use_cases}
    wanted = {u for u, v in use_cases.items() if v.get("multipleColumns")}
    assert not wanted - claimed, f"use cases with multipleColumns but no query: {sorted(wanted - claimed)}"
    assert not claimed - wanted, f"queries name use cases without multipleColumns: {sorted(claimed - wanted)}"


def test_declared_columns_are_read(all_queries, use_cases, db):
    """Every column a use case declares under multipleColumns is read by a query answering it, so the heat map
    shows nothing the queries do not read."""
    bad = {}
    for u, v in use_cases.items():
        for t, cs in (v.get("multipleColumns") or {}).items():
            read = set()
            for x in all_queries:
                if u in x.use_cases:
                    read |= set(plan_reads(x, db).get(t, []))
            if set(cs) - read:
                bad[f"{u} {t}"] = sorted(set(cs) - read)
    assert not bad, f"declared but read by no query answering the use case: {bad}"


def test_tags_are_unique_and_in_order(all_queries):
    tags = [x.tag for x in all_queries]
    assert tags == [f"M{i}" for i in range(1, len(tags) + 1)], f"query tags {tags}"
