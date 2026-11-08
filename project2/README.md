# Project 2: SQL Database

info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh). Due **Nov 8, 2026 11:59 PM**.

Site: https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/project2/  
Brief: [`brief/info579_project02.pdf`](brief/info579_project02.pdf)

Restarted Nov 6, 2026. The earlier plan (to-do list, requirements tracker, `build_plan.py`, `build_impl.py` and a first `database_implementation.sql`) was removed from the tree; it is in the history at commit `adbef02`.

## Deliverables

| File | Task | Weight | Status |
|---|---|---|---|
| `database_implementation.sql` | 1. Create the Project 1 tables and insert the Project 1 sample data | 25% | ready to test |
| `single_table.sql` | 2. Single-table queries, one per non-associative table, covering (a) to (e) | 25% | ready to test (71 tests) |
| `multiple_table.sql` | 3. INNER JOIN over an associative table, LEFT OUTER JOIN, set operation, multi-row subquery, WITH | 25% | ready to test (80 tests) |
| `routines.sql` | 4. 2 procedures + 1 function, or 1 procedure + 2 functions | 25% | not started |

Submitted as `project02_info579_group_1.zip`, built from `deliverables/` only.

Input data: the Project 1 sample data, `../project1/deliverables/data.xlsx`, also exported one CSV per table in `../project1/data_export/` (`python tools/export_p1_data.py` from the repo root).

## Task 1: database_implementation.sql

Hand-maintained; edit the `.sql` directly. Style follows the Unit 5 assignment (graded 100%) and the Unit 5 slides: a
`/* */` purpose comment before every statement, `CREATE TABLE IF NOT EXISTS crossfade.<table>`, every constraint named
(`pk_`, `fk_<child>_<parent>`, `uq_`, `ck_`), one multi-row `INSERT` with a column list per table. Types follow the
Project 1 data dictionary (fixed-length values as `CHAR`/`BINARY`, per the Unit 4 feedback).

Each comment uses the same fields as the other three files: a tag (`[B#]` database, `[T#]` table definition, `[D#]`
data load) and the table, `Use cases:` (the use cases that read the table, from `data/use_cases.json`), `Business need:`
citing the RA, the design bullets, `Requirements:` and, for loads, `Rows:`.

Choices beyond the Project 1 DDL, each explained in the script:

- `ck_listener_email CHECK (email LIKE '%@%')`, the Unit 5 slide example.
- `ON DELETE CASCADE` on `genre_probability -> track_score` and `station_blend -> station` (parts of their parent);
  `ON DELETE SET NULL` on `play -> station` (the play stays in the royalty ledger). Everything else rejects the delete.
- CHECK names describe the rule (`ck_station_ambiguity_window`) instead of `ck_station_3`.

Tested on MySQL 8.0.46: runs twice in a row without error; all 401 rows match `data.xlsx`; index names match
`physical_data_model.png`; the CHECK, PK and FK constraints reject bad rows; integrity rules I1, I2, I3, I5, I7 hold.

```
python project2/scripts/check_implementation.py            # asks for the root password
python project2/scripts/check_implementation.py --mysql "C:/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe"
```

Runs the script twice, compares every row and column with `project1/data_export/csv/` (exported from and checked
against `data.xlsx`), checks the integrity rules, prints PASS or FAIL. Needs only the `mysql` client.

## Task 2: single_table.sql

Seven queries, S1 to S7: one per single-table use case (UC-01 to UC-06, UC-08, UC-10), so every non-associative table
is queried and track twice. Each comment carries a tag, its use cases, the business need it serves (citing the RA), a
business question, the brief requirements it meets ((a) S1 to S7, (b) S3 S4 S6 S7, (c) all, (d) S2 S5, (e) S1 S3 S6 S7)
and its output columns. Day counts use the fixed report date 2026-09-30, so results are reproducible.

The last statement, `[E1]`, is a write the database must refuse: it re-uploads an existing audio file, and MySQL must
refuse it with error 1062 on `uq_track_audio_checksum` (UC-15). It is kept **DISABLED** (inside its own block comment), so
the file runs clean from top to bottom; it is not a brief requirement. The tests still run it on its own.

