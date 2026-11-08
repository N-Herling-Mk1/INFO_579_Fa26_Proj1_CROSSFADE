"""Test the tests: break routines.sql on purpose, one way at a time, and check that test_routines.py
notices every break.

    python project2/scripts/mutate_routines.py          (needs MySQL; CROSSFADE_DB_PASSWORD set)

Each mutant is a copy of routines.sql with one deliberate mistake, written to a temporary folder and run
through the full test file with --rsql. A mutant is "caught" when at least one test fails that passes on the real file. The file under test is
never changed. The database is rebuilt from database_implementation.sql once, first (--fresh), and every test
that writes does so inside a transaction it rolls back.

Writes project2/data/routines_mutants.json (read by build_vetting.py for the site and the PDF).
"""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SQL = ROOT / "project2" / "deliverables" / "routines.sql"
TEST = ROOT / "project2" / "tests" / "test_routines.py"
OUT = ROOT / "project2" / "data" / "routines_mutants.json"
src = SQL.read_text(encoding="utf-8").replace("\r\n", "\n")

# (name, routine, what the mistake is, old text, new text)
EDITS = [
    # F1 play_royalty
    ("f1-thirty-seconds-excluded", "F1", "a play of exactly 30 seconds earns nothing (> instead of >=)",
     "ELSEIF input_seconds_played >= 30 THEN", "ELSEIF input_seconds_played > 30 THEN"),
    ("f1-unknown-is-zero", "F1", "a recording that does not exist earns 0 instead of NULL",
     "IF artist_rate IS NULL OR input_seconds_played IS NULL THEN\n\t\tRETURN NULL;",
     "IF artist_rate IS NULL OR input_seconds_played IS NULL THEN\n\t\tRETURN 0;"),
    ("f1-one-rate-for-all", "F1", "every recording paid at one artist's rate (join condition wrong)",
     "INNER JOIN crossfade.artist AS a ON a.artist_id = t.artist_id", "INNER JOIN crossfade.artist AS a ON a.artist_id = 1042"),
    ("f1-declared-deterministic", "F1", "declared DETERMINISTIC, though the rate it reads can change",
     "\tNOT DETERMINISTIC\n", "\tDETERMINISTIC\n"),
    ("f1-declared-no-sql", "F1", "declared NO SQL, though it reads two tables", "\tREADS SQL DATA\nBEGIN", "\tNO SQL\nBEGIN"),
    # P1 record_play
    ("p1-completed-at-thirty", "P1", "completed means 30 seconds or more, not the whole recording",
     "SET output_completed = (input_seconds_played = track_duration);", "SET output_completed = (input_seconds_played >= 30);"),
    ("p1-awaiting-scoring-allowed", "P1", "only rejected recordings refused: one awaiting scoring can be streamed",
     "ELSEIF track_status <> 'scored' THEN", "ELSEIF track_status = 'rejected' THEN"),
    ("p1-full-play-refused", "P1", "a play as long as the recording refused (>= instead of >)",
     "ELSEIF input_seconds_played > track_duration THEN", "ELSEIF input_seconds_played >= track_duration THEN"),
    ("p1-fixed-royalty", "P1", "a fixed royalty instead of the artist's rate through play_royalty",
     "SET output_royalty_amount = crossfade.play_royalty(input_track_id, input_seconds_played);",
     "SET output_royalty_amount = 0.00400;"),
    ("p1-local-time", "P1", "no time given: local time (NOW) instead of UTC", "IFNULL(input_played_at, UTC_TIMESTAMP())",
     "IFNULL(input_played_at, NOW())"),
    ("p1-station-dropped", "P1", "the station that surfaced the play not recorded",
     "IFNULL(input_played_at, UTC_TIMESTAMP()), input_station_id,", "IFNULL(input_played_at, UTC_TIMESTAMP()), NULL,"),
    ("p1-swallows-repeats", "P1", "a repeated report of a play silently ignored (CONTINUE HANDLER FOR 1062)",
     "\tDECLARE error_message VARCHAR(128);\n\n\t-- The recording's length",
     "\tDECLARE error_message VARCHAR(128);\n\tDECLARE CONTINUE HANDLER FOR 1062 BEGIN END;\n\n\t-- The recording's length"),
    ("p1-uses-line-wrong", "P1", "the comment lists a feature the procedure does not use",
     "Uses: DECLARE, IF ... ELSEIF, SIGNAL", "Uses: DECLARE, DECLARE CONTINUE HANDLER, IF ... ELSEIF, SIGNAL"),
    ("p1-parameter-line-wrong", "P1", "the comment declares a parameter type MySQL does not have",
     "IN input_reaction VARCHAR(7), IN input_played_at DATETIME", "IN input_reaction VARCHAR(10), IN input_played_at DATETIME"),
    # P2 upload_track
    ("p2-handler-for-every-error", "P2", "the handler catches every error, not just 1062",
     "\tDECLARE EXIT HANDLER FOR 1062\n\tBEGIN", "\tDECLARE EXIT HANDLER FOR SQLEXCEPTION\n\tBEGIN"),
    ("p2-no-resignal", "P2", "a key clash on the new track ID reported as a duplicate (RESIGNAL removed)",
     "\t\tIF output_track_id IS NULL THEN\n\t\t\tRESIGNAL;      -- the duplicate key was the new track ID, not the audio file\n\t\tEND IF;\n", ""),
    ("p2-enters-as-scored", "P2", "an upload enters the catalogue as scored, skipping the pipeline",
     "input_audio_checksum, 'awaiting scoring');", "input_audio_checksum, 'scored');"),
    ("p2-reuses-an-id", "P2", "the new track takes the highest existing ID instead of the next one",
     "SET output_track_id = (SELECT IFNULL(MAX(track_id), 0) + 1 FROM crossfade.track);",
     "SET output_track_id = (SELECT IFNULL(MAX(track_id), 0) FROM crossfade.track);"),
    ("p2-artist-not-checked", "P2", "an unregistered artist is not refused in words (left to the foreign key)",
     "\tIF (SELECT COUNT(*) FROM crossfade.artist WHERE artist_id = input_artist_id) = 0 THEN",
     "\tIF FALSE THEN"),
    ("p2-tables-line-wrong", "P2", "artist left off the comment's Tables line", "Tables: artist, track", "Tables: track"),
]
FUNCS = []


def run(path, fresh=False):
    r = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q", "-p", "no:cacheprovider", "--rsql", str(path),
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
            p = pathlib.Path(tmp) / "routines.sql"
            p.write_text(text, encoding="utf-8")
            n, failed, tail = run(p)
            new = [t for t in failed if t not in base]       # caught = a test fails that passes on the real file
            results.append({"mutant": name, "query": q, "mistake": what, "caught": bool(new), "failed": len(new),
                            "first_failures": new[:4]})
            print(f"[{k}/{len(mutants)}] {name:<28} {'caught' if new else 'MISSED'}  ({len(new)} new failures)", flush=True)
    run(SQL)                                             # leave the real routines in the database
    OUT.write_text(json.dumps({"mutants": results, "caught": sum(r["caught"] for r in results), "total": len(results),
                               "not_applicable": missing, "real_file": tail, "already_failing": sorted(base)}, indent=1),
                   encoding="utf-8")
    print(f"{sum(r['caught'] for r in results)}/{len(results)} mutants caught -> {OUT.relative_to(ROOT)}"
          + (f"; edits that no longer apply: {missing}" if missing else ""))
    sys.exit(0 if all(r["caught"] for r in results) else 1)


if __name__ == "__main__":
    main()
