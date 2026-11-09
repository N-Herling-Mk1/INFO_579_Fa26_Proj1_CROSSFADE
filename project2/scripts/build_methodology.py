"""Write the one-page unit test methodology: project2/docs/unit_test_methodology.pdf and .md

    python project2/scripts/build_methodology.py

The text is fixed here; every count in it is read from the last runs: project2/data/<file>_results.json (tests),
project2/data/<file>_mutants.json (bugs planted and caught) and the clean-run record in project2/data/deliverables.js.
The script stops if the PDF runs past one page.
"""
import json, pathlib, re, sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = pathlib.Path(__file__).resolve().parents[2]
P2 = ROOT / "project2"
DATA, DOCS = P2 / "data", P2 / "docs"
SITE = "https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/"
FILES = [("implementation", "database_implementation.sql"), ("single_table", "single_table.sql"),
         ("multiple_table", "multiple_table.sql"), ("routines", "routines.sql")]


def say(i, n, msg):
    print(f"[{i}/{n}] {msg}", flush=True)


def load(name):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def numbers():
    tests, passed, caught, planted = [], 0, 0, 0
    for stem, _ in FILES:
        r = load(f"{stem}_results.json") or {"passed": 0, "failed": 0}
        m = load(f"{stem}_mutants.json") or {}
        ms = m.get("mutants", [])
        tests.append(r["passed"] + r["failed"]); passed += r["passed"]
        caught += sum(1 for x in ms if x.get("caught")); planted += len(ms)
    src = (DATA / "deliverables.js").read_text(encoding="utf-8")
    clean = [int(x) for x in re.findall(r"passed:\s*(\d+),\s*failed:\s*0", src)]
    date = (re.search(r'verified:\s*\{\s*date:\s*"([^"]+)"', src) or [None, ""])[1]
    return {"tests": tests, "total": sum(tests), "passed": passed, "caught": caught, "planted": planted,
            "clean": sum(clean), "date": date}


def content(n):
    """[(kind, text)] with kind h (heading), p (paragraph), b (bullet), links (table rows)."""
    t = n["tests"]
    return [
        ("title", "Unit testing CROSSFADE, Project 2: method and rationale"),
        ("sub", f"INFO 579 &middot; info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh) &middot; site: <a href='{SITE}'>{SITE}</a>"),
        ("h", "Why test at all"),
        ("p", "The brief asks for SQL, not tests. We added them on our own initiative so that every claim the four files make, in "
              "their comments and in their results, is checked by a machine rather than taken on trust. The premise: a query is "
              "right only if an independent computation of the same business question agrees with it, row for row."),
        ("h", "The method"),
        ("b", "<b>An independent oracle.</b> For every query and routine, plain Python with no SQL (<i>oracle.py</i>, "
              "<i>oracle_multiple.py</i>, <i>oracle_routines.py</i>) computes the expected answer from the Project 1 sample data "
              "(<i>data.csv</i>). MySQL must match it exactly: same columns, same order, same decimals."),
        ("b", "<b>Contract.</b> Each statement's comment is parsed: tag, use cases, business need, requirements claimed, output "
              "columns. A claim the SQL does not back fails, e.g. (d) declared without a LIMIT, or LIMIT used without (d)."),
        ("b", "<b>Structure.</b> MySQL's own plan (EXPLAIN FORMAT=JSON) must read exactly the tables and columns the comment and its "
              "use cases declare; queries are read-only, never SELECT *, and name every join (INNER / LEFT OUTER JOIN)."),
        ("b", "<b>Correctness and determinism.</b> The result equals the oracle's, and the ORDER BY must include a unique key, so "
              "the row order can never depend on chance."),
        ("b", "<b>Behaviour cases.</b> Edge cases the sample data lacks (ties, a play of exactly 30 s, a window of exactly 0.50, "
              "NULLs, a rejected upload, two uploads at once) are inserted inside a transaction; the query or routine is rerun "
              "and compared with the oracle; then everything is rolled back."),
        ("b", "<b>Coverage.</b> Each file as a whole: every non-associative table queried, every brief requirement met, every use "
              "case answered. database_implementation.sql is compared with the physical model through information_schema, every "
              "cell with data.csv, and every key and CHECK must refuse a bad write. Routines are compared with MySQL's catalogue, "
              "called, and pushed to their edges (each SIGNAL, the 1062 handler, a re-raised key clash)."),
        ("b", f"<b>Testing the tests.</b> A suite that never fails proves nothing, so <i>mutate_&lt;file&gt;.py</i> plants one "
              f"deliberate bug at a time (a dropped tie-break, &gt;= for &gt;, LENGTH for CHAR_LENGTH, a missing filter, an "
              f"undeclared column) and reruns the tests. A bug counts as caught when a passing test fails: "
              f"<b>{n['caught']}/{n['planted']} caught</b>."),
        ("h", "Use cases, and how they are run"),
        ("p", "The 15 use cases (UC-01 to UC-15) come from the Project 1 requirements analysis (RA). Each is defined in "
              "<i>project2/data/use_cases.json</i> with the RA phrases that justify it (quoted word for word; the build fails if a "
              "phrase is not in the RA), the columns it needs, and the file that answers it. To run one: the query's comment names "
              "the use case; pytest runs the query on the <i>crossfade</i> database; the oracle computes that use case's answer from "
              "data.csv; the rows are compared; the use case's behaviour cases run in rolled-back transactions; and the results "
              "snapshot (<i>project2/data/&lt;file&gt;_results.json</i>) feeds the site. A query may read only the columns its use "
              "cases declare."),
        ("h", "Run it, and the result"),
        ("p", "From the Deliverables page, a file's <b>file + tests</b> button downloads one folder with the file, its tests, their "
              "inputs, its rubric and the use case descriptions. Unzip it, then: <font face='Courier'>python -m venv .venv</font>; "
              "<font face='Courier'>.venv\\Scripts\\python -m pip install -r requirements.txt</font>; set "
              "<font face='Courier'>CROSSFADE_DB_PASSWORD</font>; <font face='Courier'>.venv\\Scripts\\python -m pytest --fresh</font> "
              "(database_implementation: no <font face='Courier'>--fresh</font>; it rebuilds the database itself). "
              f"<b>{n['total']} tests</b> ({t[0]} / {t[1]} / {t[2]} / {t[3]}): <b>{n['passed']} passed</b> in the repo, and "
              f"<b>{n['clean']} passed</b> in clean runs of the zips downloaded from the live site ({n['date']}, Windows, a new "
              "folder and fresh venv per zip)."),
        ("h", "Where to look (append to the site address)"),
        ("links", [("#p2/usecases", "use case definitions, their evidence from the RA, and the coverage map"),
                   ("#p2/vet-implementation, #p2/vet-single, #p2/vet-multiple, #p2/vet-routines",
                    "per file: the tests, coverage map, bugs planted and caught, and what the tests could miss"),
                   ("#p2/map-implementation, #p2/map-single, #p2/map-multiple, #p2/map-routines",
                    "each brief requirement mapped to the SQL that meets it"),
                   ("#p2/rubric", "every condition of the brief with its evidence"),
                   ("#p2/overview", "downloads and the record of tests run and passed"),
                   ("repo", "project2/tests/ (tests, oracles), project2/docs/use_case_reference.pdf (every use case's input, "
                            "expected output and test cases)")]),
    ]


