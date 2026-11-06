"""QC for Task 1: load database_implementation.sql into MySQL and compare every row and
column of the 10 tables with the Project 1 sample data.

The reference is project1/data_export/csv/<table>.csv, which tools/export_p1_data.py
exports from the graded data.xlsx and checks cell-for-cell against it.

Uses only the mysql command-line client (mysql.exe on Windows), no Python driver.

    python project2/scripts/check_implementation.py                  # user root, asks for the password
    python project2/scripts/check_implementation.py --user root --mysql "C:/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe"
    python project2/scripts/check_implementation.py --no-load        # compare only, database already loaded

Steps: [1/4] run the script, [2/4] run it a second time (it must be re-runnable),
[3/4] compare every table, [4/4] check the cross-row integrity rules on the data.
Exit code 0 when everything matches.
"""
import argparse, csv, getpass, os, subprocess, sys
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SQL = os.path.join(ROOT, "project2", "deliverables", "database_implementation.sql")
CSV_DIR = os.path.join(ROOT, "project1", "data_export", "csv")

# table -> (column, kind, select expression); kind n = number, s = text
TABLES = {
    "genre": [("genre_id", "n"), ("name", "s"), ("description", "s")],
    "artist": [("artist_id", "n"), ("stage_name", "s"), ("country", "s"), ("joined_date", "s"),
               ("payout_rate", "n"), ("verified", "n", "verified + 0")],
    "listener": [("listener_id", "n"), ("email", "s"), ("display_name", "s"), ("plan_tier", "s"), ("signup_date", "s")],
    "scoring_model": [("model_id", "n"), ("version_label", "s"), ("fusion_type", "s"), ("embedding_dimension", "n"),
                      ("segment_length", "n"), ("training_corpus", "s"), ("holdout_accuracy", "n"), ("deployed_on", "s")],
    "track": [("track_id", "n"), ("artist_id", "n"), ("title", "s"), ("duration", "n"), ("release_date", "s"),
              ("audio_checksum", "s", "CONCAT('0x', HEX(audio_checksum))"), ("ingest_status", "s")],
    "station": [("station_id", "n"), ("listener_id", "n"), ("model_id", "n"), ("name", "s"),
                ("minimum_ambiguity", "n"), ("maximum_ambiguity", "n"), ("created_on", "s")],
    "track_score": [("track_id", "n"), ("model_id", "n"), ("genre_id", "n"), ("top_probability", "n"),
                    ("posterior_entropy", "n"), ("model_divergence", "n"), ("segment_variance", "n"), ("scored_on", "s")],
    "genre_probability": [("track_id", "n"), ("model_id", "n"), ("genre_id", "n"), ("probability", "n")],
    "station_blend": [("station_id", "n"), ("genre_id", "n"), ("weight", "n")],
    "play": [("listener_id", "n"), ("track_id", "n"), ("played_at", "s"), ("station_id", "n"),
             ("seconds_played", "n"), ("completed", "n", "completed + 0"), ("reaction", "s"), ("royalty_amount", "n")],
}
RULES = [
    ("I1 station blend weights sum to 1.00",
     "SELECT COUNT(*) FROM (SELECT station_id FROM station_blend GROUP BY station_id HAVING SUM(weight) <> 1) x"),
    ("I2 ten probabilities per result, summing to 1 within 0.0010",
     "SELECT COUNT(*) FROM (SELECT track_id, model_id FROM genre_probability GROUP BY track_id, model_id "
     "HAVING COUNT(*) <> 10 OR ABS(SUM(probability) - 1) > 0.001) x"),
    ("I3 top genre and top probability agree with genre_probability",
     "SELECT COUNT(*) FROM track_score s WHERE s.top_probability <> (SELECT MAX(p.probability) FROM genre_probability p "
     "WHERE p.track_id = s.track_id AND p.model_id = s.model_id) OR s.genre_id NOT IN (SELECT p.genre_id FROM genre_probability p "
     "WHERE p.track_id = s.track_id AND p.model_id = s.model_id AND p.probability = s.top_probability)"),
    ("I5 a track is 'scored' only if it has a track_score",
     "SELECT COUNT(*) FROM track t WHERE t.ingest_status = 'scored' AND NOT EXISTS "
     "(SELECT 1 FROM track_score s WHERE s.track_id = t.track_id)"),
    ("I7 completed = (seconds_played = duration)",
     "SELECT COUNT(*) FROM play p JOIN track t ON p.track_id = t.track_id WHERE p.completed <> (p.seconds_played = t.duration)"),
    ("I7 royalty = payout_rate if 30 s or more, else 0",
     "SELECT COUNT(*) FROM play p JOIN track t ON p.track_id = t.track_id JOIN artist a ON t.artist_id = a.artist_id "
     "WHERE p.royalty_amount <> IF(p.seconds_played >= 30, a.payout_rate, 0)"),
]


