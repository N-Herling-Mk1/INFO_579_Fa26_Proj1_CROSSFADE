# Rubric: multiple_table.sql

INFO 579 Project 2, CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh).

Every condition in the assignment brief (info579_project02.pdf) that applies to this file, quoted word for word, and checked against the last test run of the file. Marks: **met** = claimed by the file and every test behind it passed; **NOT MET** = missing, not tested yet, or a test failed; **grader** = a judgement no test can decide. The same table is on the site: Project 2 > Rubric. Written by project2/scripts/build_rubric.py.

## Task 3 (25%): multiple_table.sql

Brief: "Develop a variety of SQL queries following the requirements for multiple table queries. You must present the queries in a single sql script named multiple_table.sql."

**7/7 requirements met** (last test run 2026-11-08 20:01:18: 80 passed, 0 failed)

| # | Requirement (quoted from the brief) | Met by | Evidence | Mark |
|---|---|---|---|---|
| 3.1 | "Write a query involving an associative table and two other related tables. You must use the INNER JOIN to connect with all three tables."<br>*Found in the SQL: play joined to listener, track; track_score joined to scoring_model, track.* | M1 M6 | 16/16 tests of M1, M6 | met |
| 3.2 | "Write a query including two or more tables and using the LEFT OUTER JOIN."<br>*Found in the SQL: LEFT OUTER JOIN.* | M2 | 8/8 tests of M2 | met |
| 3.3 | "Write a query including some kind of set operation."<br>*Found in the SQL: UNION.* | M3 | 8/8 tests of M3 | met |
| 3.4 | "Write a query including a subquery and some multi-row operation."<br>*Found in the SQL: IN (SELECT ...).* | M4 | 8/8 tests of M4 | met |
| 3.5 | "Write a query including a derived table using the WITH statement."<br>*Found in the SQL: WITH; WITH.* | M5 M7 | 16/16 tests of M5, M7 | met |
| 3.6 | "must be preceded by a comment explaining its purpose."<br>*Use cases, business need, business question, requirement, tables, one row per, output columns.* | 7 queries | 7/7 comment tests | met |
| 3.7 | "Every join names its type (course rule, Unit 9)."<br>*Not in the brief: the course marks bare JOIN and comma joins wrong.* | 7 queries | 7/7 join-type tests | met |

## Every file

Brief: "Every statement, query and routine should be justified within the logic of your business plan and must be preceded by a comment explaining its purpose. Avoid trivial and generic solutions."

**3/3 requirements met**

| # | Requirement (quoted from the brief) | Met by | Evidence | Mark |
|---|---|---|---|---|
| G1 | "Every statement, query and routine should be justified within the logic of your business plan"<br>*Each names the use cases it answers (quoted from the requirements analysis) and the business need behind it; the columns it reads are the ones those use cases need.* | use cases | 18/18 comment tests, 17/17 column tests | met |
| G2 | "and must be preceded by a comment explaining its purpose." | all four files | 18/18 comment tests | met |
| G3 | "Avoid trivial and generic solutions."<br>*No test can judge this. What the tests do show: no SELECT *, every query answers a stated business question, and every result is checked against an independent answer.* | - | 14/14 no-SELECT-* tests | grader |
| G4 | "Compress all the deliverables into a single zip file."<br>*The file name must follow the format: project02_groupcode.zip* | project02_info579_group_1.zip | in project2/deliverables/ | met |
| G5 | "Upload the file to the assignment of project 1 Dropbox in D2L."<br>*Quoted as written (the brief says project 1); done by hand, by the due date. Late submission will receive at most 70% of the maximum grade.* | D2L |  | grader |
