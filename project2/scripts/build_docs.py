"""Build the two PDFs that ship in both Project 2 kits (test kit and starter kit).

    python project2/scripts/build_docs.py          (needs: pip install reportlab)

    project2/docs/run_tests_locally.pdf    every step to run the Python tests on your own machine
    project2/docs/use_case_reference.pdf   per use case: tables, columns, input, expected output, test cases

Sources, so the PDFs never drift from the code:
    project2/data/use_cases.json           the use cases, their tables and columns
    project2/data/single_table_results.json the last test run: each query's SQL facts, expected rows, cases
    project1/data_export/csv/<table>.csv   row counts of the Project 1 sample data
Run the tests first (python -m pytest project2/tests), then this script, then build_kit.py / build_starter.py.
"""
import csv, json, pathlib, re, sys
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

rl_config.invariant = 1          # no build timestamp in the PDF: an unchanged source rebuilds byte-identical
ROOT = pathlib.Path(__file__).resolve().parents[2]
P2 = ROOT / "project2"
OUT = P2 / "docs"
REPORT_DATE = "2026-09-30"
INK, DIM, RULE, WASH, ACC = (colors.HexColor(c) for c in ("#0f1b26", "#4a5a68", "#cfd9e2", "#f3f7fa", "#0a8fc4"))

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=19, leading=23, textColor=INK, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13.5, leading=17, textColor=INK, spaceBefore=12, spaceAfter=4)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=2)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, textColor=INK, alignment=TA_LEFT, spaceAfter=4)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8.5, leading=11, textColor=DIM)
LABEL = ParagraphStyle("L", parent=BODY, fontSize=7.5, leading=9, textColor=DIM, fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=1)
CELL = ParagraphStyle("C", parent=BODY, fontSize=7.5, leading=9, spaceAfter=0)
MONO = ParagraphStyle("M", parent=BODY, fontName="Courier", fontSize=8, leading=10, spaceAfter=0)
CODE = ParagraphStyle("CODE", parent=BODY, fontName="Courier", fontSize=8.5, leading=10.5, backColor=WASH,
                      borderColor=RULE, borderWidth=0.5, borderPadding=5, spaceBefore=3, spaceAfter=7, leftIndent=5)


def say(n, total, msg):
    print(f"[{n}/{total}] {msg}", flush=True)


def P(text, style=BODY):
    return Paragraph(text, style)


def esc(x):
    return escape("NULL" if x is None else str(x))


def code(text):
    return Preformatted(text, CODE)


def grid(header, rows, widths=None, font=7.5, mono_cols=()):
    """A table whose cells wrap; header shaded."""
    hs = ParagraphStyle("hc", parent=CELL, fontName="Helvetica-Bold", fontSize=font, leading=font + 1.6)
    cs = ParagraphStyle("cc", parent=CELL, fontSize=font, leading=font + 1.6)
    ms = ParagraphStyle("mc", parent=MONO, fontSize=font, leading=font + 1.6)
    data = [[Paragraph(esc(h), hs) for h in header]]
    data += [[Paragraph(esc(v), ms if i in mono_cols else cs) for i, v in enumerate(r)] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), WASH), ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def footer(title):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(DIM)
        canvas.drawString(doc.leftMargin, 0.45 * inch, f"CROSSFADE  |  INFO 579 Project 2  |  {title}")
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.45 * inch, f"page {doc.page}")
        canvas.restoreState()
    return draw


def build(path, story, title, size):
    doc = SimpleDocTemplate(str(path), pagesize=size, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.7 * inch, title=title, author="info579_group_1")
    doc.build(story, onFirstPage=footer(title), onLaterPages=footer(title))


# ============================================================================ inputs
def load():
    uc = json.loads((P2 / "data" / "use_cases.json").read_text(encoding="utf-8"))["useCases"]
    res = json.loads((P2 / "data" / "single_table_results.json").read_text(encoding="utf-8"))
    pm = P2 / "data" / "multiple_table_results.json"                    # Task 3, merged into the use case reference
    res_m = json.loads(pm.read_text(encoding="utf-8")) if pm.exists() else {"queries": {}, "cases": [], "passed": 0, "failed": 0}
    res["multiple"] = res_m
    rows = {}
    for f in sorted((ROOT / "project1" / "data_export" / "csv").glob("*.csv")):
        with open(f, encoding="utf-8-sig", newline="") as h:
            rows[f.stem] = sum(1 for _ in csv.reader(h)) - 1
    return uc, res, rows