def mysql(args, sql=None, path=None):
    cmd = [args.mysql, "-u", args.user, "--batch", "--raw", "--skip-column-names", "--default-character-set=utf8mb4"]
    env = dict(os.environ)
    if args.password is not None:
        env["MYSQL_PWD"] = args.password
    if args.host: cmd += ["-h", args.host]
    if args.port: cmd += ["-P", str(args.port)]
    if sql is not None:
        cmd += ["crossfade", "-e", sql]
        stdin = None
    else:
        stdin = open(path, "rb")
    r = subprocess.run(cmd, stdin=stdin, capture_output=True, env=env)
    if r.returncode != 0:
        sys.exit("      mysql failed:\n" + r.stderr.decode("utf-8", "replace"))
    return r.stdout.decode("utf-8")


def same(a, b, kind):
    if a in ("", "NULL") or b in ("", "NULL"):
        return (a in ("", "NULL")) == (b in ("", "NULL"))
    return Decimal(a) == Decimal(b) if kind == "n" else a == b


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mysql", default="mysql", help="path to the mysql client (default: mysql on PATH)")
    ap.add_argument("--user", default="root")
    ap.add_argument("--host"); ap.add_argument("--port", type=int)
    ap.add_argument("--password", help="omit to be asked; use '' for no password")
    ap.add_argument("--no-load", action="store_true", help="skip loading; compare the database as it is")
    args = ap.parse_args()
    if args.password is None:
        args.password = getpass.getpass(f"MySQL password for {args.user} (Enter for none): ")

    if args.no_load:
        print("[1/4] load skipped (--no-load)\n[2/4] load skipped (--no-load)", flush=True)
    else:
        for step in (1, 2):
            print(f"[{step}/4] running database_implementation.sql ({'first' if step == 1 else 'second'} run)", flush=True)
            mysql(args, path=SQL)
            print("      ok", flush=True)

    print("[3/4] comparing every table with the Project 1 sample data", flush=True)
    bad, total = 0, 0
    for i, (table, cols) in enumerate(TABLES.items(), 1):
        exprs = [c[2] if len(c) > 2 else c[0] for c in cols]
        got = [line.split("\t") for line in mysql(args, f"SELECT {', '.join(exprs)} FROM {table}").splitlines()]
        with open(os.path.join(CSV_DIR, table + ".csv"), encoding="utf-8", newline="") as f:
            want = list(csv.reader(f))[1:]
        def key(r):
            return tuple((0, Decimal(0), "") if v in ("", "NULL") else
                         (1, Decimal(v), "") if k == "n" else (1, Decimal(0), v)
                         for v, (_, k, *_) in zip(r, cols))
        want.sort(key=key)
        got.sort(key=key)
        errs = 0
        if len(got) != len(want):
            print(f"      {table}: {len(got)} rows in MySQL, {len(want)} in data.xlsx"); errs += 1
        for g, w in zip(got, want):
            for v_g, v_w, (col, kind, *_) in zip(g, w, cols):
                if not same(v_g, v_w, kind):
                    errs += 1
                    if errs <= 5: print(f"      {table}.{col}: MySQL {v_g!r}, data.xlsx {v_w!r}")
        total += len(want); bad += errs
        print(f"      [{'#' * i}{'.' * (len(TABLES) - i)}] {table:<18} {len(got):>4} rows  {'ok' if not errs else str(errs) + ' differences'}", flush=True)
    print(f"      {total} rows checked, {bad} differences", flush=True)

    print("[4/4] integrity rules on the loaded data", flush=True)
    for name, q in RULES:
        n = int(mysql(args, q).strip())
        bad += n
        print(f"      {'ok  ' if n == 0 else 'FAIL'} {name}{'' if n == 0 else f' ({n} rows)'}", flush=True)

    print("PASS" if bad == 0 else "FAIL", flush=True)
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
