# Project 2, Task 2: `single_table.sql` design (draft for review)

CROSSFADE, info579_group_1. Draft of Nov 6, 2026. Nothing here is final until we sign off on the decisions at the end.

> **Revision, Nov 8, 2026.** This draft is kept as the design record; `project2/deliverables/single_table.sql` is the
> final word. Three changes since it was written:
> - **S1** now reports each payment check in its own column (`licence_check`, `payment_country`) and a `run_status`
>   (ready/held), so an artist failing both checks shows both; the single first-failure CASE below hid Saltmarsh
>   Tapes' missing country. The hold rule is labelled business policy: the RA defines Verified and Country but does
>   not say they gate payment.
> - **S3** no longer flags a missing description (that IF never fired). It reports the composer layout the RA sizes:
>   which genre sets the label column width (longest name, from the data) and how much of each description's
>   80-character line is used, counted in characters.
> - **E1** is kept DISABLED (inside its own block comment) so the file runs clean; the tests still run it on its own.
> Edge cases S1-E1 and S3-E1 in §T5 below were replaced accordingly (see `project2/tests/test_single_table.py`).

## 1. What the brief asks for

> Write queries to retrieve data from each non-associative table individually.
> (a) single-row functions, (b) aggregate functions, (c) sort by some criteria,
> (d) return just the first N results, (e) a selection control function.
> Every query justified by the business plan and preceded by a comment. Avoid trivial and generic solutions.

**Non-associative tables.** The requirements analysis (RA, Overview → Entities) marks Track Score, Play, Station Blend
and Genre Probability as associative. That leaves **six** tables: `artist`, `track`, `genre`, `listener`,
`scoring_model`, `station`. The four associative tables are needed for Task 3 anyway (3.1 requires one).

**What the course counts for each feature** (lecture slides):

| Req | Course definition | Source |
|---|---|---|
| (a) single-row | string: CONCAT, LENGTH, SUBSTR, INSTR, TRIM, REPLACE, LPAD, RPAD, UPPER, LOWER; numeric: ABS, POW, SQRT, ROUND, TRUNCATE; date: DATE, TIME, EXTRACT, DATE_FORMAT, DATE_ADD, DATE_SUB, DATEDIFF, NOW, CURDATE | Unit 6 |
| (b) aggregate | COUNT, SUM, AVG, STD, MAX, MIN (with GROUP BY) | Unit 6 |
| (c) sort | ORDER BY | Unit 6 |
| (d) first N | LIMIT | Unit 6 |
| (e) selection control | **CASE, IF only.** IFNULL, COALESCE and NULLIF are a separate category, "NULL handling functions" | Unit 8, "Control Flow Functions" |

The last row matters: an IFNULL on its own would **not** satisfy (e).

## 2. Use cases from the Project 1 business design

