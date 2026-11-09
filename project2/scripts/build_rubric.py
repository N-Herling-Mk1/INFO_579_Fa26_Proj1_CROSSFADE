"""Write the rubric, one Markdown file per deliverable: project2/docs/rubric_<file>.md

    python project2/scripts/build_rubric.py        (build_vetting.py also runs it, before it builds the test bundles)

The same checks as the site's Rubric page (project2/panels/rubric.html), worked out from the same evidence: the results
snapshot each test file writes (project2/data/<file>_results.json). Each file gets its own task's rows plus the brief's
rules for every file. Every requirement is quoted from the brief (info579_project02.pdf); each mark is
  met      claimed by the file, and every test behind it passed
  NOT MET  missing, not tested yet, or a test failed
  grader   a judgement no test can decide
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
P2 = ROOT / "project2"
DATA, DOCS = P2 / "data", P2 / "docs"
FILES = {"implementation": ("database_implementation.sql", "Task 1", "implementation_results.json"),
         "single": ("single_table.sql", "Task 2", "single_table_results.json"),
         "multiple": ("multiple_table.sql", "Task 3", "multiple_table_results.json"),
         "routines": ("routines.sql", "Task 4", "routines_results.json")}
BRIEF = {
    "implementation": "Develop the SQL statements to create the tables of your database and insert the sample data. "
                      "You must present the statements in a single sql script named database_implementation.sql.",
    "single": "Develop a variety of SQL queries following the requirements for single table queries. "
              "You must present the queries in a single sql script named single_table.sql.",
    "multiple": "Develop a variety of SQL queries following the requirements for multiple table queries. "
                "You must present the queries in a single sql script named multiple_table.sql.",
    "routines": "Implement 2 procedures and 1 function or 1 procedure and 2 functions that make use of the data in your "
                "database. The 3 routines must be presented in a single sq file named routines.sql.",
}
SINGLE_REQ = [("a", "At least one of the queries must use single row functions."),
              ("b", "At least one of the queries must use aggregate functions."),
              ("c", "At least one of the queries must sort the results according to some criteria."),
              ("d", "At least one of the queries must return just the first N results."),
              ("e", "At least one of the queries must use a selection control function.")]
MULTI_REQ = [("3.1", "Write a query involving an associative table and two other related tables. You must use the INNER "
                     "JOIN to connect with all three tables."),
             ("3.2", "Write a query including two or more tables and using the LEFT OUTER JOIN."),
             ("3.3", "Write a query including some kind of set operation."),
             ("3.4", "Write a query including a subquery and some multi-row operation."),
             ("3.5", "Write a query including a derived table using the WITH statement.")]


def load(name):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def all_tests(r):
    return [t for k in (r or {}).get("tests", {}) for t in r["tests"][k]]


def named(r, pattern):
    return [t for t in all_tests(r) if re.match(pattern, t["test"])]


def tag_tests(r, tag):
    return (r or {}).get("tests", {}).get(tag, [])


def impl_tests(r, prefix):
    return [t for g, ts in (r or {}).get("groups", {}).items() if g.startswith(prefix) for t in ts]


def passed(ts):
    return sum(t["outcome"] == "passed" for t in ts)


def ev(ts, what):
    return f"{passed(ts)}/{len(ts)} {what}"


def green(ts):
    return bool(ts) and passed(ts) == len(ts)


def tags(r, pattern):
    qs = [t for t in (r or {}).get("queries", {}) if re.match(pattern, t)]
    return sorted(qs, key=lambda t: (t[0], int(t[1:])))


def row(no, text, by, evidence, state, why=""):
    return {"no": no, "text": text, "by": by, "evidence": evidence, "state": state, "why": why}


def not_tested(no, text, file):
    return [row(no, text, "", f"no test results for {file} yet: run python -m pytest", "bad")]


# ------------------------------------------------------------------------------------------------ rows, as on the site
def rows_implementation(R):
    if not R:
        return not_tested("1", "Develop the SQL statements to create the tables of your database and insert the sample data.",
                          "database_implementation.sql")
    schema = impl_tests(R, "schema_")
    data = impl_tests(R, "data_") + impl_tests(R, "read_")
    loads = impl_tests(R, "load_first_run") + impl_tests(R, "load_second_run")
    comm = impl_tests(R, "load_every_statement_commented")
    n_rows = sum((v or {}).get("rows", 0) for v in R.get("tables", {}).values())
    return [
        row("1a", "Develop the SQL statements to create the tables of your database", f"{len(R.get('tables', {}))} tables",
            ev(schema, "schema tests"), "ok" if green(schema) else "bad",
            "Every table, column, key, foreign key and constraint of the Project 1 physical model, checked against MySQL's catalogue."),
        row("1b", "and insert the sample data.", f"{n_rows} rows", ev(data, "data tests"), "ok" if green(data) else "bad",
            "Every row and every cell of the Project 1 sample data (data.csv), and every integrity rule it satisfies."),
        row("1c", "You must present the statements in a single sql script named database_implementation.sql.",
            "database_implementation.sql", ev(loads, "load tests (first run, second run)"), "ok" if green(loads) else "bad",
            "The one script builds the database from nothing, and runs again cleanly."),
        row("1d", "must be preceded by a comment explaining its purpose.", "every statement", ev(comm, "comment test"),
            "ok" if green(comm) else "bad", "From the brief's rule for every statement, query and routine."),
    ]


def rows_single(S):
    if not S:
        return not_tested("2.1", "Write queries to retrieve data from each non-associative table individually.", "single_table.sql")
    qs = tags(S, r"S\d+$")
    every = named(S, r"test_every_non_associative_table_is_queried")
    tables = []
    for t in qs:
        tb = S["queries"][t].get("table")
        if tb and tb not in tables:
            tables.append(tb)
    out = [row("2.1", "Write queries to retrieve data from each non-associative table individually.", " ".join(qs),
               ev(every, "coverage test") + ", " + ev(named(S, r"test_result_matches_oracle"), "results match the oracle"),
               "ok" if green(every) else "bad",
               f"One table per query; together they cover {len(tables)} non-associative tables: {', '.join(tables)}.")]
    for k, text in SINGLE_REQ:
        by = [t for t in qs if k in (S["queries"][t].get("detected") or [])]
        ts = [x for t in by for x in tag_tests(S, t)]
        out.append(row(f"2.1.{k}", text, " ".join(by), ev(ts, "tests of those queries") if by else "no query does this",
                       "ok" if by and green(ts) else "bad", "Detected in the SQL itself, not just claimed in the comment."))
    comm = named(S, r"test_comment_contract")
    out.append(row("2.2", "must be preceded by a comment explaining its purpose.", f"{len(qs)} queries", ev(comm, "comment tests"),
                   "ok" if green(comm) else "bad", "Use cases, business need, business question, requirements met and output columns."))
    return out


def rows_multiple(M):
    if not M:
        return not_tested("3.1", MULTI_REQ[0][1], "multiple_table.sql")
    qs = tags(M, r"M\d+$")
    out = []
    for k, text in MULTI_REQ:
        by = [t for t in qs if M["queries"][t].get("requirement") == k and M["queries"][t].get("detected")]
        ts = [x for t in by for x in tag_tests(M, t)]
        why = ("Found in the SQL: " + "; ".join(re.sub(r"[\[\]']", "", str(M["queries"][t]["detected"])) for t in by) + ".") if by else ""
        out.append(row(k, text, " ".join(by), ev(ts, "tests of " + ", ".join(by)) if by else "no query does this",
                       "ok" if by and green(ts) else "bad", why))
    comm, joins = named(M, r"test_comment_contract"), named(M, r"test_join_types_explicit")
    out.append(row("3.6", "must be preceded by a comment explaining its purpose.", f"{len(qs)} queries", ev(comm, "comment tests"),
                   "ok" if green(comm) else "bad",
                   "Use cases, business need, business question, requirement, tables, one row per, output columns."))
    out.append(row("3.7", "Every join names its type (course rule, Unit 9).", f"{len(qs)} queries", ev(joins, "join-type tests"),
                   "ok" if green(joins) else "bad", "Not in the brief: the course marks bare JOIN and comma joins wrong."))
    return out


def rows_routines(R):
    if not R:
        return not_tested("4.1", "Implement 2 procedures and 1 function or 1 procedure and 2 functions", "routines.sql")
    rs = tags(R, r"[FP]\d+$")
    kinds = [R["queries"][t].get("kind") for t in rs]
    n_p, n_f = kinds.count("PROCEDURE"), kinds.count("FUNCTION")
    mix, reads = named(R, r"test_brief_routine_mix"), named(R, r"test_reads_declared_tables")
    beh, file_, comm = named(R, r"test_[fp]\d+_"), named(R, r"test_script_reruns"), named(R, r"test_comment_contract")
    by = " ".join(f"{t} {R['queries'][t].get('name', '')}".strip() for t in rs)
    tabs = []
    for t in rs:
        for x in R["queries"][t].get("tables") or []:
            if x not in tabs:
                tabs.append(x)
    return [
        row("4.1", "Implement 2 procedures and 1 function or 1 procedure and 2 functions", by,
            ev(mix, "mix test") + ", " + ev(named(R, r"test_created_as_declared"), "catalogue tests"), "ok" if green(mix) else "bad",
            f"{n_p} procedure{'' if n_p == 1 else 's'} and {n_f} function{'' if n_f == 1 else 's'}, as MySQL's catalogue holds them."),
        row("4.2", "that make use of the data in your database.", " ".join(tabs),
            ev(reads, "table tests") + ", " + ev(beh, "behaviour cases"), "ok" if green(reads) and green(beh) else "bad",
            "Each routine reads or writes the CROSSFADE tables, and is run against them."),
        row("4.3", "The 3 routines must be presented in a single sq file named routines.sql.", "routines.sql",
            ev(file_, "script test"), "ok" if len(rs) == 3 and green(file_) else "bad",
            "The one script re-creates all three, and can be run again."),
        row("4.4", "must be preceded by a comment explaining its purpose.", f"{len(rs)} routines", ev(comm, "comment tests"),
            "ok" if green(comm) else "bad", "Use cases, business need, what it does, Unit 9 features, tables, parameters, errors, example."),
    ]


def rows_general(I, S, M, R, zip_name):
    comm = (impl_tests(I, "load_every_statement_commented") + named(S, r"test_comment_contract")
            + named(M, r"test_comment_contract") + named(R, r"test_comment_contract"))
    cols = named(S, r"test_columns_match_use_cases") + named(M, r"test_columns_match_use_cases") + named(R, r"test_columns_are_declared")
    star = named(S, r"test_read_only_select") + named(M, r"test_read_only_select")
    missing = [f for f, x in (("single_table.sql", S), ("multiple_table.sql", M), ("routines.sql", R)) if not x]
    zip_ok = (P2 / "deliverables" / zip_name).is_file()
    return [
        row("G1", "Every statement, query and routine should be justified within the logic of your business plan", "use cases",
            ev(comm, "comment tests") + ", " + ev(cols, "column tests"), "ok" if not missing and green(comm) and green(cols) else "bad",
            "Each names the use cases it answers (quoted from the requirements analysis) and the business need behind it; the "
            "columns it reads are the ones those use cases need." + (f" Not yet tested: {', '.join(missing)}." if missing else "")),
        row("G2", "and must be preceded by a comment explaining its purpose.", "all four files", ev(comm, "comment tests"),
            "ok" if not missing and green(comm) else "bad"),
        row("G3", "Avoid trivial and generic solutions.", "", ev(star, "no-SELECT-* tests"), "rev",
            "No test can judge this. What the tests do show: no SELECT *, every query answers a stated business question, and "
            "every result is checked against an independent answer."),
        row("G4", "Compress all the deliverables into a single zip file.", zip_name,
            "in project2/deliverables/" if zip_ok else "not built yet", "ok" if zip_ok else "bad",
            "The file name must follow the format: project02_groupcode.zip"),
        row("G5", "Upload the file to the assignment of project 1 Dropbox in D2L.", "D2L", "", "rev",
            "Quoted as written (the brief says project 1); done by hand, by the due date. Late submission will receive at most "
            "70% of the maximum grade."),
    ]


# ------------------------------------------------------------------------------------------------ Markdown
MARK = {"ok": "met", "bad": "**NOT MET**", "rev": "grader"}


def md_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def section(title, brief, rows, run_line=""):
    met = sum(r["state"] == "ok" for r in rows)
    counted = sum(r["state"] != "rev" for r in rows)
    out = [f"## {title}", "", f"Brief: \"{brief}\"", "", f"**{met}/{counted} requirements met**" + (f" ({run_line})" if run_line else ""), "",
           "| # | Requirement (quoted from the brief) | Met by | Evidence | Mark |", "|---|---|---|---|---|"]
    for r in rows:
        req = f"\"{md_cell(r['text'])}\"" + (f"<br>*{md_cell(r['why'])}*" if r["why"] else "")
        out.append(f"| {r['no']} | {req} | {md_cell(r['by']) or '-'} | {md_cell(r['evidence'])} | {MARK[r['state']]} |")
    return "\n".join(out) + "\n", met, counted


def main():
    res = {k: load(v[2]) for k, v in FILES.items()}
    zip_name = "project02_info579_group_1.zip"
    m = re.search(r'zip:\s*"([^"]+)"', (DATA / "deliverables.js").read_text(encoding="utf-8"))
    if m:
        zip_name = m.group(1)
    makers = {"implementation": rows_implementation, "single": rows_single, "multiple": rows_multiple, "routines": rows_routines}
    general_rows = rows_general(res["implementation"], res["single"], res["multiple"], res["routines"], zip_name)
    written, short = [], []
    for i, (fid, (file, task, _)) in enumerate(FILES.items(), 1):
        print(f"[{i}/{len(FILES)}] rubric for {file}", flush=True)
        R = res[fid]
        run = f"last test run {R['generated'].replace('T', ' ')}: {R['passed']} passed, {R['failed']} failed" if R else ""
        body, met, counted = section(f"{task} (25%): {file}", BRIEF[fid], makers[fid](R), run)
        gen, gmet, gcounted = section("Every file", "Every statement, query and routine should be justified within the logic "
                                      "of your business plan and must be preceded by a comment explaining its purpose. "
                                      "Avoid trivial and generic solutions.", general_rows)
        text = (f"# Rubric: {file}\n\nINFO 579 Project 2, CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh).\n\n"
                "Every condition in the assignment brief (info579_project02.pdf) that applies to this file, quoted word for word, "
                "and checked against the last test run of the file. Marks: **met** = claimed by the file and every test behind it "
                "passed; **NOT MET** = missing, not tested yet, or a test failed; **grader** = a judgement no test can decide. "
                "The same table is on the site: Project 2 > Rubric. Written by project2/scripts/build_rubric.py.\n\n"
                + body + "\n" + gen)
        out = DOCS / f"rubric_{file.replace('.sql', '')}.md"
        out.write_text(text, encoding="utf-8")
        written.append(out)
        print(f"      {met}/{counted} met; every file {gmet}/{gcounted}; wrote {out.relative_to(ROOT)}")
        if met < counted:
            short.append(file)
    return written, short


if __name__ == "__main__":
    _, short = main()
    sys.exit(1 if short else 0)
