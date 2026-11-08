"""Unit tests for single_table.sql (INFO 579 Project 2, Task 2).

Four layers:
  contract     each query follows the brief and the course: purpose comment with tag, use cases and
               business question; read-only SELECT, no SELECT *; exactly one table (MySQL EXPLAIN);
               the brief requirements it declares are the ones it really uses; it reads only the
               columns its use cases declare in use_cases.json.
  correctness  each result equals an independent answer computed in Python from data.csv (oracle.py),
               row for row, in order, to the exact decimal; two runs give the same result.
  behaviour    logic the sample data never exercises: a row is added or changed inside a
               transaction, the query is checked, and everything is rolled back.
  errors       use cases whose right answer is a refusal: the [E#] statements at the end of
               single_table.sql, marked EXPECTED TO FAIL. MySQL must raise exactly the expected error and
               leave the data unchanged.
  coverage     the file as a whole: every non-associative table queried, every requirement (a)-(e)
               met at least twice, every single-table use case answered (by a query or an expected
               error), tags unique and in order.

Run (from the repo root or the test-kit folder):
    python -m pytest project2/tests -v          (repo)
    python -m pytest -v                         (test kit)
"""
import copy, json, re
from decimal import Decimal

import pytest

from conftest import run, strip_literals, canon
from oracle import ORACLES

NON_ASSOCIATIVE = ["artist", "track", "genre", "listener", "scoring_model", "station"]

# Course function lists (Unit 6: single-row and aggregate functions; Unit 8: control flow).
SINGLE_ROW = ["CONCAT", "LENGTH", "CHAR_LENGTH", "SUBSTR", "SUBSTRING", "INSTR", "TRIM", "REPLACE", "LPAD", "RPAD",
              "UPPER", "LOWER", "LEFT", "RIGHT", "ABS", "POW", "POWER", "SQRT", "ROUND", "TRUNCATE", "FLOOR", "CEIL",
              "CEILING", "MOD", "DATE", "TIME", "EXTRACT", "DATE_FORMAT", "DATE_ADD", "DATE_SUB", "DATEDIFF", "NOW",
              "CURDATE", "CURTIME", "YEAR", "MONTH", "DAY"]
# IFNULL, COALESCE and NULLIF are "NULL handling functions" in the Unit 8 slides, a group of their own: they count as
# neither (a) single-row nor (e) selection control.
AGGREGATE = ["COUNT", "SUM", "AVG", "STD", "STDDEV", "MAX", "MIN"]


def code(q):
    return strip_literals(q.sql).upper()


def call(fn, text):
    return re.search(r"\b" + fn + r"\s*\(", text) is not None


def features(q):
    c = code(q)
    found = set()
    if any(call(f, c) for f in SINGLE_ROW): found.add("a")
    if any(call(f, c) for f in AGGREGATE): found.add("b")
    if re.search(r"\bORDER\s+BY\b", c): found.add("c")
    if re.search(r"\bLIMIT\s+\d+", c): found.add("d")
    if re.search(r"\bCASE\b[\s\S]*?\bEND\b", c) or call("IF", c): found.add("e")   # Unit 8: CASE and IF
    return sorted(found)


def columns_read(q, data):
    c = strip_literals(q.sql).lower()
    c = re.sub(r"\bas\s+\w+", " ", c)                    # aliases are names we give, not columns we read
    c = re.sub(r"\bcrossfade\.\w+", " ", c)              # the table reference itself
    words = set(re.findall(r"\b[a-z_][a-z0-9_]*\b", c))
    return sorted(w for w in data[q.table]["columns"] if w in words) if q.table in data else []


def allowed_columns(q, use_cases):
    allowed = set()
    for uid in q.use_cases:
        u = use_cases.get(uid, {})
        allowed |= set((u.get("singleColumns") or {}).get(q.table) or (u.get("columns") or {}).get(q.table) or [])
    return allowed


