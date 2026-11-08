"""Shared set-up for the CROSSFADE Project 2 tests.

Finds the input files, connects to MySQL, checks (or rebuilds) the `crossfade` database, splits the
.sql files into commented statements, and writes a results snapshot when the run ends.

Files are looked for in this order: command-line option, environment variable, this folder, the
current folder, the repository layout. So the tests run the same way from a clone of the repo or
from a folder holding the test kit plus the two files downloaded from the site:

    data.csv                     Project 1 sample data, bulk view (site: Home > Project 1 data)
    database_implementation.sql  Task 1 (site: Project 2 > database_implementation)
    single_table.sql             Task 2 (site: Project 2 > single_table)
    multiple_table.sql           Task 3 (site: Project 2 > multiple_table)
    routines.sql                 Task 4 (site: Project 2 > routines)
    use_cases.json               the use cases (comes with the test kit)

test_implementation.py needs only data.csv and database_implementation.sql.

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
    g.addoption("--msql", help="multiple_table.sql")
    g.addoption("--rsql", help="routines.sql")
    g.addoption("--use-cases", dest="use_cases", help="use_cases.json")
    g.addoption("--fresh", action="store_true",
                help="rebuild `crossfade` from database_implementation.sql before testing (default: test the database as it is)")
    g.addoption("--results", help="folder for the results snapshot (default: project2/data in the repo, else ./results)")
    g.addoption("--db-user"); g.addoption("--db-password"); g.addoption("--db-host"); g.addoption("--db-port", type=int)


CANDIDATES = {
    "data": ("CROSSFADE_DATA", "data.csv", "project1/data_export/data.csv"),
    "impl": ("CROSSFADE_IMPL", "database_implementation.sql", "project2/deliverables/database_implementation.sql"),
    "sql": ("CROSSFADE_SQL", "single_table.sql", "project2/deliverables/single_table.sql"),
    "msql": ("CROSSFADE_MSQL", "multiple_table.sql", "project2/deliverables/multiple_table.sql"),
    "rsql": ("CROSSFADE_RSQL", "routines.sql", "project2/deliverables/routines.sql"),
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
        if re.match(r"DELIMITER\b", text[i:i + 9], re.I) and (i == 0 or text[i - 1] == "\n"):
            raise ValueError("DELIMITER is not supported by split_sql")
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


def split_script(text):
    """Split a script that may change its delimiter (DELIMITER $$, as routines.sql does) into
    [(comment, statement)], like split_sql. Each statement is returned without its delimiter, ready to send to
    MySQL on its own: the server never sees DELIMITER, which is a command of the mysql client and Workbench."""
    out, i, n, delim = [], 0, len(text), ";"
    comment, stmt, notes = [], [], []
    while i < n:
        c = text[i]
        if (i == 0 or text[i - 1] == "\n") and re.match(r"DELIMITER[ \t]+(\S+)", text[i:i + 30], re.I) \
                and not "".join(stmt).strip():
            m = re.match(r"DELIMITER[ \t]+(\S+)[^\n]*", text[i:], re.I)
            delim, i = m.group(1), i + m.end()
            continue
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
                stmt.append(text[i:j])          # kept: a routine body's comments are part of its definition
            else:
                notes.append(text[i + 2:j].strip())     # a -- line just before a statement labels it
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
        elif text.startswith(delim, i):
            st = "".join(stmt).strip()
            if st:
                out.append((comment[-1].strip() if comment else " ".join(notes), st))
            comment, stmt, notes, i = [], [], [], i + len(delim)
        else:
            stmt.append(c); i += 1
    st = "".join(stmt).strip()
    if st:
        out.append((comment[-1].strip() if comment else " ".join(notes), st))
    return out


def blank_code(text):
    """SQL with comments (-- and /* */) removed and the contents of string literals blanked."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("--", i) and (i + 2 >= n or text[i + 2] in " \t\r\n"):
            j = text.find("\n", i); i = n if j < 0 else j
        elif text.startswith("/*", i):
            i = text.index("*/", i + 2) + 2; out.append(" ")
        elif text[i] in "'\"":
            q, j = text[i], i + 1
            while j < n:
                if text[j] == "\\": j += 2; continue
                if text[j] == q:
                    if j + 1 < n and text[j + 1] == q: j += 2; continue
                    break
                j += 1
            out.append(q + q); i = j + 1
        else:
            out.append(text[i]); i += 1
    return "".join(out)


