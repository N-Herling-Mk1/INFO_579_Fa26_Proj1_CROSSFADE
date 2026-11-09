"""Unit tests for routines.sql (INFO 579 Project 2, Task 4).

Layers, as in the query test files:
  contract     each routine follows the brief and the course: purpose comment with tag and name, use cases,
               business need, what it does, the requirement it meets, the Unit 9 features it uses, its tables,
               parameters, return type, errors and an example; MySQL's own catalogue (information_schema) holds it
               exactly as the comment declares it (kind, parameters in order, return type, data access); every
               feature the comment lists is really in its body; it names exactly the tables listed, and only
               columns its use cases declare.
  behaviour    each routine is called on the crossfade database and compared with an independent answer computed
               in Python from data.csv (oracle_routines.py): the rows it writes, the OUT values it returns, and
               the refusals it must give (its own SIGNALs and the database's errors it must not swallow). Every
               call runs inside a transaction that is rolled back.
  coverage     the file as a whole: the brief's mix (2 procedures + 1 function, or 1 + 2), every use case with
               routine columns served, the RA's "no derived values as input", no transaction control inside a
               routine, and the script itself: it re-creates the routines when run again. When
               routines_example_usage.sql is present (repo: project2/examples; example usage, not a deliverable),
               it is run too: its results must match the oracle and it must leave the data unchanged.

Run (from the repo root or the test-kit folder):
    python -m pytest project2/tests/test_routines.py -v      (repo)
    python -m pytest test_routines.py -v                      (test kit)
"""
import copy, hashlib, re
from decimal import Decimal

import pytest

from conftest import canon, blank_code, parse_routines, split_script, find_file
import oracle_routines as O

KINDS = {"FUNCTION": "4 function", "PROCEDURE": "4 procedure"}
DERIVED = {"completed", "royalty_amount", "ingest_status"}     # values the RA says a procedure computes itself
FEATURES = {   # a "Uses:" item -> how to see it in the body
    "DECLARE": r"\bDECLARE\s+(?!EXIT\b|CONTINUE\b)\w+\s+\w+",
    "IF": r"\bIF\b.+\bTHEN\b",
    "ELSEIF": r"\bELSEIF\b",
    "ELSE": r"\bELSE\b",
    "SIGNAL": r"(?<!RE)\bSIGNAL\s+SQLSTATE\b",
    "RESIGNAL": r"\bRESIGNAL\b",
    "HANDLER": r"\bDECLARE\s+(EXIT|CONTINUE)\s+HANDLER\s+FOR\b",
    "1062": r"\bHANDLER\s+FOR\s+1062\b",
    "OUT": r"\bOUT\s+\w+",
    "READS SQL DATA": r"\bREADS\s+SQL\s+DATA\b",
    "MODIFIES SQL DATA": r"\bMODIFIES\s+SQL\s+DATA\b",
    "NOT DETERMINISTIC": r"\bNOT\s+DETERMINISTIC\b",
    "CALLS F": r"\bcrossfade\.\w+\s*\(",
}


@pytest.fixture(scope="module")
def parsed(pytestconfig):
    return parse_routines(find_file(pytestconfig, "rsql"))


@pytest.fixture(scope="module")
def routines(parsed):
    return {r.tag: r for r in parsed[0] if r.tag}


def counts(db):
    with db.cursor() as cur:
        out = {}
        for t in ("artist", "track", "listener", "station", "play", "genre", "scoring_model", "track_score",
                  "genre_probability", "station_blend"):
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            out[t] = cur.fetchone()[0]
    return out


def run_script(db, path):
    """Run a script statement by statement, as the mysql client would after reading its DELIMITER lines.
    Returns what each statement that gives a result (or is a CALL) returned."""
    steps = []
    with db.cursor() as cur:
        for comment, st in split_script(path.read_text(encoding="utf-8")):
            cur.execute(st)
            if cur.description:
                cols = [d[0] for d in cur.description]
                steps.append({"label": comment, "sql": st, "columns": cols,
                              "rows": [[None if v is None else str(canon(v)) for v in r] for r in cur.fetchall()]})
            elif re.match(r"\s*CALL\b", st, re.I):
                steps.append({"label": comment, "sql": st})
    db.rollback()
    return steps


def example_path(pytestconfig):
    """routines_example_usage.sql, or None when it is not around (the test kit ships without it)."""
    try:
        return find_file(pytestconfig, "rex")
    except pytest.UsageError:
        return None


@pytest.fixture(scope="module")
def installed(db, pytestconfig):
    """routines.sql run once (it drops and re-creates the routines), then the example usage script if present,
    its results recorded for the site."""
    before = counts(db)
    created = run_script(db, find_file(pytestconfig, "rsql"))
    ex = example_path(pytestconfig)
    steps = run_script(db, ex) if ex else []
    if ex:
        from conftest import record_demo
        record_demo(steps)
    return {"before": before, "after": counts(db), "created": created, "steps": steps, "example": ex}


def catalogue(db, name):
    with db.cursor() as cur:
        cur.execute("SELECT ROUTINE_TYPE, SQL_DATA_ACCESS, IS_DETERMINISTIC FROM information_schema.ROUTINES "
                    "WHERE ROUTINE_SCHEMA = 'crossfade' AND ROUTINE_NAME = %s", (name,))
        r = cur.fetchone()
        cur.execute("SELECT ORDINAL_POSITION, PARAMETER_MODE, PARAMETER_NAME, DTD_IDENTIFIER FROM "
                    "information_schema.PARAMETERS WHERE SPECIFIC_SCHEMA = 'crossfade' AND SPECIFIC_NAME = %s "
                    "ORDER BY ORDINAL_POSITION", (name,))
        ps = cur.fetchall()
    return r, ps


