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
  errors       use cases whose right answer is a refusal (expected_errors.sql, tagged [E#]): MySQL must
               raise exactly the expected error and leave the data unchanged.
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
              "CURDATE", "CURTIME", "YEAR", "MONTH", "DAY", "IFNULL", "COALESCE", "NULLIF"]
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
def test_comment_contract(query, use_cases):
    """Preceded by a purpose comment that carries a tag, the table, use cases, a business question and
    the requirements it meets; every use case it names exists."""
    assert query.tag, "comment has no [S#] tag"
    assert query.table in NON_ASSOCIATIVE, f"tag must name a non-associative table, got {query.table!r}"
    assert query.use_cases, "comment names no use case (Use cases: UC-xx)"
    unknown = [u for u in query.use_cases if u not in use_cases]
    assert not unknown, f"use cases not in use_cases.json: {unknown}"
    assert len(query.question) > 20, "comment has no business question"
    assert query.declared, "comment lists no brief requirements (Requirements: (a) ...)"
    from conftest import record
    record(query.tag, table=query.table, use_cases=query.use_cases, question=query.question,
           declared=query.declared, sql=query.sql)


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
    record(query.tag, columns_out=cols, rows=[[None if v is None else str(v) for v in r] for r in rows])
    assert cols == want_cols, f"columns {cols} != {want_cols}"
    assert len(rows) == len(want), f"{len(rows)} rows, oracle has {len(want)}"
    for i, (g, w) in enumerate(zip(rows, want), 1):
        assert g == w, f"row {i}: MySQL {g} != oracle {w}"


def test_result_is_deterministic(query, db):
    """Two runs give identical results: every ORDER BY breaks its ties."""
    assert run(db, query.sql) == run(db, query.sql)


# ============================================================================ behaviour (targeted)
@pytest.fixture
def tx(db):
    """A cursor inside a transaction that is always rolled back."""
    db.rollback()
    with db.cursor() as cur:
        yield cur
    db.rollback()


@pytest.fixture
def q(pytestconfig):
    from conftest import parse_queries, find_file
    return {x.tag: x for x in parse_queries(find_file(pytestconfig, "sql"))}


def add(cur, tables, table, row):
    """Insert a row in MySQL (inside tx) and the same row into a copy of the oracle's data."""
    cols = list(row)
    vals = [bytes.fromhex(v[2:]) if isinstance(v, str) and v.startswith("0x") else v for v in row.values()]
    cur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", vals)
    tables[table]["rows"].append({k: (None if v is None else str(v)) for k, v in row.items()})


def check(cur, query, tables):
    cur.execute(query.sql)
    got = [tuple(canon(v) for v in r) for r in cur.fetchall()]
    want = ORACLES[query.tag](tables)[1]
    assert got == want, f"MySQL {got} != oracle {want}"
    return got


def test_s1_verified_artist_without_country_is_held(tx, q, data):
    """The 'no payment country' branch: never reached by the sample data (the one artist with no country
    is also unverified, and the first WHEN wins)."""
    t = copy.deepcopy(data)
    add(tx, t, "artist", {"artist_id": 9001, "stage_name": "Zero Country", "country": None,
                          "joined_date": "2026-09-01", "payout_rate": "0.0020", "verified": 1})
    rows = check(tx, q["S1"], t)
    row = [r for r in rows if r[0] == 9001][0]
    assert row[4] == "HOLD: no payment country" and row[1] == "Zero Country (--)"


def test_s1_equal_rates_break_ties_on_artist_id(tx, q, data):
    t = copy.deepcopy(data)
    add(tx, t, "artist", {"artist_id": 900, "stage_name": "Aardvark Tie", "country": "US",
                          "joined_date": "2026-01-01", "payout_rate": "0.0040", "verified": 1})
    rows = check(tx, q["S1"], t)
    assert [r[0] for r in rows[:2]] == [900, 1042]


def test_s2_unscored_new_release_stays_off_the_shelf(tx, q, data):
    t = copy.deepcopy(data)
    add(tx, t, "track", {"track_id": 9100, "artist_id": 1042, "title": "Fresh But Unscored", "duration": 200,
                         "release_date": "2026-09-29", "audio_checksum": "0x" + "01" * 32, "ingest_status": "awaiting scoring"})
    rows = check(tx, q["S2"], t)
    assert 9100 not in [r[0] for r in rows]


def test_s2_same_day_releases_order_by_track_id(tx, q, data):
    t = copy.deepcopy(data)
    add(tx, t, "track", {"track_id": 4800, "artist_id": 1043, "title": "Same Day", "duration": 61,
                         "release_date": "2026-07-10", "audio_checksum": "0x" + "02" * 32, "ingest_status": "scored"})
    rows = check(tx, q["S2"], t)
    assert [r[0] for r in rows[:2]] == [4800, 4828] and rows[0][2] == "1:01"


def test_s2_shelf_never_holds_more_than_five(tx, q, data):
    t = copy.deepcopy(data)
    for k in range(3):
        add(tx, t, "track", {"track_id": 9200 + k, "artist_id": 1044, "title": f"New {k}", "duration": 120,
                             "release_date": f"2026-09-2{k}", "audio_checksum": "0x" + f"1{k}" * 32, "ingest_status": "scored"})
    rows = check(tx, q["S2"], t)
    assert len(rows) == 5 and rows[0][0] == 9202


def test_s3_genre_without_description_is_hidden(tx, q, data):
    t = copy.deepcopy(data)
    tx.execute("UPDATE genre SET description = NULL WHERE genre_id = 9")
    [g for g in t["genre"]["rows"] if g["genre_id"] == "9"][0]["description"] = None
    rows = check(tx, q["S3"], t)
    assert rows[9][2:] == ("(no description)", "HIDE: no description for the composer")


def test_s4_tier_with_no_listeners_is_absent(tx, q, data):
    t = copy.deepcopy(data)
    tx.execute("UPDATE listener SET plan_tier = 'standard' WHERE plan_tier = 'premium'")
    for l in t["listener"]["rows"]:
        if l["plan_tier"] == "premium": l["plan_tier"] = "standard"
    rows = check(tx, q["S4"], t)
    assert [r[0] for r in rows] == ["standard", "free"] and rows[0][1] == 5


def test_s5_accuracy_tie_prefers_the_newer_version(tx, q, data):
    t = copy.deepcopy(data)
    add(tx, t, "scoring_model", {"model_id": 6, "version_label": "tie_newer", "fusion_type": "gated",
                                 "embedding_dimension": 256, "segment_length": 10, "training_corpus": "GTZAN",
                                 "holdout_accuracy": "0.7887", "deployed_on": "2026-09-01"})
    rows = check(tx, q["S5"], t)
    assert [r[0] for r in rows] == ["tie_newer", "beardown_3sec", "beardown_rrm"]


def test_s6_window_of_exactly_half_is_not_wide(tx, q, data):
    t = copy.deepcopy(data)
    add(tx, t, "station", {"station_id": 7799, "listener_id": 20938, "model_id": 3, "name": "Edge Window",
                           "minimum_ambiguity": "0.25", "maximum_ambiguity": "0.75", "created_on": "2026-09-01"})
    rows = check(tx, q["S6"], t)
    m3 = [r for r in rows if r[0] == 3][0]
    assert m3[1:4] == (1, Decimal("0.50"), 0)


def test_s7_new_rejection_is_counted_in_pipeline_order(tx, q, data):
    t = copy.deepcopy(data)
    add(tx, t, "track", {"track_id": 9300, "artist_id": 1049, "title": "Clipped Master", "duration": 30,
                         "release_date": "2026-09-28", "audio_checksum": "0x" + "03" * 32, "ingest_status": "rejected"})
    rows = check(tx, q["S7"], t)
    assert [r[0] for r in rows] == ["awaiting scoring", "scored", "rejected"]
    assert rows[2][1:4] == (2, "2026-09-28", 2)


# ============================================================================ expected errors
def test_expected_error_is_raised(error_case, db, data, use_cases):
    """The database refuses the write with exactly the expected error, and nothing changes.
    Statements live in expected_errors.sql; each answers a use case marked expectsError."""
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
    record(e.tag, table=table, use_cases=e.use_cases, question=e.question, sql=e.sql, kind="expected_error",
           expects=f"{code_} {constraint}", got=(f"{got.args[0]} {got.args[1]}" if got else "no error"))
    assert got is not None, "the statement succeeded; it must be refused"
    assert got.args[0] == code_, f"error {got.args[0]} ({got.args[1]}), expected {code_}"
    assert constraint in str(got.args[1]), f"error names {got.args[1]!r}, expected {constraint}"
    assert after == before == len(data[table]["rows"]), f"{table} changed: {before} -> {after} rows"


# ============================================================================ coverage (whole file)
@pytest.fixture(scope="module")
def all_queries(pytestconfig):
    from conftest import parse_queries, find_file
    return parse_queries(find_file(pytestconfig, "sql"))


def test_every_non_associative_table_is_queried(all_queries):
    missing = sorted(set(NON_ASSOCIATIVE) - {x.table for x in all_queries})
    assert not missing, f"no query on {missing}"


def test_each_requirement_is_met_at_least_twice(all_queries):
    counts = {f: sum(1 for x in all_queries if f in features(x)) for f in "abcde"}
    weak = {f: n for f, n in counts.items() if n < 2}
    assert not weak, f"requirements met fewer than twice: {weak} (all: {counts})"


def test_every_single_table_use_case_is_answered(all_queries, use_cases):
    from conftest import parse_queries, ERRORS_FILE
    errors = parse_queries(ERRORS_FILE) if ERRORS_FILE.is_file() else []
    claimed = {(u, x.table) for x in list(all_queries) + errors for u in x.use_cases}
    missing = [u["id"] for u in use_cases.values() if u.get("single")
               and not any((u["id"], t) in claimed for t in u["single"])]
    assert not missing, f"single-table use cases with no query: {missing}"


def test_tags_are_unique_and_in_order(all_queries):
    tags = [x.tag for x in all_queries]
    assert tags == [f"S{i}" for i in range(1, len(tags) + 1)], f"tags {tags}"
