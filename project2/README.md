# Project 2: SQL Database

info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh). Due **Nov 8, 2026 11:59 PM**.

Site: https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/project2/  
Brief: [`brief/info579_project02.pdf`](brief/info579_project02.pdf)

Restarted Nov 6, 2026. The earlier plan (to-do list, requirements tracker, `build_plan.py`, `build_impl.py` and a first `database_implementation.sql`) was removed from the tree; it is in the history at commit `adbef02`.

## Deliverables

| File | Task | Weight |
|---|---|---|
| `database_implementation.sql` | 1. Create the Project 1 tables and insert the Project 1 sample data | 25% |
| `single_table.sql` | 2. Single-table queries, one per non-associative table, covering (a) to (e) | 25% |
| `multiple_table.sql` | 3. INNER JOIN over an associative table, LEFT OUTER JOIN, set operation, multi-row subquery, WITH | 25% |
| `routines.sql` | 4. 2 procedures + 1 function, or 1 procedure + 2 functions | 25% |

Submitted as `project02_info579_group_1.zip`, built from `deliverables/` only.

Input data: the Project 1 sample data, `../project1/deliverables/data.xlsx`, also exported one CSV per table in `../project1/data_export/` (`python tools/export_p1_data.py` from the repo root).

## Layout

```
brief/                 the assignment brief (PDF)
data/deliverables.js   the four files and their requirements; read by the site
panels/                site panels: overview, one per file (file.html?f=<id>), brief
deliverables/          the four .sql files; the site marks a file "draft" once it is here
submission/            project02_info579_group_1.zip
```