def norm_type(t):
    return re.sub(r"\s+", " ", t.strip().lower())


def declared_params(r):
    """[(mode, name, type)] from the comment's Parameters: line."""
    out = []
    for p in r.params:
        m = re.match(r"(IN|OUT|INOUT)\s+(\w+)\s+(.+)$", p, re.I)
        out.append((m.group(1).upper(), m.group(2).lower(), norm_type(m.group(3))) if m else ("?", p, "?"))
    return out


def schema_columns(db):
    with db.cursor() as cur:
        cur.execute("SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'crossfade'")
        out = {}
        for t, c in cur.fetchall():
            out.setdefault(t.lower(), set()).add(c.lower())
    return out


def named_tables(r):
    """Tables the body names as crossfade.<table>; crossfade.<name>( after a SELECT, SET or = is a routine call."""
    calls = set(n.lower() for n in re.findall(r"(?<!INTO )\bcrossfade\.(\w+)\s*\(", r.body, re.I))
    return sorted(set(t.lower() for t in re.findall(r"\bcrossfade\.(\w+)\b", r.body)) - calls)


def called(r, routines):
    names = set(n.lower() for n in re.findall(r"(?<!INTO )\bcrossfade\.(\w+)\s*\(", r.body, re.I))
    return [x for x in routines.values() if x.created in names and x is not r]


def touched(r, routines, cols):
    """{table: columns} the routine names in its body, plus those of any routine it calls. A column counts for a
    table the body names when its name appears as a word in the body (literals and comments removed)."""
    words = set(re.findall(r"\b[a-z_][a-z0-9_]*\b", r.body.lower()))
    out = {t: sorted(cols.get(t, set()) & words) for t in named_tables(r)}
    for f in called(r, routines):
        for t, cs in touched(f, routines, cols).items():
            out[t] = sorted(set(out.get(t, [])) | set(cs))
    return out


def declared_columns(uc_ids, use_cases):
    out = {}
    for u in uc_ids:
        for t, cs in (use_cases.get(u, {}).get("routineColumns") or {}).items():
            out.setdefault(t, set()).update(cs)
    return out


# ============================================================================ contract (per routine)
def test_comment_contract(routine, use_cases, installed):
    """Preceded by a purpose comment: tag and name, use cases, business need, what it does, the requirement, the
    Unit 9 features, its tables, parameters, return type (functions only), errors and an example call."""
    r = routine
    assert r.kind, "the statement after the comment is not CREATE FUNCTION or CREATE PROCEDURE"
    assert r.tag[0] == r.kind[0], f"[{r.tag}] tags a {r.kind.lower()}: use F# for functions, P# for procedures"
    assert r.name == r.created, f"comment names {r.name!r}, the statement creates {r.created!r}"
    assert r.schema == "crossfade", "create it as crossfade.<name>, so it lands in the right database"
    assert r.use_cases, "comment names no use case (Use cases: UC-xx)"
    unknown = [u for u in r.use_cases if u not in use_cases]
    assert not unknown, f"use cases not in use_cases.json: {unknown}"
    assert len(r.need) > 40, "comment states no business need (Business need: ...)"
    assert len(r.does) >= 2, "comment does not say what it does, step by step (What it does: - ...)"
    assert re.match(re.escape(KINDS[r.kind]) + r"(\s|$)", r.requirement), \
        f"Requirements: says {r.requirement!r}, expected it to start {KINDS[r.kind]!r}"
    assert r.uses, "comment lists no Unit 9 features (Uses: ...)"
    assert r.tables, "comment lists no tables (Tables: ...)"
    assert r.params, "comment lists no parameters (Parameters: IN name type, ...)"
    assert bool(r.returns) == (r.kind == "FUNCTION"), "Returns: is for functions only, and every function needs it"
    assert r.errors, "comment does not say what it refuses (Errors: ...)"
    assert re.search(r"crossfade\." + r.created + r"\s*\(", r.example), "Example: does not call this routine"
    from conftest import record
    record(r.tag, name=r.created, kind=r.kind, title=r.created, use_cases=r.use_cases, need=r.need, does=r.does,
           requirement=r.requirement, uses=r.uses, tables=r.tables, params=r.params, returns=r.returns,
           errors=r.errors, example=r.example, sql=r.sql)


def test_created_as_declared(routine, db, installed):
    """MySQL's catalogue (information_schema) holds the routine as the comment declares it: its kind, every
    parameter in order with its mode, name and type, and a function's return type."""
    row, ps = catalogue(db, routine.created)
    assert row, f"crossfade.{routine.created} does not exist after running routines.sql"
    assert row[0] == routine.kind, f"MySQL has a {row[0]}, the comment declares a {routine.kind}"
    got = [(m or "IN", n.lower(), norm_type(t)) for pos, m, n, t in ps if pos > 0]
    assert got == declared_params(routine), f"parameters in MySQL {got} != comment {declared_params(routine)}"
    if routine.kind == "FUNCTION":
        ret = [norm_type(t) for pos, m, n, t in ps if pos == 0]
        assert ret == [norm_type(routine.returns)], f"returns {ret} in MySQL, comment says {routine.returns}"
    from conftest import record
    record(routine.tag, catalogue={"type": row[0], "data_access": row[1], "deterministic": row[2],
                                   "parameters": [list(x) for x in got]})


