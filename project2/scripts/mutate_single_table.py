"""Test the tests: break single_table.sql on purpose, one way at a time, and check that test_single_table.py
notices every break.

    python project2/scripts/mutate_single_table.py          (needs MySQL; CROSSFADE_DB_PASSWORD set)

Each mutant is a copy of single_table.sql with one deliberate mistake, written to a temporary folder and run
through the full test file with --sql. A mutant is "caught" when at least one test fails that passes on the real file. The file under test is
never changed. The database is rebuilt from database_implementation.sql once, first (--fresh), and every test
that writes does so inside a transaction it rolls back.

Writes project2/data/single_table_mutants.json (read by build_vetting.py for the site and the PDF).
"""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SQL = ROOT / "project2" / "deliverables" / "single_table.sql"
TEST = ROOT / "project2" / "tests" / "test_single_table.py"
OUT = ROOT / "project2" / "data" / "single_table_mutants.json"
src = SQL.read_text(encoding="utf-8").replace("\r\n", "\n")

# (name, query, what the mistake is, old text, new text)
EDITS = [
    ("s1-country-check-masked", "S1", "the country check only runs for verified artists (an artist failing both shows one hold)",
     "IF(country IS NULL, 'HOLD: no country', country)", "IF(country IS NULL AND verified = 1, 'HOLD: no country', country)"),
    ("s1-ready-ignores-country", "S1", "run_status says ready for a verified artist with no country",
     "WHEN verified = 1 AND country IS NOT NULL THEN 'ready'", "WHEN verified = 1 THEN 'ready'"),
    ("s1-tie-break-dropped", "S1", "the artist_id tie-break left out of ORDER BY", "         payout_rate DESC,\n         artist_id;", "         payout_rate DESC;"),
    ("s1-ready-first-dropped", "S1", "ready artists no longer listed first",
     "ORDER BY run_status DESC,\n         payout_rate DESC,", "ORDER BY payout_rate DESC,"),
    ("s1-report-date-moved", "S1", "a different report date (2026-10-01) in days under licence",
     "DATEDIFF('2026-09-30', joined_date)", "DATEDIFF('2026-10-01', joined_date)"),
    ("s2-scored-filter-dropped", "S2", "unscored and rejected recordings allowed on the shelf", "WHERE ingest_status = 'scored'\n", ""),
    ("s2-limit-six", "S2", "six recordings on the shelf instead of five", "LIMIT 5;", "LIMIT 6;"),
    ("s2-seconds-unpadded", "S2", "run time without the zero pad (3:7 instead of 3:07)",
     "LPAD(MOD(duration, 60), 2, '0')", "MOD(duration, 60)"),
    ("s2-tie-break-dropped", "S2", "the track_id tie-break left out of ORDER BY", "ORDER BY release_date DESC,\n         track_id\nLIMIT 5;",
     "ORDER BY release_date DESC\nLIMIT 5;"),
    ("s3-width-hard-coded", "S3", "the label column width hard-coded to 9 instead of found from the data",
     "(SELECT MAX(CHAR_LENGTH(name)) FROM crossfade.genre)", "9"),
    ("s3-bytes-not-characters", "S3", "description length counted in bytes (LENGTH) instead of characters",
     "CHAR_LENGTH(description) AS description_chars", "LENGTH(description) AS description_chars"),
    ("s3-line-budget-wrong", "S3", "room left measured against 79 characters instead of the RA's 80",
     "80 - CHAR_LENGTH(description)", "79 - CHAR_LENGTH(description)"),
    ("s3-select-star", "S3", "SELECT * instead of the named columns",
     "SELECT genre_id AS model_class_index,\n       name AS label,", "SELECT *, genre_id AS model_class_index,\n       name AS label,"),
    ("s4-tiers-ascending", "S4", "plan tiers listed cheapest first", "ORDER BY plan_tier DESC;", "ORDER BY plan_tier;"),
    ("s4-average-unrounded", "S4", "average tenure not rounded", "ROUND(AVG(DATEDIFF('2026-09-30', signup_date)))", "AVG(DATEDIFF('2026-09-30', signup_date))"),
    ("s4-column-renamed", "S4", "an output column renamed (listener_count)", "COUNT(*) AS listeners,", "COUNT(*) AS listener_count,"),
    ("s5-tie-goes-to-older", "S5", "an accuracy tie goes to the older deployment", "         deployed_on DESC,\n         model_id", "         deployed_on,\n         model_id"),
    ("s5-last-tie-break-dropped", "S5", "the model_id tie-break left out (a full tie on accuracy and date picks either row)",
     "         deployed_on DESC,\n         model_id\nLIMIT 1;", "         deployed_on DESC\nLIMIT 1;"),
    ("s5-second-table", "S5", "a second table read (a subquery on station)", "FROM crossfade.scoring_model\nORDER BY",
     "FROM crossfade.scoring_model\nWHERE model_id IN (SELECT model_id FROM crossfade.station)\nORDER BY"),
    ("s5-use-cases-line-removed", "S5", "the Use cases line removed from the comment", "\tUse cases: UC-08\n", "\n"),
    ("s6-half-counts-as-wide", "S6", "a window of exactly 0.50 counted as wide (>= instead of >)",
     "maximum_ambiguity - minimum_ambiguity > 0.5", "maximum_ambiguity - minimum_ambiguity >= 0.5"),
    ("s6-undeclared-column", "S6", "a column the use cases do not declare is read (listener_id)",
     "FROM crossfade.station\nGROUP BY model_id", "FROM crossfade.station\nWHERE listener_id IS NOT NULL\nGROUP BY model_id"),
    ("s7-due-today-on-time", "S7", "a release due on the report date counted as on time (< instead of <=)",
     "WHEN MIN(release_date) <= '2026-09-30'", "WHEN MIN(release_date) < '2026-09-30'"),
    ("s2-limit-undeclared", "S2", "LIMIT used but (d) not declared in Requirements",
     "Requirements: 2.1, (a), (c), (d)  (brief", "Requirements: 2.1, (a), (c)  (brief"),
    ("e1-not-refused", "E1", "the re-upload computes a different checksum, so MySQL accepts it",
     "SELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', audio_checksum, 'awaiting scoring'",
     "SELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', UNHEX(SHA2('other file', 256)), 'awaiting scoring'"),
]


