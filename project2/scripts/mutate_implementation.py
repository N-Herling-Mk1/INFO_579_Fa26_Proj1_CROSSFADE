"""Test the tests: break database_implementation.sql on purpose, one way at a time, and check that
test_implementation.py notices every break.

    python project2/scripts/mutate_implementation.py          (needs MySQL; CROSSFADE_DB_PASSWORD set)

Each mutant is a copy of the script with one deliberate mistake, written to a temporary folder and run through
the full test file with --impl. A mutant is "caught" when at least one test fails. The script under test is
never changed; at the end the real script is run once more so `crossfade` is left as it should be.

Writes project2/data/implementation_mutants.json (read by build_vetting.py for the site and the PDF).
"""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SQL = ROOT / "project2" / "deliverables" / "database_implementation.sql"
TEST = ROOT / "project2" / "tests" / "test_implementation.py"
OUT = ROOT / "project2" / "data" / "implementation_mutants.json"
src = SQL.read_text(encoding="utf-8").replace("\r\n", "\n")

# (name, what the mistake is, old text, new text)
EDITS = [
    ("varchar-size", "a column one character wider than the model (genre.name VARCHAR(10))",
     "name VARCHAR(9) NOT NULL", "name VARCHAR(10) NOT NULL"),
    ("unsigned-dropped", "UNSIGNED missing on a key (track.track_id INT)",
     "track_id INT UNSIGNED NOT NULL,\n\tartist_id", "track_id INT NOT NULL,\n\tartist_id"),
    ("check-dropped", "a CHECK left out (I4, the ambiguity window)",
     ",\n\tCONSTRAINT ck_station_ambiguity_window CHECK (minimum_ambiguity <= maximum_ambiguity)", ""),
    ("primary-key-wrong", "an extra column in a composite primary key (play)",
     "PRIMARY KEY (listener_id, track_id, played_at)", "PRIMARY KEY (listener_id, track_id, played_at, seconds_played)"),
    ("optional-made-required", "an optional column made NOT NULL (play.reaction)",
     "\treaction ENUM('saved', 'skipped'),", "\treaction ENUM('saved', 'skipped') NOT NULL DEFAULT 'saved',"),
    ("required-made-optional", "a required column left nullable (track.title)",
     "\ttitle VARCHAR(128) NOT NULL,", "\ttitle VARCHAR(128),"),
    ("cascade-dropped", "ON DELETE CASCADE left out (station_blend -> station)",
     "REFERENCES crossfade.station (station_id)\n\t\tON DELETE CASCADE", "REFERENCES crossfade.station (station_id)"),
    ("foreign-key-renamed", "a foreign key under another name (fk_play_stn)",
     "CONSTRAINT fk_play_station FOREIGN KEY", "CONSTRAINT fk_play_stn FOREIGN KEY"),
    ("foreign-key-dropped", "a foreign key left out (track -> artist)",
     ",\n\tCONSTRAINT fk_track_artist FOREIGN KEY (artist_id)\n\t\tREFERENCES crossfade.artist (artist_id)", ""),
    ("unique-dropped", "a unique key left out (listener.email)", "UNIQUE INDEX uq_listener_email (email),", ""),
    ("checks-switched-off", "foreign-key checks switched off during the load",
     "DROP DATABASE IF EXISTS crossfade;", "DROP DATABASE IF EXISTS crossfade;\nSET FOREIGN_KEY_CHECKS = 0;"),
    ("not-re-runnable", "DROP DATABASE IF EXISTS removed (the script cannot run twice)", "DROP DATABASE IF EXISTS crossfade;", ""),
    ("decimal-rounds", "a DECIMAL one place too short, so MySQL rounds the data (probability DECIMAL(5,3))",
     "probability DECIMAL(5,4) NOT NULL,\n\tCONSTRAINT pk_genre_probability", "probability DECIMAL(5,3) NOT NULL,\n\tCONSTRAINT pk_genre_probability"),
    ("enum-extra-value", "an ENUM value the model does not have (plan_tier 'family')",
     "ENUM('free', 'standard', 'premium')", "ENUM('free', 'standard', 'premium', 'family')"),
    ("date-as-datetime", "DATE stored as DATETIME (listener.signup_date)", "signup_date DATE NOT NULL", "signup_date DATETIME NOT NULL"),
    ("checksum-varbinary", "the fixed 32-byte checksum stored as VARBINARY(64)",
     "audio_checksum BINARY(32) NOT NULL", "audio_checksum VARBINARY(64) NOT NULL"),
]


def value_changed(s):
    i = s.index("0.0035", s.index("INSERT INTO crossfade.play"))
    return s[:i] + "0.0036" + s[i + 6:]


def row_dropped(s):
    i = s.index("INSERT INTO crossfade.artist"); j = s.index(";", i)
    m = re.search(r",\s*\(1049[^)]*\)", s[i:j])
    return s[:i] + s[i:j][:m.start()] + s[i:j][m.end():] + s[j:]


def comment_removed(s):
    i = s.index("CREATE TABLE IF NOT EXISTS crossfade.listener"); j = s.rindex("/*", 0, i); k = s.index("*/", j) + 2
    return s[:j] + s[k:]


FUNCS = [("value-changed", "one royalty amount changed (0.0035 -> 0.0036)", value_changed),
         ("row-dropped", "one artist row left out (1049)", row_dropped),
         ("comment-removed", "the purpose comment before one CREATE TABLE removed (the brief)", comment_removed)]


def run(path):
    env = dict(os.environ)
    r = subprocess.run([sys.executable, "-m", "pytest", str(TEST), "-q", "-p", "no:cacheprovider", "--impl", str(path),
                        "--results", str(pathlib.Path(tempfile.gettempdir()) / "crossfade_mutants")],
                       capture_output=True, text=True, env=env, cwd=ROOT)
    failed = re.findall(r"FAILED \S+::(\S+)", r.stdout)
    m = re.search(r"(\d+) failed", r.stdout)
    return int(m.group(1)) if m else 0, failed, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]


def main():
    if os.environ.get("CROSSFADE_DB_PASSWORD") is None:
        sys.exit("set CROSSFADE_DB_PASSWORD first")
    mutants = [(n, d, src.replace(a, b, 1)) for n, d, a, b in EDITS if a in src]
    missing = [n for n, d, a, b in EDITS if a not in src]
    mutants += [(n, d, f(src)) for n, d, f in FUNCS]
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, (name, what, text) in enumerate(mutants, 1):
            p = pathlib.Path(tmp) / f"{name}.sql"
            p.write_text(text, encoding="utf-8")
            n, failed, tail = run(p)
            results.append({"mutant": name, "mistake": what, "caught": n > 0, "failed": n, "first_failures": failed[:4]})
            print(f"[{k}/{len(mutants)}] {name:<24} {'caught' if n else 'MISSED'}  ({tail})", flush=True)
    print("[final] rebuilding crossfade from the real script", flush=True)
    n, _, tail = run(SQL)
    print(f"        {tail}", flush=True)
    OUT.write_text(json.dumps({"mutants": results, "caught": sum(r["caught"] for r in results), "total": len(results),
                               "not_applicable": missing, "real_script": tail}, indent=1), encoding="utf-8")
    print(f"{sum(r['caught'] for r in results)}/{len(results)} mutants caught -> {OUT.relative_to(ROOT)}")
    sys.exit(0 if all(r["caught"] for r in results) else 1)


if __name__ == "__main__":
    main()