def test_data_access_declared(routine, db, installed):
    """The characteristic tells MySQL the truth: a function that reads tables is READS SQL DATA and NOT
    DETERMINISTIC (the payout rate it reads can change between two calls with the same arguments); a procedure
    that writes is MODIFIES SQL DATA."""
    row, _ = catalogue(db, routine.created)
    writes = re.search(r"\b(INSERT|UPDATE|DELETE|REPLACE)\b", routine.body.upper())
    reads = re.search(r"\bFROM\s+crossfade\.", routine.body, re.I)
    if routine.kind == "FUNCTION":
        assert not writes, "a function must not write (use a procedure)"
        if reads:
            assert row[1] == "READS SQL DATA", f"reads tables but declares {row[1]}"
            assert row[2] == "NO", "reads data that can change, so it must not be DETERMINISTIC"
    elif writes:
        assert row[1] == "MODIFIES SQL DATA", f"writes but declares {row[1]}"


def test_uses_what_it_lists(routine):
    """Every Unit 9 feature the comment lists under Uses: is really in the routine."""
    code = blank_code(routine.sql)
    missing = []
    for item in routine.uses:
        keys = [k for k in FEATURES if re.search(r"(?<![A-Z])" + k + r"(?![A-Z])", item.upper())]
        if not keys:
            continue                                     # a free-text item ("IN / OUT parameters" is checked by OUT)
        if not all(re.search(FEATURES[k], code, re.I | re.S) for k in keys):
            missing.append(item)
    assert not missing, f"listed under Uses: but not in the routine: {missing}"


def test_reads_declared_tables(routine, routines):
    """It names exactly the tables listed under Tables:, counting those of a routine it calls."""
    got = set(named_tables(routine))
    for f in called(routine, routines):
        got |= set(named_tables(f))
    assert got == set(routine.tables), f"names {sorted(got)}, comment says {sorted(routine.tables)}"


def test_columns_are_declared(routine, routines, db, use_cases):
    """Every column the routine reads or writes is declared under routineColumns by one of its use cases in
    use_cases.json, so the use-case heat map never misses what a routine touches."""
    got = touched(routine, routines, schema_columns(db))
    want = declared_columns(routine.use_cases, use_cases)
    from conftest import record
    record(routine.tag, columns=got)
    undeclared = {t: sorted(set(c) - want.get(t, set())) for t, c in got.items() if set(c) - want.get(t, set())}
    assert not undeclared, f"touches columns its use cases {routine.use_cases} do not declare: {undeclared}"


# ============================================================================ behaviour (targeted)
CASE = {}


@pytest.fixture(autouse=True)
def case_log(request):
    m = re.match(r"test_([fp]\d+)_", request.node.name)
    if m:
        CASE.clear()
        CASE.update(tag=m.group(1).upper(), inputs=[])
    yield
    if m:
        from conftest import record_case
        record_case(request.node.name, dict(CASE, doc=(request.node.function.__doc__ or "").strip()))


@pytest.fixture
def tx(db, installed):
    """A cursor inside a transaction that is always rolled back (the routines start no transaction of their own)."""
    db.rollback()
    with db.cursor() as cur:
        yield cur
    db.rollback()


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest().upper()


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, Decimal)):
        return str(v)
    if isinstance(v, bytes):
        return "0x" + v.hex().upper()
    return "'" + str(v).replace("'", "''") + "'"


def call(cur, sql, outs=()):
    """Run one statement, log it as a case input, and return the OUT variables (if any) as text."""
    CASE.setdefault("inputs", []).append({"kind": "call", "sql": sql})
    cur.execute(sql)
    if cur.description:
        return [canon(v) for v in cur.fetchone()]
    if outs:
        cur.execute("SELECT " + ", ".join(outs))
        return [canon(v) for v in cur.fetchone()]
    return []


def refused(cur, sql):
    """Run a statement that must fail; return (MySQL error code, message)."""
    import pymysql
    CASE.setdefault("inputs", []).append({"kind": "call", "sql": sql})
    with pytest.raises(pymysql.MySQLError) as e:
        cur.execute(sql)
    return e.value.args[0], str(e.value.args[1])


def show(columns, expected, got):
    """Log a case's expected (oracle) and actual result as one-row tables, written the same way."""
    s = lambda row: [None if v is None else str(v) for v in row]
    CASE.update(columns=columns, expected=[s(expected)], got=[s(got)])


def add(cur, t, table, row):
    cols = list(row)
    vals = [bytes.fromhex(v[2:]) if isinstance(v, str) and v.startswith("0x") else v for v in row.values()]
    cur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", vals)
    t[table]["rows"].append({k: (None if v is None else str(v)) for k, v in row.items()})
    CASE.setdefault("inputs", []).append({"kind": "insert", "table": table, "row": {k: (None if v is None else str(v)) for k, v in row.items()}})


def play_row(cur, listener, track, at):
    cur.execute("SELECT listener_id, track_id, played_at, station_id, seconds_played, completed, reaction, "
                "royalty_amount FROM play WHERE listener_id = %s AND track_id = %s AND played_at = %s",
                (listener, track, at))
    r = cur.fetchone()
    if r is None:
        return None
    r = list(r)
    r[5] = int.from_bytes(r[5], "big") if isinstance(r[5], (bytes, bytearray)) else r[5]
    return [canon(v) for v in r]


PLAY_COLS = ["listener_id", "track_id", "played_at", "station_id", "seconds_played", "completed", "reaction", "royalty_amount"]