def write_pdf(items, out):
    base = ParagraphStyle("b", fontName="Helvetica", fontSize=8.6, leading=10.9, alignment=TA_LEFT, spaceAfter=2.5)
    st = {"title": ParagraphStyle("t", parent=base, fontName="Helvetica-Bold", fontSize=13.5, leading=16, spaceAfter=1),
          "sub": ParagraphStyle("s", parent=base, fontSize=8, textColor=colors.HexColor("#4a5a68"), spaceAfter=5),
          "h": ParagraphStyle("h", parent=base, fontName="Helvetica-Bold", fontSize=9.8, leading=12, spaceBefore=4, spaceAfter=1.5,
                              textColor=colors.HexColor("#0a6f99")),
          "p": base, "b": ParagraphStyle("bl", parent=base, leftIndent=10, bulletIndent=0, spaceAfter=1.8)}
    flow = []
    for kind, text in items:
        if kind == "links":
            rows = [[Paragraph(f"<font face='Courier'>{a}</font>", ParagraphStyle("c", parent=base, fontSize=7.8, leading=9.6)),
                     Paragraph(b, ParagraphStyle("d", parent=base, fontSize=8.2, leading=10))] for a, b in text]
            tb = Table(rows, colWidths=[2.95 * inch, 4.35 * inch])
            tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 1),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                                    ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#cfd9e2"))]))
            flow.append(tb)
        elif kind == "b":
            flow.append(Paragraph(text, st["b"], bulletText="•"))
        else:
            flow.append(Paragraph(text, st[kind]))
    pages = []
    doc = SimpleDocTemplate(str(out), pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch, topMargin=0.5 * inch,
                            bottomMargin=0.45 * inch, title="Unit testing CROSSFADE, Project 2",
                            author="info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh)")
    doc.build(flow, onFirstPage=lambda c, d: pages.append(1), onLaterPages=lambda c, d: pages.append(1))
    return len(pages)


def write_md(items, out):
    def plain(s):
        s = re.sub(r"<a href='([^']+)'>[^<]*</a>", r"\1", s)
        s = re.sub(r"</?b>", "**", s); s = re.sub(r"</?i>", "*", s)
        s = re.sub(r"<font face='Courier'>(.*?)</font>", r"`\1`", s)
        return s.replace("&middot;", "·").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("\\\\", "\\")
    lines = []
    for kind, text in items:
        if kind == "title":
            lines += [f"# {plain(text)}", ""]
        elif kind == "sub":
            lines += [plain(text), ""]
        elif kind == "h":
            lines += [f"## {plain(text)}", ""]
        elif kind == "b":
            lines += [f"- {plain(text)}"]
        elif kind == "links":
            lines += ["| Path | What is there |", "|---|---|"] + [f"| `{a}` | {plain(b)} |" for a, b in text] + [""]
        else:
            lines += ["", plain(text), ""]
    out.write_text("\n".join(lines).replace("\n\n\n", "\n\n") + "\n", encoding="utf-8")


def main():
    say(1, 3, "reading the last test, mutation and clean runs")
    n = numbers()
    print(f"      {n['total']} tests {n['tests']}, {n['passed']} passed in the repo, {n['clean']} in clean runs; "
          f"{n['caught']}/{n['planted']} bugs caught")
    items = content(n)
    pdf, md = DOCS / "unit_test_methodology.pdf", DOCS / "unit_test_methodology.md"
    say(2, 3, f"writing {pdf.relative_to(ROOT)}")
    pages = write_pdf(items, pdf)
    print(f"      {pages} page(s), {pdf.stat().st_size:,} bytes")
    say(3, 3, f"writing {md.relative_to(ROOT)}")
    write_md(items, md)
    if pages > 1:
        sys.exit("      over one page: shorten the text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
