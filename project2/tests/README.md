# CROSSFADE Project 2 tests

Unit tests for the Project 2 SQL files. Today: `single_table.sql` (63 tests) plus one expected-error case (UC-15). `multiple_table.sql` and
`routines.sql` get their own test files as they are written.

## What is tested

| Layer | Per | What it proves |
|---|---|---|
| contract | query | purpose comment with `[S#]` tag, table, use cases and business question; one read-only `SELECT`, no `SELECT *`; exactly one table in MySQL's own plan (`EXPLAIN FORMAT=JSON`); the brief requirements (a)–(e) it declares are exactly the ones it uses (course function lists; selection control = `CASE`, `IF`); it reads only columns its use cases declare in `use_cases.json` |
| correctness | query | result equals an independent Python answer from `data.csv` (`oracle.py`): same columns, rows, order, exact decimals; two runs agree |
| behaviour | case | logic the sample data never reaches, checked by adding or changing rows inside a transaction that is rolled back (nothing in your database changes) |
| expected error | case | `expected_errors.sql`, tagged `[E#]`: statements that must fail. E1 re-uploads an existing audio file; MySQL must refuse it with error 1062 on `uq_track_audio_checksum` and leave `track` unchanged (run in a rolled-back transaction) |
| coverage | file | every non-associative table queried; each requirement met at least twice; every single-table use case answered; tags `S1`… unique and in order |

## Set up once

```
pip install -r requirements.txt
```

## Run it

You need these four files, either in a clone of the repo (found automatically) or together in one folder
with the test files:

| File | Where to get it |
|---|---|
| `data.csv` | site: Home → Project 1 data → Bulk → Download data.csv |
| `database_implementation.sql` | site: Project 2 → database_implementation → Download |
| `single_table.sql` | site: Project 2 → single_table → Download |
| `use_cases.json` | in the test kit (site: Project 2 → single_table → Download test kit) |

1. Build the database: run `database_implementation.sql` (Workbench: open, Execute; or
   `mysql -u root -p -e "source database_implementation.sql"`).
2. Give the tests your MySQL password, then run them. PowerShell:

```
$env:CROSSFADE_DB_PASSWORD = "your-root-password"
python -m pytest                     # inside the test-kit folder
python -m pytest project2/tests      # from the repo root
```

The tests first confirm that `crossfade` holds exactly the rows in `data.csv`, and stop with a clear message
if it does not. `--fresh` rebuilds the database from `database_implementation.sql` before testing.

Other settings: `CROSSFADE_DB_USER` (default `root`), `CROSSFADE_DB_HOST` (`127.0.0.1`), `CROSSFADE_DB_PORT`
(`3306`), or `--db-user`, `--db-host`, `--db-port`, `--db-password`. File locations can be given with
`--data`, `--impl`, `--sql`, `--use-cases`.

## Output

One line per test with a running percentage, then a pass/fail summary. Each run also writes a snapshot of
every query's result and every test outcome: `project2/data/single_table_results.json` and `.js` in the
repo (the site shows them on the single_table page), or `results/` next to the tests in a kit folder.

## Files

```
conftest.py            settings, file discovery, database check, .sql splitter, results snapshot
oracle.py              the independent Python answers, one per query
test_single_table.py   the tests
expected_errors.sql    statements that must fail (one per error use case)
pytest.ini             -v by default
requirements.txt       pytest, pymysql, cryptography
build_kit.py           builds the downloadable test kit (crossfade_p2_test_kit.zip)
```