def rp(listener, track, station, seconds, reaction, at):
    return (f"CALL crossfade.record_play({lit(listener)}, {lit(track)}, {lit(station)}, {lit(seconds)}, "
            f"{lit(reaction)}, {lit(at)}, @completed, @royalty)")


def check_play(cur, t, listener, track, station, seconds, reaction, at):
    """Call record_play and compare the row it wrote and its OUT values with the oracle."""
    want = O.record_play(t, listener, track, station, seconds, reaction, at)
    assert want[0] == "row", f"oracle expects a refusal: {want}"
    outs = call(cur, rp(listener, track, station, seconds, reaction, at), ["@completed", "@royalty"])
    w = want[1]
    exp = [canon(w[c]) for c in PLAY_COLS]
    got = play_row(cur, listener, track, at)
    show(PLAY_COLS + ["OUT completed", "OUT royalty"], exp + [canon(w["completed"]), canon(w["royalty_amount"])],
         (got or [None] * 8) + outs)
    assert got == exp, f"row written {got} != oracle {exp}"
    assert outs == [canon(w["completed"]), canon(w["royalty_amount"])], f"OUT values {outs}"
    return w


# ---------------------------------------------------------------------------- F1 play_royalty
def test_f1_agrees_with_every_recorded_play(tx, data):
    """play_royalty gives the royalty already recorded on every sample play.
    Why: rule I7 says the stored amount is the artist's rate for 30 seconds or more, else 0; the function must
    reproduce the 31 sample plays exactly (the rates have not changed since).
    Expect: for each play, play_royalty(track, seconds) = its royalty_amount = the oracle."""
    bad, rows = [], []
    for p in data["play"]["rows"]:
        got = call(tx, f"SELECT crossfade.play_royalty({p['track_id']}, {p['seconds_played']})")[0]
        want = O.royalty(data, p["track_id"], p["seconds_played"])
        rows.append([p["track_id"], p["seconds_played"], str(want), str(got)])
        if not (got == want == Decimal(p["royalty_amount"])):
            bad.append((p["track_id"], p["seconds_played"], p["royalty_amount"], got, want))
    CASE.update(inputs=[{"kind": "call", "sql": "SELECT crossfade.play_royalty(track_id, seconds_played) -- for each of the 31 sample plays"}],
                columns=["track_id", "seconds_played", "oracle", "play_royalty"], expected=rows, got=rows)
    assert not bad, f"(track, seconds, recorded, function, oracle): {bad}"


def test_f1_thirty_seconds_is_the_boundary(tx, data):
    """29 seconds earns nothing; 30 seconds earns the artist's rate; a full play earns the same rate.
    Why: rule I7's boundary is "30 seconds or more"; the sample's shortest play is 10 seconds and none is 29 or 30.
    Expect: play_royalty(4817, s) for s = 0, 29, 30, 214 gives 0, 0, 0.00400, 0.00400 (Velvet Static's rate)."""
    secs = [0, 29, 30, 214]
    got = call(tx, "SELECT " + ", ".join(f"crossfade.play_royalty(4817, {s})" for s in secs))
    want = [O.royalty(data, 4817, s) for s in secs]
    show([f"{s} s" for s in secs], want, got)
    assert got == want


def test_f1_unknown_recording_has_no_royalty(tx, data):
    """A recording that does not exist has no royalty: NULL, not 0.
    Why: 0 would read as "a short play"; there is simply no rate to apply.
    Expect: play_royalty(9999, 200) is NULL; play_royalty(4817, NULL) is NULL."""
    got = call(tx, "SELECT crossfade.play_royalty(9999, 200), crossfade.play_royalty(4817, NULL)")
    show(["track 9999", "no length"], [None, None], got)
    assert got == [None, None]


def test_f1_follows_a_rate_change(tx, data):
    """After an artist's rate changes, the function applies the new rate.
    Why: this is why play_royalty is NOT DETERMINISTIC, and why record_play stores its answer as a snapshot.
    Expect: Velvet Static's rate set to 0.00450: play_royalty(4817, 30) gives 0.00450."""
    t = copy.deepcopy(data)
    call(tx, "UPDATE artist SET payout_rate = 0.00450 WHERE artist_id = 1042")
    next(r for r in t["artist"]["rows"] if r["artist_id"] == "1042")["payout_rate"] = "0.00450"
    got = call(tx, "SELECT crossfade.play_royalty(4817, 30)")
    show(["royalty"], [O.royalty(t, 4817, 30)], got)
    assert got == [Decimal("0.00450")]


# ---------------------------------------------------------------------------- P1 record_play
def test_p1_records_an_abandoned_skip(tx, data):
    """A skipped play of half a recording is recorded as not completed, and still earns the rate.
    Why: rule I7 computes both completed and royalty_amount from the Track and Artist rows.
    Expect: dokafor (20937) skips Low Tide (4817, 214 s) after 107 s: completed 0, royalty 0.00400; the OUT
    parameters return the same two values."""
    check_play(tx, data, 20937, 4817, None, 107, "skipped", "2026-11-01 20:15:00")


def test_p1_full_length_play_is_completed(tx, data):
    """A play as long as the recording is a completed play.
    Why: completed is true "exactly when Seconds Played equals the Duration" (RA).
    Expect: 189 s of Ember Count (4829, 189 s), saved: completed 1, royalty 0.00300."""
    check_play(tx, data, 20937, 4829, None, 189, "saved", "2026-11-01 21:00:00")


def test_p1_short_play_earns_nothing(tx, data):
    """A play under 30 seconds is recorded, earns nothing, and is not completed.
    Why: the royalty rule's boundary inside the procedure, through play_royalty.
    Expect: 29 s of 4817: completed 0, royalty 0.00000."""
    check_play(tx, data, 20937, 4817, None, 29, None, "2026-11-01 22:00:00")