# ============================================================================ contract (per query)
def test_comment_contract(query, use_cases, data):
    """Preceded by a purpose comment that carries a tag, the table, use cases, the business need, a business
    question, the requirements it meets and its output columns; every use case it names exists, and the output
    columns are the ones the oracle answers with."""
    assert query.tag, "comment has no [S#] tag"
    assert query.table in NON_ASSOCIATIVE, f"tag must name a non-associative table, got {query.table!r}"
    assert query.use_cases, "comment names no use case (Use cases: UC-xx)"
    unknown = [u for u in query.use_cases if u not in use_cases]
    assert not unknown, f"use cases not in use_cases.json: {unknown}"
    assert len(query.question) > 20, "comment has no business question"
    assert query.declared, "comment lists no brief requirements (Requirements: (a) ...)"
    assert len(query.need) > 20, "comment states no business need (Business need: ...)"
    assert query.output, "comment lists no output columns (Output: col, col, ...)"
    if query.tag in ORACLES:
        want = ORACLES[query.tag](data)[0]
        assert query.output == want, f"Output: lists {query.output}, the oracle answers with {want}"
    from conftest import record
    record(query.tag, table=query.table, use_cases=query.use_cases, question=query.question, need=query.need,
           declared=query.declared, output=query.output, sql=query.sql)


def test_read_only_select(query):
    """A single read-only SELECT, no SELECT *, and nothing outside the crossfade database."""
    c = code(query)
    assert c.lstrip().startswith("SELECT"), "not a SELECT"
    assert not re.search(r"SELECT\s+(DISTINCT\s+)?\*", c), "SELECT * is a generic query (brief: avoid trivial and generic)"
    for verb in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE INTO"):
        assert not re.search(r"\b" + verb + r"\b", c), f"{verb} in a query file"
    schemas = set(re.findall(r"\b([a-z_][a-z0-9_]*)\.[a-z_]", strip_literals(query.sql).lower()))
    assert schemas <= {"crossfade"}, f"refers to other schemas: {schemas - {'crossfade'}}"


def test_reads_exactly_one_table(query, db):
    """MySQL's own plan (EXPLAIN FORMAT=JSON) touches exactly the one table the tag names."""
    with db.cursor() as cur:
        cur.execute("EXPLAIN FORMAT=JSON " + query.sql)
        plan = json.loads(cur.fetchone()[0])
    tables = set()

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("table_name"), str) and not x["table_name"].startswith("<"):
                tables.add(x["table_name"])
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(plan)
    assert tables == {query.table}, f"plan reads {sorted(tables)}, comment says {query.table}"


def test_requirements_match_declared(query):
    """The brief requirements (a)-(e) the comment claims are exactly the ones the SQL uses."""
    found = features(query)
    from conftest import record
    record(query.tag, detected=found)
    assert found == query.declared, f"comment declares {query.declared}, SQL uses {found}"


def test_columns_match_use_cases(query, data, use_cases):
    """Strict: every column the query reads is one its use cases declare (keeps the heat map honest)."""
    read = columns_read(query, data)
    allowed = allowed_columns(query, use_cases)
    from conftest import record
    record(query.tag, columns=read)
    assert read, "reads no column of its table"
    extra = sorted(set(read) - allowed)
    assert not extra, f"reads {extra}, which {query.use_cases} do not declare for {query.table} in use_cases.json"


# ============================================================================ correctness (per query)
def test_result_matches_oracle(query, db, data):
    """Same columns, same rows, same order, exact values as the Python answer from data.csv."""
    assert query.tag in ORACLES, f"no oracle for {query.tag}"
    cols, rows = run(db, query.sql)
    want_cols, want = ORACLES[query.tag](data)
    from conftest import record
    record(query.tag, columns_out=cols, rows=[[None if v is None else str(v) for v in r] for r in rows],
           expected={"columns": want_cols, "rows": strs(want)})
    assert cols == want_cols, f"columns {cols} != {want_cols}"
    assert len(rows) == len(want), f"{len(rows)} rows, oracle has {len(want)}"
    for i, (g, w) in enumerate(zip(rows, want), 1):
        assert g == w, f"row {i}: MySQL {g} != oracle {w}"


def top_level(clause_re, c):
    """The body of a top-level ORDER BY or GROUP BY (not inside a subquery) of an upper-cased, literal-free
    statement, up to the next top-level clause; None if there is none."""
    for m in re.finditer(clause_re, c):
        if c[:m.start()].count("(") != c[:m.start()].count(")"):
            continue                                      # inside parentheses: a subquery's clause
        rest = c[m.end():]
        stop = r"\b(HAVING|ORDER\s+BY|LIMIT)\b" if "GROUP" in clause_re else r"\bLIMIT\b"
        cut = re.search(stop, rest)
        return rest[:cut.start()] if cut else rest
    return None