class Routine:
    """One routine of routines.sql: its purpose comment and its CREATE statement (the DROP ... IF EXISTS
    between them is the comment's first statement, so the comment is carried over to the CREATE)."""
    def __init__(self, comment, sql):
        self.comment, self.sql = comment, sql
        m = re.search(r"\[([FP]\d+)\]\s*(\w+)?", comment)
        self.tag = m.group(1) if m else None
        self.name = (m.group(2) or "").lower() if m else ""
        m = re.match(r"\s*CREATE\s+(?:DEFINER\s*=\s*\S+\s+)?(FUNCTION|PROCEDURE)\s+(?:`?(\w+)`?\.)?`?(\w+)`?", sql, re.I)
        self.kind = m.group(1).upper() if m else None
        self.schema = (m.group(2) or "").lower() if m else ""
        self.created = m.group(3).lower() if m else ""
        field = lambda k: (re.search(k + r":\s*([^\n]+)", comment) or [None, ""])[1].strip()
        self.use_cases = re.findall(r"UC-\d+", field("Use cases?"))
        self.requirement = field("Requirements")
        self.uses = [x.strip() for x in field("Uses").split(",") if x.strip()]
        self.tables = [x.strip().lower() for x in field("Tables").split(",") if x.strip()]
        self.params = [x.strip() for x in re.split(r",(?![^()]*\))", field("Parameters")) if x.strip()]   # DECIMAL(5,5) keeps its comma
        self.returns = field("Returns")
        self.errors = field("Errors")
        self.example = field("Example")
        m = re.search(r"Business need:\s*(.+?)(?:\n\s*What it does:|$)", comment, re.S)
        self.need = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        m = re.search(r"What it does:\s*(.+?)(?:\n\s*Requirements:|$)", comment, re.S)
        self.does = [re.sub(r"\s+", " ", b).strip() for b in re.split(r"\n\s*-\s+", "\n" + m.group(1)) if b.strip()] if m else []

    @property
    def body(self):
        """The routine's BEGIN ... END, with comments removed and string literals blanked ('' each), read in one
        pass so an apostrophe inside a comment is never taken for the start of a string."""
        code = blank_code(self.sql)
        return code[code.upper().find("BEGIN"):] if "BEGIN" in code.upper() else code

    def __repr__(self):
        return self.tag or self.sql[:30]


def parse_routines(path):
    """The routines of routines.sql in file order, plus the statements that are not routines (the DROPs and the
    "Try it" block) as [(comment, statement)]."""
    routines, other, pending = [], [], ""
    for comment, st in split_script(path.read_text(encoding="utf-8")):
        if re.search(r"\[[FP]\d+\]", comment):
            pending = comment
        if re.match(r"\s*CREATE\s+(?:DEFINER\s*=\s*\S+\s+)?(FUNCTION|PROCEDURE)\b", st, re.I):
            routines.append(Routine(pending if not re.search(r"\[[FP]\d+\]", comment) else comment, st)); pending = ""
        else:
            other.append((comment, st))
    return routines, other


def strip_literals(sql):
    """The statement with string literals blanked, so words inside quotes are never mistaken for SQL."""
    return re.sub(r"'(?:[^'\\]|\\.|'')*'", "''", sql)


class Query:
    def __init__(self, comment, sql):
        self.comment, self.sql = comment, sql
        m = re.search(r"\[([SEM]\d+)\]\s*([A-Z_]+\b)?", comment)
        self.tag = m.group(1) if m else None
        self.table = m.group(2).lower() if m and m.group(2) else None
        m = re.search(r"\[M\d+\]\s*([^\n]+)", comment)
        self.title = m.group(1).strip() if m else ""
        m = re.search(r"Tables:\s*([^\n]+)", comment)                     # multiple_table.sql
        self.tables = [x.strip().lower() for x in m.group(1).split(",") if x.strip()] if m else []
        m = re.search(r"One row per:\s*([^\n]+)", comment)
        self.grain = [x.strip().lower() for x in m.group(1).split(",") if x.strip()] if m else []
        m = re.search(r"Requirements:\s*(3\.[1-5])\b", comment)
        self.requirement3 = m.group(1) if m else None
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
    if "routine" in metafunc.fixturenames:                   # routines.sql: one test per [F#] / [P#] routine
        rs = [r for r in parse_routines(find_file(metafunc.config, "rsql"))[0] if r.tag]
        metafunc.parametrize("routine", rs, ids=[r.tag for r in rs])
    if "mquery" in metafunc.fixturenames:                    # multiple_table.sql: one test per [M#] query
        ms = [q for q in parse_queries(find_file(metafunc.config, "msql")) if q.tag and q.tag.startswith("M")]
        metafunc.parametrize("mquery", ms, ids=[q.tag for q in ms])
    if not {"query", "error_case"} & set(metafunc.fixturenames):
        return                      # only the single_table.sql tests need single_table.sql
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


