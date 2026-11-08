"""Tests for database_implementation.sql (INFO 579 Project 2, Task 1): creating the database and its tables.

The script is run, twice, and the database it leaves behind is checked against three independent sources:

  SPEC below      typed by hand from the Project 1 physical model (physical_data_model.png), with the ENUM
                  values and UNSIGNED flags from the data dictionary, because the diagram abbreviates them.
                  It is NOT read from the .sql file, so a mistake in the script cannot also be in the answer.
  RULES below     the value rules from the requirements analysis (and, where the analysis is silent, the
                  rule the script's own comment states), each with a value that must be refused.
  data.csv        the Project 1 sample data as handed in (data.xlsx, exported cell for cell).

Five groups:
  load        the script runs start to finish, runs again (it must be re-runnable), raises no warnings
              (a warning means MySQL silently changed a value), has a purpose comment before every
              statement (the brief), never switches checks off, and creates and loads each table exactly once
  schema      exactly the ten tables; per table its columns in order with type, size, UNSIGNED and NULL
              exactly as the physical model; primary key columns (composite on the associative tables);
              every foreign key (columns, parent, name, ON DELETE rule); every unique key; constraint names
  read        one live SELECT per table, checking the Python type of every value that comes back
  data        row counts and every cell equal to data.csv; the cross-row integrity rules; no orphan rows
  enforce     inside a transaction that is always rolled back: a valid new row is accepted, then one bad
              write per rule must be refused with the exact MySQL error and constraint name: duplicate
              primary key (1062), duplicate unique value (1062), orphan foreign key (1452), NULL in a NOT
              NULL column (1048), CHECK violated (3819), value too long / out of range / not in the ENUM /
              not a date (1406 / 1264 / 1265 / 1292); plus the ON DELETE behaviours (CASCADE, SET NULL,
              refused with 1451)

IMPORTANT: these tests DROP and rebuild the `crossfade` database from database_implementation.sql. Nothing
else on the server is touched, and the database is left fully loaded afterwards.

Run (inside the test-kit folder, or from the repo root):
    python -m pytest test_implementation.py
    python -m pytest project2/tests/test_implementation.py
"""
import datetime, re, time
from decimal import Decimal

import pytest

from conftest import connect, load_bulk, split_sql, record_impl

DB = "crossfade"

# ------------------------------------------------------------------------------------------------ the spec
# From physical_data_model.png (Project 1). Per table: (column, COLUMN_TYPE as MySQL 8 reports it, nullable).
# Order matters: it is the column order in the diagram.
SPEC = {
    "genre": [("genre_id", "tinyint unsigned", False), ("name", "varchar(9)", False),
              ("description", "varchar(80)", True)],
    "artist": [("artist_id", "mediumint unsigned", False), ("stage_name", "varchar(64)", False),
               ("country", "char(2)", True), ("joined_date", "date", False),
               ("payout_rate", "decimal(5,5)", False), ("verified", "bit(1)", False)],
    "listener": [("listener_id", "int unsigned", False), ("email", "varchar(254)", False),
                 ("display_name", "varchar(32)", False),
                 ("plan_tier", "enum('free','standard','premium')", False), ("signup_date", "date", False)],
    "scoring_model": [("model_id", "tinyint unsigned", False), ("version_label", "varchar(32)", False),
                      ("fusion_type", "enum('concat','gated')", False),
                      ("embedding_dimension", "smallint unsigned", False),
                      ("segment_length", "tinyint unsigned", False), ("training_corpus", "varchar(16)", False),
                      ("holdout_accuracy", "decimal(5,4)", False), ("deployed_on", "date", False)],
    "track": [("track_id", "int unsigned", False), ("artist_id", "mediumint unsigned", False),
              ("title", "varchar(128)", False), ("duration", "smallint unsigned", False),
              ("release_date", "date", False), ("audio_checksum", "binary(32)", False),
              ("ingest_status", "enum('awaiting scoring','scored','rejected')", False)],
    "station": [("station_id", "int unsigned", False), ("listener_id", "int unsigned", False),
                ("model_id", "tinyint unsigned", False), ("name", "varchar(64)", False),
                ("minimum_ambiguity", "decimal(3,2)", False), ("maximum_ambiguity", "decimal(3,2)", False),
                ("created_on", "date", False)],
    "track_score": [("track_id", "int unsigned", False), ("model_id", "tinyint unsigned", False),
                    ("genre_id", "tinyint unsigned", False), ("top_probability", "decimal(5,4)", False),
                    ("posterior_entropy", "decimal(5,4)", False), ("model_divergence", "decimal(5,4)", True),
                    ("segment_variance", "decimal(4,4)", True), ("scored_on", "datetime", False)],
    "genre_probability": [("track_id", "int unsigned", False), ("model_id", "tinyint unsigned", False),
                          ("genre_id", "tinyint unsigned", False), ("probability", "decimal(5,4)", False)],
    "station_blend": [("station_id", "int unsigned", False), ("genre_id", "tinyint unsigned", False),
                      ("weight", "decimal(3,2)", False)],
    "play": [("listener_id", "int unsigned", False), ("track_id", "int unsigned", False),
             ("played_at", "datetime", False), ("station_id", "int unsigned", True),
             ("seconds_played", "smallint unsigned", False), ("completed", "bit(1)", False),
             ("reaction", "enum('saved','skipped')", True), ("royalty_amount", "decimal(5,5)", False)],
}
TABLES = list(SPEC)
ASSOCIATIVE = ["track_score", "genre_probability", "station_blend", "play"]