Tests: `project2/tests/` (pytest + PyMySQL), 71 tests: contract, correctness against an independent Python oracle,
behaviour (rolled-back transactions), the expected error [E1] (which must stay disabled) and whole-file coverage. See
`project2/tests/README.md`.
`python project2/tests/build_kit.py` rebuilds the downloadable test kit.

```
pip install -r project2/tests/requirements.txt
$env:CROSSFADE_DB_PASSWORD = "your-root-password"
python -m pytest project2/tests
```

Starter kit: `tests/crossfade_p2_starter_kit.zip`, built by `python project2/scripts/build_starter.py`: the same
comments (the specification) with every statement removed, plus the tests and both input files. See the kit's README.

Both kits carry two PDFs from `python project2/scripts/build_docs.py`: `run_tests_locally.pdf` (every step) and
`use_case_reference.pdf` (each use case's tables, columns, input and expected output). Rebuild order after a change:
tests (`python -m pytest project2/tests`), `build_usecases.py`, `build_docs.py`, `build_vetting.py`, then `build_kit.py`
and `build_starter.py`.

## Task 3: multiple_table.sql

Seven queries, each answering use cases a single table cannot. M1 to M5 meet one Task 3 requirement each; M6 and M7
meet 3.1 and 3.5 again, because their questions need that shape:

| Query | Use cases | Requirement | Question |
|---|---|---|---|
| M1 | UC-13 | 3.1 play INNER JOIN listener, track | each listener's plays, completions, saves, skips and share of audio heard |
| M2 | UC-01, UC-14 | 3.2 artist LEFT OUTER JOIN track, play | what each artist is owed in the royalty run, artists with no plays included |
| M3 | UC-07 | 3.3 UNION | how many listeners each station reaches (creator UNION players), and which are shared |
| M4 | UC-11 | 3.4 IN (SELECT ... HAVING) | recordings the model versions place in different top genres |
| M5 | UC-12, UC-10 | 3.5 WITH | which recordings fill each station under the RA's four rules, and its running time |
| M6 | UC-09 | 3.1 track_score INNER JOIN track, scoring_model | released recordings whose newest result predates the model version now in service |
| M7 | UC-11 | 3.5 WITH over genre_probability | each result's runner-up genre, how close it is to the top genre, and segment variance |

Each comment carries the tag and title, use cases, business need (citing the RA), business question, the requirement,
`Tables:`, `One row per:` and `Output:`. M5's comment lists the RA rules it applies and why the result is ordered by blend
weight then entropy (the RA does not rank recordings). Tests: `test_multiple_table.py`, 80 tests;
`python project2/scripts/mutate_multiple_table.py` checks 39 deliberate mistakes are all caught. With M6 and M7, the
files written so far read all 59 columns of the physical model.

## Task 4: routines.sql (plan)

Error *handling* belongs here. UC-15's refusal already happens in the database ([E1] in `single_table.sql` shows the raw
1062); a routine shows the business answering it: an upload procedure with `DECLARE ... HANDLER FOR 1062` that catches
the duplicate and returns a message to the uploader instead of stopping, so no script halts and it counts toward Task 4.

## Layout

```
brief/                 the assignment brief (PDF)
data/deliverables.js   the four files and their requirements; read by the site
data/use_cases.json    use cases, their RA evidence and the columns they read (source)
data/usecases.js       generated by scripts/build_usecases.py; feeds the Use cases page
data/<file>_results.js written by the tests: last run's results, shown on the file and Use cases pages
panels/                site panels: overview, usecases, file.html?f=<id> (one per .sql), brief; shown by the site shell at #p2/<page>
deliverables/          the four .sql files; the site shows a file once it is here
tests/                 pytest suite for Tasks 2 to 4 + crossfade_p2_test_kit.zip (see tests/README.md)
scripts/               check_implementation.py: QC for Task 1 (see above)
                       build_usecases.py: RA LaTeX + use_cases.json -> data/usecases.js (checks every citation)
submission/            project02_info579_group_1.zip
```
