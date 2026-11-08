# CROSSFADE Project 2 tests

Unit tests for the Project 2 SQL files. Today:

- `database_implementation.sql`: `test_implementation.py`, 228 tests (below).
- `single_table.sql`: `test_single_table.py`, 67 tests, including the expected-error case [E1] (UC-15).
- `multiple_table.sql`: `test_multiple_table.py`, 80 tests (below).

`routines.sql` gets its own test file when it is written. Each file has a page on the site:
Project 2 → Vetting & tests.

## database_implementation.sql (`test_implementation.py`)

Runs the script twice, then compares the database it leaves with three sources that do not come from the script:
the physical model (typed by hand into `SPEC`), the value rules of the requirements analysis (`CHECKS`), and `data.csv`.

| Group | Tests | What it proves |
|---|---|---|
| load | 6 | runs clean, re-runs, no warnings (no silent rounding or trimming), a comment before every statement, checks never switched off, each table created once and loaded after its parents |
| schema | 41 | exactly the ten tables; columns in order with exact type, size, UNSIGNED and NULL; primary keys (composite on the associative tables); all 13 foreign keys with columns, parent, name and ON DELETE; the five unique keys; fk_/uq_/ck_ names |
| read | 10 | one live SELECT per table; every value has the right Python type |
| data | 42 | row counts and every cell equal `data.csv`; the integrity rules I1–I5, I7 hold; no orphan rows |
| enforce | 129 | in rolled-back transactions: a valid row is accepted, then every key, NOT NULL, CHECK, type limit and ON DELETE rule refuses a bad write with the exact MySQL error and constraint name |

**It drops and rebuilds the `crossfade` database** (twice) and leaves it loaded. It needs only `data.csv` and
`database_implementation.sql`: `crossfade_impl_tests.zip` is a folder that runs as-is.

```
$env:CROSSFADE_DB_PASSWORD = "your-root-password"
python -m pytest test_implementation.py                 # test-kit folder
python -m pytest project2/tests/test_implementation.py  # repo root
```

What it covers and what it could miss: `project2/docs/test_implementation_guide.pdf`, or the site page.

## single_table.sql (`test_single_table.py`)

## What is tested

| Layer | Per | What it proves |
|---|---|---|
| contract | query | purpose comment with `[S#]` tag, table, use cases and business question; one read-only `SELECT`, no `SELECT *`; exactly one table in MySQL's own plan (`EXPLAIN FORMAT=JSON`); the brief requirements (a)–(e) it declares are exactly the ones it uses (course function lists; selection control = `CASE`, `IF`); it reads only columns its use cases declare in `use_cases.json` |
| correctness | query | result equals an independent Python answer from `data.csv` (`oracle.py`): same columns, rows, order, exact decimals; two runs agree |
| behaviour | case | logic the sample data never reaches, checked by adding or changing rows inside a transaction that is rolled back (nothing in your database changes) |
| expected error | case | the `[E#]` statements at the end of `single_table.sql`, marked EXPECTED TO FAIL: writes the database must refuse. E1 re-uploads an existing audio file; MySQL must refuse it with error 1062 on `uq_track_audio_checksum` and leave `track` unchanged (run in a rolled-back transaction) |
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
| `use_cases.json` | in the starter kit (site: Project 2 → single_table → Download starter kit), which also holds the other three; drop the downloaded `single_table.sql` in to replace the blank one |

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

## What must match between `single_table.sql` and the tests

The tests find each query by its comment, so the names below are the contract. A comment with no statement after it is
not a query: a file of comments only collects 0 queries, so the per-query tests are skipped and the coverage and behaviour
tests fail.

| In `single_table.sql` | Must match | Checked by |
|---|---|---|
| file name `single_table.sql` | what the tests look for (or pass `--sql PATH`) | file discovery |
| a `/* ... */` block right before each statement | the comment is the last block comment before the `;` statement | `split_sql` |
| `[S1]`, `[S2]`, … at the start of that comment | `S1`…`Sn`, no gaps, in file order; each tag is a key in `ORACLES` in `oracle.py` | `test_tags_are_unique_and_in_order`, `test_result_matches_oracle` |
| table word right after the tag: `[S1] ARTIST:` | one of `ARTIST TRACK GENRE LISTENER SCORING_MODEL STATION` (upper case, underscore); the only table in MySQL's plan | `test_comment_contract`, `test_reads_exactly_one_table` |
| `Use cases: UC-02, UC-01` | ids in `use_cases.json` (`useCases[].id`) | `test_comment_contract` |
| columns the query reads | listed for that table in each use case's `singleColumns` (else `columns`) in `use_cases.json` | `test_columns_match_use_cases` |
| `Business question: …` | more than 20 characters; ends at a line starting `-` or `Requirements:` | `test_comment_contract` |
| `Requirements: (a) … (c) … (e) …` | exactly the letters the SQL uses: (a) single-row function, (b) aggregate, (c) `ORDER BY`, (d) `LIMIT n`, (e) `CASE`/`IF` | `test_requirements_match_declared` |
| output column names (`AS payee`, …) and their order | the `cols` list the oracle function returns | `test_result_matches_oracle` |
| row order and values | the oracle's rows; every `ORDER BY` must include a unique key of the table (or all the `GROUP BY` columns), so no two rows can tie | `test_result_matches_oracle`, `test_result_is_deterministic` |
| table names in `FROM crossfade.<table>` | the database (`database_implementation.sql`) and the table names in `data.csv`, snake_case | `test_read_only_select`, oracle |