PRIMARY_KEY = {
    "genre": ["genre_id"], "artist": ["artist_id"], "listener": ["listener_id"], "scoring_model": ["model_id"],
    "track": ["track_id"], "station": ["station_id"],
    "track_score": ["track_id", "model_id"],                       # composite: the two foreign keys
    "genre_probability": ["track_id", "model_id", "genre_id"],
    "station_blend": ["station_id", "genre_id"],
    "play": ["listener_id", "track_id", "played_at"],              # weak-entity partial key: played_at
}

# Every relationship line in the diagram: name -> (child, child columns, parent, parent columns, ON DELETE).
# Names follow fk_<child>_<parent>; nine of them are printed in the diagram's index lists. ON DELETE is not in
# the requirements analysis; the three non-default rules are the ones the script's comments state.
DEFAULT = "NO ACTION"        # what MySQL reports when no ON DELETE is written (InnoDB treats it as RESTRICT)
FOREIGN_KEYS = {
    "fk_track_artist": ("track", ["artist_id"], "artist", ["artist_id"], DEFAULT),
    "fk_station_listener": ("station", ["listener_id"], "listener", ["listener_id"], DEFAULT),
    "fk_station_scoring_model": ("station", ["model_id"], "scoring_model", ["model_id"], DEFAULT),
    "fk_track_score_track": ("track_score", ["track_id"], "track", ["track_id"], DEFAULT),
    "fk_track_score_scoring_model": ("track_score", ["model_id"], "scoring_model", ["model_id"], DEFAULT),
    "fk_track_score_genre": ("track_score", ["genre_id"], "genre", ["genre_id"], DEFAULT),
    "fk_genre_probability_track_score": ("genre_probability", ["track_id", "model_id"], "track_score",
                                         ["track_id", "model_id"], "CASCADE"),
    "fk_genre_probability_genre": ("genre_probability", ["genre_id"], "genre", ["genre_id"], DEFAULT),
    "fk_station_blend_station": ("station_blend", ["station_id"], "station", ["station_id"], "CASCADE"),
    "fk_station_blend_genre": ("station_blend", ["genre_id"], "genre", ["genre_id"], DEFAULT),
    "fk_play_listener": ("play", ["listener_id"], "listener", ["listener_id"], DEFAULT),
    "fk_play_track": ("play", ["track_id"], "track", ["track_id"], DEFAULT),
    "fk_play_station": ("play", ["station_id"], "station", ["station_id"], "SET NULL"),
}
UNIQUE_KEYS = {                     # the uq_ indexes printed in the diagram
    "uq_genre_name": ("genre", ["name"]),
    "uq_artist_stage_name": ("artist", ["stage_name"]),
    "uq_listener_email": ("listener", ["email"]),
    "uq_scoring_model_version_label": ("scoring_model", ["version_label"]),
    "uq_track_audio_checksum": ("track", ["audio_checksum"]),
}

# Value rules. (check name, table, column -> refused value, where the rule comes from). A bad value is chosen so
# that it breaks this rule and no other, and fits the column's type (otherwise the type would refuse it first).
CHECKS = {
    "ck_genre_id": ("genre", {"genre_id": 10}, "script: genre_id equals the model output class 0 to 9"),
    "ck_artist_payout_rate": ("artist", {"payout_rate": Decimal("0")}, "script: payout rate must be positive"),
    "ck_listener_email": ("listener", {"email": "no-at-sign.example.com"}, "script: an email address has an @"),
    "ck_scoring_model_holdout_accuracy": ("scoring_model", {"holdout_accuracy": Decimal("1.5")},
                                          "RA: holdout accuracy is a proportion"),
    "ck_scoring_model_embedding_dimension": ("scoring_model", {"embedding_dimension": 0}, "script: must be positive"),
    "ck_scoring_model_segment_length": ("scoring_model", {"segment_length": 0}, "script: must be positive"),
    "ck_track_duration": ("track", {"duration": 0}, "script: duration in whole seconds, positive"),
    "ck_station_minimum_ambiguity": ("station", {"minimum_ambiguity": Decimal("-0.10")},
                                     "RA: ambiguity is on the 0 to 1 entropy scale"),
    "ck_station_maximum_ambiguity": ("station", {"maximum_ambiguity": Decimal("1.50")},
                                     "RA: ambiguity is on the 0 to 1 entropy scale"),
    "ck_station_ambiguity_window": ("station", {"minimum_ambiguity": Decimal("0.80"), "maximum_ambiguity": Decimal("0.20")},
                                    "RA I4: Minimum Ambiguity does not exceed Maximum Ambiguity"),
    "ck_track_score_top_probability": ("track_score", {"top_probability": Decimal("1.2")}, "RA: a probability"),
    "ck_track_score_posterior_entropy": ("track_score", {"posterior_entropy": Decimal("1.2")}, "RA: normalised, 0 to 1"),
    "ck_track_score_model_divergence": ("track_score", {"model_divergence": Decimal("1.2")}, "RA: base-2 JSD, 0 to 1"),
    "ck_track_score_segment_variance": ("track_score", {"segment_variance": Decimal("0.3")},
                                        "script: a variance of probabilities is at most 0.25"),
    "ck_genre_probability_probability": ("genre_probability", {"probability": Decimal("1.2")},
                                         "RA: a probability between zero and one"),
    "ck_station_blend_weight": ("station_blend", {"weight": Decimal("0")}, "RA: weight greater than zero, at most one"),
    "ck_play_royalty_amount": ("play", {"royalty_amount": Decimal("-0.001")}, "script: a royalty is never negative"),
}
# Type limits: the column's type itself refuses the value (strict SQL mode, the MySQL 8 default).
TYPE_LIMITS = {
    "artist-stage_name-too-long": ("artist", {"stage_name": "x" * 65}, 1406, "VARCHAR(64)"),
    "artist-country-too-long": ("artist", {"country": "USA"}, 1406, "CHAR(2)"),
    "track-audio_checksum-too-long": ("track", {"audio_checksum": b"\x01" * 33}, 1406, "BINARY(32)"),
    "artist-artist_id-negative": ("artist", {"artist_id": -1}, 1264, "UNSIGNED"),
    "track-duration-out-of-range": ("track", {"duration": 70000}, 1264, "SMALLINT UNSIGNED, max 65535"),
    "artist-payout_rate-out-of-range": ("artist", {"payout_rate": Decimal("1.5")}, 1264, "DECIMAL(5,5), max 0.99999"),
    "track-ingest_status-not-in-enum": ("track", {"ingest_status": "deleted"}, 1265, "ENUM"),
    "play-reaction-not-in-enum": ("play", {"reaction": "liked"}, 1265, "ENUM"),
    "listener-signup_date-not-a-date": ("listener", {"signup_date": "2026-02-30"}, 1292, "DATE"),
}


