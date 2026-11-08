"""Build the Project 2 "Vetting and tests" material, one deliverable at a time.

    python project2/scripts/build_vetting.py          (needs: pip install reportlab pytest pymysql)

One source, three outputs per tested file, so the site, the PDF and the download never disagree:
    project2/data/vetting.js                      window.P2_VET: per file, the test files, groups, coverage map,
                                                  what the tests cover and what they could miss, how to run them
    project2/docs/test_<file>_guide.pdf           the same, printable
    project2/tests/crossfade_<file>_tests.zip     a folder that runs as-is (tests, inputs, guides)

Files done: database_implementation.sql (test_implementation.py), single_table.sql (test_single_table.py),
multiple_table.sql (test_multiple_table.py), routines.sql (test_routines.py).
Inputs
    project2/tests/test_implementation.py         its spec (SPEC, FOREIGN_KEYS, CHECKS, ...) is imported, not copied
    project2/data/<file>_results.json             the last pytest run (python -m pytest project2/tests)
    project2/data/<file>_mutants.json             the last mutation run (mutate_<file>.py)
Run the tests first, then this script.
"""
import importlib.util, json, pathlib, re, sys, zipfile
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parents[2]
P2 = ROOT / "project2"
TESTS = P2 / "tests"
STAMP = (2026, 11, 7, 0, 0, 0)          # fixed zip entry time: an unchanged bundle rebuilds byte-identical
STEPS = 6


def say(n, msg):
    print(f"[{n}/{STEPS}] {msg}", flush=True)


# ------------------------------------------------------------------------------------------------ inputs
say(1, "reading the test spec and the last run")
sys.path.insert(0, str(TESTS))
spec = importlib.util.spec_from_file_location("test_implementation", TESTS / "test_implementation.py")
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
def jload(name):
    p = P2 / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


RES = jload("implementation_results.json")
MUT = jload("implementation_mutants.json")             # python project2/scripts/mutate_implementation.py
RES_S = jload("single_table_results.json")
MUT_S = jload("single_table_mutants.json")             # python project2/scripts/mutate_single_table.py
RES_M = jload("multiple_table_results.json")
MUT_M = jload("multiple_table_mutants.json")           # python project2/scripts/mutate_multiple_table.py
RES_R = jload("routines_results.json")
MUT_R = jload("routines_mutants.json")                 # python project2/scripts/mutate_routines.py

# ------------------------------------------------------------------------------------------------ the content
GROUPS = [   # (group, test-name prefixes, what it proves)
    ("load", ["load_"], "The script runs start to finish, and again on top of itself (re-runnable). No warnings: MySQL "
                        "warns when it silently rounds or trims a value, so a clean load means every value went in as "
                        "written. A purpose comment before every statement (the brief). Checks are never switched off. "
                        "Each table created once and loaded after its parents."),
    ("schema", ["schema_"], "Exactly the ten tables. Every column in the diagram's order with its exact type, size, "
                            "UNSIGNED flag and NULL / NOT NULL. Primary keys, composite on the four associative tables. "
                            "All 13 foreign keys: columns, parent, name and ON DELETE rule. The five unique keys. "
                            "Constraint names follow fk_ / uq_ / ck_."),
    ("read", ["read_"], "One live SELECT per table: the columns come back in order and every value has the right Python "
                        "type (Decimal, never float; dates as dates; the checksum as 32 bytes; BIT as one byte)."),
    ("data", ["data_"], "Every table has the row count and every cell of data.csv (the Project 1 data.xlsx). The nine "
                        "cross-row integrity checks from the requirements analysis hold. No child row points at a "
                        "missing parent."),
    ("enforce", ["enforce_"], "Inside a transaction that is always rolled back: a valid new row is accepted, then one bad "
                              "write per rule is refused with the exact MySQL error and constraint name. Duplicate keys "
                              "(1062), orphans (1452), NULLs (1048), CHECKs (3819), type limits (1406, 1264, 1265, 1292), "
                              "and the ON DELETE behaviours (CASCADE, SET NULL, refused with 1451)."),
]

FILES = [   # (file, role, href from project2/panels/)
    ("database_implementation.sql", "the file under test (Task 1)", "../deliverables/database_implementation.sql"),
    ("test_implementation.py", "the tests: the spec typed from the physical model, the value rules, all five groups",
     "../tests/test_implementation.py"),
    ("conftest.py", "shared set-up: finds the files, connects to MySQL, splits the script into statements, writes "
                    "the results snapshot", "../tests/conftest.py"),
    ("data.csv", "the Project 1 sample data, exported cell for cell from the graded data.xlsx: the expected rows",
     "../../project1/data_export/data.csv"),
    ("pytest.ini", "pytest settings (verbose, no cache folder)", "../tests/pytest.ini"),
    ("requirements.txt", "pytest, PyMySQL, cryptography (MySQL 8 sign-in)", "../tests/requirements.txt"),
    ("test_implementation_guide.pdf", "how to run the tests locally, what they cover and what they could miss",
     "../docs/test_implementation_guide.pdf"),
    ("check_implementation.py", "the no-Python-driver check: the mysql client only (runs the script twice, compares "
                                "every row, checks the integrity rules)", "../scripts/check_implementation.py"),
    ("mutate_implementation.py", "tests the tests: breaks the script 19 ways, one at a time, and checks every break "
                                 "is caught (repo only)", "../scripts/mutate_implementation.py"),
]
BUNDLE = ("crossfade_impl_tests.zip", "the tests, both input files and the guide, in one folder that runs as-is",
          "../tests/crossfade_impl_tests.zip")

SOURCES = [   # what the tests compare against, and why it is independent of the script
    ("Physical model", "physical_data_model.png (Project 1)", "Typed by hand into SPEC in test_implementation.py: "
     "tables, columns in order, types and sizes, NULL / NOT NULL, keys, the 13 relationship lines, the uq_ indexes. "
     "ENUM values and UNSIGNED flags come from the data dictionary, because the diagram abbreviates them. Never "
     "read from the .sql file."),
    ("Value rules", "requirements_analysis.pdf (Project 1)", "Each CHECK is listed with a value it must refuse and "
     "where the rule comes from. Where the analysis is silent (payout rate positive, email has an @), the rule is "
     "the one the script's own comment states, and is marked as such."),
    ("Sample data", "data.xlsx \u2192 data.csv (Project 1)", "The graded workbook, exported cell for cell and "
     "checked against itself by tools/export_p1_data.py. Rows are matched by primary key; numbers compared as exact "
     "decimals."),
]

MISSES = [   # (title, what could slip through, how much it matters / what covers it instead)
    ("A mistake in the physical model itself",
     "The schema tests prove the database matches physical_data_model.png, not that the model is the best design. "
     "If the diagram has a poor type choice, the script and the tests agree with it.",
     "The model was graded in Project 1; type choices are argued column by column in the data dictionary."),
    ("A mistake shared by the requirements analysis and the script",
     "ENUM values and UNSIGNED flags are taken from the data dictionary (built from the analysis), because the "
     "diagram abbreviates them. If the analysis is wrong there, so is the spec.",
     "check_consistency.py cross-checks the analysis, data.xlsx and the dictionary column by column."),
    ("Wrong sample data that was handed in wrong",
     "The data tests prove the database holds exactly data.xlsx. A value that was wrong in the graded workbook "
     "passes. Known case: scoring_model 2 (beardown_rrm_cfg12) is recorded as concat; its model files say gated.",
     "Listed on the History page under Known discrepancies; the brief requires the data as provided."),
    ("Running in Workbench is not the same run",
     "The tests run the script statement by statement through PyMySQL, split by our own splitter. Workbench has its "
     "own splitter and session settings (for example Safe Updates). A statement that splits differently there "
     "would not be caught.",
     "check_implementation.py runs it through the mysql client; run it once in Workbench by hand before submitting."),
    ("Different server settings",
     "Strict SQL mode is assumed (the MySQL 8 default). On a server without it, a bad value is stored with a "
     "warning instead of refused, so the type-limit tests would fail there, correctly but confusingly.",
     "Each run records the server version and sql_mode; the site page shows the last run's."),
    ("Accepted boundary values",
     "Each CHECK is tested with one value it must refuse, not with the edge values it must accept. A rule written "
     "as < 1 where the analysis says at most 1 would still refuse 1.2 and pass, while wrongly refusing exactly 1.00.",
     "The sample data contains some edge values (a blend weight of 1.00, a royalty of 0), which the load accepts."),
    ("Rules across rows are not enforced by the schema",
     "I1, I2, I3, I5 and I7 are checked on the loaded data only. Nothing in the tables stops a later insert from "
     "breaking them: by design, the analysis gives them to stored procedures.",
     "Task 4 (routines.sql) and its tests."),
    ("ON DELETE rules are the script's choice",
     "The analysis does not say what happens on delete. The tests check the three rules the script's comments state "
     "(two CASCADE, one SET NULL), so they cannot judge whether those are the right business choices.",
     "Argued in the script's table comments."),
    ("Things not looked at",
     "Collation and case (whether two stage names differing only in case count as duplicates), ON UPDATE rules, "
     "secondary indexes beyond the keys, users and privileges.",
     "Not required by the brief."),
]

