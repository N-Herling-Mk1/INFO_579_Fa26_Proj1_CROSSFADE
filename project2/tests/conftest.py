"""Shared set-up for the CROSSFADE Project 2 tests.

Finds the input files, connects to MySQL, checks (or rebuilds) the `crossfade` database, splits the
.sql files into commented statements, and writes a results snapshot when the run ends.

Files are looked for in this order: command-line option, environment variable, this folder, the
current folder, the repository layout. So the tests run the same way from a clone of the repo or
from a folder holding the test kit plus the two files downloaded from the site:

    data.csv                     Project 1 sample data, bulk view (site: Home > Project 1 data)
    database_implementation.sql  Task 1 (site: Project 2 > database_implementation)
    single_table.sql             Task 2 (site: Project 2 > single_table)
    use_cases.json               the use cases (comes with the test kit)

Connection: CROSSFADE_DB_USER (root), CROSSFADE_DB_PASSWORD, CROSSFADE_DB_HOST (127.0.0.1),
CROSSFADE_DB_PORT (3306), or the matching --db-* options.
"""
import csv, json, os, pathlib, re, datetime
from decimal import Decimal

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent if (HERE.parent.parent / "project1").is_dir() else None
DB = "crossfade"


# ----------------------------------------------------------------------------- options and files
def pytest_addoption(parser):
    g = parser.getgroup("crossfade")
    g.addoption("--data", help="bulk data.csv (Project 1 sample data)")
    g.addoption("--impl", help="database_implementation.sql")
    g.addoption("--sql", help="single_table.sql")
    g.addoption("--use-cases", dest="use_cases", help="use_cases.json")
    g.addoption("--fresh", action="store_true",
                help="rebuild `crossfade` from database_implementation.sql before testing (default: test the database as it is)")
    g.addoption("--results", help="folder for the results snapshot (default: project2/data in the repo, else ./results)")
    g.addoption("--db-user"); g.addoption("--db-password"); g.addoption("--db-host"); g.addoption("--db-port", type=int)


CANDIDATES = {
    "data": ("CROSSFADE_DATA", "data.csv", "project1/data_export/data.csv"),
    "impl": ("CROSSFADE_IMPL", "database_implementation.sql", "project2/deliverables/database_implementation.sql"),
    "sql": ("CROSSFADE_SQL", "single_table.sql", "project2/deliverables/single_table.sql"),
    "use_cases": ("CROSSFADE_USE_CASES", "use_cases.json", "project2/data/use_cases.json"),
}


def find_file(config, key):
    env, name, repo_rel = CANDIDATES[key]
    given = config.getoption(key) or os.environ.get(env)
    places = [pathlib.Path(given)] if given else []
    places += [HERE / name, pathlib.Path.cwd() / name] + ([REPO / repo_rel] if REPO else [])
    for p in places:
        if p.is_file():
            return p.resolve()
    raise pytest.UsageError(f"cannot find {name}; looked in: " + ", ".join(str(p) for p in places) +
                            f". Put it next to the tests or pass --{key.replace('_', '-')} PATH.")


# ----------------------------------------------------------------------------- Project 1 data (bulk CSV)
def snake(s):
    return re.sub(r"[^a-z0-9]+", "_", s.strip().lower()).strip("_")


