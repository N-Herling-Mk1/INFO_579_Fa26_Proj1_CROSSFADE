"""Build the Project 2 starter kit: single_table.sql with every comment kept and every statement removed,
plus everything needed to run the tests against it.

    python project2/scripts/build_starter.py

The answer key (project2/deliverables/single_table.sql) is the only source: the starter is the answer key with
each statement after a tagged comment ([S#] or [E#]) replaced by a one-line placeholder, so the two never drift.
What the tests read from a comment stays: the tag and table word, Use cases, Requirements, Output, Expects.

Writes
    project2/starter/single_table.sql            the blank-slate file (also in the kit)
    project2/tests/crossfade_p2_starter_kit.zip  crossfade_p2_starter/: the file, tests, use_cases.json,
                                                 data.csv, database_implementation.sql, README.md, STARTER.md
"""
import pathlib, re, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
P2 = ROOT / "project2"
KEY = P2 / "deliverables" / "single_table.sql"
OUT_SQL = P2 / "starter" / "single_table.sql"
OUT_ZIP = P2 / "tests" / "crossfade_p2_starter_kit.zip"
STAMP = (2026, 11, 6, 0, 0, 0)          # fixed entry time: an unchanged kit rebuilds byte-identical

BANNER = """	STARTER KIT: blank slate. The comments are the specification; keep them.
	Write each statement under its comment and end it with ;
	The tests read these lines, so do not change them: the [S#] or [E#] tag and the
	table word after it, Use cases, Requirements, Output (your column names, in
	order) and Expects. Business need and Business question say what the business
	plan needs the query for; the bullets under the question say how to meet it.
	Run the tests at any point: unwritten queries are reported by name.
	.
"""

STARTER_MD = """# CROSSFADE Project 2: single_table.sql starter kit

Everything needed to write `single_table.sql` and test it, except the SQL itself.

| File | What it is |
|---|---|
| `single_table.sql` | **the file you write.** Every comment is kept: each says which use case the query answers, the business need behind it, the question, the requirements (a)-(e) it must meet and the output columns. Write the statement under each comment. |
| `database_implementation.sql` | builds the `crossfade` database with the Project 1 sample data (401 rows) |
| `data.csv` | the Project 1 sample data; the tests compute the expected answers from it |
| `use_cases.json` | the use cases the comments refer to (UC-01 ... UC-15) |
| `conftest.py`, `oracle.py`, `test_single_table.py`, `pytest.ini`, `requirements.txt` | the tests |
| `README.md` | how the tests work, and the table of what must match between the `.sql` and the tests |
| `run_tests_locally.pdf` | every step to run the tests on your machine, and what each failure means |
| `use_case_reference.pdf` | every use case: the tables and columns it reads, each query's input and expected output, every test case |

## Steps

1. `pip install -r requirements.txt` (a venv is a good idea: `python -m venv .venv`, then `.venv\\Scripts\\python -m pip ...`)
2. Build the database: run `database_implementation.sql` in Workbench (open, Execute), or let the tests do it with `--fresh`.
3. PowerShell: `$env:CROSSFADE_DB_PASSWORD = "your-root-password"` then `python -m pytest --fresh` once, `python -m pytest` after.
4. Write a query under its comment, rerun, repeat. With nothing written the per-query tests are skipped and the
   coverage and behaviour tests fail, each naming what is missing; the target is 66 passed.

## Rules the comments fix

- `Output:` is the contract for your column names and their order (`AS payee`, ...). The expected rows come from `oracle.py`.
- `Requirements:` must list exactly the (a)-(e) features your SQL uses: (a) single-row function, (b) aggregate,
  (c) `ORDER BY`, (d) `LIMIT n`, (e) `CASE` or `IF`. If you meet them differently, change the line to match.
- Read only the columns your use cases list in `use_cases.json`, and only the one table named after the tag.
- Every day count is measured to the fixed report date `'2026-09-30'`, not `CURDATE()`.
- `[E1]` is **EXPECTED TO FAIL**: a write MySQL must refuse with error 1062. It stays last, because an error stops a
  script run.
"""


def blank(sql, eol):
    """Replace each statement that follows a tagged comment with a placeholder line."""
    out, pos = [], 0
    blocks = list(re.finditer(r"/\*.*?\*/", sql, re.S))
    if not blocks or "FILE:" not in blocks[0].group(0):
        sys.exit("answer key has no header comment")
    for k, b in enumerate(blocks):
        out.append(sql[pos:b.end()])
        nxt = blocks[k + 1].start() if k + 1 < len(blocks) else len(sql)
        tail = sql[b.end():nxt]
        m = re.search(r"\[([SE]\d+)\]\s*([A-Z_]+)", b.group(0))
        if m and tail.strip():
            tag, table = m.group(1), m.group(2).lower()
            what = (f"one SELECT that reads crossfade.{table} only, with the Output columns in order" if tag[0] == "S"
                    else f"the statement on crossfade.{table} that MySQL must refuse (see Expects)")
            out.append(f"{eol}-- [{tag}] write {what}; end it with ;{eol}{eol}{eol}")
            print(f"      [{tag}] statement removed ({len(tail.strip().splitlines())} lines)", flush=True)
        else:
            out.append(tail)
        pos = nxt
    text = "".join(out).rstrip() + eol
    head = blocks[0].group(0)
    return text.replace(head, head.replace("/*" + eol, "/*" + eol + BANNER.replace("\n", eol), 1), 1)


def main():
    print("[1/3] reading the answer key " + str(KEY.relative_to(ROOT)), flush=True)
    raw = KEY.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    starter = blank(raw, eol)
    OUT_SQL.parent.mkdir(exist_ok=True)
    OUT_SQL.write_bytes(starter.encode("utf-8"))
    print(f"[2/3] wrote {OUT_SQL.relative_to(ROOT)}", flush=True)

    t = P2 / "tests"
    files = [(OUT_SQL, "single_table.sql"),
             (P2 / "deliverables" / "database_implementation.sql", "database_implementation.sql"),
             (ROOT / "project1" / "data_export" / "data.csv", "data.csv"),
             (P2 / "data" / "use_cases.json", "use_cases.json"),
             (P2 / "docs" / "run_tests_locally.pdf", "run_tests_locally.pdf"),      # python project2/scripts/build_docs.py
             (P2 / "docs" / "use_case_reference.pdf", "use_case_reference.pdf")]
    files += [(t / n, n) for n in ("conftest.py", "oracle.py", "test_single_table.py", "pytest.ini", "requirements.txt", "README.md")]
    with zipfile.ZipFile(OUT_ZIP, "w") as z:
        for src, name in files:
            zi = zipfile.ZipInfo("crossfade_p2_starter/" + name, STAMP)
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(zi, src.read_bytes())
        zi = zipfile.ZipInfo("crossfade_p2_starter/STARTER.md", STAMP)
        zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
        z.writestr(zi, STARTER_MD.replace("\n", eol).encode("utf-8"))
    print(f"[3/3] wrote {OUT_ZIP.relative_to(ROOT)} ({OUT_ZIP.stat().st_size:,} bytes, {len(files) + 1} files)", flush=True)


if __name__ == "__main__":
    main()