FINDINGS = [
    ("Primary key names", "The script writes CONSTRAINT pk_<table> PRIMARY KEY (...) for all ten tables, but MySQL "
     "ignores a name on a primary key and always calls it PRIMARY. The tests accept PRIMARY. The header comment "
     "(\"Every constraint is named: pk_<table>, ...\") promises names the database never has; fk_, uq_ and ck_ names "
     "do survive."),
]

RUN_STEPS = [   # (title, text, code)
    ("What you need", "A running MySQL Server 8.0.16 or later (CHECK constraints) and its root password; Python 3.10 "
     "or later. The mysql command-line client and Workbench are not needed.", None),
    ("Get the files", "Download crossfade_impl_tests.zip with the button above and extract it. It holds one folder, "
     "crossfade_impl_tests, with the tests, database_implementation.sql, data.csv and this guide. (Or take the "
     "files one by one; they only need to be in the same folder.)",
     "Expand-Archive -Force $HOME\\Downloads\\crossfade_impl_tests.zip .\ncd .\\crossfade_impl_tests"),
    ("Set up Python (once)", "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
     "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"),
    ("Run the tests", "Give the tests your MySQL password, then run. These tests drop and rebuild the crossfade "
     "database from database_implementation.sql (twice), and leave it loaded; nothing else on the server is touched.",
     "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest"),
    ("Read the result", "The header names the two files it found; a counter shows each statement of the script as it "
     "runs; then one line per test and a summary. Every failure says which column, key, rule or cell differs, and "
     "what MySQL said.", "crossfade impl  ...\\database_implementation.sql\n      running database_implementation.sql: "
     "statement 22/22\ncollected {n} items\ntest_implementation.py::test_load_first_run PASSED   [  0%]\n...\n"
     "========== {n} passed in 0.8s =========="),
    ("Without Python", "From a clone of the repository, the mysql client alone: runs the script twice, compares every "
     "row with data.xlsx and checks the integrity rules; ends with PASS.",
     "python project2/scripts/check_implementation.py --mysql \"C:/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe\""),
]


# ------------------------------------------------------------------------------------------------ coverage map
def table_of(group, param):
    if param is None: return None
    if group in ("schema_columns", "schema_primary_key", "read_one_row", "data_row_count", "data_every_cell",
                 "enforce_valid_row_accepted", "enforce_duplicate_primary_key", "enforce_delete_parent_refused"):
        return [param]
    if group in ("schema_foreign_key", "data_no_orphans", "enforce_orphan_refused"): return [T.FOREIGN_KEYS[param][0]]
    if group in ("schema_unique_key", "enforce_duplicate_unique"): return [T.UNIQUE_KEYS[param][0]]
    if group in ("enforce_not_null", "enforce_null_allowed", "enforce_type_limit"): return [param.split("-")[0]]
    if group == "enforce_check": return [T.CHECKS[param][0]]
    if group == "data_integrity_rule":
        return {"I1": ["station", "station_blend"], "I2": ["genre_probability"], "I3": ["track_score", "genre_probability"],
                "I4": ["station"], "I5": ["track", "track_score"], "I7": ["play", "track", "artist"]}[param[:2]]
    return None


COLS = [  # coverage map columns: (key, label, test groups)
    ("columns", "Columns & types", ["schema_columns"]), ("pk", "Primary key", ["schema_primary_key"]),
    ("fk", "Foreign keys", ["schema_foreign_key"]), ("uq", "Unique keys", ["schema_unique_key"]),
    ("read", "Live read", ["read_one_row"]), ("rows", "Row count", ["data_row_count"]),
    ("cells", "Every cell", ["data_every_cell"]), ("rules", "Integrity rules", ["data_integrity_rule"]),
    ("orphans", "No orphans", ["data_no_orphans"]), ("valid", "Valid row accepted", ["enforce_valid_row_accepted"]),
    ("dup", "Duplicate refused", ["enforce_duplicate_primary_key", "enforce_duplicate_unique"]),
    ("orphan_ins", "Orphan refused", ["enforce_orphan_refused"]),
    ("nulls", "NULL rules", ["enforce_not_null", "enforce_null_allowed"]), ("checks", "CHECKs", ["enforce_check"]),
    ("types", "Type limits", ["enforce_type_limit"]),
    ("delete", "ON DELETE", ["enforce_delete_parent_refused", "enforce_delete_cascades_probabilities",
                             "enforce_delete_station_cascades_blend_and_keeps_plays"]),
]
DELETE_TABLES = {"enforce_delete_cascades_probabilities": ["track_score", "genre_probability"],
                 "enforce_delete_station_cascades_blend_and_keeps_plays": ["station", "station_blend", "play"]}

matrix = {t: {c[0]: [0, 0] for c in COLS} for t in T.TABLES}    # table -> col -> [tests, passed]
whole = []
for group, tests in RES["groups"].items():
    col = next((c[0] for c in COLS if group in c[2]), None)
    for t in tests:
        tabs = DELETE_TABLES.get(group) or table_of(group, t["param"])
        if not col or not tabs:
            whole.append({"test": t["test"], "outcome": t["outcome"]})
            continue
        for tb in tabs:
            matrix[tb][col][0] += 1
            matrix[tb][col][1] += t["outcome"] == "passed"

group_rows = []
for g, prefixes, text in GROUPS:
    ts = [t for k, v in RES["groups"].items() if any(k.startswith(p) for p in prefixes) for t in v]
    group_rows.append({"group": g, "tests": len(ts), "passed": sum(t["outcome"] == "passed" for t in ts), "text": text})

VET = {
    "implementation": {
        "file": "database_implementation.sql", "task": "Task 1", "status": "tested",
        "title": "Creating the database and its tables",
        "lede": "How database_implementation.sql is checked: the script is run twice, then the database it leaves "
                "behind is compared with the Project 1 physical model, the requirements analysis and the sample data, "
                "and every key and rule is made to refuse a bad write.",
        "results": "implementation_results.js", "resultsVar": "P2_IMPL",
        "pdf": "test_implementation_guide.pdf", "pdfTitle": "Testing database_implementation.sql locally",
        "mutator": "mutate_implementation.py",
        "flowTo": "<b>the crossfade database</b> that <code>database_implementation.sql</code> builds (run twice)",
        "files": [{"file": f, "role": r, "href": h} for f, r, h in FILES],
        "bundle": {"file": BUNDLE[0], "role": BUNDLE[1], "href": BUNDLE[2]},
        "sources": [{"name": a, "from": b, "how": c} for a, b, c in SOURCES],
        "groups": group_rows,
        "coverage": {"columns": [{"key": k, "label": l} for k, l, _ in COLS],
                     "rows": [{"key": t, "label": t, "sub": "assoc." if t in T.ASSOCIATIVE else ""} for t in T.TABLES],
                     "cells": matrix, "whole": whole, "caption": "tests per table and check"},
        "misses": [{"title": a, "what": b, "cover": c} for a, b, c in MISSES],
        "findings": [{"title": a, "text": b} for a, b in FINDINGS],
        "run": [{"title": a, "text": b, "code": (c or "").replace("{n}", str(RES["passed"] + RES["failed"])) or None}
                for a, b, c in RUN_STEPS],
        "mutants": MUT,
    },
}