# ============================================================================ PDF 1: run the tests locally
def guide(res, rows):
    n_tests = res["passed"] + res["failed"]
    s = [P("Running the Project 2 tests locally", H1),
         P(f"CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh). For <b>single_table.sql</b>: "
           f"{n_tests} tests, last run {esc(res['generated'].replace('T', ' '))}: {res['passed']} passed, {res['failed']} failed.", SMALL),
         P("Nothing here is taken on trust: the tests compute every expected answer in plain Python from the Project 1 "
           "sample data (<font face='Courier'>data.csv</font>), run each query on your own MySQL server, and compare the two "
           "row for row. Commands are for Windows PowerShell; the macOS / Linux form follows where it differs.")]

    s += [P("1. What you need", H2),
          grid(["Item", "Version", "Check it"],
               [["MySQL Server (a running service, not only Workbench)", "8.0.16 or later (tested 8.0.46, 8.4.9)",
                 "Get-Service *mysql*   (Status: Running)"],
                ["The MySQL root password", "", "Workbench: connecting to Local instance asks for it"],
                ["Python", "3.10 or later (tested 3.13)", "python --version"],
                ["MySQL Workbench (optional)", "8.0 or later", "only to build the database by hand (step 4)"]],
               widths=[2.6 * inch, 1.9 * inch, 2.3 * inch], font=8, mono_cols=(2,)),
          P("The <font face='Courier'>mysql</font> command-line client is <b>not</b> needed: Workbench or the tests themselves "
            "(<font face='Courier'>--fresh</font>) build the database.", SMALL)]

    s += [P("2. Get the files", H2),
          P("Site: <b>Project 2 &gt; Deliverables</b>, or <b>Project 2 &gt; single_table</b>. Download the <b>starter kit</b> "
            "(<font face='Courier'>crossfade_p2_starter_kit.zip</font>). It holds everything except the SQL you write: "),
          grid(["File", "What it is"],
               [["single_table.sql", "the file under test: blank in the starter kit (comments only). To test the answer key, "
                                     "download single_table.sql from the site and put it here, replacing the blank one."],
                ["database_implementation.sql", "builds the crossfade database with the Project 1 sample data"],
                ["data.csv", "the Project 1 sample data; the tests compute the expected answers from it"],
                ["use_cases.json", "the use cases the queries answer"],
                ["conftest.py, oracle.py, test_single_table.py", "the tests (oracle.py = the expected answers, in Python)"],
                ["pytest.ini, requirements.txt", "pytest settings; the three Python packages needed"],
                ["README.md, STARTER.md", "how the tests work; the rules the comments fix"],
                ["run_tests_locally.pdf, use_case_reference.pdf", "this guide; every use case with its input and expected output"]],
               widths=[2.6 * inch, 4.2 * inch], font=8, mono_cols=(0,)),
          P("Unzip it into a folder of your own (the zip holds one folder, <font face='Courier'>crossfade_p2_starter</font>):"),
          code("cd <your working folder>\n"
               "Expand-Archive -Force $HOME\\Downloads\\crossfade_p2_starter_kit.zip .\n"
               "cd .\\crossfade_p2_starter\n"
               "Get-ChildItem | ft Name, Length"),
          P("Windows Explorer can open a .zip without extracting it; Python cannot run files from inside one, so extract first.", SMALL)]

    s += [P("3. Set up Python (once per folder)", H2),
          code("python -m venv .venv\n"
               ".venv\\Scripts\\python -m pip install -r requirements.txt\n"
               ".venv\\Scripts\\python -c \"import pytest, pymysql, cryptography; print('ok', pytest.__version__)\""),
          P("macOS / Linux: <font face='Courier'>python3 -m venv .venv</font>, then <font face='Courier'>.venv/bin/python ...</font>. "
            "<font face='Courier'>cryptography</font> is required: MySQL 8 signs in with caching_sha2_password, which PyMySQL "
            "cannot do without it. Calling <font face='Courier'>.venv\\Scripts\\python</font> directly avoids activating the venv "
            "(no PowerShell execution-policy prompt).", SMALL)]

    counts = " + ".join(str(rows[t]) for t in ("genre", "artist", "listener", "scoring_model", "track", "station",
                                               "track_score", "genre_probability", "station_blend", "play") if t in rows)
    s += [P("4. Build the crossfade database", H2),
          P("<b>Option A, Workbench.</b> Connect to Local instance; File &gt; Open SQL Script &gt; "
            "<font face='Courier'>database_implementation.sql</font>; click the lightning-bolt <b>Run</b> (whole script). "
            f"The Output pane ends with <i>22 statements executed successfully</i>; the ten INSERTs report {counts} = "
            f"{sum(rows.values())} rows. Right-click the Schemas list &gt; Refresh All to see <font face='Courier'>crossfade</font>. Check:"),
          code("SELECT COUNT(*) FROM crossfade.genre_probability;   -- 270\n"
               "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'crossfade';   -- 10"),
          P("<b>Option B, let the tests build it:</b> add <font face='Courier'>--fresh</font> to the pytest command in step 5. "
            "It drops and rebuilds <font face='Courier'>crossfade</font> from database_implementation.sql, printing "
            "<i>--fresh: statement k/22</i> as it goes."),
          P("Rebuilding is always safe: the script drops the database first. Before testing, the tests confirm every table "
            "holds exactly the rows in data.csv and stop with a message if not.", SMALL)]

    s += [P("5. Run the tests", H2),
          code("$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n"
               ".venv\\Scripts\\python -m pytest            # add --fresh to rebuild the database first"),
          P("macOS / Linux: <font face='Courier'>export CROSSFADE_DB_PASSWORD='...'</font> then "
            "<font face='Courier'>.venv/bin/python -m pytest</font>. The header lists the four input files found and the mode; "
            "then one line per test with a running percentage, then the summary:", SMALL),
          code(f"crossfade data       ...\\data.csv\n"
               f"crossfade impl       ...\\database_implementation.sql\n"
               f"crossfade sql        ...\\single_table.sql\n"
               f"crossfade use_cases  ...\\use_cases.json\n"
               f"crossfade mode       test the existing `crossfade` database\n"
               f"collected {n_tests} items\n"
               f"test_single_table.py::test_comment_contract[S1] PASSED      [  1%]\n"
               f"...\n"
               f"=================== {n_tests} passed in 0.35s ===================")]

    s += [P("6. Read the results", H2),
          grid(["Test", "Per", "What a failure means"],
               [["test_comment_contract", "query", "the comment is missing a field the tests read (tag, Use cases, Business need, "
                                                   "Business question, Requirements, Output), or Output differs from the oracle's columns"],
                ["test_read_only_select", "query", "not a single SELECT, uses SELECT *, or reaches outside crossfade"],
                ["test_reads_exactly_one_table", "query", "MySQL's EXPLAIN shows a table other than the one after the tag"],
                ["test_requirements_match_declared", "query", "Requirements: lists (a)-(e) the SQL does not use, or misses one it does"],
                ["test_columns_match_use_cases", "query", "reads a column its use cases do not declare in use_cases.json"],
                ["test_result_matches_oracle", "query", "columns, row count, a value or the row order differ from the expected answer"],
                ["test_result_is_deterministic", "query", "the ORDER BY includes no unique key (or GROUP BY columns), so tied rows could come back in any order; or two runs differ"],
                ["test_s#_...", "case", "logic the sample data never reaches (a row added or changed, rolled back) gives the wrong rows"],
                ["test_expected_error_is_raised[E1]", "error", "the duplicate upload was not refused with error 1062, or the table changed"],
                ["coverage tests (4)", "file", "a table never queried, a requirement met fewer than twice, a use case unanswered, "
                                               "tags out of order or an [E#] before an [S#]"]],
               widths=[2.2 * inch, 0.5 * inch, 4.1 * inch], font=7.5, mono_cols=(0,)),
          P("Each run writes <font face='Courier'>results/single_table_results.json</font>: every query's rows, the expected "
            "rows, every case's inputs, and every outcome.", SMALL)]

    s += [P("7. When something goes wrong", H2),
          grid(["Message", "Cause and fix"],
               [["set CROSSFADE_DB_PASSWORD ...", "step 5's first line was not run in this PowerShell window"],
                ["cannot open the crossfade database ... (2003, Can't connect)", "MySQL is not running (Get-Service *mysql*; "
                 "Start-Service from an admin window) or listens on another port: add --db-port 3307 (or yours)"],
                ["(1045, Access denied for user 'root')", "wrong password in CROSSFADE_DB_PASSWORD"],
                ["(1049, Unknown database 'crossfade')", "build it: step 4, or rerun with --fresh"],
                ["crossfade.<table> has N rows but data.csv has M", "the database was changed or built from another file: rebuild (--fresh)"],
                ["cannot find data.csv; looked in: ...", "a file is missing from the folder; or pass --data PATH (also --impl, --sql, --use-cases)"],
                ["RuntimeError: 'cryptography' package is required", "run the pip install line of step 3 inside the venv"],
                ["[S1] has no statement in single_table.sql yet", "starter kit: that query is not written yet (expected while you work)"],
                ["'mysql' is not recognized", "harmless: the command-line client is not needed (Workbench or --fresh)"]],
               widths=[2.9 * inch, 3.9 * inch], font=7.5, mono_cols=(0,))]

    s += [P("8. Writing the queries (starter kit)", H2),
          P("The comment above each placeholder is the specification. The tests read its <b>[S#] TABLE</b> tag, <b>Use cases</b>, "
            "<b>Requirements</b>, <b>Output</b> and (for [E1]) <b>Expects</b> lines: keep them. Your column names and their order "
            "must equal <b>Output</b>; your rows must equal oracle.py's, in order, so every ORDER BY must break its ties. Every day "
            f"count is measured to the fixed report date <font face='Courier'>'{REPORT_DATE}'</font>. [E1] is EXPECTED TO FAIL and "
            "stays last: an error stops a script run. The use_case_reference.pdf in this kit shows each query's input and "
            "expected output.")]
    return s


