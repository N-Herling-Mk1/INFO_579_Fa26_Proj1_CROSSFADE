# Project 2: SQL Database

info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh). Due **Nov 8, 2026 11:59 PM**.

Site: https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/project2/  
Brief: [`brief/info579_project02.pdf`](brief/info579_project02.pdf)

Restarted Nov 6, 2026. The earlier plan (to-do list, requirements tracker, `build_plan.py`, `build_impl.py` and a first `database_implementation.sql`) was removed from the tree; it is in the history at commit `adbef02`.

## Deliverables

| File | Task | Weight | Status |
|---|---|---|---|
| `database_implementation.sql` | 1. Create the Project 1 tables and insert the Project 1 sample data | 25% | ready to test |
| `single_table.sql` | 2. Single-table queries, one per non-associative table, covering (a) to (e) | 25% | not started |
| `multiple_table.sql` | 3. INNER JOIN over an associative table, LEFT OUTER JOIN, set operation, multi-row subquery, WITH | 25% | not started |
| `routines.sql` | 4. 2 procedures + 1 function, or 1 procedure + 2 functions | 25% | not started |

Submitted as `project02_info579_group_1.zip`, built from `deliverables/` only.

Input data: the Project 1 sample data, `../project1/deliverables/data.xlsx`, also exported one CSV per table in `../project1/data_export/` (`python tools/export_p1_data.py` from the repo root).

## Task 1: database_implementation.sql

Hand-maintained; edit the `.sql` directly. Style follows the Unit 5 assignment (graded 100%) and the Unit 5 slides: a
`/* */` purpose comment before every statement, `CREATE TABLE IF NOT EXISTS crossfade.<table>`, every constraint named
(`pk_`, `fk_<child>_<parent>`, `uq_`, `ck_`), one multi-row `INSERT` with a column list per table. Types follow the
Project 1 data dictionary (fixed-length values as `CHAR`/`BINARY`, per the Unit 4 feedback).

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

## Layout

```
brief/                 the assignment brief (PDF)
data/deliverables.js   the four files and their requirements; read by the site
panels/                site panels: overview, one per file (file.html?f=<id>), brief
deliverables/          the four .sql files; the site shows a file once it is here
scripts/               check_implementation.py: QC for Task 1 (see above)
submission/            project02_info579_group_1.zip
```