def ctype(table, col):
    return next(t for c, t, _ in SPEC[table] if c == col)


# ------------------------------------------------------------------------------------------------ fixtures
class Load:
    def __init__(self):
        self.runs, self.statements, self.comments = [], [], []


def _run_script(config, stmts):
    """Run every statement on one connection. Returns (seconds, warnings, error or None)."""
    con = connect(config, database=None)
    warnings, t0 = [], time.perf_counter()
    try:
        with con.cursor() as cur:
            for k, s in enumerate(stmts, 1):
                try:
                    cur.execute(s)
                except Exception as e:
                    return time.perf_counter() - t0, warnings, f"statement {k}: {e}  [{s[:80]}...]"
                cur.execute("SHOW WARNINGS")
                for level, code, msg in cur.fetchall():
                    if code == 1008 and s.upper().startswith("DROP DATABASE IF EXISTS"):
                        continue                        # "database doesn't exist" on a first-ever run: expected
                    warnings.append(f"statement {k}: {level} {code} {msg}")
                print(f"\r      running database_implementation.sql: statement {k}/{len(stmts)}", end="", flush=True)
        con.commit()
        print(flush=True)
        return time.perf_counter() - t0, warnings, None
    finally:
        con.close()


@pytest.fixture(scope="session")
def load(pytestconfig, paths):
    """Run database_implementation.sql twice and keep what happened."""
    text = paths["impl"].read_text(encoding="utf-8")
    ld = Load()
    parts = split_sql(text)
    ld.statements = [s for _, s in parts]
    ld.comments = [c for c, _ in parts]
    for n in (1, 2):
        secs, warns, err = _run_script(pytestconfig, ld.statements)
        ld.runs.append({"run": n, "seconds": round(secs, 3), "warnings": warns, "error": err})
    record_impl("load", "statements", len(ld.statements))
    c = connect(pytestconfig, database=None)
    try:
        with c.cursor() as cur:
            cur.execute("SELECT VERSION(), @@sql_mode")
            v, mode = cur.fetchone()
        record_impl("load", "server", {"version": v, "sql_mode": mode})
    finally:
        c.close()
    record_impl("load", "runs", ld.runs)
    return ld


@pytest.fixture(scope="session")
def con(pytestconfig, load):
    c = connect(pytestconfig)
    yield c
    c.rollback()
    c.close()


@pytest.fixture(scope="module", autouse=True)
def release_locks(con):
    """End the shared connection's transaction when this file is done: an open read keeps a metadata lock on
    each table it touched, which would make later DDL (test_routines.py creates a trigger) wait."""
    yield
    con.rollback()


@pytest.fixture(scope="session")
def data(paths):
    return load_bulk(paths["data"])


@pytest.fixture
def tx(con):
    """A cursor inside a transaction that is always rolled back, whatever the test does."""
    con.rollback()
    cur = con.cursor()
    yield cur
    con.rollback()
    cur.close()


def query(cur, sql, args=None):
    cur.execute(sql, args)
    return cur.fetchall()


def columns_of(cur, table):
    return [r[0] for r in query(cur, "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s "
                                     "AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION", (DB, table))]


def sample_row(cur, table):
    cur.execute(f"SELECT * FROM {DB}.{table} ORDER BY {', '.join(PRIMARY_KEY[table])} LIMIT 1")
    names = [d[0] for d in cur.description]
    return dict(zip(names, cur.fetchone()))


