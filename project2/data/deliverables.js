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
      title: "Database implementation", weight: 25, state: "ready to test",
      summary: "Builds the Project 1 physical model as the MySQL database crossfade (10 tables, every key, " +
        "index and CHECK named) and loads the Project 1 sample data unchanged: 401 rows. " +
        "Drops and rebuilds the database, so it can be run any number of times.",
      test: [
        "Download the script with the button above.",
        "MySQL Workbench: File \u2192 Open SQL Script, then Execute (the lightning bolt). " +
          "Or from a terminal in the download folder (works in PowerShell too): " +
          "<code>mysql -u root -p -e \"source database_implementation.sql\"</code>",
        "Refresh the schema list: <code>crossfade</code> should hold 10 tables. " +
          "<code>SELECT COUNT(*) FROM crossfade.genre_probability;</code> returns 270.",
        "Python tests (228): <code>python -m pytest project2/tests/test_implementation.py</code>. They rebuild the database, check every " +
          "column, key and rule against the physical model, every cell against data.xlsx, and make each constraint refuse a bad write. " +
          "Files, coverage and what they could miss: <a href=\"../../index.html#p2/vet-implementation\">Vetting &amp; tests \u2192 database_implementation</a>.",
        "Without Python, from the repo root: <code>python project2/scripts/check_implementation.py</code> (the mysql client only). " +
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
      title: "Single-table queries", weight: 25, state: "ready to test",
      summary: "Seven queries, S1 to S7, one per question a single table answers: every non-associative table, " +
        "track twice. Each comment names its use cases, the business need it serves, the brief requirements it meets and its " +
        "output columns. The file ends with [E1], EXPECTED TO FAIL: a duplicate upload MySQL must refuse with error 1062 (UC-15). " +
        "67 tests check it against an independent Python answer computed from the Project 1 data. " +
        "The starter kit is the same file with every comment and no SQL, plus the tests and both input files.",
      results: "single_table_results.js",
      kit: "../tests/crossfade_p2_test_kit.zip", kitLocked: true,   // answer-key kit: stays in the repo, no download button
      starter: "../tests/crossfade_p2_starter_kit.zip",
      test: [
        "Download the starter kit (button above) and unzip it: tests, <code>data.csv</code> and <code>database_implementation.sql</code> are inside. " +
          "Install once: <code>pip install -r requirements.txt</code>",
        "Download <code>single_table.sql</code> (button above) and put it in the kit folder, replacing the blank one.",
        "Build the database: run <code>database_implementation.sql</code> in Workbench, or " +
          "<code>mysql -u root -p -e \"source database_implementation.sql\"</code>",
        "Run the tests (PowerShell): <code>$env:CROSSFADE_DB_PASSWORD = \"your-password\"</code> then " +
          "<code>python -m pytest test_single_table.py</code>. Expect 67 passed. Results land in <code>results/</code>.",
        "From a clone of the repo instead: <code>python -m pytest project2/tests/test_single_table.py</code> (it finds every file itself). " +
          "Files, coverage and what the tests could miss: <a href=\"../../index.html#p2/vet-single\">Vetting &amp; tests \u2192 single_table</a>."
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
      starter: "../tests/crossfade_p2_starter_kit.zip",
      test: [
        "Download the starter kit (button above) and unzip it: tests, <code>data.csv</code>, <code>use_cases.json</code> and " +
          "<code>database_implementation.sql</code> are inside. Install once: <code>pip install -r requirements.txt</code>",
        "Download <code>multiple_table.sql</code> (button above) and put it in the kit folder, replacing the blank one.",
        "Build the database: run <code>database_implementation.sql</code> in Workbench, or " +
          "<code>mysql -u root -p -e \"source database_implementation.sql\"</code>",
        "Run the tests (PowerShell): <code>$env:CROSSFADE_DB_PASSWORD = \"your-password\"</code> then " +
          "<code>python -m pytest test_multiple_table.py</code>. Expect 80 passed. Results land in <code>results/</code>.",
        "From a clone of the repo instead: <code>python -m pytest project2/tests/test_multiple_table.py</code>. " +
          "Files, coverage and what the tests could miss: <a href=\"../../index.html#p2/vet-multiple\">Vetting &amp; tests \u2192 multiple_table</a>."
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
      title: "Routines", weight: 25, state: "ready to test",
      summary: "One function and two procedures, the write path the business plan gives its two everyday events: " +
        "play_royalty (F1) works out what one play earns the artist (rule I7); record_play (P1) records a play, " +
        "computing completed and the royalty itself and refusing an invalid play with SIGNAL; upload_track (P2) adds " +
        "an upload as 'awaiting scoring' and answers a duplicate upload with a message, using a HANDLER for error 1062. " +
        "50 tests check each routine against MySQL's catalogue and an independent Python answer computed from the " +
        "Project 1 data.",
      test: [
        "Build the database: run <code>database_implementation.sql</code>, then <code>routines.sql</code> (Workbench, or " +
          "<code>mysql -u root -p -e \"source routines.sql\"</code>). Its Try it block calls each routine and rolls back.",
        "From a clone of the repo: <code>$env:CROSSFADE_DB_PASSWORD = \"your-password\"</code> then " +
          "<code>python -m pytest project2/tests/test_routines.py</code>. Expect 50 passed."
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