def test_p1_shared_station_is_accepted(tx, data):
    """A listener may play through a station another listener created.
    Why: rule I6: "A play's Station ID may refer to a station created by another listener."
    Expect: dokafor (20937) plays 4819 through Late Jazz Hop (7710, created by 20931): recorded with station 7710."""
    check_play(tx, data, 20937, 4819, 7710, 241, None, "2026-11-02 08:00:00")


REFUSALS = [   # (id, listener, track, station, seconds, why)
    ("unknown_track", 20937, 9999, None, 100, "a recording that does not exist"),
    ("awaiting_scoring", 20937, 4830, None, 100, "a recording still awaiting scoring"),
    ("rejected", 20937, 4831, None, 40, "a rejected recording"),
    ("longer_than_the_recording", 20937, 4817, None, 215, "215 seconds of a 214-second recording"),
]


@pytest.mark.parametrize("case", REFUSALS, ids=[c[0] for c in REFUSALS])
def test_p1_refuses_an_invalid_play(tx, data, case):
    """record_play refuses an invalid play with SIGNAL SQLSTATE '45000' and a message naming the problem, and
    writes nothing.
    Why: only released recordings can be streamed, and a play cannot outlast its recording; none of these is in
    the sample data.
    Expect: MySQL error 1644 (SQLSTATE 45000) with the oracle's message; the play table is unchanged."""
    _, listener, track, station, seconds, why = case
    want = O.record_play(data, listener, track, station, seconds, None, "2026-11-03 09:00:00")
    tx.execute("SELECT COUNT(*) FROM play"); n = tx.fetchone()[0]
    code, msg = refused(tx, rp(listener, track, station, seconds, None, "2026-11-03 09:00:00"))
    tx.execute("SELECT COUNT(*) FROM play"); after = tx.fetchone()[0]
    show(["error", "message", "plays"], [want[1], "record_play: " + want[2], n], [code, msg, after])
    assert (code, after) == (1644, n) and want[2] in msg, f"{why}: got {code} {msg!r}"


def test_p1_repeated_report_is_rejected(tx, data):
    """A second report of a play already recorded is rejected by the database, not paid twice.
    Why: the key (listener, recording, start time) "is what keeps a double-counted royalty out of the ledger"
    (RA); record_play must not catch or hide that error.
    Expect: re-reporting dokafor's sample play of 4829 at 2026-08-19 13:32:05 fails with 1062; the ledger total
    is unchanged."""
    tx.execute("SELECT SUM(royalty_amount) FROM play"); before = tx.fetchone()[0]
    code, msg = refused(tx, rp(20937, 4829, None, 189, "saved", "2026-08-19 13:32:05"))
    tx.execute("SELECT SUM(royalty_amount) FROM play"); after = tx.fetchone()[0]
    show(["error", "ledger total"], [1062, canon(before)], [code, canon(after)])
    assert code == 1062 and after == before


def test_p1_unknown_listener_is_refused_by_the_database(tx, data):
    """A play by a listener who does not exist is refused by the foreign key, and nothing is written.
    Why: the procedure leaves the database's own checks in place rather than duplicating them.
    Expect: listener 99999: MySQL error 1452 (fk_play_listener)."""
    want = O.record_play(data, 99999, 4817, None, 60, None, "2026-11-03 10:00:00")
    code, msg = refused(tx, rp(99999, 4817, None, 60, None, "2026-11-03 10:00:00"))
    show(["error"], [want[1]], [code])
    assert code == 1452 and "fk_play_listener" in msg


def test_p1_ledger_survives_a_rate_change(tx, data):
    """A royalty already recorded keeps its amount when the artist's rate later changes; the next play earns the
    new rate.
    Why: rule I7: "Royalty Amount is computed once, when the play is recorded, and never updated."
    Expect: play of 4817 recorded at 0.00400; rate raised to 0.00450; that play still holds 0.00400, a new play
    holds 0.00450."""
    t = copy.deepcopy(data)
    check_play(tx, t, 20937, 4817, None, 120, None, "2026-11-04 10:00:00")
    call(tx, "UPDATE artist SET payout_rate = 0.00450 WHERE artist_id = 1042")
    next(r for r in t["artist"]["rows"] if r["artist_id"] == "1042")["payout_rate"] = "0.00450"
    call(tx, rp(20937, 4817, None, 120, None, "2026-11-05 10:00:00"))
    first, second = play_row(tx, 20937, 4817, "2026-11-04 10:00:00"), play_row(tx, 20937, 4817, "2026-11-05 10:00:00")
    show(["first play", "second play"], [Decimal("0.00400"), O.royalty(t, 4817, 120)], [first[7], second[7]])
    assert first[7] == Decimal("0.00400") and second[7] == Decimal("0.00450")


def test_p1_no_time_given_records_utc_now(tx, data):
    """With no start time given, the play is recorded at the current UTC time, whatever the session's time zone.
    Why: "Played At is recorded in UTC" (RA), so a daylight-saving change can never repeat a key. The session is
    put in Arizona time (UTC-7) first, so local time and UTC differ by seven hours.
    Expect: played_at falls between UTC_TIMESTAMP() just before and just after the call."""
    tx.execute("SET time_zone = '-07:00'")
    try:
        tx.execute("SELECT UTC_TIMESTAMP()"); t0 = tx.fetchone()[0]
        call(tx, rp(20937, 4818, None, 60, None, None))
        tx.execute("SELECT UTC_TIMESTAMP()"); t1 = tx.fetchone()[0]
    finally:
        tx.execute("SET time_zone = DEFAULT")
    tx.execute("SELECT MAX(played_at) FROM play WHERE listener_id = 20937 AND track_id = 4818"); at = tx.fetchone()[0]
    show(["from", "played_at", "to"], [canon(t0), "between", canon(t1)], [canon(t0), canon(at), canon(t1)])
    assert t0 <= at <= t1


