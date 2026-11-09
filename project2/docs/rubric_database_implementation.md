# Rubric: database_implementation.sql

INFO 579 Project 2, CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh).

Every condition in the assignment brief (info579_project02.pdf) that applies to this file, quoted word for word, and checked against the last test run of the file. Marks: **met** = claimed by the file and every test behind it passed; **NOT MET** = missing, not tested yet, or a test failed; **grader** = a judgement no test can decide. The same table is on the site: Project 2 > Rubric. Written by project2/scripts/build_rubric.py.

## Task 1 (25%): database_implementation.sql

Brief: "Develop the SQL statements to create the tables of your database and insert the sample data. You must present the statements in a single sql script named database_implementation.sql."

**4/4 requirements met** (last test run 2026-11-08 20:01:18: 228 passed, 0 failed)

| # | Requirement (quoted from the brief) | Met by | Evidence | Mark |
|---|---|---|---|---|
| 1a | "Develop the SQL statements to create the tables of your database"<br>*Every table, column, key, foreign key and constraint of the Project 1 physical model, checked against MySQL's catalogue.* | 10 tables | 41/41 schema tests | met |
| 1b | "and insert the sample data."<br>*Every row and every cell of the Project 1 sample data (data.csv), and every integrity rule it satisfies.* | 401 rows | 52/52 data tests | met |
| 1c | "You must present the statements in a single sql script named database_implementation.sql."<br>*The one script builds the database from nothing, and runs again cleanly.* | database_implementation.sql | 2/2 load tests (first run, second run) | met |
| 1d | "must be preceded by a comment explaining its purpose."<br>*From the brief's rule for every statement, query and routine.* | every statement | 1/1 comment test | met |

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