# ================================================================================================ single_table.sql
say(2, "single_table.sql and multiple_table.sql: content, coverage maps")
S_GROUPS = [   # (group, test names, what it proves)
    ("contract", ["comment_contract", "read_only_select", "reads_exactly_one_table", "requirements_match_declared",
                  "columns_match_use_cases"],
     "Each query is preceded by a purpose comment with its tag, table, use cases, business need, business question, "
     "requirements and output columns. It is one read-only SELECT with no SELECT *. MySQL's own plan (EXPLAIN) shows "
     "it reads exactly the table its comment names. The brief requirements (a)-(e) it claims are exactly the ones it "
     "uses. It reads only columns its use cases declare."),
    ("correctness", ["result_matches_oracle", "result_is_deterministic"],
     "Each result equals an answer computed independently in plain Python from data.csv: same columns, same rows, same "
     "order, exact decimals. Its ORDER BY includes a unique key (or the GROUP BY columns), so no two rows can tie and "
     "come back in a chance order; and two runs agree."),
    ("behaviour", ["s#_..."],
     "Logic the sample data never reaches: a row is added or changed inside a transaction that is rolled back, and the "
     "query must still agree with the oracle on the changed data. Each case targets one branch, boundary or tie."),
    ("expected error", ["error_statement_is_disabled", "expected_error_is_raised"],
     "The [E1] statement at the end of the file is kept DISABLED (commented out), so a script run never stops on it. "
     "Run on its own, it must be refused by MySQL with exactly error 1062 on uq_track_audio_checksum, and track must be "
     "unchanged afterwards."),
    ("coverage", ["every_non_associative_table_is_queried", "each_requirement_is_met_at_least_twice",
                  "every_single_table_use_case_is_answered", "tags_are_unique_and_in_order"],
     "The file as a whole: all six non-associative tables are queried; each requirement (a)-(e) is met at least twice; "
     "every use case a single table can answer is answered; tags run S1, S2, ... in order, and [E#] comes after them."),
]
S_FILES = [
    ("single_table.sql", "the file under test (Task 2)", "../deliverables/single_table.sql"),
    ("test_single_table.py", "the tests: contract, correctness, behaviour cases, the expected error, file coverage",
     "../tests/test_single_table.py"),
    ("oracle.py", "the independent answers: each query recomputed in plain Python from data.csv, no SQL",
     "../tests/oracle.py"),
    ("conftest.py", "shared set-up: finds the files, connects, splits the .sql into commented statements, writes the "
                    "results snapshot", "../tests/conftest.py"),
    ("use_cases.json", "the use cases: their RA evidence, the columns each may read, the expected error",
     "../data/use_cases.json"),
    ("data.csv", "the Project 1 sample data the oracle reads", "../../project1/data_export/data.csv"),
    ("database_implementation.sql", "builds the database the queries run on (--fresh)",
     "../deliverables/database_implementation.sql"),
    ("pytest.ini", "pytest settings (verbose, no cache folder)", "../tests/pytest.ini"),
    ("requirements.txt", "pytest, PyMySQL, cryptography (MySQL 8 sign-in)", "../tests/requirements.txt"),
    ("test_single_table_guide.pdf", "how to run the tests locally, what they cover and what they could miss",
     "../docs/test_single_table_guide.pdf"),
    ("use_case_reference.pdf", "every use case: tables, columns, input, expected output, test cases",
     "../docs/use_case_reference.pdf"),
    ("mutate_single_table.py", "tests the tests: breaks single_table.sql 23 ways, one at a time, and checks every "
                               "break is caught (repo only)", "../scripts/mutate_single_table.py"),
]
S_BUNDLE = ("crossfade_single_tests.zip", "the tests, the oracle, every input file and both guides, in one folder that "
            "runs as-is", "../tests/crossfade_single_tests.zip")
S_SOURCES = [
    ("Independent answers", "oracle.py + data.csv", "Each query's answer is recomputed in plain Python from data.csv: no "
     "SQL, no database. MySQL must return the same columns, rows and order, to the exact decimal."),
    ("The use cases", "use_cases.json ← requirements_analysis.pdf", "Each query names the use cases it answers. Each "
     "use case quotes the requirements analysis word for word (build_usecases.py fails if a quote is not in it) and "
     "lists the columns it may read."),
    ("MySQL's own plan", "EXPLAIN FORMAT=JSON", "Proves each query reads exactly the one table its comment names, from "
     "MySQL's execution plan rather than a text search of the SQL."),
    ("The brief and the slides", "info579_project02.pdf, Units 6 and 8", "Requirements (a)-(e) are recognised from the "
     "course's own lists: single-row and aggregate functions (Unit 6), CASE and IF as selection control (Unit 8). "
     "IFNULL is a NULL-handling function in the slides, so it counts as neither."),
]
S_MISSES = [
    ("Independent code, not an independent reading",
     "The oracle was written from the same use cases as the queries. If a use case was misread (who counts as "
     "payable, what 'newest' means), the query and its expected answer agree and the test passes.",
     "Each use case quotes the requirements analysis word for word on the Use cases page; a second reader."),
    ("A small sample",
     "8 artists, 15 tracks, 10 genres, 8 listeners, 5 models, 8 stations. Many CASE branches, boundaries and ties are "
     "reached by no row at all; they are tested only where a behaviour case adds the row.",
     "The 13 behaviour cases, and the deliberate-mistake run below."),
    ("A fixed report date",
     "Every 'days since' figure is measured to 2026-09-30, so results never change. A live report would use "
     "CURDATE(); that version is not tested.",
     "Stated in the file header."),
    ("Requirements recognised by name, not by merit",
     "(a)-(e) are detected from the course's function lists. Whether a use is 'trivial or generic' (the brief's words) "
     "is the grader's judgement, which no test can make.",
     "Each comment says why the function is needed for the business question."),
    ("Comments checked for shape, not truth",
     "The tests check that every comment field is present and that each use case exists. Whether the business "
     "reasoning in the comment is sound is not testable.",
     "The comments cite the requirements analysis section by section."),
    ("Our own column lists",
     "'Reads only declared columns' is checked against use_cases.json, which we wrote. A wrong list there would "
     "pass a query that reads the wrong column.",
     "build_usecases.py checks every listed column exists in the physical model."),
    ("Running in Workbench is not the same run",
     "The tests run each statement on its own through PyMySQL. Workbench runs the file top to bottom and stops at the "
     "first error, which is [E1] by design; splitting can also differ.",
     "A test checks [E1] comes after every query; run the file once in Workbench by hand."),
    ("One refusal",
     "Only the duplicate-upload refusal (1062) is exercised here. Other refusals (orphans, NULLs, CHECKs) belong to "
     "the database, not to this file.",
     "test_implementation.py checks every constraint refuses a bad write."),
    ("Speed",
     "No query plan is judged for cost. The tables are tiny, so this matters little here.",
     "Not required by the brief."),
]


def s_findings():
    out = []
    s5 = [t for t in RES_S["tests"].get("S5", []) if t["test"] == "test_result_is_deterministic[S5]"]
    if s5 and s5[0]["outcome"] != "passed":
        out.append(("[S5] can tie", "ORDER BY holdout_accuracy DESC, deployed_on DESC picks one row with LIMIT 1. If "
                    "two model versions ever share both their accuracy and their deployment date, which one becomes the "
                    "default is up to MySQL. Fix: add model_id as the last sort key."))
    else:
        out.append(("[S5] could tie (fixed Nov 7)", "S5 picks one row with LIMIT 1 and sorted only by accuracy and "
                    "deployment date, so two versions tied on both would have made the default MySQL's choice. The "
                    "strengthened order check caught it; model_id is now the last sort key (the lower one wins a full "
                    "tie), the comment says so, and a behaviour case pins it. The sample data never had such a tie, so "
                    "no result changed."))
    out.append(("The tests had a blind spot (now fixed)", "The deliberate-mistake run showed that removing the tie-break "
                "from [S1] or [S2] went unnoticed: MySQL happened to return tied rows in primary-key order, which is "
                "the order the tie-break asks for, so the two tie-break behaviour cases still passed. The determinism "
                "test now checks that every ORDER BY includes a unique key, which catches both mistakes."))
    return out


S_RUN = [
    ("What you need", "A running MySQL Server 8.0.16 or later and its root password; Python 3.10 or later. The mysql "
     "command-line client and Workbench are not needed: --fresh builds the database for you.", None),
    ("Get the files", "Download crossfade_single_tests.zip with the button above and extract it. It holds one folder, "
     "crossfade_single_tests, with the tests, the oracle, single_table.sql, database_implementation.sql, data.csv, "
     "use_cases.json and both guides.",
     "Expand-Archive -Force $HOME\\Downloads\\crossfade_single_tests.zip .\ncd .\\crossfade_single_tests"),
    ("Set up Python (once)", "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
     "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"),
    ("Run the tests", "--fresh rebuilds the crossfade database from database_implementation.sql first. Without it the "
     "tests use the database as it is, after checking it holds exactly the rows in data.csv. Every write a test makes "
     "is rolled back.", "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest --fresh"),
    ("Read the result", "One line per test, then a summary. A correctness failure prints the first row where MySQL and "
     "the oracle differ; a contract failure names the comment field, table or column. Each query's result as the tests "
     "saw it is on the single_table page (Project 2 → Files).",
     "collected {n} items\ntest_single_table.py::test_comment_contract[S1] PASSED   [  1%]\n...\n"
     "========== {n} passed in 0.3s =========="),
    ("Write the queries yourself", "The starter kit (Project 2 → single_table → Download starter kit) is the same "
     "folder with every comment kept and every query removed. Run the tests at any point: unwritten queries are "
     "reported by name.", None),
]
S_COLS = [  # (key, label, test names, mark?)
    ("contract", "Comment fields", ["comment_contract"]), ("select", "Read-only SELECT", ["read_only_select"]),
    ("one", "One table (EXPLAIN)", ["reads_exactly_one_table"]),
    ("reqs", "Requirements as declared", ["requirements_match_declared"]),
    ("cols", "Columns as declared", ["columns_match_use_cases"]), ("oracle", "Matches the oracle", ["result_matches_oracle"]),
    ("order", "Order cannot tie", ["result_is_deterministic"]), ("cases", "Behaviour cases", ["s#"]),
    ("error", "Refused as expected", ["expected_error_is_raised"]),
]
REQ_COLS = [("a", "(a) single-row fn"), ("b", "(b) aggregate"), ("c", "(c) ORDER BY"), ("d", "(d) LIMIT"), ("e", "(e) CASE / IF")]


