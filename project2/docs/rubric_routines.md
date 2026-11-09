# Rubric: routines.sql

INFO 579 Project 2, CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh).

Every condition in the assignment brief (info579_project02.pdf) that applies to this file, quoted word for word, and checked against the last test run of the file. Marks: **met** = claimed by the file and every test behind it passed; **NOT MET** = missing, not tested yet, or a test failed; **grader** = a judgement no test can decide. The same table is on the site: Project 2 > Rubric. Written by project2/scripts/build_rubric.py.

## Task 4 (25%): routines.sql

Brief: "Implement 2 procedures and 1 function or 1 procedure and 2 functions that make use of the data in your database. The 3 routines must be presented in a single sq file named routines.sql."

**4/4 requirements met** (last test run 2026-11-08 20:01:18: 50 passed, 0 failed)

| # | Requirement (quoted from the brief) | Met by | Evidence | Mark |
|---|---|---|---|---|
| 4.1 | "Implement 2 procedures and 1 function or 1 procedure and 2 functions"<br>*2 procedures and 1 function, as MySQL's catalogue holds them.* | F1 play_royalty P1 record_play P2 upload_track | 1/1 mix test, 3/3 catalogue tests | met |
| 4.2 | "that make use of the data in your database."<br>*Each routine reads or writes the CROSSFADE tables, and is run against them.* | track artist play | 3/3 table tests, 24/24 behaviour cases | met |
| 4.3 | "The 3 routines must be presented in a single sq file named routines.sql."<br>*The one script re-creates all three, and can be run again.* | routines.sql | 1/1 script test | met |
| 4.4 | "must be preceded by a comment explaining its purpose."<br>*Use cases, business need, what it does, Unit 9 features, tables, parameters, errors, example.* | 3 routines | 3/3 comment tests | met |

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