def plain_columns(clause):
    """Bare column names in a comma list at depth 0 (`col`, `col DESC`, `t.col ASC`); expressions are skipped."""
    out, d, cur = [], 0, ""
    for ch in clause + ",":
        if ch == "(": d += 1
        if ch == ")": d -= 1
        if ch == "," and d == 0:
            m = re.fullmatch(r"\s*(?:\w+\.)?(\w+)(?:\s+(?:ASC|DESC))?\s*", cur)
            if m: out.append(m.group(1).lower())
            cur = ""
        else:
            cur += ch
    return out


def test_result_is_deterministic(query, db):
    """The row order cannot depend on chance: ORDER BY includes columns that are unique per output row (a primary
    or unique key of the table, or all the GROUP BY columns), so no two rows can tie on every sort key. Two runs
    alone cannot prove this: MySQL usually returns tied rows in primary-key order, which hides a missing
    tie-break. Then two runs must also agree."""
    c = code(query)
    order = top_level(r"\bORDER\s+BY\b", c)
    assert order is not None, "no ORDER BY: the row order is up to the server"
    keys = plain_columns(order)
    with db.cursor() as cur:
        cur.execute("SELECT INDEX_NAME, COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = 'crossfade' "
                    "AND TABLE_NAME = %s AND NON_UNIQUE = 0 ORDER BY INDEX_NAME, SEQ_IN_INDEX", (query.table,))
        unique = {}
        for idx, col in cur.fetchall():
            unique.setdefault(idx, []).append(col.lower())
    sets = list(unique.values())
    group = top_level(r"\bGROUP\s+BY\b", c)
    if group is not None:
        sets = [plain_columns(group)]                    # one output row per group: the group key is unique
    ok = any(s and set(s) <= set(keys) for s in sets)
    assert ok, (f"ORDER BY {', '.join(keys) or order.strip()} can tie: it includes no unique key "
                f"({' or '.join('(' + ', '.join(s) + ')' for s in sets)}), so tied rows come back in whatever order "
                f"MySQL finds them")
    assert run(db, query.sql) == run(db, query.sql)


# ============================================================================ behaviour (targeted)
# Each behaviour test is one "case": its inputs (rows added, statements run), the oracle's expected
# result on the changed data, and MySQL's actual result are logged and written to the results
# snapshot, so the site can show every case. The docstring is the case's description:
# first line = title, then "Why:" and "Expect:".
CASE = {}


def strs(rows):
    return [[None if v is None else str(v) for v in r] for r in rows]


@pytest.fixture(autouse=True)
def case_log(request):
    m = re.match(r"test_s(\d+)_", request.node.name)
    if m:
        CASE.clear()
        CASE.update(tag="S" + m.group(1), inputs=[])
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
        pytest.fail(f"[{tag}] has no statement in single_table.sql yet: write the query under its comment")


@pytest.fixture
def q(pytestconfig):
    from conftest import parse_queries, find_file
    return Written({x.tag: x for x in parse_queries(find_file(pytestconfig, "sql"))})


def add(cur, tables, table, row):
    """Insert a row in MySQL (inside tx) and the same row into a copy of the oracle's data."""
    cols = list(row)
    vals = [bytes.fromhex(v[2:]) if isinstance(v, str) and v.startswith("0x") else v for v in row.values()]
    cur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", vals)
    tables[table]["rows"].append({k: (None if v is None else str(v)) for k, v in row.items()})
    CASE.setdefault("inputs", []).append({"kind": "insert", "table": table,
                                          "row": {k: (None if v is None else str(v)) for k, v in row.items()}})


def change(cur, sql):
    """Run a data change inside tx (it is rolled back) and log it as a case input."""
    cur.execute(sql)
    CASE.setdefault("inputs", []).append({"kind": "update", "sql": sql, "rows": cur.rowcount})


def check(cur, query, tables):
    cur.execute(query.sql)
    got = [tuple(canon(v) for v in r) for r in cur.fetchall()]
    want_cols, want = ORACLES[query.tag](tables)
    CASE.update(columns=want_cols, expected=strs(want), got=strs(got))
    assert got == want, f"MySQL {got} != oracle {want}"
    return got


def test_s1_verified_artist_without_country_is_held(tx, q, data):
    """A verified artist with no payment country is held, not paid.
    Why: the sample data never reaches this CASE branch (its one artist with no country is also unverified,
    and the first WHEN wins).
    Expect: artist 9001 reads 'HOLD: no payment country', payee 'Zero Country (--)'."""
    t = copy.deepcopy(data)
    add(tx, t, "artist", {"artist_id": 9001, "stage_name": "Zero Country", "country": None,
                          "joined_date": "2026-09-01", "payout_rate": "0.0020", "verified": 1})
    rows = check(tx, q["S1"], t)
    row = [r for r in rows if r[0] == 9001][0]
    assert row[4] == "HOLD: no payment country" and row[1] == "Zero Country (--)"