def s_entry():
    tags = sorted([k for k in RES_S["tests"] if re.fullmatch(r"[SE]\d+", k)], key=lambda k: (k[0] != "S", int(k[1:])))
    cells = {t: {c[0]: [0, 0] for c in S_COLS} for t in tags}
    for t in tags:
        for test in RES_S["tests"][t]:
            name = re.sub(r"^test_|\[.*$", "", test["test"])
            col = next((c[0] for c in S_COLS if name in c[2]), None)
            if col:
                cells[t][col][0] += 1; cells[t][col][1] += test["outcome"] == "passed"
    whole, by_name = [], {}
    for test in RES_S["tests"].get("file", []):
        m = re.match(r"test_s(\d+)_", test["test"])
        if m and "S" + m.group(1) in cells:
            c = cells["S" + m.group(1)]["cases"]; c[0] += 1; c[1] += test["outcome"] == "passed"
        else:
            whole.append({"test": test["test"], "outcome": test["outcome"]})
    for t in tags:                                                   # brief requirements met (marks, not tests)
        det = (RES_S["queries"].get(t) or {}).get("detected") or []
        for k, _ in REQ_COLS:
            cells[t]["req_" + k] = [1, 1] if k in det else [0, 0]
    groups = []
    all_tests = [x for v in RES_S["tests"].values() for x in v]
    for g, names, text in S_GROUPS:
        if g == "behaviour":
            ts = [x for x in all_tests if re.match(r"test_s\d+_", x["test"])]
        else:
            ts = [x for x in all_tests if re.sub(r"^test_|\[.*$", "", x["test"]) in names]
        groups.append({"group": g, "tests": len(ts), "passed": sum(x["outcome"] == "passed" for x in ts), "text": text})
    rows = [{"key": t, "label": t, "sub": (RES_S["queries"].get(t) or {}).get("table", "")} for t in tags]
    n = RES_S["passed"] + RES_S["failed"]
    return {
        "file": "single_table.sql", "task": "Task 2", "status": "tested", "title": "Single-table queries",
        "lede": "How single_table.sql is checked: every query is run on the crossfade database and compared with an "
                "answer computed independently in Python from data.csv; its comment, table, columns and brief "
                "requirements are checked against the use cases; logic the sample data never reaches is tested by "
                "adding rows in rolled-back transactions; and the one statement that must fail is made to fail.",
        "results": "single_table_results.js", "resultsVar": "P2_SINGLE",
        "pdf": "test_single_table_guide.pdf", "pdfTitle": "Testing single_table.sql locally", "mutator": "mutate_single_table.py",
        "flowTo": "<b>each query's result in MySQL</b>, run on the <code>crossfade</code> database",
        "files": [{"file": f, "role": r, "href": h} for f, r, h in S_FILES],
        "bundle": {"file": S_BUNDLE[0], "role": S_BUNDLE[1], "href": S_BUNDLE[2]},
        "sources": [{"name": a, "from": b, "how": c} for a, b, c in S_SOURCES],
        "groups": groups,
        "coverage": {"columns": [{"key": k, "label": l} for k, l, _ in S_COLS] +
                                [{"key": "req_" + k, "label": l, "mark": True} for k, l in REQ_COLS],
                     "rows": rows, "cells": cells, "whole": whole,
                     "caption": "tests per query and check; ✓ = brief requirement met"},
        "misses": [{"title": a, "what": b, "cover": c} for a, b, c in S_MISSES],
        "findings": [{"title": a, "text": b} for a, b in s_findings()],
        "run": [{"title": a, "text": b, "code": (c or "").replace("{n}", str(n)) or None} for a, b, c in S_RUN],
        "mutants": MUT_S,
    }


if RES_S:
    VET["single"] = s_entry()
else:
    VET["single"] = {"file": "single_table.sql", "task": "Task 2", "status": "next", "title": "Single-table queries",
                     "lede": "Run the tests (python -m pytest project2/tests) to build this page."}
# ================================================================================================ multiple_table.sql
M_GROUPS = [   # (group, test names, what it proves)
    ("contract", ["comment_contract", "read_only_select", "reads_declared_tables", "meets_its_requirement",
                  "join_types_explicit", "columns_match_use_cases"],
     "Each query is preceded by a purpose comment with its tag, title, use cases, business need, business question, "
     "the Task 3 requirement it meets, the tables it reads, what one result row is and its output columns. It is one "
     "read-only SELECT (or WITH ... SELECT) with no SELECT *. MySQL's own plan (EXPLAIN) reads exactly the tables the "
     "comment lists. The SQL really meets the requirement it claims (3.1 an associative table INNER JOINed to the two "
     "tables it relates, found from the live foreign keys; 3.2 LEFT OUTER JOIN; 3.3 a set operation; 3.4 a multi-row "
     "subquery operator; 3.5 WITH). Every join names its type. Every column MySQL reads is one its use cases "
     "declare."),
    ("correctness", ["result_matches_oracle", "result_is_deterministic"],
     "Each result equals an answer computed independently in plain Python from data.csv (oracle_multiple.py: joins are "
     "dictionary look-ups, UNION is a set, WITH is a list built first): same columns, rows, order, exact decimals. "
     "There is one row per declared grain, the ORDER BY includes every grain column so no two rows can tie, and two "
     "runs agree."),
    ("behaviour", ["m#_..."],
     "Logic the sample data never reaches: rows are added inside a transaction that is rolled back, and the query must "
     "still agree with the oracle on the changed data. Each case targets one join, boundary, NULL or tie."),
    ("coverage", ["each_requirement_is_met", "every_multiple_table_use_case_is_answered", "declared_columns_are_read",
                  "tags_are_unique_and_in_order"],
     "The file as a whole: each of the five Task 3 requirements is met by a query that claims it; every use case with "
     "multiple-table columns is answered, and no query names one without them; every column a use case declares is "
     "read by a query answering it (two queries can answer one use case: M4 and M7 both answer UC-11); tags run M1, "
     "M2, ... in order."),
]
M_FILES = [
    ("multiple_table.sql", "the file under test (Task 3)", "../deliverables/multiple_table.sql"),
    ("test_multiple_table.py", "the tests: contract, correctness, behaviour cases, file coverage",
     "../tests/test_multiple_table.py"),
    ("oracle_multiple.py", "the independent answers: each query recomputed in plain Python from data.csv, no SQL",
     "../tests/oracle_multiple.py"),
    ("oracle.py", "shared helpers the multiple-table oracle imports (MySQL-style rounding)", "../tests/oracle.py"),
    ("conftest.py", "shared set-up: finds the files, connects, splits the .sql into commented statements, writes the "
                    "results snapshot", "../tests/conftest.py"),
    ("use_cases.json", "the use cases: their RA evidence and the columns each multiple-table query may read "
                       "(multipleColumns)", "../data/use_cases.json"),
    ("data.csv", "the Project 1 sample data the oracle reads", "../../project1/data_export/data.csv"),
    ("database_implementation.sql", "builds the database the queries run on (--fresh)",
     "../deliverables/database_implementation.sql"),
    ("pytest.ini", "pytest settings (verbose, no cache folder)", "../tests/pytest.ini"),
    ("requirements.txt", "pytest, PyMySQL, cryptography (MySQL 8 sign-in)", "../tests/requirements.txt"),
    ("test_multiple_table_guide.pdf", "how to run the tests locally, what they cover and what they could miss",
     "../docs/test_multiple_table_guide.pdf"),
    ("mutate_multiple_table.py", "tests the tests: breaks multiple_table.sql {nm} ways, one at a time, and checks every "
                                 "break is caught (repo only)", "../scripts/mutate_multiple_table.py"),
]
M_BUNDLE = ("crossfade_multiple_tests.zip", "the tests, the oracle, every input file and the guide, in one folder that "
            "runs as-is", "../tests/crossfade_multiple_tests.zip")