def insert(cur, table, row):
    cols = list(row)
    cur.execute(f"INSERT INTO {DB}.{table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                [row[c] for c in cols])


def fresh_row(cur, table):
    """A new row that the table accepts: a sample row with its keys and unique values replaced by unused ones.
    Rows it depends on (a scoring result for a probability) are inserted first, in the same transaction."""
    r = sample_row(cur, table)
    if table == "artist":
        r.update(artist_id=1999, stage_name="Test Artist 1999")
    elif table == "listener":
        r.update(listener_id=29999, email="test29999@example.com")
    elif table == "scoring_model":
        r.update(model_id=99, version_label="test_model_99")
    elif table == "track":
        r.update(track_id=99999, audio_checksum=b"\xab" * 32)
    elif table == "station":
        r.update(station_id=9999)
    elif table in ("track_score", "genre_probability"):
        t, m = query(cur, f"SELECT t.track_id, m.model_id FROM {DB}.track t CROSS JOIN {DB}.scoring_model m "
                          f"WHERE NOT EXISTS (SELECT 1 FROM {DB}.track_score s WHERE s.track_id = t.track_id "
                          f"AND s.model_id = m.model_id) ORDER BY t.track_id, m.model_id LIMIT 1")[0]
        if table == "genre_probability":
            score = sample_row(cur, "track_score"); score.update(track_id=t, model_id=m)
            insert(cur, "track_score", score)
        r.update(track_id=t, model_id=m)
    elif table == "station_blend":
        s, g = query(cur, f"SELECT s.station_id, g.genre_id FROM {DB}.station s CROSS JOIN {DB}.genre g "
                          f"WHERE NOT EXISTS (SELECT 1 FROM {DB}.station_blend b WHERE b.station_id = s.station_id "
                          f"AND b.genre_id = g.genre_id) ORDER BY s.station_id, g.genre_id LIMIT 1")[0]
        r.update(station_id=s, genre_id=g)
    elif table == "play":
        r.update(played_at=datetime.datetime(2026, 12, 31, 23, 59, 59))
    else:
        raise ValueError(f"{table}: no unused key exists (genre ids 0-9 are all taken)")
    return r


def refused(cur, sql_or_fn, code, name=None):
    """Run a write that must fail; check MySQL's error number and that the message names the constraint."""
    import pymysql
    with pytest.raises(pymysql.err.MySQLError) as exc:
        sql_or_fn() if callable(sql_or_fn) else cur.execute(sql_or_fn)
    got, msg = exc.value.args[0], str(exc.value.args[1]) if len(exc.value.args) > 1 else ""
    assert got == code, f"expected MySQL error {code}, got {got}: {msg}"
    if name:
        assert name in msg, f"error {code} raised, but by another rule: {msg}"
    return msg


def counts(cur):
    return {t: query(cur, f"SELECT COUNT(*) FROM {DB}.{t}")[0][0] for t in TABLES}


# ================================================================================================ 1. load
def test_load_first_run(load):
    """The script runs from start to finish on this server."""
    assert load.runs[0]["error"] is None, load.runs[0]["error"]


def test_load_second_run(load):
    """It runs again on top of its own result (DROP DATABASE IF EXISTS makes it re-runnable)."""
    assert load.runs[1]["error"] is None, load.runs[1]["error"]


def test_load_no_warnings(load):
    """No statement raised a warning or note. MySQL warns when it silently changes a value (rounds a decimal,
    trims a string), so a clean load means every value went in exactly as written."""
    warns = load.runs[0]["warnings"] + load.runs[1]["warnings"]
    record_impl("load", "warnings", warns)
    assert not warns, "\n".join(warns[:10])


def test_load_every_statement_commented(load):
    """The brief: every statement is preceded by a comment explaining its purpose. Each statement must have its
    own /* ... */ block right before it, of more than a few words."""
    bare = [s[:60] for c, s in zip(load.comments, load.statements) if len(c.split()) < 5]
    assert not bare, f"statements with no purpose comment: {bare}"


def test_load_never_switches_checks_off(load):
    """No SET FOREIGN_KEY_CHECKS / UNIQUE_CHECKS / sql_mode: every row was checked as it went in (the load order
    is parents first, so it never needs to switch them off)."""
    bad = [s[:80] for s in load.statements if re.search(r"\b(FOREIGN_KEY_CHECKS|UNIQUE_CHECKS|SQL_MODE)\b", s, re.I)]
    assert not bad, bad


def test_load_inventory(load):
    """One DROP DATABASE and one CREATE DATABASE; each of the ten tables created once and loaded by one INSERT
    after its CREATE; parents created before the tables that reference them; nothing else."""
    kinds, created, loaded, other = [], {}, {}, []
    for i, s in enumerate(load.statements):
        u = re.sub(r"\s+", " ", s).upper()
        if u.startswith("DROP DATABASE"): kinds.append("drop")
        elif u.startswith("CREATE DATABASE"): kinds.append("create")
        elif (m := re.match(r"CREATE TABLE (?:IF NOT EXISTS )?(?:CROSSFADE\.)?`?(\w+)", u)):
            created.setdefault(m.group(1).lower(), []).append(i)
        elif (m := re.match(r"INSERT INTO (?:CROSSFADE\.)?`?(\w+)", u)):
            loaded.setdefault(m.group(1).lower(), []).append(i)
        else:
            other.append(s[:60])
    record_impl("load", "inventory", {"created": {t: len(v) for t, v in created.items()},
                                      "inserts": {t: len(v) for t, v in loaded.items()}})
    assert kinds == ["drop", "create"], kinds
    assert sorted(created) == sorted(TABLES) and all(len(v) == 1 for v in created.values()), created
    assert sorted(loaded) == sorted(TABLES), f"tables never loaded: {sorted(set(TABLES) - set(loaded))}"
    assert all(min(loaded[t]) > created[t][0] for t in TABLES), "a table is loaded before it is created"
    for name, (child, _, parent, _, _) in FOREIGN_KEYS.items():
        assert created[parent][0] < created[child][0], f"{child} is created before its parent {parent}"
    assert not other, f"unexpected statements: {other}"


# ================================================================================================ 2. schema
def test_schema_tables(con):
    """The database holds exactly the ten tables of the physical model, no more."""
    with con.cursor() as cur:
        got = sorted(r[0] for r in query(cur, "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", (DB,)))
    assert got == sorted(TABLES)


@pytest.mark.parametrize("table", TABLES)
def test_schema_columns(con, table):
    """Columns in the diagram's order, each with the type, size, UNSIGNED flag and NULL / NOT NULL of the model."""
    with con.cursor() as cur:
        got = [(c, t, n == "YES") for c, t, n in query(
            cur, "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s "
                 "AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION", (DB, table))]
    want = SPEC[table]
    diffs = [f"{w[0]}: model {w[1]}{' NULL' if w[2] else ' NOT NULL'}, database "
             f"{g[1]}{' NULL' if g[2] else ' NOT NULL'}" for w, g in zip(want, got) if w != g]
    assert [c for c, *_ in got] == [c for c, *_ in want], f"columns differ: {[c for c, *_ in got]}"
    assert not diffs, "; ".join(diffs)


@pytest.mark.parametrize("table", TABLES)
def test_schema_primary_key(con, table):
    """Primary key columns, in order. Associative tables use the foreign keys (instructor feedback, Project 1)."""
    with con.cursor() as cur:
        got = [r[0] for r in query(cur, "SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = %s "
                                        "AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY' ORDER BY ORDINAL_POSITION",
                                   (DB, table))]
    assert got == PRIMARY_KEY[table]


@pytest.mark.parametrize("fk", FOREIGN_KEYS)
def test_schema_foreign_key(con, fk):
    """The foreign key exists under its fk_<child>_<parent> name, on the right columns, pointing at the right
    parent columns, with the ON DELETE rule the design states."""
    child, ccols, parent, pcols, rule = FOREIGN_KEYS[fk]
    with con.cursor() as cur:
        rows = query(cur, "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                          "FROM information_schema.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA = %s AND CONSTRAINT_NAME = %s "
                          "ORDER BY ORDINAL_POSITION", (DB, fk))
        assert rows, f"no constraint named {fk}"
        rc = query(cur, "SELECT DELETE_RULE FROM information_schema.REFERENTIAL_CONSTRAINTS "
                        "WHERE CONSTRAINT_SCHEMA = %s AND CONSTRAINT_NAME = %s", (DB, fk))
    assert {r[0] for r in rows} == {child}
    assert [r[1] for r in rows] == ccols
    assert {r[2] for r in rows} == {parent}
    assert [r[3] for r in rows] == pcols
    assert rc and rc[0][0] == rule, f"ON DELETE {rc[0][0] if rc else '?'}, expected {rule}"


def test_schema_no_extra_foreign_keys(con):
    """No foreign key beyond the thirteen relationships in the diagram."""
    with con.cursor() as cur:
        got = sorted(r[0] for r in query(cur, "SELECT CONSTRAINT_NAME FROM information_schema.REFERENTIAL_CONSTRAINTS "
                                              "WHERE CONSTRAINT_SCHEMA = %s", (DB,)))
    assert got == sorted(FOREIGN_KEYS)


@pytest.mark.parametrize("uq", UNIQUE_KEYS)
def test_schema_unique_key(con, uq):
    """The unique index exists under its uq_ name on the right column."""
    table, cols = UNIQUE_KEYS[uq]
    with con.cursor() as cur:
        got = [r[0] for r in query(cur, "SELECT COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = %s "
                                        "AND TABLE_NAME = %s AND INDEX_NAME = %s AND NON_UNIQUE = 0 ORDER BY SEQ_IN_INDEX",
                                   (DB, table, uq))]
    assert got == cols


def test_schema_constraint_names(con):
    """Every named constraint follows the course convention: fk_<child>_<parent>, uq_<table>_<column>,
    ck_<table>_<rule>. (MySQL ignores a name on a PRIMARY KEY and always calls it PRIMARY.)"""
    with con.cursor() as cur:
        rows = query(cur, "SELECT TABLE_NAME, CONSTRAINT_NAME, CONSTRAINT_TYPE FROM information_schema.TABLE_CONSTRAINTS "
                          "WHERE CONSTRAINT_SCHEMA = %s", (DB,))
    prefix = {"FOREIGN KEY": "fk_", "UNIQUE": "uq_", "CHECK": "ck_"}
    bad = [f"{t}.{n} ({k})" for t, n, k in rows
           if (k == "PRIMARY KEY" and n != "PRIMARY") or (k in prefix and not n.startswith(prefix[k] + t + "_"))]
    assert not bad, bad
    checks = sorted(n for _, n, k in rows if k == "CHECK")
    assert checks == sorted(CHECKS), f"CHECK constraints differ: extra {sorted(set(checks) - set(CHECKS))}, " \
                                     f"missing {sorted(set(CHECKS) - set(checks))}"


# ================================================================================================ 3. read
PY_TYPE = [(r"^(tiny|small|medium|big)?int", int), (r"^decimal", Decimal), (r"^(var)?char|^enum", str),
           (r"^datetime", datetime.datetime), (r"^date$", datetime.date), (r"^(binary|bit)", bytes)]


@pytest.mark.parametrize("table", TABLES)
def test_read_one_row(con, table):
    """A live SELECT returns a row whose columns and Python value types match the model: whole numbers as int,
    DECIMAL as Decimal (exact, never float), DATE/DATETIME as dates, BINARY(32) as 32 bytes, BIT(1) as 1 byte."""
    with con.cursor() as cur:
        cur.execute(f"SELECT * FROM {DB}.{table} LIMIT 1")
        names = [d[0] for d in cur.description]
        row = cur.fetchone()
    assert row is not None, f"{table} is empty"
    assert names == [c for c, *_ in SPEC[table]]
    for (col, typ, nullable), v in zip(SPEC[table], row):
        if v is None:
            assert nullable, f"{col} is NULL but NOT NULL in the model"
            continue
        want = next(py for pat, py in PY_TYPE if re.search(pat, typ))
        assert isinstance(v, want), f"{col} ({typ}) came back as {type(v).__name__}"
        if typ.startswith("binary("):
            assert len(v) == int(typ[7:-1]), f"{col} is {len(v)} bytes"
        if typ == "bit(1)":
            assert v in (b"\x00", b"\x01")


# ================================================================================================ 4. data
def canon_db(typ, v):
    if v is None: return None
    if typ == "bit(1)": return str(int.from_bytes(v, "big"))
    if typ.startswith("binary"): return "0x" + v.hex().upper()
    if isinstance(v, datetime.datetime): return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, datetime.date): return v.isoformat()
    if isinstance(v, (int, Decimal)): return Decimal(v)
    return str(v)