# ---------------------------------------------------------------------------- P2 upload_track
def up(artist, title, duration, release, checksum):
    return (f"CALL crossfade.upload_track({lit(artist)}, {lit(title)}, {lit(duration)}, {lit(release)}, "
            f"{checksum}, @track_id, @status, @message)")


def check_upload(cur, t, artist, title, duration, release, hexsum):
    want = O.upload(t, artist, title, duration, release, hexsum)
    outs = call(cur, up(artist, title, duration, release, "0x" + hexsum), ["@track_id", "@status", "@message"])
    if want[0] == "uploaded":
        msg = f"uploaded as track {want[1]}, awaiting scoring"
        t["track"]["rows"].append({k: str(v) for k, v in want[2].items()})
    else:
        msg = f"already in the catalogue as track {want[1]} ({want[2]})"
    show(["OUT track_id", "OUT status", "OUT message"], [Decimal(want[1]), want[0], msg], outs)
    assert outs == [Decimal(want[1]), want[0], msg], f"OUT values {outs}"
    return want


def test_p2_new_upload_awaits_scoring(tx, data):
    """A new recording enters the catalogue awaiting scoring, under the next track ID.
    Why: the first stage of the upload pipeline (RA: no score "while it is awaiting scoring").
    Expect: Kestrel Ave (1049) uploads First Light: track 4832, status 'uploaded', and the row holds the upload
    with ingest_status 'awaiting scoring'."""
    t = copy.deepcopy(data)
    hexsum = sha("first light")
    want = check_upload(tx, t, 1049, "First Light", 201, "2026-12-01", hexsum)
    tx.execute("SELECT track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status FROM track "
               "WHERE track_id = %s", (want[1],))
    got = [canon(v) for v in tx.fetchone()]
    assert got == [canon(v) if k != "audio_checksum" else v for k, v in want[2].items()]


def test_p2_duplicate_is_answered_not_raised(tx, data):
    """Uploading audio already in the catalogue is answered, not raised: nothing is inserted and the uploader is
    told which recording it is.
    Why: the UNIQUE index on audio_checksum detects the duplicate (error 1062), and the EXIT HANDLER turns it
    into an answer.
    Expect: Velvet Static re-uploads Low Tide's audio: no error, status 'duplicate', track 4817 named; the track
    count is unchanged."""
    tx.execute("SELECT COUNT(*) FROM track"); n = tx.fetchone()[0]
    hexsum = next(r for r in data["track"]["rows"] if r["track_id"] == "4817")["audio_checksum"][2:]
    check_upload(tx, copy.deepcopy(data), 1042, "Low Tide (again)", 214, "2026-11-01", hexsum)
    tx.execute("SELECT COUNT(*) FROM track"); assert tx.fetchone()[0] == n


def test_p2_duplicate_of_another_artists_audio(tx, data):
    """The same audio uploaded by a different artist is still a duplicate.
    Why: the checksum identifies the audio, whoever uploads it; a second licence for the same file is refused.
    Expect: Kestrel Ave (1049) uploads Ember Count's audio (4829, by 1048): status 'duplicate', track 4829."""
    hexsum = next(r for r in data["track"]["rows"] if r["track_id"] == "4829")["audio_checksum"][2:]
    check_upload(tx, copy.deepcopy(data), 1049, "Ember Count", 189, "2026-11-01", hexsum)


def test_p2_batch_carries_on_after_a_duplicate(tx, data):
    """A run of uploads carries on past a duplicate: new, duplicate, new.
    Why: this is why the duplicate is caught: an uncaught 1062 would stop a script at the second upload.
    Expect: tracks 4832 'uploaded', 4817 'duplicate', 4833 'uploaded'."""
    t = copy.deepcopy(data)
    dup = next(r for r in data["track"]["rows"] if r["track_id"] == "4817")["audio_checksum"][2:]
    got = []
    for artist, title, h in ((1049, "First Light", sha("first light")), (1042, "Low Tide (again)", dup),
                             (1049, "Second Light", sha("second light"))):
        w = O.upload(t, artist, title, 200, "2026-12-01", h)
        outs = call(tx, up(artist, title, 200, "2026-12-01", "0x" + h), ["@track_id", "@status"])
        if w[0] == "uploaded":
            t["track"]["rows"].append({k: str(v) for k, v in w[2].items()})
        got.append((outs, [Decimal(w[1]), w[0]]))
    CASE.update(columns=["OUT track_id", "OUT status"], expected=[[str(x) for x in e] for _, e in got],
                got=[[str(x) for x in o] for o, _ in got])
    assert all(o == e for o, e in got), got


def test_p2_unregistered_artist_is_refused(tx, data):
    """An upload from an artist who is not registered is refused with SIGNAL, and nothing is inserted.
    Why: artists upload "under a direct streaming licence" (RA); the procedure says so in words.
    Expect: artist 9999: MySQL error 1644 (SQLSTATE 45000), "artist 9999 is not registered"."""
    want = O.upload(data, 9999, "Nobody", 120, "2026-12-01", sha("nobody"))
    tx.execute("SELECT COUNT(*) FROM track"); n = tx.fetchone()[0]
    code, msg = refused(tx, up(9999, "Nobody", 120, "2026-12-01", "0x" + sha("nobody")))
    tx.execute("SELECT COUNT(*) FROM track"); after = tx.fetchone()[0]
    show(["error", "message", "tracks"], [want[1], "upload_track: " + want[2], n], [code, msg, after])
    assert code == 1644 and want[2] in msg and after == n