class _Paths(dict):
    """File paths, each looked up the first time a test asks for it, so a test file only needs its own inputs."""
    def __init__(self, config):
        super().__init__(); self.config = config
    def __missing__(self, key):
        self[key] = find_file(self.config, key)
        return self[key]


@pytest.fixture(scope="session")
def paths(pytestconfig):
    return _Paths(pytestconfig)


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
NEEDED_BY = {"data": "every test file", "impl": "every test file", "sql": "test_single_table.py",
             "msql": "test_multiple_table.py", "rsql": "test_routines.py", "use_cases": "the query test files"}


def pytest_report_header(config):
    lines = []
    for k in CANDIDATES:
        try:
            lines.append(f"crossfade {k:<10} {find_file(config, k)}")
        except pytest.UsageError:
            lines.append(f"crossfade {k:<10} not here (needed only by {NEEDED_BY[k]})")
    modes = []
    if (HERE / "test_implementation.py").exists():
        modes.append("test_implementation.py: drops and rebuilds `crossfade` from the script (twice)")
    for f in ("test_single_table.py", "test_multiple_table.py", "test_routines.py"):
        if (HERE / f).exists():
            modes.append(f"{f + ':':<24}" + ("--fresh: rebuild `crossfade` first, then test" if config.getoption("fresh")
                                            else "tests the existing `crossfade` database"))
    for i, m in enumerate(modes):
        lines.append(("crossfade mode       " if i == 0 else "                     ") + m)
    return lines


SNAPSHOT = {"queries": {}, "outcomes": {}, "cases": {}}             # single_table.sql ([S#], [E#])
SNAPSHOT_M = {"queries": {}, "cases": {}}                          # multiple_table.sql ([M#])
SNAPSHOT_R = {"queries": {}, "cases": {}, "demo": []}              # routines.sql ([F#], [P#])


def _snap(tag):
    tag = str(tag or "")
    return SNAPSHOT_M if tag.startswith("M") else SNAPSHOT_R if tag[:1] in ("F", "P") else SNAPSHOT


def record(tag, **kw):
    _snap(tag)["queries"].setdefault(tag, {}).update(kw)


def record_case(name, case):
    """A behaviour case: tag, inputs, expected and actual rows, docstring (see test_single_table.py)."""
    _snap(case.get("tag"))["cases"][name] = case


def record_demo(steps):
    """What the "Try it" block of routines.sql returned, statement by statement."""
    SNAPSHOT_R["demo"] = steps


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        SNAPSHOT["outcomes"][report.nodeid] = report.outcome


IMPL = {"load": {}, "tables": {}}          # filled by test_implementation.py


def record_impl(section, key, value):
    """Facts from test_implementation.py for the site's results snapshot (implementation_results.js)."""
    IMPL.setdefault(section, {})[key] = value


def _results_dir(cfg):
    return pathlib.Path(cfg.getoption("results")) if cfg.getoption("results") else \
        (REPO / "project2" / "data" if REPO else pathlib.Path.cwd() / "results")


def _write_snapshot(out, stem, var, doc):
    out.mkdir(parents=True, exist_ok=True)
    js = json.dumps(doc, indent=1, default=str, ensure_ascii=False)
    (out / f"{stem}.json").write_text(js, encoding="utf-8")
    (out / f"{stem}.js").write_text(
        "/* Written by project2/tests (pytest) at the end of a run. Do not edit. */\nwindow." + var + " = " + js + ";\n",
        encoding="utf-8")
    print(f"\nresults snapshot: {out / (stem + '.json')}")