def canon_csv(typ, v):
    if v is None: return None
    if re.search(r"int|decimal", typ): return Decimal(v)
    if typ.startswith("binary"): return v.upper().replace("0X", "0x")
    return v


@pytest.mark.parametrize("table", TABLES)
def test_data_row_count(con, data, table):
    """As many rows as the table has in data.csv (Project 1 data.xlsx)."""
    with con.cursor() as cur:
        n = query(cur, f"SELECT COUNT(*) FROM {DB}.{table}")[0][0]
    record_impl("tables", table, {"rows": n, "csv_rows": len(data[table]["rows"])})
    assert n == len(data[table]["rows"])


@pytest.mark.parametrize("table", TABLES)
def test_data_every_cell(con, data, table):
    """Every cell equals data.csv: numbers compared as exact decimals, dates and times as text, the checksum as
    hex, BIT as 0/1, empty cells as NULL. Rows are matched by primary key, so order does not matter."""
    cols = [c for c, *_ in SPEC[table]]
    types = {c: t for c, t, _ in SPEC[table]}
    assert data[table]["columns"] == cols, f"data.csv columns {data[table]['columns']}"
    pk = [cols.index(c) for c in PRIMARY_KEY[table]]
    with con.cursor() as cur:
        cur.execute(f"SELECT {', '.join(cols)} FROM {DB}.{table}")
        got = {tuple(canon_db(types[c], v) for c, v in zip(cols, r)) for r in cur.fetchall()}
    want = {tuple(canon_csv(types[c], r[c]) for c in cols) for r in data[table]["rows"]}
    key = lambda row: tuple(row[i] for i in pk)
    got_by, want_by = {key(r): r for r in got}, {key(r): r for r in want}
    missing, extra = sorted(set(want_by) - set(got_by), key=str), sorted(set(got_by) - set(want_by), key=str)
    diffs = [f"{k}: {cols[i]} database {got_by[k][i]!r}, data.csv {want_by[k][i]!r}"
             for k in sorted(set(got_by) & set(want_by), key=str)
             for i in range(len(cols)) if got_by[k][i] != want_by[k][i]]
    assert not missing, f"rows missing from the database: {missing[:5]}"
    assert not extra, f"rows not in data.csv: {extra[:5]}"
    assert not diffs, "; ".join(diffs[:5])