An `[E1] TABLE:` statement (EXPECTED TO FAIL) follows the same comment shape plus `Expects: 1062 uq_track_audio_checksum`,
which must equal `expectsError.code` and `expectsError.constraint` of its use case in `use_cases.json`; the constraint name must be the
one `database_implementation.sql` creates. `[E#]` statements come after every `[S#]` query: an error stops a script run.

The behaviour tests (`test_s2_…`) refer to a query by its tag (`q["S2"]`) and to result columns by position, so renumbering a query or
reordering its output columns means updating them too.

A query stub that satisfies the contract shape (the tests will then tell you what is still missing):

```sql
/*
	[S8] TRACK: one line naming what this answers
	Use cases: UC-03
	Business question: The question the business asks, in a full sentence of more than twenty characters?
	- Why the query is written this way, citing the RA.
	Requirements: (c) ORDER BY
*/
SELECT track_id, title
FROM crossfade.track
ORDER BY track_id;
```

Adding `[S8]` also means adding `def s8(t)` to `oracle.py` and `"S8": s8` to `ORACLES`.

## multiple_table.sql (`test_multiple_table.py`)

Same layers as `test_single_table.py`, adapted to joins. Expected answers come from `oracle_multiple.py` (plain Python:
joins are dictionary look-ups, `UNION` is a set, `WITH` is a list built first).

| Layer | Per | What it proves |
|---|---|---|
| contract | query | comment with `[M#]` tag and title, use cases, business need and question, `Requirements: 3.x`, `Tables:`, `One row per:`, `Output:`; one read-only `SELECT` or `WITH ... SELECT`, no `SELECT *`; MySQL's plan reads exactly the `Tables:`; the SQL really meets its 3.x (3.1 = an associative table `INNER JOIN`ed to two tables it references, from the live foreign keys); every join named in full; the columns MySQL reads (`used_columns` in `EXPLAIN FORMAT=JSON`) equal the use cases' `multipleColumns` |
| correctness | query | result equals `oracle_multiple.py` exactly; one row per `One row per:` value, the `ORDER BY` includes those columns, two runs agree |
| behaviour | case | 21 cases in rolled-back transactions: rows dropped or kept by each join, the 30-second boundary, `UNION` versus `UNION ALL`, a third model version, `NULL` divergence, the entropy window's edges, a rejected recording, blend and model rules, the deployment-day boundary, ties for the runner-up genre and a tied top genre |
| coverage | file | each of 3.1-3.5 met; every use case with `multipleColumns` answered; tags `M1`… in order |

```
python -m pytest test_multiple_table.py                  # test-kit folder
python -m pytest project2/tests/test_multiple_table.py   # repo root
python project2/scripts/mutate_multiple_table.py         # tests the tests (39 deliberate mistakes)
```

File option: `--msql PATH` (or `CROSSFADE_MSQL`). Adding `[M6]` means adding `def m6(t)` to `oracle_multiple.py` and
`"M6": m6` to `ORACLES`, and its use cases' `multipleColumns` in `use_cases.json`.

## Output

One line per test with a running percentage, then a pass/fail summary. Each run also writes a snapshot of
every query's result, its expected (oracle) result, every behaviour case's inputs and expected rows, and every test outcome:
`project2/data/single_table_results.json` / `multiple_table_results.json` and `.js` in the repo (the site shows them on
the file pages and the Use cases page), or `results/` next to the tests in a kit folder.

## Files

Both kits also carry `run_tests_locally.pdf` (every step, and what each failure means) and `use_case_reference.pdf`
(each use case's tables, columns, input and expected output), built by `python project2/scripts/build_docs.py` from
`use_cases.json` and the last test run.

```
conftest.py            settings, file discovery, database check, .sql splitter, results snapshot
oracle.py              the independent Python answers, one per single_table.sql query
oracle_multiple.py     the same for multiple_table.sql
test_single_table.py   the tests for single_table.sql
test_multiple_table.py the tests for multiple_table.sql
pytest.ini             -v by default
requirements.txt       pytest, pymysql, cryptography
build_kit.py           builds the answer-key test kit (crossfade_p2_test_kit.zip; kept in the repo, its site button is locked)
```