def e1_enabled(s):
    """Take the [E1] statement out of its block comment: a script run would then end on error 1062."""
    i = s.index("/*\n\t[E1]")
    head, tail = s[:i], s[i:]
    j = tail.index("*/\n/*\n") + len("*/\n")          # end of the [E1] comment, start of the statement's block
    stmt = tail[j:]
    stmt = stmt.replace("/*\n", "", 1)
    k = stmt.rindex("*/")
    return head + tail[:j] + stmt[:k] + stmt[k + 2:]


FUNCS = [("e1-enabled", "E1", "the disabled expected-to-fail statement switched back on (the file no longer runs clean)", e1_enabled)]


def run(path, fresh=False):
    r = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q", "-p", "no:cacheprovider", "--sql", str(path),
                        "--results", str(pathlib.Path(tempfile.gettempdir()) / "crossfade_mutants")] + (["--fresh"] if fresh else []),
                       capture_output=True, text=True, cwd=ROOT)
    failed = re.findall(r"FAILED \S+::(\S+)", r.stdout)
    errors = re.findall(r"ERROR \S+::(\S+)", r.stdout)
    m = re.search(r"(\d+) failed", r.stdout)
    e = re.search(r"(\d+) error", r.stdout)
    n = (int(m.group(1)) if m else 0) + (int(e.group(1)) if e else 0)
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
    return n, failed + errors, tail


def main():
    if os.environ.get("CROSSFADE_DB_PASSWORD") is None:
        sys.exit("set CROSSFADE_DB_PASSWORD first")
    print("[setup] rebuilding crossfade and running the real file", flush=True)
    n, base_failed, tail = run(SQL, fresh=True)
    base = set(base_failed)
    print(f"        {tail}" + (f"  (already failing: {sorted(base)})" if base else ""), flush=True)
    mutants = [(n_, q, d, src.replace(a, b, 1)) for n_, q, d, a, b in EDITS if a in src]
    missing = [n_ for n_, q, d, a, b in EDITS if a not in src]
    mutants += [(n_, q, d, f(src)) for n_, q, d, f in FUNCS]
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, (name, q, what, text) in enumerate(mutants, 1):
            p = pathlib.Path(tmp) / "single_table.sql"
            p.write_text(text, encoding="utf-8")
            n, failed, tail = run(p)
            new = [t for t in failed if t not in base]       # caught = a test fails that passes on the real file
            results.append({"mutant": name, "query": q, "mistake": what, "caught": bool(new), "failed": len(new),
                            "first_failures": new[:4]})
            print(f"[{k}/{len(mutants)}] {name:<28} {'caught' if new else 'MISSED'}  ({len(new)} new failures)", flush=True)
    OUT.write_text(json.dumps({"mutants": results, "caught": sum(r["caught"] for r in results), "total": len(results),
                               "not_applicable": missing, "real_file": tail, "already_failing": sorted(base)}, indent=1),
                   encoding="utf-8")
    print(f"{sum(r['caught'] for r in results)}/{len(results)} mutants caught -> {OUT.relative_to(ROOT)}"
          + (f"; edits that no longer apply: {missing}" if missing else ""))
    sys.exit(0 if all(r["caught"] for r in results) else 1)


if __name__ == "__main__":
    main()