INTEGRITY = {   # requirements analysis, Integrity rules (I6 is deliberately unconstrained)
    "I1-blend-weights-sum-to-one":
        "SELECT COUNT(*) FROM (SELECT station_id FROM crossfade.station_blend GROUP BY station_id "
        "HAVING SUM(weight) <> 1) x",
    "I1-every-station-has-a-blend":
        "SELECT COUNT(*) FROM crossfade.station s LEFT OUTER JOIN crossfade.station_blend b "
        "ON b.station_id = s.station_id WHERE b.station_id IS NULL",
    "I2-ten-probabilities-summing-to-one":
        "SELECT COUNT(*) FROM (SELECT track_id, model_id FROM crossfade.genre_probability GROUP BY track_id, model_id "
        "HAVING COUNT(*) <> (SELECT COUNT(*) FROM crossfade.genre) OR ABS(SUM(probability) - 1) > 0.001) x",
    "I3-top-genre-agrees-with-probabilities":
        "SELECT COUNT(*) FROM crossfade.track_score s INNER JOIN crossfade.genre_probability p "
        "ON p.track_id = s.track_id AND p.model_id = s.model_id AND p.genre_id = s.genre_id "
        "WHERE p.probability <> s.top_probability OR p.probability < (SELECT MAX(q.probability) "
        "FROM crossfade.genre_probability q WHERE q.track_id = s.track_id AND q.model_id = s.model_id)",
    "I3-every-score-has-its-top-genre-row":
        "SELECT COUNT(*) FROM crossfade.track_score s LEFT OUTER JOIN crossfade.genre_probability p "
        "ON p.track_id = s.track_id AND p.model_id = s.model_id AND p.genre_id = s.genre_id WHERE p.track_id IS NULL",
    "I4-minimum-ambiguity-not-above-maximum":
        "SELECT COUNT(*) FROM crossfade.station WHERE minimum_ambiguity > maximum_ambiguity",
    "I5-scored-only-with-a-score":
        "SELECT COUNT(*) FROM crossfade.track t WHERE t.ingest_status = 'scored' AND NOT EXISTS "
        "(SELECT 1 FROM crossfade.track_score s WHERE s.track_id = t.track_id)",
    "I7-completed-means-whole-track":
        "SELECT COUNT(*) FROM crossfade.play p INNER JOIN crossfade.track t ON t.track_id = p.track_id "
        "WHERE p.completed <> (p.seconds_played = t.duration)",
    "I7-royalty-is-payout-rate-from-30-seconds":
        "SELECT COUNT(*) FROM crossfade.play p INNER JOIN crossfade.track t ON t.track_id = p.track_id "
        "INNER JOIN crossfade.artist a ON a.artist_id = t.artist_id "
        "WHERE p.royalty_amount <> IF(p.seconds_played >= 30, a.payout_rate, 0)",
}