def test_s1_equal_rates_break_ties_on_artist_id(tx, q, data):
    """Two payable artists on the same rate are ordered by artist_id.
    Why: without a tie-break the order of equal rates is up to MySQL and could change between runs.
    Expect: artist 900 (rate 0.0040, same as 1042) is listed first, 1042 second."""
    t = copy.deepcopy(data)
    add(tx, t, "artist", {"artist_id": 900, "stage_name": "Aardvark Tie", "country": "US",
                          "joined_date": "2026-01-01", "payout_rate": "0.0040", "verified": 1})
    rows = check(tx, q["S1"], t)
    assert [r[0] for r in rows[:2]] == [900, 1042]


def test_s2_unscored_new_release_stays_off_the_shelf(tx, q, data):
    """The newest upload stays off the shelf until it is scored.
    Why: only scored recordings can be streamed, so date alone must not put a track on the shelf.
    Expect: track 9100 (released 2026-09-29, awaiting scoring) is not in the result."""
    t = copy.deepcopy(data)
    add(tx, t, "track", {"track_id": 9100, "artist_id": 1042, "title": "Fresh But Unscored", "duration": 200,
                         "release_date": "2026-09-29", "audio_checksum": "0x" + "01" * 32, "ingest_status": "awaiting scoring"})
    rows = check(tx, q["S2"], t)
    assert 9100 not in [r[0] for r in rows]


def test_s2_same_day_releases_order_by_track_id(tx, q, data):
    """Two releases on the same day are ordered by track_id, and run time is shown as m:ss.
    Why: same-day releases tie on the date; 61 seconds checks the seconds are zero-padded.
    Expect: 4800 then 4828 at the top; 4800's run_time is '1:01'."""
    t = copy.deepcopy(data)
    add(tx, t, "track", {"track_id": 4800, "artist_id": 1043, "title": "Same Day", "duration": 61,
                         "release_date": "2026-07-10", "audio_checksum": "0x" + "02" * 32, "ingest_status": "scored"})
    rows = check(tx, q["S2"], t)
    assert [r[0] for r in rows[:2]] == [4800, 4828] and rows[0][2] == "1:01"


def test_s2_shelf_never_holds_more_than_five(tx, q, data):
    """The shelf never shows more than five recordings.
    Why: the sample data has exactly enough scored tracks that LIMIT 5 is never pushed.
    Expect: 5 rows, newest first: track 9202 (released 2026-09-22)."""
    t = copy.deepcopy(data)
    for k in range(3):
        add(tx, t, "track", {"track_id": 9200 + k, "artist_id": 1044, "title": f"New {k}", "duration": 120,
                             "release_date": f"2026-09-2{k}", "audio_checksum": "0x" + f"1{k}" * 32, "ingest_status": "scored"})
    rows = check(tx, q["S2"], t)
    assert len(rows) == 5 and rows[0][0] == 9202


def test_s3_genre_without_description_is_hidden(tx, q, data):
    """A genre with no description is flagged to be hidden from the blend composer.
    Why: every genre in the sample data has a description, so the HIDE branch is never reached.
    Expect: genre 9 (rock) shows 'rock: (no description)' and 'HIDE: no description for the composer'."""
    t = copy.deepcopy(data)
    change(tx, "UPDATE genre SET description = NULL WHERE genre_id = 9")
    [g for g in t["genre"]["rows"] if g["genre_id"] == "9"][0]["description"] = None
    rows = check(tx, q["S3"], t)
    assert rows[9][2:] == ("rock: (no description)", "HIDE: no description for the composer")


def test_s4_tier_with_no_listeners_is_absent(tx, q, data):
    """A plan tier nobody is on does not appear in the subscriber mix.
    Why: every tier has listeners in the sample data; GROUP BY must not invent an empty tier.
    Expect: only standard and free, in tier order, standard with 5 listeners."""
    t = copy.deepcopy(data)
    change(tx, "UPDATE listener SET plan_tier = 'standard' WHERE plan_tier = 'premium'")
    for l in t["listener"]["rows"]:
        if l["plan_tier"] == "premium": l["plan_tier"] = "standard"
    rows = check(tx, q["S4"], t)
    assert [r[0] for r in rows] == ["standard", "free"] and rows[0][1] == 5