def load_bulk(path):
    """data.csv as laid out in data.xlsx: per table a title row, a header row, data rows, a blank row.
    Returns {table: {"columns": [...], "rows": [{col: str or None}]}}; empty cell = NULL."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    tables, i = {}, 0
    while i < len(rows):
        r = [c.strip() for c in rows[i]]
        if r and r[0] and not any(r[1:]):
            name, header = snake(r[0]), [snake(c) for c in rows[i + 1] if c.strip()]
            data, j = [], i + 2
            while j < len(rows) and any(c.strip() for c in rows[j]):
                vals = rows[j][:len(header)]
                data.append({h: (v if v != "" else None) for h, v in zip(header, vals)})
                j += 1
            tables[name] = {"columns": header, "rows": data}
            i = j
        else:
            i += 1
    return tables


# ----------------------------------------------------------------------------- SQL files
def split_sql(text):
    """Split a script into [(comment, statement)], where comment is the /* */ block right before the
    statement (a file header further up is not part of it). Understands quotes and both comment styles; no DELIMITER support (not needed here)."""
    out, i, n = [], 0, len(text)
    comment, stmt = [], []
    while i < n:
        c = text[i]
        if text.startswith("/*", i):
            j = text.index("*/", i + 2) + 2
            if "".join(stmt).strip():
                stmt.append(text[i:j])
            else:
                comment.append(text[i + 2:j - 2])
            i = j
        elif text.startswith("--", i) and (i + 2 >= n or text[i + 2] in " \t\r\n"):
            j = text.find("\n", i); j = n if j < 0 else j
            if "".join(stmt).strip():
                stmt.append(" ")
            i = j
        elif c in "'\"`":
            j = i + 1
            while j < n:
                if text[j] == "\\": j += 2; continue
                if text[j] == c:
                    if j + 1 < n and text[j + 1] == c: j += 2; continue
                    break
                j += 1
            stmt.append(text[i:j + 1]); i = j + 1
        elif c == ";":
            s = "".join(stmt).strip()
            if s:
                out.append((comment[-1].strip() if comment else "", s))
            comment, stmt, i = [], [], i + 1
        else:
            stmt.append(c); i += 1
    s = "".join(stmt).strip()
    if s:
        out.append((comment[-1].strip() if comment else "", s))
    return out


def strip_literals(sql):
    """The statement with string literals blanked, so words inside quotes are never mistaken for SQL."""
    return re.sub(r"'(?:[^'\\]|\\.|'')*'", "''", sql)


class Query:
    def __init__(self, comment, sql):
        self.comment, self.sql = comment, sql
        m = re.search(r"\[([SE]\d+)\]\s*([A-Z_]+)?", comment)
        self.tag = m.group(1) if m else None
        self.table = m.group(2).lower() if m and m.group(2) else None
        m = re.search(r"Use cases?:\s*([^\n]+)", comment)
        self.use_cases = re.findall(r"UC-\d+", m.group(1)) if m else []
        m = re.search(r"Business question:\s*(.+?)(?:\n\s*-|\n\s*Requirements:|$)", comment, re.S)
        self.question = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        m = re.search(r"Requirements:\s*([^\n]+)", comment)
        self.declared = sorted(set(re.findall(r"\(([a-e])\)", m.group(1)))) if m else []
        m = re.search(r"Expects:\s*(\d+)\s+(\w+)", comment)
        self.expects = (int(m.group(1)), m.group(2)) if m else None
        m = re.search(r"Output:\s*([^\n]+)", comment)
        self.output = [c.strip() for c in m.group(1).split(",") if c.strip()] if m else []
        m = re.search(r"Business need:\s*(.+?)(?:\n\s*Business question:|$)", comment, re.S)
        self.need = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

    @property
    def is_error(self):
        """[E#] statements are writes the database must refuse; [S#] statements are queries."""
        return bool(self.tag and self.tag.startswith("E"))

    def __repr__(self):
        return self.tag or self.sql[:30]


def parse_queries(path):
    return [Query(c, s) for c, s in split_sql(path.read_text(encoding="utf-8"))]


# ----------------------------------------------------------------------------- collection: one test per query
# single_table.sql holds the queries ([S1]...) and, last, the statements that must fail ([E1]...).
def pytest_generate_tests(metafunc):
    stmts = parse_queries(find_file(metafunc.config, "sql"))
    if "query" in metafunc.fixturenames:
        qs = [s for s in stmts if not s.is_error]
        metafunc.parametrize("query", qs, ids=[q.tag or f"stmt{i + 1}" for i, q in enumerate(qs)])
    if "error_case" in metafunc.fixturenames:
        es = [s for s in stmts if s.is_error]
        metafunc.parametrize("error_case", es, ids=[e.tag for e in es])


# ----------------------------------------------------------------------------- database
def connect(config, database=DB):
    import pymysql
    opt = lambda o, e, d: config.getoption(o) or os.environ.get(e) or d
    pw = config.getoption("db_password")
    if pw is None:
        pw = os.environ.get("CROSSFADE_DB_PASSWORD")
    if pw is None:
        raise pytest.UsageError("set CROSSFADE_DB_PASSWORD (PowerShell: $env:CROSSFADE_DB_PASSWORD = \"...\"), "
                                "or pass --db-password; use an empty string if root has no password")
    return pymysql.connect(host=opt("db_host", "CROSSFADE_DB_HOST", "127.0.0.1"),
                           port=int(opt("db_port", "CROSSFADE_DB_PORT", 3306)),
                           user=opt("db_user", "CROSSFADE_DB_USER", "root"), password=pw,
                           database=database, charset="utf8mb4", autocommit=False)


def build_database(config, impl_path):
    stmts = split_sql(impl_path.read_text(encoding="utf-8"))
    con = connect(config, database=None)
    try:
        with con.cursor() as cur:
            for k, (_, s) in enumerate(stmts, 1):
                cur.execute(s)
                print(f"\r      --fresh: statement {k}/{len(stmts)}", end="", flush=True)
        con.commit()
        print(flush=True)
    finally:
        con.close()


@pytest.fixture(scope="session")
def paths(pytestconfig):
    return {k: find_file(pytestconfig, k) for k in CANDIDATES}


@pytest.fixture(scope="session")
def data(paths):
    return load_bulk(paths["data"])


@pytest.fixture(scope="session")
def use_cases(paths):
    return {u["id"]: u for u in json.loads(paths["use_cases"].read_text(encoding="utf-8"))["useCases"]}


@pytest.fixture(scope="session")
def db(pytestconfig, paths, data):
    """A connection to `crossfade`, after confirming it holds exactly the Project 1 sample data."""
    if pytestconfig.getoption("fresh"):
        build_database(pytestconfig, paths["impl"])
    try:
        con = connect(pytestconfig)
    except pytest.UsageError as e:
        pytest.exit(str(e), returncode=4)
    except Exception as e:
        pytest.exit(f"cannot open the `crossfade` database ({e}). Build it first by running "
                    f"database_implementation.sql, or rerun with --fresh.", returncode=3)
    with con.cursor() as cur:
        for t, spec in data.items():
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            n = cur.fetchone()[0]
            if n != len(spec["rows"]):
                pytest.exit(f"`crossfade`.{t} has {n} rows but data.csv has {len(spec['rows'])}. Rebuild the "
                            f"database from database_implementation.sql (or rerun with --fresh).", returncode=3)
    con.rollback()
    yield con
    con.rollback()
    con.close()


def canon(v):
    """One comparable form for a value from MySQL or from the oracle."""
    if v is None:
        return None
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat(sep=" ") if isinstance(v, datetime.datetime) else v.isoformat()
    if isinstance(v, (int, Decimal, float)) and not isinstance(v, bool):
        return Decimal(str(v))
    if isinstance(v, (bytes, bytearray)):
        return "0x" + bytes(v).hex().upper()
    return str(v)


def run(con, sql):
    with con.cursor() as cur:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return cols, [tuple(canon(v) for v in r) for r in cur.fetchall()]


# ----------------------------------------------------------------------------- report header and snapshot
def pytest_report_header(config):
    lines = []
    for k in CANDIDATES:
        try:
            lines.append(f"crossfade {k:<10} {find_file(config, k)}")
        except pytest.UsageError as e:
            lines.append(f"crossfade {k:<10} MISSING: {e}")
    lines.append("crossfade mode       " + ("--fresh: rebuild the database first" if config.getoption("fresh")
                                            else "test the existing `crossfade` database"))
    return lines


SNAPSHOT = {"queries": {}, "outcomes": {}, "cases": {}}


def record(tag, **kw):
    SNAPSHOT["queries"].setdefault(tag, {}).update(kw)


def record_case(name, case):
    """A behaviour case: tag, inputs, expected and actual rows, docstring (see test_single_table.py)."""
    SNAPSHOT["cases"][name] = case


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        SNAPSHOT["outcomes"][report.nodeid] = report.outcome


def pytest_sessionfinish(session, exitstatus):
    if not SNAPSHOT["queries"]:
        return
    cfg = session.config
    out = pathlib.Path(cfg.getoption("results")) if cfg.getoption("results") else \
        (REPO / "project2" / "data" if REPO else pathlib.Path.cwd() / "results")
    out.mkdir(parents=True, exist_ok=True)
    tests = {}
    for nodeid, outcome in SNAPSHOT["outcomes"].items():
        m = re.search(r"\[([SE]\d+)\]", nodeid)
        key = m.group(1) if m else "file"
        tests.setdefault(key, []).append({"test": nodeid.split("::")[-1], "outcome": outcome})
    doc = {"file": "single_table.sql", "generated": datetime.datetime.now().isoformat(timespec="seconds"),
           "passed": sum(1 for o in SNAPSHOT["outcomes"].values() if o == "passed"),
           "failed": sum(1 for o in SNAPSHOT["outcomes"].values() if o != "passed"),
           "queries": SNAPSHOT["queries"], "tests": tests,
           "cases": [dict(c, test=n, outcome=next((o for k, o in SNAPSHOT["outcomes"].items() if k.endswith("::" + n)), "not run"))
                     for n, c in SNAPSHOT["cases"].items()]}
    js = json.dumps(doc, indent=1, default=str, ensure_ascii=False)
    (out / "single_table_results.json").write_text(js, encoding="utf-8")
    (out / "single_table_results.js").write_text(
        "/* Written by project2/tests (pytest) at the end of a run. Do not edit. */\nwindow.P2_SINGLE = " + js + ";\n",
        encoding="utf-8")
    print(f"\nresults snapshot: {out / 'single_table_results.json'}")