@pytest.mark.parametrize("rule", INTEGRITY)
def test_data_integrity_rule(con, rule):
    """A cross-row rule from the requirements analysis holds on the loaded data (0 rows break it)."""
    with con.cursor() as cur:
        n = query(cur, INTEGRITY[rule])[0][0]
    assert n == 0, f"{n} rows break {rule}"


@pytest.mark.parametrize("fk", FOREIGN_KEYS)
def test_data_no_orphans(con, fk):
    """Every child row's foreign key value has a parent row (a NULL optional key is allowed)."""
    child, ccols, parent, pcols, _ = FOREIGN_KEYS[fk]
    on = " AND ".join(f"p.{pc} = c.{cc}" for cc, pc in zip(ccols, pcols))
    notnull = " AND ".join(f"c.{cc} IS NOT NULL" for cc in ccols)
    with con.cursor() as cur:
        n = query(cur, f"SELECT COUNT(*) FROM {DB}.{child} c LEFT OUTER JOIN {DB}.{parent} p ON {on} "
                       f"WHERE {notnull} AND p.{pcols[0]} IS NULL")[0][0]
    assert n == 0, f"{n} {child} rows point at no {parent}"


# ================================================================================================ 5. enforce
INSERTABLE = [t for t in TABLES if t != "genre"]       # genre ids 0-9 are all used and the CHECK allows no other


@pytest.mark.parametrize("table", INSERTABLE)
def test_enforce_valid_row_accepted(tx, table):
    """Control: a new, valid row is accepted. Each refusal test below starts from this same row and changes one
    value, so a refusal is caused by that value and nothing else."""
    row = fresh_row(tx, table)
    insert(tx, table, row)
    pk = PRIMARY_KEY[table]
    assert query(tx, f"SELECT COUNT(*) FROM {DB}.{table} WHERE " + " AND ".join(f"{c} = %s" for c in pk),
                 [row[c] for c in pk])[0][0] == 1


@pytest.mark.parametrize("table", TABLES)
def test_enforce_duplicate_primary_key(tx, table):
    """Inserting a copy of an existing row is refused on the primary key (1062)."""
    row = sample_row(tx, table)
    refused(tx, lambda: insert(tx, table, row), 1062, f"{table}.PRIMARY")


@pytest.mark.parametrize("uq", UNIQUE_KEYS)
def test_enforce_duplicate_unique(tx, uq):
    """A second row with an existing unique value is refused on that unique index (1062)."""
    table, (col,) = UNIQUE_KEYS[uq]
    taken = sample_row(tx, table)[col]
    if table == "genre":
        refused(tx, f"UPDATE {DB}.genre SET name = (SELECT n FROM (SELECT name AS n FROM {DB}.genre WHERE genre_id = 1) x) "
                    f"WHERE genre_id = 0", 1062, uq)
        return
    row = fresh_row(tx, table)
    row[col] = taken
    refused(tx, lambda: insert(tx, table, row), 1062, uq)