The RA has no numbered use-case list, but it states what the database is for (Overview: the database "must manage the
artist roster and its catalogue, the versioned scoring models, the output each model produced…, listener accounts and the
stations they define, and a record of every play for… learning listener taste and paying artists"). Each attribute
description also says what the value is *used for*. Those statements become the use cases below. Every query in all
three Project 2 files is tagged with the use cases it serves, and the second heat map is built from those tags.

| ID | Use case | RA evidence | Tables |
|---|---|---|---|
| UC-01 | Pay each artist a per-stream royalty on qualifying plays | Artist entity; Payout Rate; Play.Royalty Amount; I7 | artist, play |
| UC-02 | Route payments: country sets payment channel and tax; only verified artists may license material | Country "used to determine which royalty payment channels and tax treatments apply"; Verified | artist |
| UC-03 | Surface new uploads as readily as hits | Overview: "a track uploaded an hour ago is as recommendable as one with a million plays" | track |
| UC-04 | Track the upload pipeline and reject duplicate uploads | Ingest Status; Audio Checksum "used to detect duplicate uploads"; I5 | track, track_score |
| UC-05 | Show listeners the genre legend while they compose a blend | Genre.Description "shown to listeners when they are composing a station blend"; Genre ID = model class index | genre |
| UC-06 | Bill subscribers by plan tier from their signup anniversary | Plan Tier "determines the monthly charge and the limits placed on station creation"; Signup Date "used to anchor the monthly billing cycle" | listener |
| UC-07 | Share stations under the creator's display name | Display Name; Play.Station ID (shared stations, I6) | listener, station, play |
| UC-08 | Decide how much weight each model version's output carries | Holdout Accuracy "used to decide how much weight its output carries"; Version Label "used in internal reporting" | scoring_model |
| UC-09 | Know which results predate a model redeployment | Scored On "used to establish which results predate a model redeployment and must be recomputed" | track_score, scoring_model |
| UC-10 | Define stations by blend and ambiguity window; measure how long stations stay in use | Station; Min/Max Ambiguity; Created On "used… to measure how long a station remains in use"; I1, I4 | station, station_blend |
| UC-11 | Place each recording between genres (full distribution, entropy, model disagreement) | Track Score, Genre Probability; I2, I3 | track_score, genre_probability, genre |
| UC-12 | Fill a station: recordings that match its blend and ambiguity window under its model | Station ("the service returns recordings that genuinely occupy that region") | station, station_blend, track_score, genre_probability |
| UC-13 | Learn listener taste from completions, saves and skips | Play: "the record from which listener taste is inferred"; Completed; Reaction | play, track |
| UC-14 | Keep an exact royalty ledger: no double-counted plays, rate snapshot at play time | Play key (Played At); Royalty Amount snapshot; I7 | play, artist, track |

Task 2 (single-table) covers UC-02, 03, 05, 06, 08 and 10. Tasks 3 and 4 take the multi-table ones (UC-01, 04, 07, 09, 11 to 14).

## 3. Proposed queries: six, one per non-associative table

Every feature appears at least twice, so a single disputed query cannot lose a requirement.

| ID | Table | Business question | Use cases | (a) | (b) | (c) | (d) | (e) |
|---|---|---|---|:-:|:-:|:-:|:-:|:-:|
| S1 | artist | Who can be paid in this royalty run, who is on hold, and why? | UC-01, UC-02 | ● | | ● | | ● |
| S2 | track | What goes on the "new uploads" shelf? (5 newest streamable recordings) | UC-03, UC-04 | ● | | ● | ● | |
| S3 | genre | Is every genre ready to show in the blend composer, in model class order? | UC-05 | ● | | ● | | ● |
| S4 | listener | What is the subscriber mix by plan tier, and how long has each tier been billing? | UC-06 | ● | ● | ● | | |
| S5 | scoring_model | Which three model versions should a new station default to? | UC-08 | ● | | ● | ● | |
| S6 | station | How many stations rely on each model version, and how adventurous are they? | UC-08, UC-10 | ● | ● | ● | | ● |
| | | | **count** | 6 | 2 | 6 | 2 | 3 |

Draft SQL, run against the loaded database (MySQL 8.0.46). Results are shown so we can judge them. Comments will be
written in the house style once the list is agreed. All dates are measured against a fixed report date,
`'2026-09-30'` (see decision D2).

### S1 artist: royalty payment run (UC-01, UC-02)

```sql
SELECT artist_id,
       CONCAT(stage_name, ' (', IFNULL(country, '--'), ')') AS payee,
       ROUND(payout_rate * 1000, 2) AS usd_per_1000_streams,
       DATEDIFF('2026-09-30', joined_date) AS days_under_licence,
       CASE
           WHEN verified = 0 THEN 'HOLD: identity not verified'
           WHEN country IS NULL THEN 'HOLD: no payment country'
           ELSE 'PAYABLE'
       END AS payment_status
FROM artist
ORDER BY payment_status DESC, payout_rate DESC, artist_id;
```
Result: 5 PAYABLE (Velvet Static 4.00 … Juno Fleet 3.00), then 3 on HOLD (Kestrel Ave, Tin Harbour, Saltmarsh Tapes).
**Finding:** the "no payment country" branch never fires on the sample data, because the only artist with no country
(Saltmarsh Tapes) is also unverified, and the first WHEN wins. The query is still right, but only an edge-case test can
prove that branch works (test S1-E1 below). Ordering by a status string relies on 'PAYABLE' > 'HOLD…'. A
`CASE`-based sort key would be more explicit (decision D4).

### S2 track: new-uploads shelf (UC-03, UC-04)

```sql
SELECT track_id, title,
       CONCAT(FLOOR(duration / 60), ':', LPAD(MOD(duration, 60), 2, '0')) AS length,
       release_date,
       DATEDIFF('2026-09-30', release_date) AS days_since_release
FROM track
WHERE ingest_status = 'scored'
ORDER BY release_date DESC, track_id
LIMIT 5;
```
Result: Afterimage Club (3:41), Plaza at Noon, Tapeworm Blues, Stahlwerk, Hymn for a Server Room. *Brine* (2026-09-21) is
the newest release but is still awaiting scoring, so it is correctly kept off the shelf. That is the WHERE clause doing
real work.

### S3 genre: blend-composer legend (UC-05)

```sql
SELECT genre_id AS model_class_index,
       UPPER(name) AS label,
       IFNULL(description, '(no description)') AS description,
       IF(description IS NULL, 'HIDE: no description for the composer', 'READY') AS composer_status
FROM genre
ORDER BY genre_id;
```
Result: 10 rows, all READY. Genre is a 10-row lookup table, so this is the query most at risk of looking trivial (G3).
Its justification: Description is the one optional column the RA says listeners see, and the IDs must stay in the
model's class order (Genre ID = output index). The IF branch only fires in the edge-case test.

### S4 listener: subscriber mix by plan tier (UC-06)

```sql
SELECT plan_tier,
       COUNT(*) AS listeners,
       MIN(signup_date) AS first_signup,
       MAX(signup_date) AS latest_signup,
       ROUND(AVG(DATEDIFF('2026-09-30', signup_date))) AS avg_days_subscribed
FROM listener
GROUP BY plan_tier
ORDER BY plan_tier DESC;
```
Result: premium 2 (avg 154 days), standard 3 (116), free 3 (104). `ORDER BY plan_tier DESC` sorts by the ENUM's
declared order (free < standard < premium), which is the revenue order, not alphabetical.

### S5 scoring_model: default model for new stations (UC-08)

```sql
SELECT version_label,
       CONCAT(fusion_type, ' / ', embedding_dimension, 'd / ', segment_length, 's') AS architecture,
       ROUND(holdout_accuracy * 100, 2) AS accuracy_pct,
       deployed_on
FROM scoring_model
ORDER BY holdout_accuracy DESC, deployed_on DESC
LIMIT 3;
```
Result: beardown_3sec 78.87%, beardown_rrm 76.00%, beardown_rrm_cfg17 76.00%. Two versions tie at 0.7600. The
`deployed_on DESC` tie-break makes the order deterministic and means "prefer the newer model", which the test pins down.

### S6 station: model reliance and adventurousness (UC-08, UC-10)

```sql
SELECT model_id,
       COUNT(*) AS stations,
       ROUND(AVG(maximum_ambiguity - minimum_ambiguity), 2) AS avg_window,
       SUM(CASE WHEN maximum_ambiguity - minimum_ambiguity > 0.5 THEN 1 ELSE 0 END) AS wide_stations,
       MIN(created_on) AS oldest_station
FROM station
GROUP BY model_id
ORDER BY stations DESC, model_id;
```
Result: model 4 → 3 stations (2 wide), model 2 → 2 (2), model 5 → 2 (1), model 1 → 1 (1). Model 3 serves no station
and does not appear. That is a fact a multi-table LEFT JOIN query (Task 3.2) can expose properly. "Wide" (> 0.5, i.e.
more than half the 0 to 1 ambiguity scale) is a reporting band we choose, not an RA rule (decision D3). The
subtraction is DECIMAL, so the threshold is exact.

## 4. Tests: `project2/tests/test_single_table.py`

### Principle

Each query is checked against an **independent oracle**: the same business question answered in plain Python from the
Project 1 CSVs (`project1/data_export/csv/`, exported from and checked against `data.xlsx`). The SQL and the oracle
share no code, so agreement means the SQL means what its comment says. No synthetic data: the oracle reads the graded
sample data. The edge-case tests add rows inside a transaction and roll them back.

### How the file is read

`single_table.sql` is split into blocks of *comment + statement*. Each comment starts with a tag, e.g. `[S1]`, and
contains `Use case: UC-01, UC-02`. The tests find queries by tag, so editing comments or reordering never breaks them.

### Test list (about 50 tests)

| Group | Per query (×6) or file-wide | What it proves |
|---|---|---|
| T1 structure | per query | preceded by a `/* */` comment carrying its tag, a business question and ≥1 use case; no `SELECT *` |
| T2 single table | per query | `EXPLAIN FORMAT=JSON` lists exactly one table, the declared one (catches hidden subqueries or joins) |
| T3 features | per query | the declared (a) to (e) features are really present, detected with the course's own function lists (§1) |
| T4 oracle | per query | result equals the Python oracle: same columns, same rows, same order, exact DECIMAL values |
| T5 edge cases | targeted | S1-E1 verified artist with NULL country → "HOLD: no payment country"; S2-E1 a new unscored track never reaches the shelf, S2-E2 two tracks on the same date are ordered by track_id, S2-E3 never more than 5 rows; S3-E1 NULL description → HIDE; S4-E1 a tier with no listeners is absent, not 0; S5-E1 ties resolved newest-first; S6-E1 a window of exactly 0.50 is not wide |
| T6 determinism | per query | two runs give identical results (every ORDER BY breaks its ties) |
| T7 file coverage | file-wide | every non-associative table has a query; every feature (a) to (e) appears ≥2 times; tags unique; every UC tag exists in the use-case table |
| T0 fixture | session | before anything else, a fresh `crossfade` is loaded from `database_implementation.sql` and its 401 rows are confirmed |

### How to run it

One-time setup:

```
pip install pytest pymysql
```

Each run, from the repo root (PowerShell):

```
$env:CROSSFADE_DB_PASSWORD = "your-root-password"
python -m pytest project2/tests -v
```

Optional variables: `CROSSFADE_DB_USER` (default `root`), `CROSSFADE_DB_HOST` (default `127.0.0.1`), `CROSSFADE_DB_PORT`
(default `3306`). PyMySQL is a pure-Python driver, so the tests do not need `mysql.exe` on the PATH. `pytest -v` prints one
line per test with a running percentage, and the run ends with a pass/fail summary.

A run also writes `project2/data/coverage.js`, which feeds the heat maps (§5). The site therefore always shows the
coverage of the last tested version.

Layout:

```
project2/tests/conftest.py            DB connection, fresh load of database_implementation.sql, SQL file parser
project2/tests/oracle.py              loads the CSVs; one function per query that answers it in Python
project2/tests/features.py            (a) to (e) detectors built from the course's function lists
project2/tests/use_cases.py           UC-01 to UC-14 (the table in §2), shared by all three task files
project2/tests/test_single_table.py   T1 to T7 for single_table.sql
project2/tests/test_multiple_table.py later
project2/tests/test_routines.py       later
```

## 5. Heat maps on the Project 2 site

Both maps are generated by the test run, so they cannot drift from the SQL.

**Map A: data coverage (table × column).** One row per table, one cell per column (all 10 tables, 59 columns). Cell
shade is the number of queries across all three task files that read the column; 0 is shown hollow. Each row ends with
**row coverage**: the share of the table's rows that contribute to at least one query result, computed by the oracle.
For Task 2 alone: artist 8/8, genre 10/10, listener 8/8, station 8/8, scoring_model 3/5 (LIMIT 3), track 5/15 (LIMIT 5).

**Map B: use cases × queries.** Rows UC-01 to UC-14, columns S1 to S6, then M1 to M5 and R1 to R3 as those tasks land.
A cell is filled where a query serves that use case. A last block of rows shows the brief's requirements ((a) to (e),
3.1 to 3.5, 4.x), so one picture answers both "is every business need served?" and "is every requirement met?".

## 6. Decisions to make before writing the final SQL and tests

| # | Question | Proposal |
|---|---|---|
| D1 | Six queries (non-associative tables only) or also track_score and play? | **Six.** It is the literal brief, and associative tables are Task 3 material. |
| D2 | Report date: fixed `'2026-09-30'` or `CURDATE()`? | **Fixed.** CURDATE makes every day-count change daily, so tests cannot pin results. 2026-09-30 is Q3 close, after the last sample event (Aug 29) and after the last release (Sep 22). |
| D3 | "Wide" station threshold in S6 | > 0.50 of the ambiguity scale, stated in the comment as a reporting band. |
| D4 | S1 sort by status string or an explicit CASE sort key? | Explicit `CASE` key (PAYABLE first). Clearer, and it uses (e) twice in one query. |
| D5 | Test driver | PyMySQL + pytest (`pip install pytest pymysql`). |