def test_p2_handler_catches_only_duplicates(tx, data):
    """Only error 1062 is caught: an invalid length is still refused by the database, even for audio that is
    already in the catalogue.
    Why: an EXIT HANDLER for every error would hide real problems (here it would answer 'duplicate' and hide the
    invalid length); this one names 1062 alone.
    Expect: a 0-second upload of new audio, and of Low Tide's audio, both fail with 3819 (ck_track_duration)."""
    known = next(r for r in data["track"]["rows"] if r["track_id"] == "4817")["audio_checksum"]
    want = O.upload(data, 1049, "Silence", 0, "2026-12-01", sha("silence"))
    c1, m1 = refused(tx, up(1049, "Silence", 0, "2026-12-01", "0x" + sha("silence")))
    c2, m2 = refused(tx, up(1042, "Low Tide (silent)", 0, "2026-12-01", known))
    show(["new audio", "known audio"], [want[1], want[1]], [c1, c2])
    assert (c1, c2) == (3819, 3819) and "ck_track_duration" in m1 + m2


def test_p2_simultaneous_uploads_never_report_a_false_duplicate(db, installed, pytestconfig, data):
    """Two uploads of different audio at the same moment both get an honest answer, never 'duplicate'.
    Why: both compute the next track ID. Two connections reproduce it: A uploads and holds its new row, B uploads
    different audio, A commits. On MySQL 8 the second upload's ID lookup waits for the first, so B takes the next
    ID; if a server let both take the same ID, B would get the primary-key clash (1062 on PRIMARY), which the
    handler re-raises (see the next case). What must never happen is B being told its new audio is a duplicate.
    Expect: A gets track 4832; B gets track 4833 'uploaded', or error 1062 on PRIMARY. Both rows are deleted again
    afterwards."""
    import threading, time, pymysql
    from conftest import connect
    a, b = connect(pytestconfig), connect(pytestconfig)
    sa, sb = sha("race a"), sha("race b")
    got = {}
    CASE.update(inputs=[{"kind": "call", "sql": "-- connection A\n" + up(1049, "Race A", 200, "2026-12-01", "0x" + sa)},
                        {"kind": "call", "sql": "-- connection B, at the same moment\n" + up(1048, "Race B", 200, "2026-12-01", "0x" + sb)},
                        {"kind": "call", "sql": "-- connection A\nCOMMIT"}])

    def upload_b():
        try:
            with b.cursor() as cur:
                cur.execute(up(1048, "Race B", 200, "2026-12-01", "0x" + sb))
                cur.execute("SELECT @track_id, @status"); got["b"] = cur.fetchone()
        except pymysql.MySQLError as e:
            got["b"] = ("error", e.args[0], str(e.args[1]))
    try:
        with a.cursor() as cur:
            cur.execute(up(1049, "Race A", 200, "2026-12-01", "0x" + sa))
            cur.execute("SELECT @track_id, @status"); got["a"] = cur.fetchone()
        th = threading.Thread(target=upload_b); th.start()
        time.sleep(0.6)                                  # B is now waiting on A
        a.commit(); th.join(15)
        assert not th.is_alive(), "B never finished"
    finally:
        b.rollback()                     # a failed insert by B would hold a lock on A's row until B's transaction ends
        with a.cursor() as cur:
            cur.execute("DELETE FROM track WHERE audio_checksum IN (%s, %s)", (bytes.fromhex(sa), bytes.fromhex(sb)))
        a.commit(); a.close(); b.close()
    new_id = max(int(r["track_id"]) for r in data["track"]["rows"]) + 1
    gb = got.get("b", ("no answer",))
    show(["A", "B"], [f"{new_id} uploaded", f"{new_id + 1} uploaded, or error 1062 PRIMARY"],
         [f"{got['a'][0]} {got['a'][1]}", " ".join(str(x) for x in gb)])
    assert tuple(got["a"]) == (new_id, "uploaded")
    assert tuple(gb) == (new_id + 1, "uploaded") or (gb[0] == "error" and gb[1] == 1062 and "PRIMARY" in gb[2]), gb


