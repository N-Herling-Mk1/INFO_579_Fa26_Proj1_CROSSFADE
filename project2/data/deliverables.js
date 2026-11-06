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
      title: "Database implementation", weight: 25,
      reqs: [
        "SQL statements that create the tables of the Project 1 design.",
        "SQL statements that insert the sample data provided in Project 1.",
        "Both in a single script named database_implementation.sql."
      ]
    },
    {
      id: "single", task: "Task 2", file: "single_table.sql",
      title: "Single-table queries", weight: 25,
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
      title: "Multiple-table queries", weight: 25,
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
      title: "Routines", weight: 25,
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