def test_s5_accuracy_tie_prefers_the_newer_version(tx, q, data):
    """On equal holdout accuracy the more recently deployed version becomes the default.
    Why: the sample's top version has no tie, so the deployed_on tie-break is never used for the default.
    Expect: tie_newer (accuracy 0.7887 like beardown_3sec, but deployed later, 2026-09-01) is the one default."""
    t = copy.deepcopy(data)
    add(tx, t, "scoring_model", {"model_id": 6, "version_label": "tie_newer", "fusion_type": "gated",
                                 "embedding_dimension": 256, "segment_length": 10, "training_corpus": "GTZAN",
                                 "holdout_accuracy": "0.7887", "deployed_on": "2026-09-01"})
    rows = check(tx, q["S5"], t)
    assert [r[0] for r in rows] == ["tie_newer"]


def test_s5_full_tie_goes_to_the_lower_model_id(tx, q, data):
    """Two versions tied on both accuracy and deployment date: the lower model_id is the default, every time.
    Why: without a last tie-break, LIMIT 1 would return whichever tied row MySQL found first.
    Expect: tie_low (model_id 6) wins over tie_high (model_id 7); both at 0.9000, both deployed 2026-09-01, above
    every sample version. tie_high is inserted first, so insertion order cannot be what decides."""
    t = copy.deepcopy(data)
    for mid, label in ((7, "tie_high"), (6, "tie_low")):
        add(tx, t, "scoring_model", {"model_id": mid, "version_label": label, "fusion_type": "concat",
                                     "embedding_dimension": 384, "segment_length": 3, "training_corpus": "GTZAN",
                                     "holdout_accuracy": "0.9000", "deployed_on": "2026-09-01"})
    rows = check(tx, q["S5"], t)
    assert [r[0] for r in rows] == ["tie_low"]


def test_s6_window_of_exactly_half_is_not_wide(tx, q, data):
    """An ambiguity window of exactly 0.50 is not counted as wide.
    Why: 'wide' means more than half the range; the boundary itself is not in the sample data.
    Expect: model 3 (only station 7799, window 0.25 to 0.75): 1 station, avg_window 0.50, 0 wide."""
    t = copy.deepcopy(data)
    add(tx, t, "station", {"station_id": 7799, "listener_id": 20938, "model_id": 3, "name": "Edge Window",
                           "minimum_ambiguity": "0.25", "maximum_ambiguity": "0.75", "created_on": "2026-09-01"})
    rows = check(tx, q["S6"], t)
    m3 = [r for r in rows if r[0] == 3][0]
    assert m3[1:4] == (1, Decimal("0.50"), 0)


def test_s7_new_rejection_is_counted_in_pipeline_order(tx, q, data):
    """A new rejection is counted, and statuses stay in pipeline order, not alphabetical.
    Why: ingest_status is an ENUM; ORDER BY must follow awaiting scoring, scored, rejected.
    Expect: rejected shows 2 recordings, earliest release 2026-09-22 (8 days ago), 'never streamable: rejected'."""
    t = copy.deepcopy(data)
    add(tx, t, "track", {"track_id": 9300, "artist_id": 1049, "title": "Clipped Master", "duration": 30,
                         "release_date": "2026-09-28", "audio_checksum": "0x" + "03" * 32, "ingest_status": "rejected"})
    rows = check(tx, q["S7"], t)
    assert [r[0] for r in rows] == ["awaiting scoring", "scored", "rejected"]
    assert rows[2][1:] == (2, "2026-09-22", -8, "never streamable: rejected")


def test_s7_unscored_recording_before_its_release_is_on_time(tx, q, data):
    """An unscored recording whose release date is still ahead is on time, not late.
    Why: the sample's one unscored recording is already past its release date (LATE), so the on-time branch is
    never reached.
    Expect: with its release moved to 2026-10-15, awaiting scoring reads 15 days ahead, 'on time: release date still ahead'."""
    t = copy.deepcopy(data)
    change(tx, "UPDATE track SET release_date = '2026-10-15' WHERE ingest_status = 'awaiting scoring'")
    for r in t["track"]["rows"]:
        if r["ingest_status"] == "awaiting scoring": r["release_date"] = "2026-10-15"
    rows = check(tx, q["S7"], t)
    assert rows[0][1:] == (1, "2026-10-15", 15, "on time: release date still ahead")