M_SOURCES = [
    ("Independent answers", "oracle_multiple.py + data.csv", "Each query's answer is recomputed in plain Python from "
     "data.csv, no SQL and no database. MySQL must return the same columns, rows and order, to the exact decimal."),
    ("The use cases", "use_cases.json ← requirements_analysis.pdf", "Each query names the use cases it answers; each use "
     "case quotes the requirements analysis word for word and lists, under multipleColumns, the columns its query reads."),
    ("MySQL's own plan", "EXPLAIN FORMAT=JSON", "The tables each query reads and the columns it uses from each "
     "(used_columns), from MySQL's execution plan rather than a text search of the SQL."),
    ("The live schema", "information_schema", "Which tables are associative and which tables they relate (3.1), "
     "from the foreign keys database_implementation.sql created."),
    ("The brief and the slides", "info579_project02.pdf, Units 8 and 9", "Requirements 3.1-3.5 from the brief; set "
     "operations, multi-row operators and WITH from Unit 8; named join types (no bare JOIN, no comma join) from Unit 9."),
]
M_MISSES = [
    ("Independent code, not an independent reading",
     "The oracle was written from the same comments as the queries. If a business rule was misread (what 'reach' "
     "means, which plays qualify), the query and its expected answer agree and the test passes.",
     "Each comment cites the requirements analysis section by section; a second reader."),
    ("A small sample",
     "8 artists, 15 tracks, 8 listeners, 8 stations, 27 scores, 270 probabilities, 31 plays. Some joins never lose a row and some "
     "boundaries are never reached; they are tested only where a behaviour case adds the row.",
     "The {nc} behaviour cases, and the deliberate-mistake run below."),
    ("Which version counts as newest",
     "M6 reads 'a model redeployment' (RA: Scored On) as a newer version going into service. Several versions stay in "
     "service at once (RA: Scoring Model), so 'out of date' is measured against the one deployed last. "
     "If the business meant redeploying the same version (its deployed_on moving later), the same comparison applies "
     "to that version's own results, and M6 would need a second condition.",
     "The reading is stated in M6's comment; a behaviour case deploys a new version and checks every recording "
     "becomes due."),
    ("Two versions always agree on divergence",
     "Every disagreement in the sample is between exactly two model versions, whose divergences from each other are "
     "the same number, so MAX and MIN give the same answer on the sample data.",
     "A behaviour case adds a third version with a higher divergence (found by the mistake run)."),
    ("Requirements recognised by shape, not by merit",
     "3.1-3.5 are detected from the SQL (join types, UNION, IN (SELECT, WITH). Whether a query is 'trivial or "
     "generic' (the brief's words) is the grader's judgement, which no test can make.",
     "Each comment says why the join, set operation or subquery is needed for the business question."),
    ("Comments checked for shape, not truth",
     "Every comment field must be present and agree with the SQL (tables, grain, output, requirement). Whether the "
     "business reasoning is sound is not testable.",
     "The comments cite the requirements analysis."),
    ("Our own column lists",
     "'Columns as declared' is checked against multipleColumns in use_cases.json, which we wrote. A wrong list there "
     "would pass a query that reads the wrong column.",
     "build_usecases.py checks each multipleColumns entry is a column the use case needs and exists in the model."),
    ("A plan-dependent column check",
     "used_columns comes from MySQL's optimizer. A different MySQL version could list a column differently (an index "
     "it chose), and the strict both-ways check would then fail on a correct query.",
     "Only columns the statement names count, which drops the index-only extras; verified on MySQL 8.0."),
    ("Speed",
     "No plan is judged for cost (M4's correlated subqueries run once per recording). The tables are tiny.",
     "Not required by the brief."),
]
M_RUN = [
    ("What you need", "A running MySQL Server 8.0.16 or later and its root password; Python 3.10 or later. The mysql "
     "command-line client and Workbench are not needed: --fresh builds the database for you.", None),
    ("Get the files", "Download crossfade_multiple_tests.zip with the button above and extract it. It holds one folder, "
     "crossfade_multiple_tests, with the tests, the oracle, multiple_table.sql, database_implementation.sql, data.csv, "
     "use_cases.json and the guide.",
     "Expand-Archive -Force $HOME\\Downloads\\crossfade_multiple_tests.zip .\ncd .\\crossfade_multiple_tests"),
    ("Set up Python (once)", "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
     "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"),
    ("Run the tests", "--fresh rebuilds the crossfade database from database_implementation.sql first. Without it the "
     "tests use the database as it is, after checking it holds exactly the rows in data.csv. Every write a test makes "
     "is rolled back.", "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest --fresh"),
    ("Read the result", "One line per test, then a summary. A correctness failure prints the first row where MySQL and "
     "the oracle differ; a contract failure names the comment field, table, column or join. Each query's result as the "
     "tests saw it is on the multiple_table page (Project 2 → Files) and on the Use cases page.",
     "collected {n} items\ntest_multiple_table.py::test_comment_contract[M1] PASSED   [  1%]\n...\n"
     "========== {n} passed in 0.3s =========="),
    ("Write the queries yourself", "The starter kit (Project 2 → single_table → Download starter kit) holds "
     "multiple_table.sql with every comment kept and every query removed. Run the tests at any point: unwritten "
     "queries are reported by name.", None),
]
M_COLS = [  # (key, label, test names)
    ("contract", "Comment fields", ["comment_contract"]), ("select", "Read-only SELECT", ["read_only_select"]),
    ("tables", "Tables (EXPLAIN)", ["reads_declared_tables"]), ("req", "Requirement met", ["meets_its_requirement"]),
    ("joins", "Join types named", ["join_types_explicit"]), ("cols", "Columns as declared", ["columns_match_use_cases"]),
    ("oracle", "Matches the oracle", ["result_matches_oracle"]), ("order", "Order cannot tie", ["result_is_deterministic"]),
    ("cases", "Behaviour cases", ["m#"]),
]
REQ3_COLS = [("3.1", "3.1 INNER JOIN"), ("3.2", "3.2 LEFT OUTER"), ("3.3", "3.3 set op"), ("3.4", "3.4 subquery"),
             ("3.5", "3.5 WITH")]


def m_entry():
    R = RES_M
    tags = sorted([k for k in R["tests"] if re.fullmatch(r"M\d+", k)], key=lambda k: int(k[1:]))
    cells = {t: {c[0]: [0, 0] for c in M_COLS} for t in tags}
    for t in tags:
        for test in R["tests"][t]:
            name = re.sub(r"^test_|\[.*$", "", test["test"])
            col = next((c[0] for c in M_COLS if name in c[2]), None)
            if col:
                cells[t][col][0] += 1; cells[t][col][1] += test["outcome"] == "passed"
    whole = []
    for test in R["tests"].get("file", []):
        m = re.match(r"test_m(\d+)_", test["test"])
        if m and "M" + m.group(1) in cells:
            c = cells["M" + m.group(1)]["cases"]; c[0] += 1; c[1] += test["outcome"] == "passed"
        else:
            whole.append({"test": test["test"], "outcome": test["outcome"]})
    for t in tags:                                                   # Task 3 requirement met (marks, not tests)
        q = R["queries"].get(t) or {}
        for k, _ in REQ3_COLS:
            cells[t]["req_" + k] = [1, 1] if q.get("requirement") == k and q.get("detected") else [0, 0]
    groups, all_tests = [], [x for v in R["tests"].values() for x in v]
    for g, names, text in M_GROUPS:
        ts = ([x for x in all_tests if re.match(r"test_m\d+_", x["test"])] if g == "behaviour" else
              [x for x in all_tests if re.sub(r"^test_|\[.*$", "", x["test"]) in names])
        groups.append({"group": g, "tests": len(ts), "passed": sum(x["outcome"] == "passed" for x in ts), "text": text})
    rows = [{"key": t, "label": t, "sub": (R["queries"].get(t) or {}).get("title", "")} for t in tags]
    n, nc = R["passed"] + R["failed"], len(R.get("cases", []))
    nm = (MUT_M or {}).get("total", "several")
    return {
        "file": "multiple_table.sql", "task": "Task 3", "status": "tested", "title": "Multiple-table queries",
        "lede": "How multiple_table.sql is checked: every query is run on the crossfade database and compared with an "
                "answer computed independently in Python from data.csv; MySQL's own plan proves which tables and columns "
                "it reads; the SQL must really meet the Task 3 requirement its comment claims, with every join named; "
                "and joins, boundaries and NULLs the sample data never reaches are tested by adding rows in rolled-back "
                "transactions.",
        "results": "multiple_table_results.js", "resultsVar": "P2_MULTIPLE",
        "pdf": "test_multiple_table_guide.pdf", "pdfTitle": "Testing multiple_table.sql locally",
        "mutator": "mutate_multiple_table.py",
        "flowTo": "<b>each query's result in MySQL</b>, run on the <code>crossfade</code> database",
        "files": [{"file": f, "role": r.replace("{nm}", str(nm)), "href": h} for f, r, h in M_FILES],
        "bundle": {"file": M_BUNDLE[0], "role": M_BUNDLE[1], "href": M_BUNDLE[2]},
        "sources": [{"name": a, "from": b, "how": c} for a, b, c in M_SOURCES],
        "groups": groups,
        "coverage": {"columns": [{"key": k, "label": l} for k, l, _ in M_COLS] +
                                [{"key": "req_" + k, "label": l, "mark": True} for k, l in REQ3_COLS],
                     "rows": rows, "cells": cells, "whole": whole,
                     "caption": "tests per query and check; ✓ = Task 3 requirement met"},
        "misses": [{"title": a, "what": b.replace("{nc}", str(nc)), "cover": c.replace("{nc}", str(nc))} for a, b, c in M_MISSES],
        "findings": [{"title": "The tests had a blind spot (now fixed)",
                      "text": "The deliberate-mistake run showed that reporting the lowest divergence instead of the "
                              "highest in [M4] went unnoticed: every listed sample recording is scored by exactly two "
                              "versions, whose divergences from each other are equal. A behaviour case now adds a third "
                              "version with a higher divergence."}],
        "run": [{"title": a, "text": b, "code": (c or "").replace("{n}", str(n)) or None} for a, b, c in M_RUN],
        "mutants": MUT_M,
    }


