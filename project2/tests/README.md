# CROSSFADE Project 2 tests

Unit tests for the Project 2 SQL files. Today: `single_table.sql`: 66 tests, including the expected-error case [E1] (UC-15). `multiple_table.sql` and
`routines.sql` get their own test files as they are written.

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
| row order and values | the oracle's rows: every `ORDER BY` must break its ties | `test_result_matches_oracle`, `test_result_is_deterministic` |
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

## Output

One line per test with a running percentage, then a pass/fail summary. Each run also writes a snapshot of
every query's result, its expected (oracle) result, every behaviour case's inputs and expected rows, and every test outcome: `project2/data/single_table_results.json` and `.js` in the
repo (the site shows them on the single_table page), or `results/` next to the tests in a kit folder.

## Files

Both kits also carry `run_tests_locally.pdf` (every step, and what each failure means) and `use_case_reference.pdf`
(each use case's tables, columns, input and expected output), built by `python project2/scripts/build_docs.py` from
`use_cases.json` and the last test run.

```
conftest.py            settings, file discovery, database check, .sql splitter, results snapshot
oracle.py              the independent Python answers, one per query
test_single_table.py   the tests
pytest.ini             -v by default
requirements.txt       pytest, pymysql, cryptography
build_kit.py           builds the answer-key test kit (crossfade_p2_test_kit.zip; kept in the repo, its site button is locked)
```