def pytest_sessionfinish(session, exitstatus):
    cfg = session.config
    now = datetime.datetime.now().isoformat(timespec="seconds")
    out = _results_dir(cfg)

    # database_implementation.sql (test_implementation.py)
    impl = {k: o for k, o in SNAPSHOT["outcomes"].items() if "test_implementation.py" in k}
    if impl:
        groups = {}
        for nodeid, outcome in impl.items():
            name = nodeid.split("::")[-1]
            m = re.match(r"test_(\w+?)(?:\[(.*)\])?$", name)
            groups.setdefault(m.group(1) if m else name, []).append({"test": name, "param": m.group(2) if m else None,
                                                                      "outcome": outcome})
        _write_snapshot(out, "implementation_results", "P2_IMPL", {
            "file": "database_implementation.sql", "generated": now,
            "passed": sum(1 for o in impl.values() if o == "passed"),
            "failed": sum(1 for o in impl.values() if o != "passed"),
            "groups": groups, "load": IMPL["load"], "tables": IMPL["tables"]})

    # multiple_table.sql (test_multiple_table.py)
    multi = {k: o for k, o in SNAPSHOT["outcomes"].items() if "test_multiple_table.py" in k}
    if multi and SNAPSHOT_M["queries"]:
        tests = {}
        for nodeid, outcome in multi.items():
            m = re.search(r"\[(M\d+)\]", nodeid)
            tests.setdefault(m.group(1) if m else "file", []).append({"test": nodeid.split("::")[-1], "outcome": outcome})
        _write_snapshot(out, "multiple_table_results", "P2_MULTIPLE", {
            "file": "multiple_table.sql", "generated": now,
            "passed": sum(1 for o in multi.values() if o == "passed"),
            "failed": sum(1 for o in multi.values() if o != "passed"),
            "queries": SNAPSHOT_M["queries"], "tests": tests,
            "cases": [dict(c, test=n, outcome=next((o for k, o in multi.items() if k.endswith("::" + n)), "not run"))
                      for n, c in SNAPSHOT_M["cases"].items()]})

    # routines.sql (test_routines.py)
    rout = {k: o for k, o in SNAPSHOT["outcomes"].items() if "test_routines.py" in k}
    if rout and SNAPSHOT_R["queries"]:
        tests = {}
        for nodeid, outcome in rout.items():
            m = re.search(r"\[([FP]\d+)\]", nodeid) or re.match(r".*::test_([fp]\d+)_", nodeid)
            tests.setdefault(m.group(1).upper() if m else "file", []).append({"test": nodeid.split("::")[-1], "outcome": outcome})
        _write_snapshot(out, "routines_results", "P2_ROUTINES", {
            "file": "routines.sql", "generated": now,
            "passed": sum(1 for o in rout.values() if o == "passed"),
            "failed": sum(1 for o in rout.values() if o != "passed"),
            "queries": SNAPSHOT_R["queries"], "tests": tests, "demo": SNAPSHOT_R["demo"],
            "cases": [dict(c, test=n, outcome=next((o for k, o in rout.items() if k.endswith("::" + n)), "not run"))
                      for n, c in SNAPSHOT_R["cases"].items()]})

    # single_table.sql (test_single_table.py)
    if not SNAPSHOT["queries"]:
        return
    single = {k: o for k, o in SNAPSHOT["outcomes"].items() if "test_single_table.py" in k}
    tests = {}
    for nodeid, outcome in single.items():
        m = re.search(r"\[([SE]\d+)\]", nodeid)
        key = m.group(1) if m else "file"
        tests.setdefault(key, []).append({"test": nodeid.split("::")[-1], "outcome": outcome})
    _write_snapshot(out, "single_table_results", "P2_SINGLE", {
        "file": "single_table.sql", "generated": now,
        "passed": sum(1 for o in single.values() if o == "passed"),
        "failed": sum(1 for o in single.values() if o != "passed"),
        "queries": SNAPSHOT["queries"], "tests": tests,
        "cases": [dict(c, test=n, outcome=next((o for k, o in single.items() if k.endswith("::" + n)), "not run"))
                  for n, c in SNAPSHOT["cases"].items()]})
