# Rubric: single_table.sql

INFO 579 Project 2, CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh).

Every condition in the assignment brief (info579_project02.pdf) that applies to this file, quoted word for word, and checked against the last test run of the file. Marks: **met** = claimed by the file and every test behind it passed; **NOT MET** = missing, not tested yet, or a test failed; **grader** = a judgement no test can decide. The same table is on the site: Project 2 > Rubric. Written by project2/scripts/build_rubric.py.

## Task 2 (25%): single_table.sql

Brief: "Develop a variety of SQL queries following the requirements for single table queries. You must present the queries in a single sql script named single_table.sql."

**7/7 requirements met** (last test run 2026-11-08 20:01:18: 71 passed, 0 failed)

| # | Requirement (quoted from the brief) | Met by | Evidence | Mark |
|---|---|---|---|---|
| 2.1 | "Write queries to retrieve data from each non-associative table individually."<br>*One table per query; together they cover 6 non-associative tables: artist, track, genre, listener, scoring_model, station.* | S1 S2 S3 S4 S5 S6 S7 | 1/1 coverage test, 7/7 results match the oracle | met |
| 2.1.a | "At least one of the queries must use single row functions."<br>*Detected in the SQL itself, not just claimed in the comment.* | S1 S2 S3 S4 S5 S6 S7 | 49/49 tests of those queries | met |
| 2.1.b | "At least one of the queries must use aggregate functions."<br>*Detected in the SQL itself, not just claimed in the comment.* | S3 S4 S6 S7 | 28/28 tests of those queries | met |
| 2.1.c | "At least one of the queries must sort the results according to some criteria."<br>*Detected in the SQL itself, not just claimed in the comment.* | S1 S2 S3 S4 S5 S6 S7 | 49/49 tests of those queries | met |
| 2.1.d | "At least one of the queries must return just the first N results."<br>*Detected in the SQL itself, not just claimed in the comment.* | S2 S5 | 14/14 tests of those queries | met |
| 2.1.e | "At least one of the queries must use a selection control function."<br>*Detected in the SQL itself, not just claimed in the comment.* | S1 S3 S6 S7 | 28/28 tests of those queries | met |
| 2.2 | "must be preceded by a comment explaining its purpose."<br>*Use cases, business need, business question, requirements met and output columns.* | 7 queries | 7/7 comment tests | met |

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