VET["multiple"] = m_entry() if RES_M else {
    "file": "multiple_table.sql", "task": "Task 3", "status": "next", "title": "Multiple-table queries",
    "lede": "Run the tests (python -m pytest project2/tests) to build this page."}
# ================================================================================================ routines.sql
R_GROUPS = [   # (group, test names, what it proves)
    ("contract", ["comment_contract", "created_as_declared", "data_access_declared", "uses_what_it_lists",
                  "reads_declared_tables", "columns_are_declared"],
     "Each routine is preceded by a purpose comment with its tag and name, use cases, business need, what it does "
     "step by step, the requirement, the Unit 9 features it uses, its tables, parameters, return type, errors and an "
     "example call. MySQL's own catalogue (information_schema.ROUTINES and PARAMETERS) holds it exactly as declared: "
     "its kind, every parameter in order with mode, name and type, and a function's return type. The characteristic "
     "tells the truth (a function that reads tables is READS SQL DATA and NOT DETERMINISTIC; a procedure that writes "
     "is MODIFIES SQL DATA). Every feature listed under Uses: is in the body. It names exactly the tables listed, "
     "counting those of a routine it calls, and every column it touches is declared by one of its use cases."),
    ("behaviour", ["f#_...", "p#_..."],
     "Each routine is called on the crossfade database and compared with an independent answer computed in plain "
     "Python from data.csv (oracle_routines.py): the row a procedure writes, its OUT values, a function's result, and "
     "the refusals it must give, both its own SIGNALs and the database's errors it must not swallow. Every call runs "
     "inside a transaction that is rolled back. Two cases go further: two connections upload at the same moment, and "
     "a temporary trigger forces a primary-key clash so the handler's RESIGNAL branch runs."),
    ("coverage", ["brief_routine_mix", "tags_are_unique_and_in_order", "every_routine_use_case_is_served",
                  "declared_columns_are_touched", "no_derived_values_as_input", "no_transaction_control_inside",
                  "script_reruns_and_leaves_data_unchanged", "try_it_block_gives_the_documented_answers"],
     "The file as a whole: the brief's mix (2 procedures + 1 function, or 1 + 2); tags F1.., P1.. in order; every use "
     "case with routine columns served, and every declared column touched by a routine serving it; the RA's rule that "
     "procedures take no derived values as input; no transaction control inside a routine; and the script itself: it "
     "re-creates the routines when run again, and its Try it block leaves the data unchanged and returns what its "
     "comments promise."),
]
R_FILES = [
    ("routines.sql", "the file under test (Task 4)", "../deliverables/routines.sql"),
    ("test_routines.py", "the tests: contract, behaviour cases, file coverage", "../tests/test_routines.py"),
    ("oracle_routines.py", "the independent answers: what each routine must write, return or refuse, in plain Python "
                           "from data.csv", "../tests/oracle_routines.py"),
    ("conftest.py", "shared set-up: finds the files, connects, splits routines.sql at its DELIMITER lines, writes the "
                    "results snapshot", "../tests/conftest.py"),
    ("use_cases.json", "the use cases: their RA evidence and the columns each routine may read or write "
                       "(routineColumns)", "../data/use_cases.json"),
    ("data.csv", "the Project 1 sample data the oracle reads", "../../project1/data_export/data.csv"),
    ("database_implementation.sql", "builds the database the routines run on (--fresh)",
     "../deliverables/database_implementation.sql"),
    ("pytest.ini", "pytest settings (verbose, no cache folder)", "../tests/pytest.ini"),
    ("requirements.txt", "pytest, PyMySQL, cryptography (MySQL 8 sign-in)", "../tests/requirements.txt"),
    ("test_routines_guide.pdf", "how to run the tests locally, what they cover and what they could miss",
     "../docs/test_routines_guide.pdf"),
    ("mutate_routines.py", "tests the tests: breaks routines.sql {nm} ways, one at a time, and checks every break is "
                           "caught (repo only)", "../scripts/mutate_routines.py"),
]
R_BUNDLE = ("crossfade_routines_tests.zip", "the tests, the oracle, every input file and the guide, in one folder that "
            "runs as-is", "../tests/crossfade_routines_tests.zip")
R_SOURCES = [
    ("Independent answers", "oracle_routines.py + data.csv", "What each routine must write, return or refuse, worked "
     "out in plain Python from data.csv and the RA's rules, no SQL. MySQL must agree value for value, including the "
     "error code of every refusal."),
    ("MySQL's catalogue", "information_schema.ROUTINES, PARAMETERS", "Each routine's kind, parameters, return type and "
     "data-access characteristic, as MySQL stored them, compared with the comment."),
    ("The RA's integrity rules", "requirements_analysis.pdf", "I7 (completed and royalty computed by the procedure "
     "that records a play, once, never updated), I6 (shared stations), the play key that keeps a double-counted "
     "royalty out of the ledger, and \"the procedures do not accept derived values as input\"."),
    ("Live behaviour", "rolled-back calls, two connections, a test trigger", "Every call runs in a transaction that is "
     "rolled back; the race uses two connections; the RESIGNAL branch is forced with a temporary trigger, dropped "
     "afterwards."),
    ("The brief and the slides", "info579_project02.pdf, Unit 9", "2 procedures + 1 function or 1 + 2, in one file; "
     "DELIMITER, DECLARE, IF, SIGNAL, handlers and IN / OUT parameters from Unit 9."),
]
R_MISSES = [
    ("Independent code, not an independent reading",
     "The oracle was written from the same comments and RA rules as the routines. If a rule was misread (what "
     "'released' means, whether 30 seconds exactly qualifies), the routine and its expected answer agree.",
     "Each comment quotes the RA rule it applies; a second reader."),
    ("Columns found by name, not by plan",
     "EXPLAIN cannot see inside a routine, so the column check counts the column names that appear in its body. A "
     "name shared by two tables it uses (track_id, artist_id) counts for both.",
     "The tables are checked separately; the behaviour cases check what is actually written."),
    ("One interleaving of a race",
     "The simultaneous-upload case runs one timing: A uploads, B waits, A commits. On MySQL 8 the second upload's ID "
     "lookup waits for the first, so B takes the next ID; other timings, and other servers, are not tried.",
     "The handler's RESIGNAL branch is tested directly with a forced key clash."),
    ("A forced clash, not a natural one",
     "The primary-key clash that RESIGNAL guards against is produced by a temporary trigger, because it does not "
     "happen on its own here. The test proves the branch works, not how often it is needed.",
     "The comment says the branch is defensive."),
    ("Permissions not tested",
     "The RA grants the application EXECUTE on the procedures and no direct writes, making them the only write path. "
     "The tests run as root and do not check grants (they are not part of the brief).",
     "Not required by the brief."),
    ("One time zone",
     "\"Recorded in UTC\" is tested with the session set to UTC-7 (Arizona). Other offsets and daylight-saving "
     "changes are not tried.",
     "UTC_TIMESTAMP ignores the session time zone by definition."),
    ("Comments checked for shape, not truth",
     "Every field must be present and agree with MySQL (kind, parameters, tables, features). Whether the business "
     "reasoning is sound is not testable.",
     "The comments cite the RA."),
]
R_RUN = [
    ("What you need", "A running MySQL Server 8.0.16 or later and its root password; Python 3.10 or later. --fresh "
     "builds the database; the tests create the routines themselves by running routines.sql.", None),
    ("Get the files", "Download crossfade_routines_tests.zip with the button above and extract it. It holds one folder, "
     "crossfade_routines_tests, with the tests, the oracle, routines.sql, database_implementation.sql, data.csv, "
     "use_cases.json and the guide.",
     "Expand-Archive -Force $HOME\\Downloads\\crossfade_routines_tests.zip .\ncd .\\crossfade_routines_tests"),
    ("Set up Python (once)", "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
     "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"),
    ("Run the tests", "--fresh rebuilds the crossfade database from database_implementation.sql first. The tests then "
     "run routines.sql (it drops and re-creates the three routines) and call each one; every write is rolled back, "
     "and the race and key-clash cases delete what they add.",
     "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest --fresh"),
    ("Read the result", "One line per test, then a summary. A failure names the comment field, catalogue entry, "
     "column, value or error code that differs from the oracle.",
     "collected {n} items\ntest_routines.py::test_comment_contract[F1] PASSED   [  2%]\n...\n"
     "========== {n} passed in 1.0s =========="),
]
R_COLS = [  # (key, label, test names)
    ("contract", "Comment fields", ["comment_contract"]), ("catalogue", "Catalogue (MySQL)", ["created_as_declared"]),
    ("access", "Data access", ["data_access_declared"]), ("uses", "Uses: features", ["uses_what_it_lists"]),
    ("tables", "Tables", ["reads_declared_tables"]), ("cols", "Columns declared", ["columns_are_declared"]),
    ("cases", "Behaviour cases", ["[fp]#"]),
]
R_MARKS = [("fn", "Function", lambda q: q.get("kind") == "FUNCTION"),
           ("proc", "Procedure", lambda q: q.get("kind") == "PROCEDURE"),
           ("signal", "SIGNAL", lambda q: any("SIGNAL SQLSTATE" in u.upper() for u in q.get("uses", []))),
           ("handler", "HANDLER", lambda q: any("HANDLER" in u.upper() for u in q.get("uses", [])))]