def test_s7_release_due_on_the_report_date_is_late(tx, q, data):
    """A release due on the report date itself, still unscored, is already late.
    Why: the boundary: on its release day the recording must already be streamable, so 'reached' includes the day.
    Expect: with its release moved to 2026-09-30, awaiting scoring reads 0 days, 'LATE: release date reached, still unscored'."""
    t = copy.deepcopy(data)
    change(tx, "UPDATE track SET release_date = '2026-09-30' WHERE ingest_status = 'awaiting scoring'")
    for r in t["track"]["rows"]:
        if r["ingest_status"] == "awaiting scoring": r["release_date"] = "2026-09-30"
    rows = check(tx, q["S7"], t)
    assert rows[0][1:] == (1, "2026-09-30", 0, "LATE: release date reached, still unscored")


# ============================================================================ expected errors
def test_expected_error_is_raised(error_case, db, data, use_cases):
    """The database refuses the write with exactly the expected error, and nothing changes.
    The [E#] statements sit at the end of single_table.sql; each answers a use case marked expectsError."""
    import pymysql
    e = error_case
    assert e.tag and e.tag.startswith("E"), "error statements are tagged [E#]"
    assert e.expects, "comment has no 'Expects: <errno> <constraint>' line"
    assert e.use_cases and all(use_cases.get(u, {}).get("expectsError") for u in e.use_cases), \
        f"{e.use_cases} must be use cases marked expectsError in use_cases.json"
    code_, constraint = e.expects
    for u in e.use_cases:
        assert use_cases[u]["expectsError"]["code"] == code_ and use_cases[u]["expectsError"]["constraint"] == constraint, \
            f"comment expects {code_} {constraint}, use_cases.json says {use_cases[u]['expectsError']}"
    table = e.table
    db.rollback()
    with db.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        before = cur.fetchone()[0]
        got = None
        try:
            cur.execute(e.sql)
        except pymysql.err.MySQLError as err:
            got = err
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        after = cur.fetchone()[0]
    db.rollback()
    from conftest import record
    record(e.tag, table=table, use_cases=e.use_cases, question=e.question, need=e.need, sql=e.sql, kind="expected_error",
           expects=f"{code_} {constraint}", got=(f"{got.args[0]} {got.args[1]}" if got else "no error"))
    assert got is not None, "the statement succeeded; it must be refused"
    assert got.args[0] == code_, f"error {got.args[0]} ({got.args[1]}), expected {code_}"
    assert constraint in str(got.args[1]), f"error names {got.args[1]!r}, expected {constraint}"
    assert after == before == len(data[table]["rows"]), f"{table} changed: {before} -> {after} rows"


# ============================================================================ coverage (whole file)
@pytest.fixture(scope="module")
def all_statements(pytestconfig):
    from conftest import parse_queries, find_file
    return parse_queries(find_file(pytestconfig, "sql"))


@pytest.fixture(scope="module")
def all_queries(all_statements):
    return [x for x in all_statements if not x.is_error]


def test_every_non_associative_table_is_queried(all_queries):
    missing = sorted(set(NON_ASSOCIATIVE) - {x.table for x in all_queries})
    assert not missing, f"no query on {missing}"


def test_each_requirement_is_met_at_least_twice(all_queries):
    counts = {f: sum(1 for x in all_queries if f in features(x)) for f in "abcde"}
    weak = {f: n for f, n in counts.items() if n < 2}
    assert not weak, f"requirements met fewer than twice: {weak} (all: {counts})"


def test_every_single_table_use_case_is_answered(all_statements, use_cases):
    claimed = {(u, x.table) for x in all_statements for u in x.use_cases}
    missing = [u["id"] for u in use_cases.values() if u.get("single")
               and not any((u["id"], t) in claimed for t in u["single"])]
    assert not missing, f"single-table use cases with no query: {missing}"


def test_tags_are_unique_and_in_order(all_statements):
    """Queries S1, S2, ... in order, then the EXPECTED TO FAIL statements E1, E2, ... last: an error stops a
    script run, so nothing may come after one."""
    tags = [x.tag for x in all_statements]
    s = [t for t in tags if t and t[0] == "S"]
    e = [t for t in tags if t and t[0] == "E"]
    assert s == [f"S{i}" for i in range(1, len(s) + 1)], f"query tags {s}"
    assert e == [f"E{i}" for i in range(1, len(e) + 1)], f"error tags {e}"
    assert tags == s + e, f"every [E#] statement must come after every [S#] query; file order is {tags}"