def test_p2_key_clash_is_not_reported_as_a_duplicate(db, installed, pytestconfig, data):
    """A 1062 that is not about the audio (the new track ID already taken) is re-raised, not answered as a
    duplicate.
    Why: the handler catches every 1062, but only a clash on audio_checksum is a duplicate upload; for any other
    it finds no recording with the new checksum and must RESIGNAL. To make the new ID clash on demand, a
    temporary trigger rewrites it to 4817, an ID already in use (the trigger is dropped again afterwards).
    Expect: uploading new audio fails with 1062 on PRIMARY; nothing is inserted."""
    import pymysql
    from conftest import connect
    db.rollback()                        # end db's transaction first: an open one holds a lock the CREATE TRIGGER waits for
    ddl = connect(pytestconfig)
    with ddl.cursor() as cur:
        cur.execute("SET SESSION lock_wait_timeout = 10")
        cur.execute("DROP TRIGGER IF EXISTS crossfade.test_take_used_id")
        cur.execute("CREATE TRIGGER crossfade.test_take_used_id BEFORE INSERT ON crossfade.track FOR EACH ROW "
                    "SET NEW.track_id = 4817")
    CASE.update(inputs=[{"kind": "call", "sql": "CREATE TRIGGER test_take_used_id BEFORE INSERT ON track FOR EACH ROW "
                                                 "SET NEW.track_id = 4817   -- test only, dropped afterwards"}])
    try:
        db.rollback()
        with db.cursor() as cur:
            code, msg = refused(cur, up(1049, "Clash", 200, "2026-12-01", "0x" + sha("clash")))
            cur.execute("SELECT COUNT(*) FROM track"); n = cur.fetchone()[0]
        db.rollback()
    finally:
        db.rollback()
        with ddl.cursor() as cur:
            cur.execute("DROP TRIGGER IF EXISTS crossfade.test_take_used_id")
        ddl.close()
    show(["error", "on", "tracks"], [1062, "PRIMARY", len(data["track"]["rows"])],
         [code, "PRIMARY" if "PRIMARY" in msg else msg, n])
    assert code == 1062 and "PRIMARY" in msg and n == len(data["track"]["rows"])


# ============================================================================ coverage (whole file)
def test_brief_routine_mix(routines):
    """The brief: 2 procedures and 1 function, or 1 procedure and 2 functions."""
    kinds = sorted(r.kind for r in routines.values())
    assert kinds in (["FUNCTION", "PROCEDURE", "PROCEDURE"], ["FUNCTION", "FUNCTION", "PROCEDURE"]), \
        f"routines.sql has {kinds}"


def test_tags_are_unique_and_in_order(routines):
    for k in "FP":
        tags = [t for t in routines if t[0] == k]
        assert tags == [f"{k}{i}" for i in range(1, len(tags) + 1)], f"{k} tags {tags}"


def test_every_routine_use_case_is_served(routines, use_cases):
    """Every use case with routineColumns in use_cases.json is served by a routine, and every use case a routine
    names has routineColumns."""
    claimed = {u for r in routines.values() for u in r.use_cases}
    wanted = {u for u, v in use_cases.items() if v.get("routineColumns")}
    assert not wanted - claimed, f"use cases with routineColumns but no routine: {sorted(wanted - claimed)}"
    assert not claimed - wanted, f"routines name use cases without routineColumns: {sorted(claimed - wanted)}"


def test_declared_columns_are_touched(routines, use_cases, db):
    """Every column a use case declares under routineColumns is read or written by a routine serving it, so the
    heat map shows nothing the routines do not do."""
    cols = schema_columns(db)
    bad = {}
    for u, v in use_cases.items():
        for t, cs in (v.get("routineColumns") or {}).items():
            done = set()
            for r in routines.values():
                if u in r.use_cases:
                    done |= set(touched(r, routines, cols).get(t, []))
            if set(cs) - done:
                bad[f"{u} {t}"] = sorted(set(cs) - done)
    assert not bad, f"declared but touched by no routine serving the use case: {bad}"


def test_no_derived_values_as_input(routines):
    """The RA: "the procedures do not accept derived values as input". No routine takes a parameter for a value
    the RA says is computed (completed, royalty_amount, ingest_status)."""
    bad = [(r.tag, p) for r in routines.values() for mode, p, _ in declared_params(r)
           if mode in ("IN", "INOUT") and any(p.endswith(d) for d in DERIVED)]
    assert not bad, f"derived values taken as input: {bad}"


def test_no_transaction_control_inside(routines):
    """No routine starts, commits or rolls back a transaction: each makes one write, which MySQL applies whole,
    and the caller keeps control (a COMMIT inside would also defeat the caller's ROLLBACK)."""
    bad = [r.tag for r in routines.values()
           if re.search(r"\b(START\s+TRANSACTION|BEGIN\s+WORK|COMMIT|ROLLBACK)\b", r.body, re.I)]
    assert not bad, f"transaction control inside {bad}"


def test_script_reruns_and_leaves_data_unchanged(db, installed, pytestconfig):
    """routines.sql can be run again (it drops and re-creates each routine) and returns no result rows: it only
    creates routines. Neither it nor the example usage script changes the data."""
    assert installed["after"] == installed["before"], f"rows changed by the scripts: {installed}"
    assert not [s for s in installed["created"] if s.get("rows") is not None or re.match(r"\s*CALL\b", s["sql"], re.I)], \
        "routines.sql runs a query or a CALL; it should only create the routines (example calls go in the example script)"
    run_script(db, find_file(pytestconfig, "rsql"))
    assert counts(db) == installed["before"]


def test_example_usage_gives_the_documented_answers(installed, data):
    """routines_example_usage.sql returns what its comments promise: 0 and 0.00400 from play_royalty, completed 0
    and royalty 0.00400 from record_play, a duplicate named and a new upload numbered by upload_track."""
    if not installed["example"]:
        pytest.skip("routines_example_usage.sql not found (example usage, not a deliverable)")
    rows = [s["rows"][0] for s in installed["steps"] if s.get("rows")]
    dup = next(r for r in data["track"]["rows"] if r["track_id"] == "4817")
    new_id = max(int(r["track_id"]) for r in data["track"]["rows"]) + 1
    want = [[str(O.royalty(data, 4817, 29)), str(O.royalty(data, 4817, 30))],
            ["0", str(O.royalty(data, 4817, 107))],
            ["4817", "duplicate", f"already in the catalogue as track 4817 ({dup['title']})"],
            [str(new_id), "uploaded", f"uploaded as track {new_id}, awaiting scoring"]]
    assert rows == want