def r_entry():
    R = RES_R
    tags = sorted([k for k in R["tests"] if re.fullmatch(r"[FP]\d+", k)], key=lambda k: (k[0], int(k[1:])))
    cells = {t: {c[0]: [0, 0] for c in R_COLS} for t in tags}
    whole = []
    for key, tests in R["tests"].items():
        for test in tests:
            name = re.sub(r"^test_|\[.*$", "", test["test"])
            if key in cells:
                col = "cases" if re.match(r"[fp]\d+_", name) else next((c[0] for c in R_COLS if name in c[2]), None)
                if col:
                    cells[key][col][0] += 1; cells[key][col][1] += test["outcome"] == "passed"
            else:
                whole.append({"test": test["test"], "outcome": test["outcome"]})
    for t in tags:
        q = R["queries"].get(t) or {}
        for k, _, f in R_MARKS:
            cells[t]["m_" + k] = [1, 1] if f(q) else [0, 0]
    groups, all_tests = [], [x for v in R["tests"].values() for x in v]
    for g, names, text in R_GROUPS:
        ts = ([x for x in all_tests if re.match(r"test_[fp]\d+_", x["test"])] if g == "behaviour" else
              [x for x in all_tests if re.sub(r"^test_|\[.*$", "", x["test"]) in names])
        groups.append({"group": g, "tests": len(ts), "passed": sum(x["outcome"] == "passed" for x in ts), "text": text})
    rows = [{"key": t, "label": t, "sub": (R["queries"].get(t) or {}).get("name", "")} for t in tags]
    n, nc = R["passed"] + R["failed"], len(R.get("cases", []))
    nm = (MUT_R or {}).get("total", "several")
    return {
        "file": "routines.sql", "task": "Task 4", "status": "tested", "title": "Routines",
        "lede": "How routines.sql is checked: MySQL's own catalogue must hold each routine exactly as its comment "
                "declares it; each routine is called on the crossfade database and must write, return and refuse "
                "exactly what an independent Python answer from data.csv says; the RA's rules (no derived values as "
                "input, a royalty computed once, plays in UTC) are tested directly; and the duplicate-upload handler is "
                "pushed to its edges: a duplicate answered, every other error passed on, a key clash re-raised.",
        "results": "routines_results.js", "resultsVar": "P2_ROUTINES",
        "pdf": "test_routines_guide.pdf", "pdfTitle": "Testing routines.sql locally",
        "mutator": "mutate_routines.py",
        "flowTo": "<b>each routine called in MySQL</b>, inside a transaction that is rolled back",
        "files": [{"file": f, "role": r.replace("{nm}", str(nm)), "href": h} for f, r, h in R_FILES],
        "bundle": {"file": R_BUNDLE[0], "role": R_BUNDLE[1], "href": R_BUNDLE[2]},
        "sources": [{"name": a, "from": b, "how": c} for a, b, c in R_SOURCES],
        "groups": groups,
        "coverage": {"columns": [{"key": k, "label": l} for k, l, _ in R_COLS] +
                                [{"key": "m_" + k, "label": l, "mark": True} for k, l, _ in R_MARKS],
                     "rows": rows, "cells": cells, "whole": whole,
                     "caption": "tests per routine and check; ✓ = what the routine is and uses"},
        "misses": [{"title": a, "what": b, "cover": c} for a, b, c in R_MISSES],
        "findings": [
            {"title": "The deliberate-mistake run had a blind spot of its own (now fixed)",
             "text": "Its first run reported one mistake missed: catching every error instead of only 1062. The edit "
                     "had landed in the file's header comment, where the same words appear, so the routine never "
                     "changed. The edit now names the handler's own code line, and that mistake is caught. The other "
                     "19 edits were checked by hand to land where they mean to: 16 in code, 3 in the comment fields "
                     "the contract tests read."},
            {"title": "Simultaneous uploads wait for each other on MySQL 8",
             "text": "The two-connection case showed that the second upload's lookup of the next track ID waits for "
                     "the first upload to commit, then takes the next ID. The primary-key clash the handler re-raises "
                     "(RESIGNAL) therefore does not occur on its own here; the branch is tested with a forced clash."}],
        "run": [{"title": a, "text": b, "code": (c or "").replace("{n}", str(n)) or None} for a, b, c in R_RUN],
        "mutants": MUT_R,
    }


VET["routines"] = r_entry() if RES_R else {
    "file": "routines.sql", "task": "Task 4", "status": "next", "title": "Routines",
    "lede": "Run the tests (python -m pytest project2/tests) to build this page."}
ORDER = ["implementation", "single", "multiple", "routines"]
VET = {k: VET[k] for k in ORDER}

# ================================================================================================ PDFs
say(3, "writing the guide PDFs")
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Table, TableStyle

rl_config.invariant = 1
INK, DIM, RULE, WASH = (colors.HexColor(c) for c in ("#0f1b26", "#4a5a68", "#cfd9e2", "#f3f7fa"))
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=19, leading=23, textColor=INK, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13, leading=16, textColor=INK, spaceBefore=11, spaceAfter=4,
                    keepWithNext=1)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, textColor=INK, spaceAfter=4)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8.5, leading=11, textColor=DIM)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")
CODE = ParagraphStyle("CODE", parent=BODY, fontName="Courier", fontSize=8.3, leading=10.5, backColor=WASH,
                      borderColor=RULE, borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=8, leftIndent=5)


def grid(header, rows, widths):
    data = [[Paragraph(escape(h), CELLB) for h in header]] + [[Paragraph(escape(str(v)), CELL) for v in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), WASH), ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def guide(v, res, task_line, path):
    n = res["passed"] + res["failed"]
    srv = (res.get("load") or {}).get("server", {})
    story = [Paragraph(escape(v["pdfTitle"]), H1),
             Paragraph(f"CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh). {task_line}. {n} tests; "
                       f"last run {escape(res['generated'].replace('T', ' '))}: {res['passed']} passed, {res['failed']} "
                       f"failed" + (f", on MySQL {escape(srv['version'])}" if srv.get("version") else "") + ".", SMALL),
             Paragraph(escape(v["lede"]), BODY),
             Paragraph("1. What the tests compare against", H2),
             grid(["Source", "From", "How it is used"], [[s["name"], s["from"], s["how"]] for s in v["sources"]],
                  [1.2 * inch, 1.6 * inch, 4.0 * inch]),
             Paragraph("2. Run them", H2)]
    for i, st in enumerate(v["run"], 1):
        block = [Paragraph(f"<b>{chr(96 + i)}. {escape(st['title'])}.</b> {escape(st['text'])}", BODY)]
        if st["code"]:
            block.append(Preformatted(st["code"], CODE))
        story.append(KeepTogether(block))
    story += [Paragraph("3. What each group proves", H2),
              grid(["Group", "Tests", "What it proves"], [[g["group"], f"{g['passed']}/{g['tests']}", g["text"]]
                                                          for g in v["groups"]], [0.9 * inch, 0.6 * inch, 5.3 * inch]),
              Paragraph("4. Files", H2),
              grid(["File", "Role"], [[f["file"], f["role"]] for f in v["files"]] + [[v["bundle"]["file"], v["bundle"]["role"]]],
                   [2.2 * inch, 4.6 * inch]),
              Paragraph("5. What the tests could miss", H2),
              Paragraph("Passing means the file agrees with its sources and refuses what they forbid. It does not mean "
                        "the following:", BODY),
              grid(["Gap", "What could slip through", "What covers it instead"],
                   [[m["title"], m["what"], m["cover"]] for m in v["misses"]], [1.4 * inch, 3.3 * inch, 2.1 * inch])]
    k = 6
    M = v.get("mutants")
    if M:
        story += [Paragraph(f"{k}. Testing the tests", H2),
                  Paragraph(f"{escape(v['mutator'])} copies the file, makes one deliberate mistake, and runs every test "
                            f"against the copy. A mistake is caught when a test fails that passes on the real file. "
                            f"{M['caught']} of {M['total']} were caught.", BODY),
                  grid(["Mistake", "Caught", "First failing tests"],
                       [[m["mistake"], f"yes ({m['failed']} failed)" if m["caught"] else "NO",
                         ", ".join(m["first_failures"][:3])] for m in M["mutants"]], [2.7 * inch, 0.9 * inch, 3.2 * inch])]
        k += 1
    if v.get("findings"):
        story += [Paragraph(f"{k}. Findings", H2)] + [Paragraph(f"<b>{escape(f['title'])}.</b> {escape(f['text'])}", BODY)
                                                    for f in v["findings"]]

    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(DIM)
        canvas.drawString(doc.leftMargin, 0.45 * inch, f"CROSSFADE  |  INFO 579 Project 2  |  {v['pdfTitle']}")
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.45 * inch, f"page {doc.page}")
        canvas.restoreState()
    SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.7 * inch, rightMargin=0.7 * inch, topMargin=0.6 * inch,
                      bottomMargin=0.7 * inch, title=v["pdfTitle"], author="info579_group_1"
                      ).build(story, onFirstPage=footer, onLaterPages=footer)


