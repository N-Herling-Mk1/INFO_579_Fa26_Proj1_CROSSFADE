"""Test the tests: break multiple_table.sql on purpose, one way at a time, and check that test_multiple_table.py
notices every break.

    python project2/scripts/mutate_multiple_table.py          (needs MySQL; CROSSFADE_DB_PASSWORD set)

Each mutant is a copy of multiple_table.sql with one deliberate mistake, written to a temporary folder and run
through the full test file with --msql. A mutant is "caught" when at least one test fails that passes on the real file. The file under test is
never changed. The database is rebuilt from database_implementation.sql once, first (--fresh), and every test
that writes does so inside a transaction it rolls back.

Writes project2/data/multiple_table_mutants.json (read by build_vetting.py for the site and the PDF).
"""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SQL = ROOT / "project2" / "deliverables" / "multiple_table.sql"
TEST = ROOT / "project2" / "tests" / "test_multiple_table.py"
OUT = ROOT / "project2" / "data" / "multiple_table_mutants.json"
src = SQL.read_text(encoding="utf-8").replace("\r\n", "\n")

# (name, query, what the mistake is, old text, new text)
EDITS = [
    # M1 listener taste (3.1)
    ("m1-listener-left-join", "M1", "listener joined with LEFT OUTER JOIN (3.1 asks for INNER JOIN on all three tables)",
     "INNER JOIN crossfade.listener AS l ON l.listener_id = p.listener_id",
     "LEFT OUTER JOIN crossfade.listener AS l ON l.listener_id = p.listener_id"),
    ("m1-average-of-ratios", "M1", "share heard as the average of per-play ratios, not total heard / total length",
     "ROUND(100 * SUM(p.seconds_played) / SUM(t.duration), 1)", "ROUND(100 * AVG(p.seconds_played / t.duration), 1)"),
    ("m1-least-engaged-first", "M1", "least engaged listeners first", "ORDER BY pct_of_audio_heard DESC,", "ORDER BY pct_of_audio_heard,"),
    ("m1-tie-break-dropped", "M1", "the listener_id tie-break left out of ORDER BY",
     "ORDER BY pct_of_audio_heard DESC,\n         l.listener_id;", "ORDER BY pct_of_audio_heard DESC;"),
    ("m1-tables-line-wrong", "M1", "track left off the comment's Tables line", "Tables: play, listener, track", "Tables: play, listener"),
    # M2 royalty run (3.2)
    ("m2-play-inner-join", "M2", "play joined with INNER JOIN: artists with no plays drop out of the royalty run",
     "LEFT OUTER JOIN crossfade.play AS p", "INNER JOIN crossfade.play AS p"),
    ("m2-ifnull-dropped", "M2", "IFNULL removed: an artist with no plays is owed NULL instead of 0",
     "IFNULL(SUM(p.royalty_amount), 0) AS usd_owed", "SUM(p.royalty_amount) AS usd_owed"),
    ("m2-count-star", "M2", "COUNT(*) instead of COUNT(p.track_id): an artist with no plays shows 1 play",
     "COUNT(p.track_id) AS plays", "COUNT(*) AS plays"),
    ("m2-thirty-seconds-excluded", "M2", "a play of exactly 30 seconds does not qualify (> instead of >=)",
     "p.seconds_played >= 30", "p.seconds_played > 30"),
    ("m2-left-join-without-outer", "M2", "LEFT JOIN written without OUTER (the course asks for the full join type)",
     "LEFT OUTER JOIN crossfade.track AS t", "LEFT JOIN crossfade.track AS t"),
    ("m2-undeclared-column", "M2", "a column the use cases do not declare is read (artist.country)",
     "GROUP BY a.artist_id, a.stage_name", "WHERE a.country IS NULL OR a.country IS NOT NULL\nGROUP BY a.artist_id, a.stage_name"),
    # M3 station reach (3.3)
    ("m3-union-all", "M3", "UNION ALL: a listener who plays a station twice is counted twice",
     "      FROM crossfade.station\n      UNION\n", "      FROM crossfade.station\n      UNION ALL\n"),
    ("m3-creator-only-is-shared", "M3", "a station reaching only its creator labelled shared (>= 1 instead of > 1)",
     "WHEN COUNT(*) > 1 THEN 'shared'", "WHEN COUNT(*) >= 1 THEN 'shared'"),
    ("m3-bare-join", "M3", "a bare JOIN with no join type", "INNER JOIN crossfade.listener AS l ON l.listener_id = s.listener_id",
     "JOIN crossfade.listener AS l ON l.listener_id = s.listener_id"),
    ("m3-tie-break-dropped", "M3", "the station_id tie-break left out of ORDER BY",
     "ORDER BY listeners_reached DESC,\n         s.station_id;", "ORDER BY listeners_reached DESC;"),
    ("m3-grain-wrong", "M3", "the comment says one row per creator (a creator can have two stations)",
     "One row per: station_id", "One row per: created_by"),
    # M4 model disagreement (3.4)
    ("m4-scores-not-genres", "M4", "two scores of any genre counted as a disagreement (COUNT(*) instead of COUNT(DISTINCT genre_id))",
     "HAVING COUNT(DISTINCT s.genre_id) > 1", "HAVING COUNT(*) > 1"),
    ("m4-not-in", "M4", "NOT IN: the recordings the models agree on", "WHERE t.track_id IN (SELECT", "WHERE t.track_id NOT IN (SELECT"),
    ("m4-lowest-divergence", "M4", "the lowest divergence instead of the highest", "MAX(sd.model_divergence)", "MIN(sd.model_divergence)"),
    ("m4-tie-break-dropped", "M4", "the track_id tie-break left out of ORDER BY",
     "ORDER BY highest_divergence DESC,\n         t.track_id;", "ORDER BY highest_divergence DESC;"),
    ("m4-claims-union", "M4", "the comment claims requirement 3.3 (a set operation) instead of 3.4",
     "Requirements: 3.4 subquery", "Requirements: 3.3 subquery"),
    # M5 filling each station (3.5)
    ("m5-window-edges-excluded", "M5", "the window's edges left out (> and < instead of BETWEEN)",
     "s.posterior_entropy BETWEEN st.minimum_ambiguity AND st.maximum_ambiguity",
     "s.posterior_entropy > st.minimum_ambiguity AND s.posterior_entropy < st.maximum_ambiguity"),
    ("m5-status-filter-dropped", "M5", "rejected recordings allowed on stations (ingest status not checked)",
     "    WHERE t.ingest_status = 'scored'\n      AND s.posterior_entropy", "    WHERE s.posterior_entropy"),
    ("m5-any-model", "M5", "scores from every model version used, not the station's own",
     "ON s.model_id = st.model_id", "ON s.model_id = s.model_id"),
    ("m5-blend-genre-ignored", "M5", "top genre not matched to the blend (any blend row joins)",
     "ON b.station_id = st.station_id\n                                           AND b.genre_id = s.genre_id",
     "ON b.station_id = st.station_id"),
    ("m5-weight-ascending", "M5", "lowest blend weight first", "         e.genre_weight DESC,", "         e.genre_weight,"),
    ("m5-tie-break-dropped", "M5", "the track_id tie-break left out of ORDER BY",
     "         e.posterior_entropy DESC,\n         e.track_id;", "         e.posterior_entropy DESC;"),
    ("m5-minutes-unrounded", "M5", "station running time not rounded", "ROUND(SUM(duration) / 60, 1) AS run_minutes",
     "SUM(duration) / 60 AS run_minutes"),
    # M6 results to recompute (3.1)
    ("m6-deployment-day-stale", "M6", "a result scored at midnight on the deployment day counted as out of date (<= instead of <)",
     "HAVING MAX(s.scored_on) < (SELECT", "HAVING MAX(s.scored_on) <= (SELECT"),
    ("m6-oldest-result", "M6", "the oldest result judged instead of the newest: rescored recordings stay listed",
     "HAVING MAX(s.scored_on)", "HAVING MIN(s.scored_on)"),
    ("m6-rejected-included", "M6", "rejected recordings queued for rescoring (release status not checked)",
     "WHERE t.ingest_status = 'scored'\nGROUP BY t.track_id, t.title", "GROUP BY t.track_id, t.title"),
    ("m6-days-from-first-deployment", "M6", "days counted from the first deployment instead of the one in service",
     "DATEDIFF((SELECT MAX(n.deployed_on)", "DATEDIFF((SELECT MIN(n.deployed_on)"),
    ("m6-versions-alphabetical", "M6", "the versions listed alphabetically instead of oldest first",
     "ORDER BY m.deployed_on, m.model_id SEPARATOR", "ORDER BY m.version_label SEPARATOR"),
    ("m6-tie-break-dropped", "M6", "the track_id tie-break left out of ORDER BY",
     "ORDER BY days_out_of_date DESC,\n         t.track_id;", "ORDER BY days_out_of_date DESC;"),
    # M7 between genres (3.5)
    ("m7-second-place-includes-top", "M7", "the top genre allowed as its own runner-up: every margin is 0",
     "    WHERE gp.genre_id <> s.genre_id\n    GROUP BY gp.track_id, gp.model_id\n),", "    GROUP BY gp.track_id, gp.model_id\n),"),
    ("m7-higher-genre-on-tie", "M7", "a tie for second place goes to the higher genre_id", "MIN(gp.genre_id) AS genre_id",
     "MAX(gp.genre_id) AS genre_id"),
    ("m7-largest-margin-first", "M7", "the most clearly placed recordings first", "ORDER BY margin,", "ORDER BY margin DESC,"),
    ("m7-tie-break-dropped", "M7", "the model_id tie-break left out of ORDER BY",
     "ORDER BY margin,\n         t.track_id,\n         s.model_id;", "ORDER BY margin,\n         t.track_id;"),
]
FUNCS = [   # (name, query, what the mistake is, function of the file text): mistakes that need more than one edit
    ("m7-runner-up-optional", "M7", "results with no distribution kept, half empty (runner_up and its genre joined LEFT OUTER)",
     lambda t: t.replace("INNER JOIN runner_up AS r", "LEFT OUTER JOIN runner_up AS r", 1)
                .replace("INNER JOIN crossfade.genre AS g2", "LEFT OUTER JOIN crossfade.genre AS g2", 1)),
]


def run(path, fresh=False):
    r = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q", "-p", "no:cacheprovider", "--msql", str(path),
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
            p = pathlib.Path(tmp) / "multiple_table.sql"
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