# ============================================================================ PDF 2: use case reference
FILE_OF = {"S": "single_table.sql", "E": "single_table.sql", "M": "multiple_table.sql"}


def reference(uc, res, rows):
    rm = res.get("multiple") or {"queries": {}, "cases": []}
    Q, cases = {**res["queries"], **rm["queries"]}, res.get("cases", []) + rm.get("cases", [])
    tags_for = lambda uid: sorted((t for t, q in Q.items() if uid in (q.get("use_cases") or [])),
                                  key=lambda t: ("SEM".index(t[0]), int(t[1:])))
    W = landscape(letter)[0] - 1.4 * inch
    s = [P("Use case reference", H1),
         P(f"CROSSFADE, INFO 579 Project 2. {len(uc)} use cases from the Project 1 requirements analysis (RA). For each: the "
           "tables and columns it needs, which Project 2 file answers it, and, for each query in single_table.sql and "
           "multiple_table.sql, its input and expected output and every test case. Expected outputs are computed in Python "
           "from the Project 1 sample data (oracle.py, oracle_multiple.py) and were matched by MySQL in the last test runs: "
           f"single_table.sql {esc(res['generated'].replace('T', ' '))} ({res['passed']} passed, {res['failed']} failed)"
           + (f"; multiple_table.sql {esc(rm['generated'].replace('T', ' '))} ({rm['passed']} passed, {rm['failed']} failed)"
              if rm.get("generated") else "") + f". Day counts use the fixed report date {REPORT_DATE}.", SMALL)]

    # summary table
    summ = []
    for u in uc:
        tags = tags_for(u["id"])
        by = {}
        for t in tags:
            by.setdefault(FILE_OF[t[0]], []).append(t)
        summ.append([u["id"], u["title"], ", ".join(u["columns"]),
                     "; ".join(f"{f}: {', '.join(ts)}" for f, ts in by.items()) or "routines.sql (not written yet)"])
    s += [P("Summary", H2), grid(["UC", "Use case", "Tables it needs", "Answered by"], summ,
                                 widths=[0.55 * inch, 3.6 * inch, 2.9 * inch, W - 7.05 * inch], font=8, mono_cols=(0,))]

    for u in uc:
        s.append(PageBreak())
        s.append(P(f"{u['id']}  {esc(u['title'])}", H2))
        if u.get("question"):
            s.append(P("<b>Question:</b> " + esc(u["question"]), BODY))
        if u.get("rest"):
            s.append(P(esc(u["rest"]), SMALL))
        need = [[t, ", ".join(cols), f"{rows.get(t, '?')} rows",
                 ("alone: " + u["single"][t]) if t in (u.get("single") or {}) else "with a join"] for t, cols in u["columns"].items()]
        s += [P("DATA IT ACCESSES", LABEL),
              grid(["Table", "Columns", "Sample data", "Single table?"], need,
                   widths=[1.3 * inch, W - 3.6 * inch, 1.0 * inch, 1.3 * inch], font=8, mono_cols=(0, 1))]
        tags = tags_for(u["id"])
        if not tags:
            s.append(P("<b>Input / expected output:</b> not defined yet. This use case is answered in routines.sql; its "
                       "routine, input and expected output are added when that file and its tests are written.", BODY))
            continue
        for tag in tags:
            q = Q[tag]
            where = esc(q.get("table") and "crossfade." + q["table"] or ", ".join(q.get("tables") or []))
            block = [P(f"{tag}  |  {where}  |  {FILE_OF[tag[0]]}", H3)]
            if q.get("need"):
                block += [P("BUSINESS NEED", LABEL), P(esc(q["need"]), BODY)]
            if q.get("kind") == "expected_error":
                block += [P("INPUT: a write the database must refuse (EXPECTED TO FAIL, the last statement in the file)", LABEL),
                          code(q["sql"] + ";"),
                          P("EXPECTED OUTPUT", LABEL),
                          P(f"MySQL raises error <b>{esc(q.get('expects'))}</b>; crossfade.{esc(q['table'])} keeps its "
                            f"{rows.get(q['table'], '?')} rows. Test run: "
                            + esc(re.sub(r"Duplicate entry '.*' for key", "Duplicate entry '...' for key", q.get("got", ""))), BODY)]
                s.append(KeepTogether(block))
                continue
            if isinstance(q.get("columns"), dict):                     # multiple_table.sql: columns per table
                reads = "; ".join(f"<font face='Courier'>crossfade.{esc(t)}</font> ({rows.get(t, '?')} rows): "
                                  f"<font face='Courier'>{esc(', '.join(c))}</font>" for t, c in q["columns"].items())
                inp = (f"The Project 1 sample data, read through these tables and columns: {reads}. Task 3 requirement met: "
                       f"{esc(q.get('requirement', ''))} {esc(q.get('requirement_text', ''))}. One row per "
                       f"{esc(', '.join(q.get('grain') or []))}.")
            else:
                inp = (f"The Project 1 sample data in <font face='Courier'>crossfade.{esc(q['table'])}</font> "
                       f"({rows.get(q['table'], '?')} rows), read through these columns: "
                       f"<font face='Courier'>{esc(', '.join(q.get('columns') or []))}</font>. "
                       f"Brief requirements met: {esc(' '.join('(' + r + ')' for r in q.get('declared') or []))}.")
            block += [P("QUESTION", LABEL), P(esc(q.get("question", "")), BODY), P("INPUT", LABEL), P(inp, BODY),
                      code(q["sql"] + ";")]
            s += block
            exp = q.get("expected") or {"columns": q.get("columns_out", []), "rows": q.get("rows", [])}
            s += [P(f"EXPECTED OUTPUT: {len(exp['rows'])} row(s), in this order", LABEL),
                  grid(exp["columns"], exp["rows"], font=7.5)]
            mine = [c for c in cases if c.get("tag") == tag]
            for k, c in enumerate(mine):
                doc = (c.get("doc") or c["test"]).split("\n")
                title, why, expect, cur = doc[0], "", "", None
                for line in (l.strip() for l in doc[1:]):
                    m = re.match(r"^(Why|Expect):\s*(.*)$", line)
                    if m:
                        cur = m.group(1); why, expect = (m.group(2), expect) if cur == "Why" else (why, m.group(2))
                    elif cur == "Why" and line: why += " " + line
                    elif cur == "Expect" and line: expect += " " + line
                ins = []
                for i in c.get("inputs", []):
                    if i["kind"] == "insert":
                        ins.append(f"INSERT into {i['table']}: " + ", ".join(
                            f"{k}={'NULL' if v is None else (v[:18] + '...' if len(str(v)) > 21 else v)}" for k, v in i["row"].items()))
                    else:
                        ins.append(f"{i['sql']}  ({i['rows']} row(s) changed)")
                case = [P("TEST CASES: data the sample never reaches; each runs in a transaction that is rolled back", LABEL)] if k == 0 else []
                case.append(P(f"<b>{'PASS' if c.get('outcome') == 'passed' else 'FAIL'}</b>  {esc(title)}", BODY))
                if why:
                    case.append(P("<i>Why:</i> " + esc(why), SMALL))
                case += [P("<i>Input:</i>", SMALL)] + [P(esc(x), MONO) for x in ins]
                case.append(P("<i>Expected:</i> " + esc(expect), SMALL))
                if c.get("columns") and c.get("expected"):
                    case.append(grid(c["columns"], c["expected"], font=7))
                case.append(Spacer(1, 6))
                s.append(KeepTogether(case))
    return s


def main():
    say(1, 4, "reading use_cases.json, the last test run and the sample-data row counts")
    uc, res, rows = load()
    if res.get("failed"):
        print(f"      WARNING: the last test run had {res['failed']} failure(s); the expected outputs are still the oracle's", flush=True)
    OUT.mkdir(exist_ok=True)
    say(2, 4, "writing docs/run_tests_locally.pdf")
    build(OUT / "run_tests_locally.pdf", guide(res, rows), "Running the tests locally", letter)
    say(3, 4, "writing docs/use_case_reference.pdf")
    build(OUT / "use_case_reference.pdf", reference(uc, res, rows), "Use case reference", landscape(letter))
    for f in ("run_tests_locally.pdf", "use_case_reference.pdf"):
        print(f"      {f}: {(OUT / f).stat().st_size:,} bytes", flush=True)
    say(4, 4, "done; now rebuild the kits: build_kit.py and build_starter.py")


if __name__ == "__main__":
    main()