guide(VET["implementation"], RES, "INFO 579 Project 2, Task 1", P2 / "docs" / "test_implementation_guide.pdf")
if RES_S:
    guide(VET["single"], RES_S, "INFO 579 Project 2, Task 2", P2 / "docs" / "test_single_table_guide.pdf")
if RES_M:
    guide(VET["multiple"], RES_M, "INFO 579 Project 2, Task 3", P2 / "docs" / "test_multiple_table_guide.pdf")
if RES_R:
    guide(VET["routines"], RES_R, "INFO 579 Project 2, Task 4", P2 / "docs" / "test_routines_guide.pdf")


# ================================================================================================ bundles
def bundle(v, folder, members, readme):
    out = TESTS / v["bundle"]["file"]
    with zipfile.ZipFile(out, "w") as z:
        for src, name in members + [(None, "README.txt")]:
            zi = zipfile.ZipInfo(folder + "/" + name, STAMP)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, src.read_bytes() if src else readme.replace("\n", "\r\n").encode())
    with zipfile.ZipFile(out) as z:
        v["bundle"].update(bytes=out.stat().st_size, contents=[i.filename.split("/", 1)[1] for i in z.infolist()])


say(4, "writing project2/tests/crossfade_impl_tests.zip")
bundle(VET["implementation"], "crossfade_impl_tests",
       [(TESTS / "test_implementation.py", "test_implementation.py"), (TESTS / "conftest.py", "conftest.py"),
        (TESTS / "pytest.ini", "pytest.ini"), (TESTS / "requirements.txt", "requirements.txt"),
        (P2 / "deliverables" / "database_implementation.sql", "database_implementation.sql"),
        (ROOT / "project1" / "data_export" / "data.csv", "data.csv"),
        (P2 / "docs" / "test_implementation_guide.pdf", "test_implementation_guide.pdf")],
       """CROSSFADE - tests for database_implementation.sql (INFO 579 Project 2, Task 1)

  python -m venv .venv
  .venv\\Scripts\\python -m pip install -r requirements.txt
  $env:CROSSFADE_DB_PASSWORD = "your-root-password"
  .venv\\Scripts\\python -m pytest

The tests DROP and rebuild the `crossfade` database from database_implementation.sql (twice) and leave it loaded.
Full guide, coverage and what the tests could miss: test_implementation_guide.pdf.
""")
if RES_S:
    say(5, "writing project2/tests/crossfade_single_tests.zip")
    bundle(VET["single"], "crossfade_single_tests",
           [(TESTS / "test_single_table.py", "test_single_table.py"), (TESTS / "oracle.py", "oracle.py"),
            (TESTS / "conftest.py", "conftest.py"), (TESTS / "pytest.ini", "pytest.ini"),
            (TESTS / "requirements.txt", "requirements.txt"),
            (P2 / "deliverables" / "single_table.sql", "single_table.sql"),
            (P2 / "deliverables" / "database_implementation.sql", "database_implementation.sql"),
            (ROOT / "project1" / "data_export" / "data.csv", "data.csv"), (P2 / "data" / "use_cases.json", "use_cases.json"),
            (P2 / "docs" / "test_single_table_guide.pdf", "test_single_table_guide.pdf"),
            (P2 / "docs" / "use_case_reference.pdf", "use_case_reference.pdf")],
           """CROSSFADE - tests for single_table.sql (INFO 579 Project 2, Task 2)

  python -m venv .venv
  .venv\\Scripts\\python -m pip install -r requirements.txt
  $env:CROSSFADE_DB_PASSWORD = "your-root-password"
  .venv\\Scripts\\python -m pytest --fresh

--fresh rebuilds the `crossfade` database from database_implementation.sql first; every write a test makes is rolled back.
Full guide, coverage and what the tests could miss: test_single_table_guide.pdf.
""")

if RES_M:
    say(5, "writing project2/tests/crossfade_multiple_tests.zip")
    bundle(VET["multiple"], "crossfade_multiple_tests",
           [(TESTS / "test_multiple_table.py", "test_multiple_table.py"), (TESTS / "oracle_multiple.py", "oracle_multiple.py"),
            (TESTS / "oracle.py", "oracle.py"), (TESTS / "conftest.py", "conftest.py"), (TESTS / "pytest.ini", "pytest.ini"),
            (TESTS / "requirements.txt", "requirements.txt"),
            (P2 / "deliverables" / "multiple_table.sql", "multiple_table.sql"),
            (P2 / "deliverables" / "database_implementation.sql", "database_implementation.sql"),
            (ROOT / "project1" / "data_export" / "data.csv", "data.csv"), (P2 / "data" / "use_cases.json", "use_cases.json"),
            (P2 / "docs" / "test_multiple_table_guide.pdf", "test_multiple_table_guide.pdf")],
           """CROSSFADE - tests for multiple_table.sql (INFO 579 Project 2, Task 3)

  python -m venv .venv
  .venv\\Scripts\\python -m pip install -r requirements.txt
  $env:CROSSFADE_DB_PASSWORD = "your-root-password"
  .venv\\Scripts\\python -m pytest --fresh

--fresh rebuilds the `crossfade` database from database_implementation.sql first; every write a test makes is rolled back.
Full guide, coverage and what the tests could miss: test_multiple_table_guide.pdf.
""")

if RES_R:
    say(5, "writing project2/tests/crossfade_routines_tests.zip")
    bundle(VET["routines"], "crossfade_routines_tests",
           [(TESTS / "test_routines.py", "test_routines.py"), (TESTS / "oracle_routines.py", "oracle_routines.py"),
            (TESTS / "conftest.py", "conftest.py"), (TESTS / "pytest.ini", "pytest.ini"),
            (TESTS / "requirements.txt", "requirements.txt"),
            (P2 / "deliverables" / "routines.sql", "routines.sql"),
            (P2 / "deliverables" / "database_implementation.sql", "database_implementation.sql"),
            (ROOT / "project1" / "data_export" / "data.csv", "data.csv"), (P2 / "data" / "use_cases.json", "use_cases.json"),
            (P2 / "docs" / "test_routines_guide.pdf", "test_routines_guide.pdf")],
           """CROSSFADE - tests for routines.sql (INFO 579 Project 2, Task 4)

  python -m venv .venv
  .venv\\Scripts\\python -m pip install -r requirements.txt
  $env:CROSSFADE_DB_PASSWORD = "your-root-password"
  .venv\\Scripts\\python -m pytest --fresh

--fresh rebuilds the `crossfade` database from database_implementation.sql first; the tests then run routines.sql
and call each routine; every write is rolled back.
Full guide, coverage and what the tests could miss: test_routines_guide.pdf.
""")

say(6, "writing project2/data/vetting.js")
(P2 / "data" / "vetting.js").write_text(
    "/* Written by project2/scripts/build_vetting.py from the tests and their last runs. Do not edit. */\n"
    "window.P2_VET = " + json.dumps(VET, indent=1, ensure_ascii=False) + ";\n", encoding="utf-8")
for k, v in VET.items():
    if v.get("status") == "tested":
        print(f"      {k:<15} {sum(g['tests'] for g in v['groups'])} tests, {len(v['coverage']['rows'])} x "
              f"{len(v['coverage']['columns'])} coverage map, {len(v['misses'])} gaps, "
              f"{(v['mutants'] or {}).get('caught', 0)}/{(v['mutants'] or {}).get('total', 0)} mutants caught", flush=True)
