/* Project 2 deliverables: the four graded .sql files, from brief/info579_project02.pdf.
   Read by project2/index.html, project2/panels/*.html and the front page.
   A file counts as present when project2/deliverables/<file> exists. */
window.P2 = {
  due: "Nov 8, 2026 11:59 PM",
  zip: "project02_info579_group_1.zip",
  general: [
    "Every statement, query and routine is justified within the logic of the business plan.",
    "Every statement, query and routine is preceded by a comment explaining its purpose.",
    "Avoid trivial and generic solutions.",
    "All deliverables compressed into one zip, project02_groupcode.zip, uploaded to the D2L Dropbox.",
    "Late submission receives at most 70% of the maximum grade."
  ],
  files: [
    {
      id: "implementation", task: "Task 1", file: "database_implementation.sql",
      bundle: "../tests/crossfade_impl_tests.zip",   // the file, its tests and inputs, its rubric, the use case reference
      title: "Database implementation", weight: 25, state: "ready to test",
      summary: "Builds the Project 1 physical model as the MySQL database crossfade (10 tables, every key, " +
        "index and CHECK named) and loads the Project 1 sample data unchanged: 401 rows. Each statement's comment is tagged " +
        "[B#], [T#] or [D#] and names the use cases that read its table. " +
        "Drops and rebuilds the database, so it can be run any number of times.",
      test: [
        "Download <code>crossfade_impl_tests.zip</code> with the first button above (the second gets <code>database_implementation.sql</code> alone) and unzip it. One folder, <code>crossfade_impl_tests</code>, holds <code>database_implementation.sql</code>, its tests, <code>data.csv</code> (the Project 1 sample data), its rubric (<code>rubric_database_implementation.md</code>) and the use case descriptions (<code>use_case_reference.pdf</code>). Extract it first: Python cannot run files from inside a zip.",
        "Set up Python once, in that folder: <code>python -m venv .venv</code> then <code>.venv\\Scripts\\python -m pip install -r requirements.txt</code> (macOS / Linux: <code>.venv/bin/python</code>). You also need a running MySQL Server 8.0.16 or later and its root password.",
        "Run the tests (PowerShell): <code>$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"</code> then <code>.venv\\Scripts\\python -m pytest</code>. Expect 228 passed. The tests drop and rebuild the <code>crossfade</code> database from the script (twice) and leave it loaded.",
        "By hand instead: MySQL Workbench, File → Open SQL Script, then Execute (the lightning bolt), or <code>mysql -u root -p -e \"source database_implementation.sql\"</code>. <code>crossfade</code> should hold 10 tables; <code>SELECT COUNT(*) FROM crossfade.genre_probability;</code> returns 270.",
        "Files, coverage and what the tests could miss: <a href=\"../../index.html#p2/vet-implementation\">Vetting &amp; tests → database_implementation</a>.",
        "Without Python, from a clone of the repo: <code>python project2/scripts/check_implementation.py</code> (the mysql client only). " +
          "It runs the script twice, compares all 401 rows with data.xlsx and checks integrity rules I1, I2, I3, I5 and I7; it ends with PASS."
      ],
      reqs: [
        "SQL statements that create the tables of the Project 1 design.",
        "SQL statements that insert the sample data provided in Project 1.",
        "Both in a single script named database_implementation.sql."
      ]
    },
    {
      id: "single", task: "Task 2", file: "single_table.sql",
      bundle: "../tests/crossfade_single_tests.zip",   // the file, its tests and inputs, its rubric, the use case reference
      title: "Single-table queries", weight: 25, state: "ready to test",
      summary: "Seven queries, S1 to S7, one per question a single table answers: every non-associative table, " +
        "track twice. Each comment names its use cases, the business need it serves, the brief requirements it meets and its " +
        "output columns. The file ends with [E1], kept disabled so the file runs clean: a duplicate upload MySQL must refuse " +
        "with error 1062 (UC-15). 71 tests check it against an independent Python answer computed from the Project 1 data.",
      results: "single_table_results.js",
      test: [
        "Download <code>crossfade_single_tests.zip</code> with the first button above (the second gets <code>single_table.sql</code> alone) and unzip it. One folder, <code>crossfade_single_tests</code>, holds <code>single_table.sql</code>, its tests, <code>database_implementation.sql</code>, <code>data.csv</code>, <code>use_cases.json</code>, its rubric (<code>rubric_single_table.md</code>) and the use case descriptions (<code>use_case_reference.pdf</code>). Extract it first: Python cannot run files from inside a zip.",
        "Set up Python once, in that folder: <code>python -m venv .venv</code> then <code>.venv\\Scripts\\python -m pip install -r requirements.txt</code> (macOS / Linux: <code>.venv/bin/python</code>). You also need a running MySQL Server 8.0.16 or later and its root password.",
        "Run the tests (PowerShell): <code>$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"</code> then <code>.venv\\Scripts\\python -m pytest --fresh</code>. Expect 71 passed. <code>--fresh</code> builds the <code>crossfade</code> database from <code>database_implementation.sql</code> first; every write a test makes is rolled back.",
        "From a clone of the repo instead: <code>python -m pytest project2/tests/test_single_table.py</code> (it finds every file itself). Files, coverage and what the tests could miss: <a href=\"../../index.html#p2/vet-single\">Vetting &amp; tests → single_table</a>."
      ],
      reqs: [
        "Queries that retrieve data from each non-associative table individually.",
        "(a) At least one query uses single-row functions.",
        "(b) At least one query uses aggregate functions.",
        "(c) At least one query sorts the results by some criteria.",
        "(d) At least one query returns just the first N results.",
        "(e) At least one query uses a selection control function."
      ]
    },
    {
      id: "multiple", task: "Task 3", file: "multiple_table.sql",
      bundle: "../tests/crossfade_multiple_tests.zip",   // the file, its tests and inputs, its rubric, the use case reference
      title: "Multiple-table queries", weight: 25, state: "ready to test",
      summary: "Seven queries, M1 to M7, each answering business questions a single table " +
        "cannot: listener taste (UC-13, INNER JOIN through play), the royalty run (UC-01, UC-14, LEFT OUTER JOIN), " +
        "station reach (UC-07, UNION), recordings the models disagree on (UC-11, IN subquery) and filling each station " +
        "under the business plan's four rules (UC-12, UC-10, WITH). Each comment names its use cases, business need, the " +
        "requirement it meets, the tables it reads, what one result row is and its output columns. " +
        "M6 lists recordings whose newest result predates the model version now in service (UC-09, INNER JOIN through " +
        "track_score); M7 reads each result's full genre distribution for its runner-up genre (UC-11, WITH). " +
        "80 tests check it against an independent Python answer computed from the Project 1 data.",
      results: "multiple_table_results.js", resultsVar: "P2_MULTIPLE",
      test: [
        "Download <code>crossfade_multiple_tests.zip</code> with the first button above (the second gets <code>multiple_table.sql</code> alone) and unzip it. One folder, <code>crossfade_multiple_tests</code>, holds <code>multiple_table.sql</code>, its tests, <code>database_implementation.sql</code>, <code>data.csv</code>, <code>use_cases.json</code>, its rubric (<code>rubric_multiple_table.md</code>) and the use case descriptions (<code>use_case_reference.pdf</code>). Extract it first: Python cannot run files from inside a zip.",
        "Set up Python once, in that folder: <code>python -m venv .venv</code> then <code>.venv\\Scripts\\python -m pip install -r requirements.txt</code> (macOS / Linux: <code>.venv/bin/python</code>). You also need a running MySQL Server 8.0.16 or later and its root password.",
        "Run the tests (PowerShell): <code>$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"</code> then <code>.venv\\Scripts\\python -m pytest --fresh</code>. Expect 80 passed. <code>--fresh</code> builds the <code>crossfade</code> database from <code>database_implementation.sql</code> first; every write a test makes is rolled back.",
        "From a clone of the repo instead: <code>python -m pytest project2/tests/test_multiple_table.py</code>. Files, coverage and what the tests could miss: <a href=\"../../index.html#p2/vet-multiple\">Vetting &amp; tests → multiple_table</a>."
      ],
      reqs: [
        "(1) An associative table and two other related tables, all three connected with INNER JOIN.",
        "(2) Two or more tables using LEFT OUTER JOIN.",
        "(3) Some kind of set operation.",
        "(4) A subquery and some multi-row operation.",
        "(5) A derived table using the WITH statement."
      ]
    },
    {
      id: "routines", task: "Task 4", file: "routines.sql",
      bundle: "../tests/crossfade_routines_tests.zip",   // the file, its tests and inputs, its rubric, the use case reference
      title: "Routines", weight: 25, state: "ready to test",
      summary: "One function and two procedures, the write path the business plan gives its two everyday events: " +
        "play_royalty (F1) works out what one play earns the artist (rule I7); record_play (P1) records a play, " +
        "computing completed and the royalty itself and refusing an invalid play with SIGNAL; upload_track (P2) adds " +
        "an upload as 'awaiting scoring' and answers a duplicate upload with a message, using a HANDLER for error 1062. " +
        "50 tests check each routine against MySQL's catalogue and an independent Python answer computed from the " +
        "Project 1 data.",
      test: [
        "Download <code>crossfade_routines_tests.zip</code> with the first button above (the second gets <code>routines.sql</code> alone) and unzip it. One folder, <code>crossfade_routines_tests</code>, holds <code>routines.sql</code>, its tests, <code>database_implementation.sql</code>, <code>data.csv</code>, <code>use_cases.json</code> and <code>routines_example_usage.sql</code> (example usage, not a deliverable), its rubric (<code>rubric_routines.md</code>) and the use case descriptions (<code>use_case_reference.pdf</code>). Extract it first: Python cannot run files from inside a zip.",
        "Set up Python once, in that folder: <code>python -m venv .venv</code> then <code>.venv\\Scripts\\python -m pip install -r requirements.txt</code> (macOS / Linux: <code>.venv/bin/python</code>). You also need a running MySQL Server 8.0.16 or later and its root password.",
        "Run the tests (PowerShell): <code>$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"</code> then <code>.venv\\Scripts\\python -m pytest --fresh</code>. Expect 50 passed. <code>--fresh</code> builds the <code>crossfade</code> database from <code>database_implementation.sql</code> first; every write a test makes is rolled back.",
        "By hand: run <code>database_implementation.sql</code>, then <code>routines.sql</code>, then <code>routines_example_usage.sql</code> to see each routine called on the sample data (it rolls back). Files, coverage and what the tests could miss: <a href=\"../../index.html#p2/vet-routines\">Vetting &amp; tests → routines</a>."
      ],
      reqs: [
        "2 procedures and 1 function, or 1 procedure and 2 functions.",
        "Each makes use of the data in the database.",
        "All three routines in a single file named routines.sql."
      ]
    }
  ]
};

/* present(base, cb): cb(file, true|false) for each deliverable, base = path to project2/ */
window.P2.present = function (base, cb) {
  window.P2.files.forEach(function (f) {
    fetch(base + "deliverables/" + f.file, { method: "HEAD", cache: "no-store" })
      .then(function (r) { cb(f, r.ok); })
      .catch(function () { cb(f, false); });
  });
};