@pytest.mark.parametrize("fk", FOREIGN_KEYS)
def test_enforce_orphan_refused(tx, fk):
    """A row whose foreign key points at no parent row is refused by that foreign key (1452)."""
    child, ccols, *_ = FOREIGN_KEYS[fk]
    row = fresh_row(tx, child)
    row[ccols[0]] = 250 if "tinyint" in ctype(child, ccols[0]) else 999999
    refused(tx, lambda: insert(tx, child, row), 1452, fk)


NOT_NULL = [f"{t}-{c}" for t in TABLES for c, _, n in SPEC[t] if not n]
NULLABLE = [f"{t}-{c}" for t in TABLES for c, _, n in SPEC[t] if n]


@pytest.mark.parametrize("tc", NOT_NULL)
def test_enforce_not_null(tx, tc):
    """NULL in a NOT NULL column is refused (1048)."""
    table, col = tc.split("-")
    if table == "genre":
        refused(tx, f"UPDATE {DB}.genre SET {col} = NULL WHERE genre_id = 0", 1048, col)
        return
    row = fresh_row(tx, table)
    row[col] = None
    refused(tx, lambda: insert(tx, table, row), 1048, col)


@pytest.mark.parametrize("tc", NULLABLE)
def test_enforce_null_allowed(tx, tc):
    """An optional column accepts NULL (the model shows it as optional)."""
    table, col = tc.split("-")
    if table == "genre":
        tx.execute(f"UPDATE {DB}.genre SET {col} = NULL WHERE genre_id = 0")
        assert tx.rowcount == 1
        return
    row = fresh_row(tx, table)
    row[col] = None
    insert(tx, table, row)


@pytest.mark.parametrize("ck", CHECKS)
def test_enforce_check(tx, ck):
    """A value that breaks the rule is refused by that CHECK constraint (3819)."""
    table, bad, _source = CHECKS[ck]
    if table == "genre":
        refused(tx, lambda: insert(tx, "genre", {"genre_id": bad["genre_id"], "name": "zz", "description": None}),
                3819, ck)
        return
    row = fresh_row(tx, table)
    row.update(bad)
    refused(tx, lambda: insert(tx, table, row), 3819, ck)


@pytest.mark.parametrize("case", TYPE_LIMITS)
def test_enforce_type_limit(tx, case):
    """The column's type refuses a value it cannot hold, instead of silently trimming or rounding it."""
    table, bad, code, _type = TYPE_LIMITS[case]
    row = fresh_row(tx, table)
    row.update(bad)
    refused(tx, lambda: insert(tx, table, row), code, list(bad)[0])


def test_enforce_delete_cascades_probabilities(tx):
    """Deleting a scoring result deletes its ten genre probabilities with it (ON DELETE CASCADE)."""
    t, m = query(tx, f"SELECT track_id, model_id FROM {DB}.track_score ORDER BY track_id, model_id LIMIT 1")[0]
    before = counts(tx)
    tx.execute(f"DELETE FROM {DB}.track_score WHERE track_id = %s AND model_id = %s", (t, m))
    assert query(tx, f"SELECT COUNT(*) FROM {DB}.genre_probability WHERE track_id = %s AND model_id = %s", (t, m))[0][0] == 0
    assert counts(tx)["genre_probability"] == before["genre_probability"] - 10


def test_enforce_delete_station_cascades_blend_and_keeps_plays(tx):
    """Deleting a station deletes its blend rows (CASCADE) and keeps its plays with no station (SET NULL)."""
    s = query(tx, f"SELECT station_id FROM {DB}.play WHERE station_id IS NOT NULL ORDER BY station_id LIMIT 1")[0][0]
    plays = query(tx, f"SELECT COUNT(*) FROM {DB}.play WHERE station_id = %s", (s,))[0][0]
    before = counts(tx)
    tx.execute(f"DELETE FROM {DB}.station WHERE station_id = %s", (s,))
    assert query(tx, f"SELECT COUNT(*) FROM {DB}.station_blend WHERE station_id = %s", (s,))[0][0] == 0
    after = counts(tx)
    assert after["play"] == before["play"], "plays were deleted with the station"
    assert query(tx, f"SELECT COUNT(*) FROM {DB}.play WHERE station_id IS NULL", ())[0][0] >= plays


@pytest.mark.parametrize("parent,where", [("artist", "artist_id = (SELECT a FROM (SELECT MIN(artist_id) AS a FROM crossfade.track) x)"),
                                          ("genre", "genre_id = (SELECT g FROM (SELECT MIN(genre_id) AS g FROM crossfade.track_score) x)"),
                                          ("listener", "listener_id = (SELECT l FROM (SELECT MIN(listener_id) AS l FROM crossfade.play) x)"),
                                          ("track", "track_id = (SELECT t FROM (SELECT MIN(track_id) AS t FROM crossfade.play) x)")],
                         ids=["artist", "genre", "listener", "track"])
def test_enforce_delete_parent_refused(tx, parent, where):
    """A parent row that child rows still point at cannot be deleted (1451): royalties, scores and plays keep
    their artist, genre, listener and track."""
    refused(tx, f"DELETE FROM {DB}.{parent} WHERE {where}", 1451)


def test_enforce_rollback_leaves_data(con, data):
    """After all the refused and rolled-back writes, every table still holds exactly the data.csv row count."""
    con.rollback()
    with con.cursor() as cur:
        got = counts(cur)
    assert got == {t: len(data[t]["rows"]) for t in TABLES}
