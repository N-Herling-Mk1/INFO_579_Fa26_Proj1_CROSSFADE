/* Written by project2/scripts/build_vetting.py from the tests and their last runs. Do not edit. */
window.P2_VET = {
 "implementation": {
  "file": "database_implementation.sql",
  "task": "Task 1",
  "status": "tested",
  "title": "Creating the database and its tables",
  "lede": "How database_implementation.sql is checked: the script is run twice, then the database it leaves behind is compared with the Project 1 physical model, the requirements analysis and the sample data, and every key and rule is made to refuse a bad write.",
  "results": "implementation_results.js",
  "resultsVar": "P2_IMPL",
  "pdf": "test_implementation_guide.pdf",
  "pdfTitle": "Testing database_implementation.sql locally",
  "mutator": "mutate_implementation.py",
  "flowTo": "<b>the crossfade database</b> that <code>database_implementation.sql</code> builds (run twice)",
  "files": [
   {
    "file": "database_implementation.sql",
    "role": "the file under test (Task 1)",
    "href": "../deliverables/database_implementation.sql"
   },
   {
    "file": "test_implementation.py",
    "role": "the tests: the spec typed from the physical model, the value rules, all five groups",
    "href": "../tests/test_implementation.py"
   },
   {
    "file": "conftest.py",
    "role": "shared set-up: finds the files, connects to MySQL, splits the script into statements, writes the results snapshot",
    "href": "../tests/conftest.py"
   },
   {
    "file": "data.csv",
    "role": "the Project 1 sample data, exported cell for cell from the graded data.xlsx: the expected rows",
    "href": "../../project1/data_export/data.csv"
   },
   {
    "file": "pytest.ini",
    "role": "pytest settings (verbose, no cache folder)",
    "href": "../tests/pytest.ini"
   },
   {
    "file": "requirements.txt",
    "role": "pytest, PyMySQL, cryptography (MySQL 8 sign-in)",
    "href": "../tests/requirements.txt"
   },
   {
    "file": "test_implementation_guide.pdf",
    "role": "how to run the tests locally, what they cover and what they could miss",
    "href": "../docs/test_implementation_guide.pdf"
   },
   {
    "file": "check_implementation.py",
    "role": "the no-Python-driver check: the mysql client only (runs the script twice, compares every row, checks the integrity rules)",
    "href": "../scripts/check_implementation.py"
   },
   {
    "file": "mutate_implementation.py",
    "role": "tests the tests: breaks the script 19 ways, one at a time, and checks every break is caught (repo only)",
    "href": "../scripts/mutate_implementation.py"
   }
  ],
  "bundle": {
   "file": "crossfade_impl_tests.zip",
   "role": "the tests, both input files and the guide, in one folder that runs as-is",
   "href": "../tests/crossfade_impl_tests.zip",
   "bytes": 163514,
   "contents": [
    "test_implementation.py",
    "conftest.py",
    "pytest.ini",
    "requirements.txt",
    "database_implementation.sql",
    "data.csv",
    "test_implementation_guide.pdf",
    "rubric_database_implementation.md",
    "use_case_reference.pdf",
    "README.txt"
   ]
  },
  "sources": [
   {
    "name": "Physical model",
    "from": "physical_data_model.png (Project 1)",
    "how": "Typed by hand into SPEC in test_implementation.py: tables, columns in order, types and sizes, NULL / NOT NULL, keys, the 13 relationship lines, the uq_ indexes. ENUM values and UNSIGNED flags come from the data dictionary, because the diagram abbreviates them. Never read from the .sql file."
   },
   {
    "name": "Value rules",
    "from": "requirements_analysis.pdf (Project 1)",
    "how": "Each CHECK is listed with a value it must refuse and where the rule comes from. Where the analysis is silent (payout rate positive, email has an @), the rule is the one the script's own comment states, and is marked as such."
   },
   {
    "name": "Sample data",
    "from": "data.xlsx → data.csv (Project 1)",
    "how": "The graded workbook, exported cell for cell and checked against itself by tools/export_p1_data.py. Rows are matched by primary key; numbers compared as exact decimals."
   }
  ],
  "groups": [
   {
    "group": "load",
    "tests": 6,
    "passed": 6,
    "text": "The script runs start to finish, and again on top of itself (re-runnable). No warnings: MySQL warns when it silently rounds or trims a value, so a clean load means every value went in as written. A purpose comment before every statement (the brief). Checks are never switched off. Each table created once and loaded after its parents."
   },
   {
    "group": "schema",
    "tests": 41,
    "passed": 41,
    "text": "Exactly the ten tables. Every column in the diagram's order with its exact type, size, UNSIGNED flag and NULL / NOT NULL. Primary keys, composite on the four associative tables. All 13 foreign keys: columns, parent, name and ON DELETE rule. The five unique keys. Constraint names follow fk_ / uq_ / ck_."
   },
   {
    "group": "read",
    "tests": 10,
    "passed": 10,
    "text": "One live SELECT per table: the columns come back in order and every value has the right Python type (Decimal, never float; dates as dates; the checksum as 32 bytes; BIT as one byte)."
   },
   {
    "group": "data",
    "tests": 42,
    "passed": 42,
    "text": "Every table has the row count and every cell of data.csv (the Project 1 data.xlsx). The nine cross-row integrity checks from the requirements analysis hold. No child row points at a missing parent."
   },
   {
    "group": "enforce",
    "tests": 129,
    "passed": 129,
    "text": "Inside a transaction that is always rolled back: a valid new row is accepted, then one bad write per rule is refused with the exact MySQL error and constraint name. Duplicate keys (1062), orphans (1452), NULLs (1048), CHECKs (3819), type limits (1406, 1264, 1265, 1292), and the ON DELETE behaviours (CASCADE, SET NULL, refused with 1451)."
   }
  ],
  "coverage": {
   "columns": [
    {
     "key": "columns",
     "label": "Columns & types"
    },
    {
     "key": "pk",
     "label": "Primary key"
    },
    {
     "key": "fk",
     "label": "Foreign keys"
    },
    {
     "key": "uq",
     "label": "Unique keys"
    },
    {
     "key": "read",
     "label": "Live read"
    },
    {
     "key": "rows",
     "label": "Row count"
    },
    {
     "key": "cells",
     "label": "Every cell"
    },
    {
     "key": "rules",
     "label": "Integrity rules"
    },
    {
     "key": "orphans",
     "label": "No orphans"
    },
    {
     "key": "valid",
     "label": "Valid row accepted"
    },
    {
     "key": "dup",
     "label": "Duplicate refused"
    },
    {
     "key": "orphan_ins",
     "label": "Orphan refused"
    },
    {
     "key": "nulls",
     "label": "NULL rules"
    },
    {
     "key": "checks",
     "label": "CHECKs"
    },
    {
     "key": "types",
     "label": "Type limits"
    },
    {
     "key": "delete",
     "label": "ON DELETE"
    }
   ],
   "rows": [
    {
     "key": "genre",
     "label": "genre",
     "sub": ""
    },
    {
     "key": "artist",
     "label": "artist",
     "sub": ""
    },
    {
     "key": "listener",
     "label": "listener",
     "sub": ""
    },
    {
     "key": "scoring_model",
     "label": "scoring_model",
     "sub": ""
    },
    {
     "key": "track",
     "label": "track",
     "sub": ""
    },
    {
     "key": "station",
     "label": "station",
     "sub": ""
    },
    {
     "key": "track_score",
     "label": "track_score",
     "sub": "assoc."
    },
    {
     "key": "genre_probability",
     "label": "genre_probability",
     "sub": "assoc."
    },
    {
     "key": "station_blend",
     "label": "station_blend",
     "sub": "assoc."
    },
    {
     "key": "play",
     "label": "play",
     "sub": "assoc."
    }
   ],
   "cells": {
    "genre": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      0,
      0
     ],
     "uq": [
      1,
      1
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      0,
      0
     ],
     "orphans": [
      0,
      0
     ],
     "valid": [
      0,
      0
     ],
     "dup": [
      2,
      2
     ],
     "orphan_ins": [
      0,
      0
     ],
     "nulls": [
      3,
      3
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      0,
      0
     ],
     "delete": [
      1,
      1
     ]
    },
    "artist": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      0,
      0
     ],
     "uq": [
      1,
      1
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      2,
      2
     ],
     "orphans": [
      0,
      0
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      2,
      2
     ],
     "orphan_ins": [
      0,
      0
     ],
     "nulls": [
      6,
      6
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      4,
      4
     ],
     "delete": [
      1,
      1
     ]
    },
    "listener": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      0,
      0
     ],
     "uq": [
      1,
      1
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      0,
      0
     ],
     "orphans": [
      0,
      0
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      2,
      2
     ],
     "orphan_ins": [
      0,
      0
     ],
     "nulls": [
      5,
      5
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      1,
      1
     ],
     "delete": [
      1,
      1
     ]
    },
    "scoring_model": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      0,
      0
     ],
     "uq": [
      1,
      1
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      0,
      0
     ],
     "orphans": [
      0,
      0
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      2,
      2
     ],
     "orphan_ins": [
      0,
      0
     ],
     "nulls": [
      8,
      8
     ],
     "checks": [
      3,
      3
     ],
     "types": [
      0,
      0
     ],
     "delete": [
      0,
      0
     ]
    },
    "track": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      1,
      1
     ],
     "uq": [
      1,
      1
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      3,
      3
     ],
     "orphans": [
      1,
      1
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      2,
      2
     ],
     "orphan_ins": [
      1,
      1
     ],
     "nulls": [
      7,
      7
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      3,
      3
     ],
     "delete": [
      1,
      1
     ]
    },
    "station": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      2,
      2
     ],
     "uq": [
      0,
      0
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      3,
      3
     ],
     "orphans": [
      2,
      2
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      1,
      1
     ],
     "orphan_ins": [
      2,
      2
     ],
     "nulls": [
      7,
      7
     ],
     "checks": [
      3,
      3
     ],
     "types": [
      0,
      0
     ],
     "delete": [
      1,
      1
     ]
    },
    "track_score": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      3,
      3
     ],
     "uq": [
      0,
      0
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      3,
      3
     ],
     "orphans": [
      3,
      3
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      1,
      1
     ],
     "orphan_ins": [
      3,
      3
     ],
     "nulls": [
      8,
      8
     ],
     "checks": [
      4,
      4
     ],
     "types": [
      0,
      0
     ],
     "delete": [
      1,
      1
     ]
    },
    "genre_probability": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      2,
      2
     ],
     "uq": [
      0,
      0
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      3,
      3
     ],
     "orphans": [
      2,
      2
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      1,
      1
     ],
     "orphan_ins": [
      2,
      2
     ],
     "nulls": [
      4,
      4
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      0,
      0
     ],
     "delete": [
      1,
      1
     ]
    },
    "station_blend": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      2,
      2
     ],
     "uq": [
      0,
      0
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      2,
      2
     ],
     "orphans": [
      2,
      2
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      1,
      1
     ],
     "orphan_ins": [
      2,
      2
     ],
     "nulls": [
      3,
      3
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      0,
      0
     ],
     "delete": [
      1,
      1
     ]
    },
    "play": {
     "columns": [
      1,
      1
     ],
     "pk": [
      1,
      1
     ],
     "fk": [
      3,
      3
     ],
     "uq": [
      0,
      0
     ],
     "read": [
      1,
      1
     ],
     "rows": [
      1,
      1
     ],
     "cells": [
      1,
      1
     ],
     "rules": [
      2,
      2
     ],
     "orphans": [
      3,
      3
     ],
     "valid": [
      1,
      1
     ],
     "dup": [
      1,
      1
     ],
     "orphan_ins": [
      3,
      3
     ],
     "nulls": [
      8,
      8
     ],
     "checks": [
      1,
      1
     ],
     "types": [
      1,
      1
     ],
     "delete": [
      1,
      1
     ]
    }
   },
   "whole": [
    {
     "test": "test_load_first_run",
     "outcome": "passed"
    },
    {
     "test": "test_load_second_run",
     "outcome": "passed"
    },
    {
     "test": "test_load_no_warnings",
     "outcome": "passed"
    },
    {
     "test": "test_load_every_statement_commented",
     "outcome": "passed"
    },
    {
     "test": "test_load_never_switches_checks_off",
     "outcome": "passed"
    },
    {
     "test": "test_load_inventory",
     "outcome": "passed"
    },
    {
     "test": "test_schema_tables",
     "outcome": "passed"
    },
    {
     "test": "test_schema_no_extra_foreign_keys",
     "outcome": "passed"
    },
    {
     "test": "test_schema_constraint_names",
     "outcome": "passed"
    },
    {
     "test": "test_enforce_rollback_leaves_data",
     "outcome": "passed"
    }
   ],
   "caption": "tests per table and check"
  },
  "misses": [
   {
    "title": "A mistake in the physical model itself",
    "what": "The schema tests prove the database matches physical_data_model.png, not that the model is the best design. If the diagram has a poor type choice, the script and the tests agree with it.",
    "cover": "The model was graded in Project 1; type choices are argued column by column in the data dictionary."
   },
   {
    "title": "A mistake shared by the requirements analysis and the script",
    "what": "ENUM values and UNSIGNED flags are taken from the data dictionary (built from the analysis), because the diagram abbreviates them. If the analysis is wrong there, so is the spec.",
    "cover": "check_consistency.py cross-checks the analysis, data.xlsx and the dictionary column by column."
   },
   {
    "title": "Wrong sample data that was handed in wrong",
    "what": "The data tests prove the database holds exactly data.xlsx. A value that was wrong in the graded workbook passes. Known case: scoring_model 2 (beardown_rrm_cfg12) is recorded as concat; its model files say gated.",
    "cover": "Listed on the History page under Known discrepancies; the brief requires the data as provided."
   },
   {
    "title": "Running in Workbench is not the same run",
    "what": "The tests run the script statement by statement through PyMySQL, split by our own splitter. Workbench has its own splitter and session settings (for example Safe Updates). A statement that splits differently there would not be caught.",
    "cover": "check_implementation.py runs it through the mysql client; run it once in Workbench by hand before submitting."
   },
   {
    "title": "Different server settings",
    "what": "Strict SQL mode is assumed (the MySQL 8 default). On a server without it, a bad value is stored with a warning instead of refused, so the type-limit tests would fail there, correctly but confusingly.",
    "cover": "Each run records the server version and sql_mode; the site page shows the last run's."
   },
   {
    "title": "Accepted boundary values",
    "what": "Each CHECK is tested with one value it must refuse, not with the edge values it must accept. A rule written as < 1 where the analysis says at most 1 would still refuse 1.2 and pass, while wrongly refusing exactly 1.00.",
    "cover": "The sample data contains some edge values (a blend weight of 1.00, a royalty of 0), which the load accepts."
   },
   {
    "title": "Rules across rows are not enforced by the schema",
    "what": "I1, I2, I3, I5 and I7 are checked on the loaded data only. Nothing in the tables stops a later insert from breaking them: by design, the analysis gives them to stored procedures.",
    "cover": "Task 4 (routines.sql) and its tests."
   },
   {
    "title": "ON DELETE rules are the script's choice",
    "what": "The analysis does not say what happens on delete. The tests check the three rules the script's comments state (two CASCADE, one SET NULL), so they cannot judge whether those are the right business choices.",
    "cover": "Argued in the script's table comments."
   },
   {
    "title": "Things not looked at",
    "what": "Collation and case (whether two stage names differing only in case count as duplicates), ON UPDATE rules, secondary indexes beyond the keys, users and privileges.",
    "cover": "Not required by the brief."
   }
  ],
  "findings": [
   {
    "title": "Primary key names",
    "text": "The script writes CONSTRAINT pk_<table> PRIMARY KEY (...) for all ten tables, but MySQL ignores a name on a primary key and always calls it PRIMARY. The tests accept PRIMARY. The header comment (\"Every constraint is named: pk_<table>, ...\") promises names the database never has; fk_, uq_ and ck_ names do survive."
   }
  ],
  "run": [
   {
    "title": "What you need",
    "text": "A running MySQL Server 8.0.16 or later (CHECK constraints) and its root password; Python 3.10 or later. The mysql command-line client and Workbench are not needed.",
    "code": null
   },
   {
    "title": "Get the files",
    "text": "Download crossfade_impl_tests.zip with the button above and extract it. It holds one folder, crossfade_impl_tests, with the tests, database_implementation.sql, data.csv and this guide. (Or take the files one by one; they only need to be in the same folder.)",
    "code": "Expand-Archive -Force $HOME\\Downloads\\crossfade_impl_tests.zip .\ncd .\\crossfade_impl_tests"
   },
   {
    "title": "Set up Python (once)",
    "text": "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
    "code": "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"
   },
   {
    "title": "Run the tests",
    "text": "Give the tests your MySQL password, then run. These tests drop and rebuild the crossfade database from database_implementation.sql (twice), and leave it loaded; nothing else on the server is touched.",
    "code": "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest"
   },
   {
    "title": "Read the result",
    "text": "The header names the two files it found; a counter shows each statement of the script as it runs; then one line per test and a summary. Every failure says which column, key, rule or cell differs, and what MySQL said.",
    "code": "crossfade impl  ...\\database_implementation.sql\n      running database_implementation.sql: statement 22/22\ncollected 228 items\ntest_implementation.py::test_load_first_run PASSED   [  0%]\n...\n========== 228 passed in 0.8s =========="
   },
   {
    "title": "Without Python",
    "text": "From a clone of the repository, the mysql client alone: runs the script twice, compares every row with data.xlsx and checks the integrity rules; ends with PASS.",
    "code": "python project2/scripts/check_implementation.py --mysql \"C:/Program Files/MySQL/MySQL Server 8.4/bin/mysql.exe\""
   }
  ],
  "mutants": {
   "mutants": [
    {
     "mutant": "varchar-size",
     "mistake": "a column one character wider than the model (genre.name VARCHAR(10))",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_schema_columns[genre]"
     ]
    },
    {
     "mutant": "unsigned-dropped",
     "mistake": "UNSIGNED missing on a key (track.track_id INT)",
     "caught": true,
     "failed": 200,
     "first_failures": [
      "test_load_first_run",
      "test_load_second_run",
      "test_schema_tables",
      "test_schema_columns[track]"
     ]
    },
    {
     "mutant": "check-dropped",
     "mistake": "a CHECK left out (I4, the ambiguity window)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_schema_constraint_names",
      "test_enforce_check[ck_station_ambiguity_window]"
     ]
    },
    {
     "mutant": "primary-key-wrong",
     "mistake": "an extra column in a composite primary key (play)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_schema_primary_key[play]"
     ]
    },
    {
     "mutant": "optional-made-required",
     "mistake": "an optional column made NOT NULL (play.reaction)",
     "caught": true,
     "failed": 161,
     "first_failures": [
      "test_load_first_run",
      "test_load_second_run",
      "test_schema_columns[play]",
      "test_read_one_row[genre]"
     ]
    },
    {
     "mutant": "required-made-optional",
     "mistake": "a required column left nullable (track.title)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_schema_columns[track]",
      "test_enforce_not_null[track-title]"
     ]
    },
    {
     "mutant": "cascade-dropped",
     "mistake": "ON DELETE CASCADE left out (station_blend -> station)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_schema_foreign_key[fk_station_blend_station]",
      "test_enforce_delete_station_cascades_blend_and_keeps_plays"
     ]
    },
    {
     "mutant": "foreign-key-renamed",
     "mistake": "a foreign key under another name (fk_play_stn)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_schema_foreign_key[fk_play_station]",
      "test_schema_no_extra_foreign_keys",
      "test_enforce_orphan_refused[fk_play_station]"
     ]
    },
    {
     "mutant": "foreign-key-dropped",
     "mistake": "a foreign key left out (track -> artist)",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_schema_foreign_key[fk_track_artist]",
      "test_schema_no_extra_foreign_keys",
      "test_enforce_orphan_refused[fk_track_artist]",
      "test_enforce_delete_parent_refused[artist]"
     ]
    },
    {
     "mutant": "unique-dropped",
     "mistake": "a unique key left out (listener.email)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_schema_unique_key[uq_listener_email]",
      "test_enforce_duplicate_unique[uq_listener_email]"
     ]
    },
    {
     "mutant": "checks-switched-off",
     "mistake": "foreign-key checks switched off during the load",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_load_every_statement_commented",
      "test_load_never_switches_checks_off",
      "test_load_inventory"
     ]
    },
    {
     "mutant": "not-re-runnable",
     "mistake": "DROP DATABASE IF EXISTS removed (the script cannot run twice)",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_load_first_run",
      "test_load_second_run",
      "test_load_no_warnings",
      "test_load_inventory"
     ]
    },
    {
     "mutant": "decimal-rounds",
     "mistake": "a DECIMAL one place too short, so MySQL rounds the data (probability DECIMAL(5,3))",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_load_no_warnings",
      "test_schema_columns[genre_probability]",
      "test_data_every_cell[genre_probability]",
      "test_data_integrity_rule[I2-ten-probabilities-summing-to-one]"
     ]
    },
    {
     "mutant": "enum-extra-value",
     "mistake": "an ENUM value the model does not have (plan_tier 'family')",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_schema_columns[listener]"
     ]
    },
    {
     "mutant": "date-as-datetime",
     "mistake": "DATE stored as DATETIME (listener.signup_date)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_schema_columns[listener]",
      "test_data_every_cell[listener]"
     ]
    },
    {
     "mutant": "checksum-varbinary",
     "mistake": "the fixed 32-byte checksum stored as VARBINARY(64)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_schema_columns[track]",
      "test_enforce_type_limit[track-audio_checksum-too-long]"
     ]
    },
    {
     "mutant": "value-changed",
     "mistake": "one royalty amount changed (0.0035 -> 0.0036)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_data_every_cell[play]",
      "test_data_integrity_rule[I7-royalty-is-payout-rate-from-30-seconds]"
     ]
    },
    {
     "mutant": "row-dropped",
     "mistake": "one artist row left out (1049)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_data_row_count[artist]",
      "test_data_every_cell[artist]",
      "test_enforce_rollback_leaves_data"
     ]
    },
    {
     "mutant": "comment-removed",
     "mistake": "the purpose comment before one CREATE TABLE removed (the brief)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_load_every_statement_commented"
     ]
    }
   ],
   "caught": 19,
   "total": 19,
   "not_applicable": [],
   "real_script": "============================= 228 passed in 0.74s =============================="
  }
 },
 "single": {
  "file": "single_table.sql",
  "task": "Task 2",
  "status": "tested",
  "title": "Single-table queries",
  "lede": "How single_table.sql is checked: every query is run on the crossfade database and compared with an answer computed independently in Python from data.csv; its comment, table, columns and brief requirements are checked against the use cases; logic the sample data never reaches is tested by adding rows in rolled-back transactions; and the one statement that must fail is made to fail.",
  "results": "single_table_results.js",
  "resultsVar": "P2_SINGLE",
  "pdf": "test_single_table_guide.pdf",
  "pdfTitle": "Testing single_table.sql locally",
  "mutator": "mutate_single_table.py",
  "flowTo": "<b>each query's result in MySQL</b>, run on the <code>crossfade</code> database",
  "files": [
   {
    "file": "single_table.sql",
    "role": "the file under test (Task 2)",
    "href": "../deliverables/single_table.sql"
   },
   {
    "file": "test_single_table.py",
    "role": "the tests: contract, correctness, behaviour cases, the expected error, file coverage",
    "href": "../tests/test_single_table.py"
   },
   {
    "file": "oracle.py",
    "role": "the independent answers: each query recomputed in plain Python from data.csv, no SQL",
    "href": "../tests/oracle.py"
   },
   {
    "file": "conftest.py",
    "role": "shared set-up: finds the files, connects, splits the .sql into commented statements, writes the results snapshot",
    "href": "../tests/conftest.py"
   },
   {
    "file": "use_cases.json",
    "role": "the use cases: their RA evidence, the columns each may read, the expected error",
    "href": "../data/use_cases.json"
   },
   {
    "file": "data.csv",
    "role": "the Project 1 sample data the oracle reads",
    "href": "../../project1/data_export/data.csv"
   },
   {
    "file": "database_implementation.sql",
    "role": "builds the database the queries run on (--fresh)",
    "href": "../deliverables/database_implementation.sql"
   },
   {
    "file": "pytest.ini",
    "role": "pytest settings (verbose, no cache folder)",
    "href": "../tests/pytest.ini"
   },
   {
    "file": "requirements.txt",
    "role": "pytest, PyMySQL, cryptography (MySQL 8 sign-in)",
    "href": "../tests/requirements.txt"
   },
   {
    "file": "test_single_table_guide.pdf",
    "role": "how to run the tests locally, what they cover and what they could miss",
    "href": "../docs/test_single_table_guide.pdf"
   },
   {
    "file": "use_case_reference.pdf",
    "role": "every use case: tables, columns, input, expected output, test cases",
    "href": "../docs/use_case_reference.pdf"
   },
   {
    "file": "mutate_single_table.py",
    "role": "tests the tests: breaks single_table.sql 23 ways, one at a time, and checks every break is caught (repo only)",
    "href": "../scripts/mutate_single_table.py"
   }
  ],
  "bundle": {
   "file": "crossfade_single_tests.zip",
   "role": "the tests, the oracle, every input file and both guides, in one folder that runs as-is",
   "href": "../tests/crossfade_single_tests.zip",
   "bytes": 178309,
   "contents": [
    "test_single_table.py",
    "oracle.py",
    "conftest.py",
    "pytest.ini",
    "requirements.txt",
    "single_table.sql",
    "database_implementation.sql",
    "data.csv",
    "use_cases.json",
    "test_single_table_guide.pdf",
    "use_case_reference.pdf",
    "rubric_single_table.md",
    "README.txt"
   ]
  },
  "sources": [
   {
    "name": "Independent answers",
    "from": "oracle.py + data.csv",
    "how": "Each query's answer is recomputed in plain Python from data.csv: no SQL, no database. MySQL must return the same columns, rows and order, to the exact decimal."
   },
   {
    "name": "The use cases",
    "from": "use_cases.json ← requirements_analysis.pdf",
    "how": "Each query names the use cases it answers. Each use case quotes the requirements analysis word for word (build_usecases.py fails if a quote is not in it) and lists the columns it may read."
   },
   {
    "name": "MySQL's own plan",
    "from": "EXPLAIN FORMAT=JSON",
    "how": "Proves each query reads exactly the one table its comment names, from MySQL's execution plan rather than a text search of the SQL."
   },
   {
    "name": "The brief and the slides",
    "from": "info579_project02.pdf, Units 6 and 8",
    "how": "Requirements (a)-(e) are recognised from the course's own lists: single-row and aggregate functions (Unit 6), CASE and IF as selection control (Unit 8). IFNULL is a NULL-handling function in the slides, so it counts as neither."
   }
  ],
  "groups": [
   {
    "group": "contract",
    "tests": 35,
    "passed": 35,
    "text": "Each query is preceded by a purpose comment with its tag, table, use cases, business need, business question, requirements and output columns. It is one read-only SELECT with no SELECT *. MySQL's own plan (EXPLAIN) shows it reads exactly the table its comment names. The brief requirements (a)-(e) it claims are exactly the ones it uses. It reads only columns its use cases declare."
   },
   {
    "group": "correctness",
    "tests": 14,
    "passed": 14,
    "text": "Each result equals an answer computed independently in plain Python from data.csv: same columns, same rows, same order, exact decimals. Its ORDER BY includes a unique key (or the GROUP BY columns), so no two rows can tie and come back in a chance order; and two runs agree."
   },
   {
    "group": "behaviour",
    "tests": 16,
    "passed": 16,
    "text": "Logic the sample data never reaches: a row is added or changed inside a transaction that is rolled back, and the query must still agree with the oracle on the changed data. Each case targets one branch, boundary or tie."
   },
   {
    "group": "expected error",
    "tests": 2,
    "passed": 2,
    "text": "The [E1] statement at the end of the file is kept DISABLED (commented out), so a script run never stops on it. Run on its own, it must be refused by MySQL with exactly error 1062 on uq_track_audio_checksum, and track must be unchanged afterwards."
   },
   {
    "group": "coverage",
    "tests": 4,
    "passed": 4,
    "text": "The file as a whole: all six non-associative tables are queried; each requirement (a)-(e) is met at least twice; every use case a single table can answer is answered; tags run S1, S2, ... in order, and [E#] comes after them."
   }
  ],
  "coverage": {
   "columns": [
    {
     "key": "contract",
     "label": "Comment fields"
    },
    {
     "key": "select",
     "label": "Read-only SELECT"
    },
    {
     "key": "one",
     "label": "One table (EXPLAIN)"
    },
    {
     "key": "reqs",
     "label": "Requirements as declared"
    },
    {
     "key": "cols",
     "label": "Columns as declared"
    },
    {
     "key": "oracle",
     "label": "Matches the oracle"
    },
    {
     "key": "order",
     "label": "Order cannot tie"
    },
    {
     "key": "cases",
     "label": "Behaviour cases"
    },
    {
     "key": "error",
     "label": "Refused as expected"
    },
    {
     "key": "req_a",
     "label": "(a) single-row fn",
     "mark": true
    },
    {
     "key": "req_b",
     "label": "(b) aggregate",
     "mark": true
    },
    {
     "key": "req_c",
     "label": "(c) ORDER BY",
     "mark": true
    },
    {
     "key": "req_d",
     "label": "(d) LIMIT",
     "mark": true
    },
    {
     "key": "req_e",
     "label": "(e) CASE / IF",
     "mark": true
    }
   ],
   "rows": [
    {
     "key": "S1",
     "label": "S1",
     "sub": "artist"
    },
    {
     "key": "S2",
     "label": "S2",
     "sub": "track"
    },
    {
     "key": "S3",
     "label": "S3",
     "sub": "genre"
    },
    {
     "key": "S4",
     "label": "S4",
     "sub": "listener"
    },
    {
     "key": "S5",
     "label": "S5",
     "sub": "scoring_model"
    },
    {
     "key": "S6",
     "label": "S6",
     "sub": "station"
    },
    {
     "key": "S7",
     "label": "S7",
     "sub": "track"
    },
    {
     "key": "E1",
     "label": "E1",
     "sub": "track"
    }
   ],
   "cells": {
    "S1": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      3,
      3
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      0,
      0
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      0,
      0
     ],
     "req_e": [
      1,
      1
     ]
    },
    "S2": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      3,
      3
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      0,
      0
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      1,
      1
     ],
     "req_e": [
      0,
      0
     ]
    },
    "S3": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      3,
      3
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      1,
      1
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      0,
      0
     ],
     "req_e": [
      1,
      1
     ]
    },
    "S4": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      1,
      1
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      1,
      1
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      0,
      0
     ],
     "req_e": [
      0,
      0
     ]
    },
    "S5": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      2,
      2
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      0,
      0
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      1,
      1
     ],
     "req_e": [
      0,
      0
     ]
    },
    "S6": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      1,
      1
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      1,
      1
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      0,
      0
     ],
     "req_e": [
      1,
      1
     ]
    },
    "S7": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "one": [
      1,
      1
     ],
     "reqs": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      3,
      3
     ],
     "error": [
      0,
      0
     ],
     "req_a": [
      1,
      1
     ],
     "req_b": [
      1,
      1
     ],
     "req_c": [
      1,
      1
     ],
     "req_d": [
      0,
      0
     ],
     "req_e": [
      1,
      1
     ]
    },
    "E1": {
     "contract": [
      0,
      0
     ],
     "select": [
      0,
      0
     ],
     "one": [
      0,
      0
     ],
     "reqs": [
      0,
      0
     ],
     "cols": [
      0,
      0
     ],
     "oracle": [
      0,
      0
     ],
     "order": [
      0,
      0
     ],
     "cases": [
      0,
      0
     ],
     "error": [
      1,
      1
     ],
     "req_a": [
      0,
      0
     ],
     "req_b": [
      0,
      0
     ],
     "req_c": [
      0,
      0
     ],
     "req_d": [
      0,
      0
     ],
     "req_e": [
      0,
      0
     ]
    }
   },
   "whole": [
    {
     "test": "test_every_non_associative_table_is_queried",
     "outcome": "passed"
    },
    {
     "test": "test_each_requirement_is_met_at_least_twice",
     "outcome": "passed"
    },
    {
     "test": "test_every_single_table_use_case_is_answered",
     "outcome": "passed"
    },
    {
     "test": "test_tags_are_unique_and_in_order",
     "outcome": "passed"
    }
   ],
   "caption": "tests per query and check; ✓ = brief requirement met"
  },
  "misses": [
   {
    "title": "Independent code, not an independent reading",
    "what": "The oracle was written from the same use cases as the queries. If a use case was misread (who counts as payable, what 'newest' means), the query and its expected answer agree and the test passes.",
    "cover": "Each use case quotes the requirements analysis word for word on the Use cases page; a second reader."
   },
   {
    "title": "A small sample",
    "what": "8 artists, 15 tracks, 10 genres, 8 listeners, 5 models, 8 stations. Many CASE branches, boundaries and ties are reached by no row at all; they are tested only where a behaviour case adds the row.",
    "cover": "The 13 behaviour cases, and the deliberate-mistake run below."
   },
   {
    "title": "A fixed report date",
    "what": "Every 'days since' figure is measured to 2026-09-30, so results never change. A live report would use CURDATE(); that version is not tested.",
    "cover": "Stated in the file header."
   },
   {
    "title": "Requirements recognised by name, not by merit",
    "what": "(a)-(e) are detected from the course's function lists. Whether a use is 'trivial or generic' (the brief's words) is the grader's judgement, which no test can make.",
    "cover": "Each comment says why the function is needed for the business question."
   },
   {
    "title": "Comments checked for shape, not truth",
    "what": "The tests check that every comment field is present and that each use case exists. Whether the business reasoning in the comment is sound is not testable.",
    "cover": "The comments cite the requirements analysis section by section."
   },
   {
    "title": "Our own column lists",
    "what": "'Reads only declared columns' is checked against use_cases.json, which we wrote. A wrong list there would pass a query that reads the wrong column.",
    "cover": "build_usecases.py checks every listed column exists in the physical model."
   },
   {
    "title": "Running in Workbench is not the same run",
    "what": "The tests run each statement on its own through PyMySQL. Workbench runs the file top to bottom and stops at the first error, which is [E1] by design; splitting can also differ.",
    "cover": "A test checks [E1] comes after every query; run the file once in Workbench by hand."
   },
   {
    "title": "One refusal",
    "what": "Only the duplicate-upload refusal (1062) is exercised here. Other refusals (orphans, NULLs, CHECKs) belong to the database, not to this file.",
    "cover": "test_implementation.py checks every constraint refuses a bad write."
   },
   {
    "title": "Speed",
    "what": "No query plan is judged for cost. The tables are tiny, so this matters little here.",
    "cover": "Not required by the brief."
   }
  ],
  "findings": [
   {
    "title": "[S5] could tie (fixed Nov 7)",
    "text": "S5 picks one row with LIMIT 1 and sorted only by accuracy and deployment date, so two versions tied on both would have made the default MySQL's choice. The strengthened order check caught it; model_id is now the last sort key (the lower one wins a full tie), the comment says so, and a behaviour case pins it. The sample data never had such a tie, so no result changed."
   },
   {
    "title": "The tests had a blind spot (now fixed)",
    "text": "The deliberate-mistake run showed that removing the tie-break from [S1] or [S2] went unnoticed: MySQL happened to return tied rows in primary-key order, which is the order the tie-break asks for, so the two tie-break behaviour cases still passed. The determinism test now checks that every ORDER BY includes a unique key, which catches both mistakes."
   }
  ],
  "run": [
   {
    "title": "What you need",
    "text": "A running MySQL Server 8.0.16 or later and its root password; Python 3.10 or later. The mysql command-line client and Workbench are not needed: --fresh builds the database for you.",
    "code": null
   },
   {
    "title": "Get the files",
    "text": "Download crossfade_single_tests.zip with the button above and extract it. It holds one folder, crossfade_single_tests, with the tests, the oracle, single_table.sql, database_implementation.sql, data.csv, use_cases.json and both guides.",
    "code": "Expand-Archive -Force $HOME\\Downloads\\crossfade_single_tests.zip .\ncd .\\crossfade_single_tests"
   },
   {
    "title": "Set up Python (once)",
    "text": "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
    "code": "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"
   },
   {
    "title": "Run the tests",
    "text": "--fresh rebuilds the crossfade database from database_implementation.sql first. Without it the tests use the database as it is, after checking it holds exactly the rows in data.csv. Every write a test makes is rolled back.",
    "code": "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest --fresh"
   },
   {
    "title": "Read the result",
    "text": "One line per test, then a summary. A correctness failure prints the first row where MySQL and the oracle differ; a contract failure names the comment field, table or column. Each query's result as the tests saw it is on the single_table page (Project 2 → Files).",
    "code": "collected 71 items\ntest_single_table.py::test_comment_contract[S1] PASSED   [  1%]\n...\n========== 71 passed in 0.3s =========="
   },
   {
    "title": "Write the queries yourself",
    "text": "The starter kit, project2/tests/crossfade_p2_starter_kit.zip in the repo (not offered for download on the site), is the same folder with every comment kept and every query removed. Run the tests at any point: unwritten queries are reported by name.",
    "code": null
   }
  ],
  "mutants": {
   "mutants": [
    {
     "mutant": "s1-country-check-masked",
     "query": "S1",
     "mistake": "the country check only runs for verified artists (an artist failing both shows one hold)",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S1]",
      "test_s1_verified_artist_without_country_is_held_for_country_alone",
      "test_s1_held_artist_never_outranks_a_ready_one",
      "test_s1_equal_rates_break_ties_on_artist_id"
     ]
    },
    {
     "mutant": "s1-ready-ignores-country",
     "query": "S1",
     "mistake": "run_status says ready for a verified artist with no country",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_s1_verified_artist_without_country_is_held_for_country_alone"
     ]
    },
    {
     "mutant": "s1-tie-break-dropped",
     "query": "S1",
     "mistake": "the artist_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[S1]"
     ]
    },
    {
     "mutant": "s1-ready-first-dropped",
     "query": "S1",
     "mistake": "ready artists no longer listed first",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S1]",
      "test_s1_verified_artist_without_country_is_held_for_country_alone",
      "test_s1_held_artist_never_outranks_a_ready_one",
      "test_s1_equal_rates_break_ties_on_artist_id"
     ]
    },
    {
     "mutant": "s1-report-date-moved",
     "query": "S1",
     "mistake": "a different report date (2026-10-01) in days under licence",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S1]",
      "test_s1_verified_artist_without_country_is_held_for_country_alone",
      "test_s1_held_artist_never_outranks_a_ready_one",
      "test_s1_equal_rates_break_ties_on_artist_id"
     ]
    },
    {
     "mutant": "s2-scored-filter-dropped",
     "query": "S2",
     "mistake": "unscored and rejected recordings allowed on the shelf",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S2]",
      "test_s2_unscored_new_release_stays_off_the_shelf",
      "test_s2_same_day_releases_order_by_track_id",
      "test_s2_shelf_never_holds_more_than_five"
     ]
    },
    {
     "mutant": "s2-limit-six",
     "query": "S2",
     "mistake": "six recordings on the shelf instead of five",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S2]",
      "test_s2_unscored_new_release_stays_off_the_shelf",
      "test_s2_same_day_releases_order_by_track_id",
      "test_s2_shelf_never_holds_more_than_five"
     ]
    },
    {
     "mutant": "s2-seconds-unpadded",
     "query": "S2",
     "mistake": "run time without the zero pad (3:7 instead of 3:07)",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S2]",
      "test_s2_unscored_new_release_stays_off_the_shelf",
      "test_s2_same_day_releases_order_by_track_id",
      "test_s2_shelf_never_holds_more_than_five"
     ]
    },
    {
     "mutant": "s2-tie-break-dropped",
     "query": "S2",
     "mistake": "the track_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[S2]"
     ]
    },
    {
     "mutant": "s3-width-hard-coded",
     "query": "S3",
     "mistake": "the label column width hard-coded to 9 instead of found from the data",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_requirements_match_declared[S3]",
      "test_s3_label_width_follows_the_data_and_ties_share_it"
     ]
    },
    {
     "mutant": "s3-bytes-not-characters",
     "query": "S3",
     "mistake": "description length counted in bytes (LENGTH) instead of characters",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_s3_description_length_counts_characters_not_bytes"
     ]
    },
    {
     "mutant": "s3-line-budget-wrong",
     "query": "S3",
     "mistake": "room left measured against 79 characters instead of the RA's 80",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[S3]",
      "test_s3_genre_without_description_has_no_line_figures",
      "test_s3_label_width_follows_the_data_and_ties_share_it",
      "test_s3_description_length_counts_characters_not_bytes"
     ]
    },
    {
     "mutant": "s3-select-star",
     "query": "S3",
     "mistake": "SELECT * instead of the named columns",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_read_only_select[S3]",
      "test_result_matches_oracle[S3]",
      "test_s3_genre_without_description_has_no_line_figures",
      "test_s3_label_width_follows_the_data_and_ties_share_it"
     ]
    },
    {
     "mutant": "s4-tiers-ascending",
     "query": "S4",
     "mistake": "plan tiers listed cheapest first",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_result_matches_oracle[S4]",
      "test_s4_tier_with_no_listeners_is_absent"
     ]
    },
    {
     "mutant": "s4-average-unrounded",
     "query": "S4",
     "mistake": "average tenure not rounded",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_result_matches_oracle[S4]",
      "test_s4_tier_with_no_listeners_is_absent"
     ]
    },
    {
     "mutant": "s4-column-renamed",
     "query": "S4",
     "mistake": "an output column renamed (listener_count)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_matches_oracle[S4]"
     ]
    },
    {
     "mutant": "s5-tie-goes-to-older",
     "query": "S5",
     "mistake": "an accuracy tie goes to the older deployment",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_s5_accuracy_tie_prefers_the_newer_version"
     ]
    },
    {
     "mutant": "s5-last-tie-break-dropped",
     "query": "S5",
     "mistake": "the model_id tie-break left out (a full tie on accuracy and date picks either row)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[S5]"
     ]
    },
    {
     "mutant": "s5-second-table",
     "query": "S5",
     "mistake": "a second table read (a subquery on station)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_reads_exactly_one_table[S5]",
      "test_s5_accuracy_tie_prefers_the_newer_version",
      "test_s5_full_tie_goes_to_the_lower_model_id"
     ]
    },
    {
     "mutant": "s5-use-cases-line-removed",
     "query": "S5",
     "mistake": "the Use cases line removed from the comment",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_comment_contract[S5]",
      "test_columns_match_use_cases[S5]"
     ]
    },
    {
     "mutant": "s6-half-counts-as-wide",
     "query": "S6",
     "mistake": "a window of exactly 0.50 counted as wide (>= instead of >)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_result_matches_oracle[S6]",
      "test_s6_window_of_exactly_half_is_not_wide"
     ]
    },
    {
     "mutant": "s6-undeclared-column",
     "query": "S6",
     "mistake": "a column the use cases do not declare is read (listener_id)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_columns_match_use_cases[S6]"
     ]
    },
    {
     "mutant": "s7-due-today-on-time",
     "query": "S7",
     "mistake": "a release due on the report date counted as on time (< instead of <=)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_s7_release_due_on_the_report_date_is_late"
     ]
    },
    {
     "mutant": "s2-limit-undeclared",
     "query": "S2",
     "mistake": "LIMIT used but (d) not declared in Requirements",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_requirements_match_declared[S2]"
     ]
    },
    {
     "mutant": "e1-not-refused",
     "query": "E1",
     "mistake": "the re-upload computes a different checksum, so MySQL accepts it",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_expected_error_is_raised[E1]"
     ]
    },
    {
     "mutant": "e1-enabled",
     "query": "E1",
     "mistake": "the disabled expected-to-fail statement switched back on (the file no longer runs clean)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_error_statement_is_disabled[E1]"
     ]
    }
   ],
   "caught": 26,
   "total": 26,
   "not_applicable": [],
   "real_file": "========================= 1 failed, 70 passed in 0.20s =========================",
   "already_failing": []
  }
 },
 "multiple": {
  "file": "multiple_table.sql",
  "task": "Task 3",
  "status": "tested",
  "title": "Multiple-table queries",
  "lede": "How multiple_table.sql is checked: every query is run on the crossfade database and compared with an answer computed independently in Python from data.csv; MySQL's own plan proves which tables and columns it reads; the SQL must really meet the Task 3 requirement its comment claims, with every join named; and joins, boundaries and NULLs the sample data never reaches are tested by adding rows in rolled-back transactions.",
  "results": "multiple_table_results.js",
  "resultsVar": "P2_MULTIPLE",
  "pdf": "test_multiple_table_guide.pdf",
  "pdfTitle": "Testing multiple_table.sql locally",
  "mutator": "mutate_multiple_table.py",
  "flowTo": "<b>each query's result in MySQL</b>, run on the <code>crossfade</code> database",
  "files": [
   {
    "file": "multiple_table.sql",
    "role": "the file under test (Task 3)",
    "href": "../deliverables/multiple_table.sql"
   },
   {
    "file": "test_multiple_table.py",
    "role": "the tests: contract, correctness, behaviour cases, file coverage",
    "href": "../tests/test_multiple_table.py"
   },
   {
    "file": "oracle_multiple.py",
    "role": "the independent answers: each query recomputed in plain Python from data.csv, no SQL",
    "href": "../tests/oracle_multiple.py"
   },
   {
    "file": "oracle.py",
    "role": "shared helpers the multiple-table oracle imports (MySQL-style rounding)",
    "href": "../tests/oracle.py"
   },
   {
    "file": "conftest.py",
    "role": "shared set-up: finds the files, connects, splits the .sql into commented statements, writes the results snapshot",
    "href": "../tests/conftest.py"
   },
   {
    "file": "use_cases.json",
    "role": "the use cases: their RA evidence and the columns each multiple-table query may read (multipleColumns)",
    "href": "../data/use_cases.json"
   },
   {
    "file": "data.csv",
    "role": "the Project 1 sample data the oracle reads",
    "href": "../../project1/data_export/data.csv"
   },
   {
    "file": "database_implementation.sql",
    "role": "builds the database the queries run on (--fresh)",
    "href": "../deliverables/database_implementation.sql"
   },
   {
    "file": "pytest.ini",
    "role": "pytest settings (verbose, no cache folder)",
    "href": "../tests/pytest.ini"
   },
   {
    "file": "requirements.txt",
    "role": "pytest, PyMySQL, cryptography (MySQL 8 sign-in)",
    "href": "../tests/requirements.txt"
   },
   {
    "file": "test_multiple_table_guide.pdf",
    "role": "how to run the tests locally, what they cover and what they could miss",
    "href": "../docs/test_multiple_table_guide.pdf"
   },
   {
    "file": "mutate_multiple_table.py",
    "role": "tests the tests: breaks multiple_table.sql 39 ways, one at a time, and checks every break is caught (repo only)",
    "href": "../scripts/mutate_multiple_table.py"
   }
  ],
  "bundle": {
   "file": "crossfade_multiple_tests.zip",
   "role": "the tests, the oracle, every input file and the guide, in one folder that runs as-is",
   "href": "../tests/crossfade_multiple_tests.zip",
   "bytes": 184791,
   "contents": [
    "test_multiple_table.py",
    "oracle_multiple.py",
    "oracle.py",
    "conftest.py",
    "pytest.ini",
    "requirements.txt",
    "multiple_table.sql",
    "database_implementation.sql",
    "data.csv",
    "use_cases.json",
    "test_multiple_table_guide.pdf",
    "rubric_multiple_table.md",
    "use_case_reference.pdf",
    "README.txt"
   ]
  },
  "sources": [
   {
    "name": "Independent answers",
    "from": "oracle_multiple.py + data.csv",
    "how": "Each query's answer is recomputed in plain Python from data.csv, no SQL and no database. MySQL must return the same columns, rows and order, to the exact decimal."
   },
   {
    "name": "The use cases",
    "from": "use_cases.json ← requirements_analysis.pdf",
    "how": "Each query names the use cases it answers; each use case quotes the requirements analysis word for word and lists, under multipleColumns, the columns its query reads."
   },
   {
    "name": "MySQL's own plan",
    "from": "EXPLAIN FORMAT=JSON",
    "how": "The tables each query reads and the columns it uses from each (used_columns), from MySQL's execution plan rather than a text search of the SQL."
   },
   {
    "name": "The live schema",
    "from": "information_schema",
    "how": "Which tables are associative and which tables they relate (3.1), from the foreign keys database_implementation.sql created."
   },
   {
    "name": "The brief and the slides",
    "from": "info579_project02.pdf, Units 8 and 9",
    "how": "Requirements 3.1-3.5 from the brief; set operations, multi-row operators and WITH from Unit 8; named join types (no bare JOIN, no comma join) from Unit 9."
   }
  ],
  "groups": [
   {
    "group": "contract",
    "tests": 42,
    "passed": 42,
    "text": "Each query is preceded by a purpose comment with its tag, title, use cases, business need, business question, the Task 3 requirement it meets, the tables it reads, what one result row is and its output columns. It is one read-only SELECT (or WITH ... SELECT) with no SELECT *. MySQL's own plan (EXPLAIN) reads exactly the tables the comment lists. The SQL really meets the requirement it claims (3.1 an associative table INNER JOINed to the two tables it relates, found from the live foreign keys; 3.2 LEFT OUTER JOIN; 3.3 a set operation; 3.4 a multi-row subquery operator; 3.5 WITH). Every join names its type. Every column MySQL reads is one its use cases declare."
   },
   {
    "group": "correctness",
    "tests": 14,
    "passed": 14,
    "text": "Each result equals an answer computed independently in plain Python from data.csv (oracle_multiple.py: joins are dictionary look-ups, UNION is a set, WITH is a list built first): same columns, rows, order, exact decimals. There is one row per declared grain, the ORDER BY includes every grain column so no two rows can tie, and two runs agree."
   },
   {
    "group": "behaviour",
    "tests": 20,
    "passed": 20,
    "text": "Logic the sample data never reaches: rows are added inside a transaction that is rolled back, and the query must still agree with the oracle on the changed data. Each case targets one join, boundary, NULL or tie."
   },
   {
    "group": "coverage",
    "tests": 4,
    "passed": 4,
    "text": "The file as a whole: each of the five Task 3 requirements is met by a query that claims it; every use case with multiple-table columns is answered, and no query names one without them; every column a use case declares is read by a query answering it (two queries can answer one use case: M4 and M7 both answer UC-11); tags run M1, M2, ... in order."
   }
  ],
  "coverage": {
   "columns": [
    {
     "key": "contract",
     "label": "Comment fields"
    },
    {
     "key": "select",
     "label": "Read-only SELECT"
    },
    {
     "key": "tables",
     "label": "Tables (EXPLAIN)"
    },
    {
     "key": "req",
     "label": "Requirement met"
    },
    {
     "key": "joins",
     "label": "Join types named"
    },
    {
     "key": "cols",
     "label": "Columns as declared"
    },
    {
     "key": "oracle",
     "label": "Matches the oracle"
    },
    {
     "key": "order",
     "label": "Order cannot tie"
    },
    {
     "key": "cases",
     "label": "Behaviour cases"
    },
    {
     "key": "req_3.1",
     "label": "3.1 INNER JOIN",
     "mark": true
    },
    {
     "key": "req_3.2",
     "label": "3.2 LEFT OUTER",
     "mark": true
    },
    {
     "key": "req_3.3",
     "label": "3.3 set op",
     "mark": true
    },
    {
     "key": "req_3.4",
     "label": "3.4 subquery",
     "mark": true
    },
    {
     "key": "req_3.5",
     "label": "3.5 WITH",
     "mark": true
    }
   ],
   "rows": [
    {
     "key": "M1",
     "label": "M1",
     "sub": "listener taste profile"
    },
    {
     "key": "M2",
     "label": "M2",
     "sub": "royalty run: what each artist is owed"
    },
    {
     "key": "M3",
     "label": "M3",
     "sub": "station reach"
    },
    {
     "key": "M4",
     "label": "M4",
     "sub": "recordings the models disagree on"
    },
    {
     "key": "M5",
     "label": "M5",
     "sub": "filling each station"
    },
    {
     "key": "M6",
     "label": "M6",
     "sub": "results to recompute"
    },
    {
     "key": "M7",
     "label": "M7",
     "sub": "where each recording sits between genres"
    }
   ],
   "cells": {
    "M1": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      2,
      2
     ],
     "req_3.1": [
      1,
      1
     ],
     "req_3.2": [
      0,
      0
     ],
     "req_3.3": [
      0,
      0
     ],
     "req_3.4": [
      0,
      0
     ],
     "req_3.5": [
      0,
      0
     ]
    },
    "M2": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      2,
      2
     ],
     "req_3.1": [
      0,
      0
     ],
     "req_3.2": [
      1,
      1
     ],
     "req_3.3": [
      0,
      0
     ],
     "req_3.4": [
      0,
      0
     ],
     "req_3.5": [
      0,
      0
     ]
    },
    "M3": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      2,
      2
     ],
     "req_3.1": [
      0,
      0
     ],
     "req_3.2": [
      0,
      0
     ],
     "req_3.3": [
      1,
      1
     ],
     "req_3.4": [
      0,
      0
     ],
     "req_3.5": [
      0,
      0
     ]
    },
    "M4": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      4,
      4
     ],
     "req_3.1": [
      0,
      0
     ],
     "req_3.2": [
      0,
      0
     ],
     "req_3.3": [
      0,
      0
     ],
     "req_3.4": [
      1,
      1
     ],
     "req_3.5": [
      0,
      0
     ]
    },
    "M5": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      3,
      3
     ],
     "req_3.1": [
      0,
      0
     ],
     "req_3.2": [
      0,
      0
     ],
     "req_3.3": [
      0,
      0
     ],
     "req_3.4": [
      0,
      0
     ],
     "req_3.5": [
      1,
      1
     ]
    },
    "M6": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      4,
      4
     ],
     "req_3.1": [
      1,
      1
     ],
     "req_3.2": [
      0,
      0
     ],
     "req_3.3": [
      0,
      0
     ],
     "req_3.4": [
      0,
      0
     ],
     "req_3.5": [
      0,
      0
     ]
    },
    "M7": {
     "contract": [
      1,
      1
     ],
     "select": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "req": [
      1,
      1
     ],
     "joins": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "oracle": [
      1,
      1
     ],
     "order": [
      1,
      1
     ],
     "cases": [
      3,
      3
     ],
     "req_3.1": [
      0,
      0
     ],
     "req_3.2": [
      0,
      0
     ],
     "req_3.3": [
      0,
      0
     ],
     "req_3.4": [
      0,
      0
     ],
     "req_3.5": [
      1,
      1
     ]
    }
   },
   "whole": [
    {
     "test": "test_each_requirement_is_met",
     "outcome": "passed"
    },
    {
     "test": "test_every_multiple_table_use_case_is_answered",
     "outcome": "passed"
    },
    {
     "test": "test_declared_columns_are_read",
     "outcome": "passed"
    },
    {
     "test": "test_tags_are_unique_and_in_order",
     "outcome": "passed"
    }
   ],
   "caption": "tests per query and check; ✓ = Task 3 requirement met"
  },
  "misses": [
   {
    "title": "Independent code, not an independent reading",
    "what": "The oracle was written from the same comments as the queries. If a business rule was misread (what 'reach' means, which plays qualify), the query and its expected answer agree and the test passes.",
    "cover": "Each comment cites the requirements analysis section by section; a second reader."
   },
   {
    "title": "A small sample",
    "what": "8 artists, 15 tracks, 8 listeners, 8 stations, 27 scores, 270 probabilities, 31 plays. Some joins never lose a row and some boundaries are never reached; they are tested only where a behaviour case adds the row.",
    "cover": "The 20 behaviour cases, and the deliberate-mistake run below."
   },
   {
    "title": "Which version counts as newest",
    "what": "M6 reads 'a model redeployment' (RA: Scored On) as a newer version going into service. Several versions stay in service at once (RA: Scoring Model), so 'out of date' is measured against the one deployed last. If the business meant redeploying the same version (its deployed_on moving later), the same comparison applies to that version's own results, and M6 would need a second condition.",
    "cover": "The reading is stated in M6's comment; a behaviour case deploys a new version and checks every recording becomes due."
   },
   {
    "title": "Two versions always agree on divergence",
    "what": "Every disagreement in the sample is between exactly two model versions, whose divergences from each other are the same number, so MAX and MIN give the same answer on the sample data.",
    "cover": "A behaviour case adds a third version with a higher divergence (found by the mistake run)."
   },
   {
    "title": "Requirements recognised by shape, not by merit",
    "what": "3.1-3.5 are detected from the SQL (join types, UNION, IN (SELECT, WITH). Whether a query is 'trivial or generic' (the brief's words) is the grader's judgement, which no test can make.",
    "cover": "Each comment says why the join, set operation or subquery is needed for the business question."
   },
   {
    "title": "Comments checked for shape, not truth",
    "what": "Every comment field must be present and agree with the SQL (tables, grain, output, requirement). Whether the business reasoning is sound is not testable.",
    "cover": "The comments cite the requirements analysis."
   },
   {
    "title": "Our own column lists",
    "what": "'Columns as declared' is checked against multipleColumns in use_cases.json, which we wrote. A wrong list there would pass a query that reads the wrong column.",
    "cover": "build_usecases.py checks each multipleColumns entry is a column the use case needs and exists in the model."
   },
   {
    "title": "A plan-dependent column check",
    "what": "used_columns comes from MySQL's optimizer. A different MySQL version could list a column differently (an index it chose), and the strict both-ways check would then fail on a correct query.",
    "cover": "Only columns the statement names count, which drops the index-only extras; verified on MySQL 8.0."
   },
   {
    "title": "Speed",
    "what": "No plan is judged for cost (M4's correlated subqueries run once per recording). The tables are tiny.",
    "cover": "Not required by the brief."
   }
  ],
  "findings": [
   {
    "title": "The tests had a blind spot (now fixed)",
    "text": "The deliberate-mistake run showed that reporting the lowest divergence instead of the highest in [M4] went unnoticed: every listed sample recording is scored by exactly two versions, whose divergences from each other are equal. A behaviour case now adds a third version with a higher divergence."
   }
  ],
  "run": [
   {
    "title": "What you need",
    "text": "A running MySQL Server 8.0.16 or later and its root password; Python 3.10 or later. The mysql command-line client and Workbench are not needed: --fresh builds the database for you.",
    "code": null
   },
   {
    "title": "Get the files",
    "text": "Download crossfade_multiple_tests.zip with the button above and extract it. It holds one folder, crossfade_multiple_tests, with the tests, the oracle, multiple_table.sql, database_implementation.sql, data.csv, use_cases.json and the guide.",
    "code": "Expand-Archive -Force $HOME\\Downloads\\crossfade_multiple_tests.zip .\ncd .\\crossfade_multiple_tests"
   },
   {
    "title": "Set up Python (once)",
    "text": "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
    "code": "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"
   },
   {
    "title": "Run the tests",
    "text": "--fresh rebuilds the crossfade database from database_implementation.sql first. Without it the tests use the database as it is, after checking it holds exactly the rows in data.csv. Every write a test makes is rolled back.",
    "code": "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest --fresh"
   },
   {
    "title": "Read the result",
    "text": "One line per test, then a summary. A correctness failure prints the first row where MySQL and the oracle differ; a contract failure names the comment field, table, column or join. Each query's result as the tests saw it is on the multiple_table page (Project 2 → Files) and on the Use cases page.",
    "code": "collected 80 items\ntest_multiple_table.py::test_comment_contract[M1] PASSED   [  1%]\n...\n========== 80 passed in 0.3s =========="
   },
   {
    "title": "Write the queries yourself",
    "text": "The starter kit, project2/tests/crossfade_p2_starter_kit.zip in the repo (not offered for download on the site), holds multiple_table.sql with every comment kept and every query removed. Run the tests at any point: unwritten queries are reported by name.",
    "code": null
   }
  ],
  "mutants": {
   "mutants": [
    {
     "mutant": "m1-listener-left-join",
     "query": "M1",
     "mistake": "listener joined with LEFT OUTER JOIN (3.1 asks for INNER JOIN on all three tables)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_meets_its_requirement[M1]"
     ]
    },
    {
     "mutant": "m1-average-of-ratios",
     "query": "M1",
     "mistake": "share heard as the average of per-play ratios, not total heard / total length",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M1]",
      "test_m1_listener_with_no_plays_is_absent",
      "test_m1_abandoned_skip_lowers_the_share_heard"
     ]
    },
    {
     "mutant": "m1-least-engaged-first",
     "query": "M1",
     "mistake": "least engaged listeners first",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M1]",
      "test_m1_listener_with_no_plays_is_absent",
      "test_m1_abandoned_skip_lowers_the_share_heard"
     ]
    },
    {
     "mutant": "m1-tie-break-dropped",
     "query": "M1",
     "mistake": "the listener_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M1]"
     ]
    },
    {
     "mutant": "m1-tables-line-wrong",
     "query": "M1",
     "mistake": "track left off the comment's Tables line",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_reads_declared_tables[M1]"
     ]
    },
    {
     "mutant": "m2-play-inner-join",
     "query": "M2",
     "mistake": "play joined with INNER JOIN: artists with no plays drop out of the royalty run",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M2]",
      "test_m2_artist_with_uploads_but_no_plays_is_owed_zero",
      "test_m2_short_play_is_counted_but_does_not_qualify"
     ]
    },
    {
     "mutant": "m2-ifnull-dropped",
     "query": "M2",
     "mistake": "IFNULL removed: an artist with no plays is owed NULL instead of 0",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M2]",
      "test_m2_artist_with_uploads_but_no_plays_is_owed_zero",
      "test_m2_short_play_is_counted_but_does_not_qualify"
     ]
    },
    {
     "mutant": "m2-count-star",
     "query": "M2",
     "mistake": "COUNT(*) instead of COUNT(p.track_id): an artist with no plays shows 1 play",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M2]",
      "test_m2_artist_with_uploads_but_no_plays_is_owed_zero",
      "test_m2_short_play_is_counted_but_does_not_qualify"
     ]
    },
    {
     "mutant": "m2-thirty-seconds-excluded",
     "query": "M2",
     "mistake": "a play of exactly 30 seconds does not qualify (> instead of >=)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_m2_short_play_is_counted_but_does_not_qualify"
     ]
    },
    {
     "mutant": "m2-left-join-without-outer",
     "query": "M2",
     "mistake": "LEFT JOIN written without OUTER (the course asks for the full join type)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_join_types_explicit[M2]"
     ]
    },
    {
     "mutant": "m2-undeclared-column",
     "query": "M2",
     "mistake": "a column the use cases do not declare is read (artist.country)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_columns_match_use_cases[M2]"
     ]
    },
    {
     "mutant": "m3-union-all",
     "query": "M3",
     "mistake": "UNION ALL: a listener who plays a station twice is counted twice",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M3]",
      "test_m3_listener_playing_anothers_station_shares_it",
      "test_m3_unplayed_station_still_reaches_its_creator"
     ]
    },
    {
     "mutant": "m3-creator-only-is-shared",
     "query": "M3",
     "mistake": "a station reaching only its creator labelled shared (>= 1 instead of > 1)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_result_matches_oracle[M3]",
      "test_m3_listener_playing_anothers_station_shares_it",
      "test_m3_unplayed_station_still_reaches_its_creator"
     ]
    },
    {
     "mutant": "m3-bare-join",
     "query": "M3",
     "mistake": "a bare JOIN with no join type",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_join_types_explicit[M3]"
     ]
    },
    {
     "mutant": "m3-tie-break-dropped",
     "query": "M3",
     "mistake": "the station_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M3]"
     ]
    },
    {
     "mutant": "m3-grain-wrong",
     "query": "M3",
     "mistake": "the comment says one row per creator (a creator can have two stations)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M3]"
     ]
    },
    {
     "mutant": "m4-scores-not-genres",
     "query": "M4",
     "mistake": "two scores of any genre counted as a disagreement (COUNT(*) instead of COUNT(DISTINCT genre_id))",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_result_matches_oracle[M4]",
      "test_m4_new_disagreeing_score_adds_the_recording",
      "test_m4_third_version_raises_the_highest_divergence",
      "test_m4_agreeing_new_score_adds_nothing"
     ]
    },
    {
     "mutant": "m4-not-in",
     "query": "M4",
     "mistake": "NOT IN: the recordings the models agree on",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_result_matches_oracle[M4]",
      "test_m4_new_disagreeing_score_adds_the_recording",
      "test_m4_third_version_raises_the_highest_divergence",
      "test_m4_agreeing_new_score_adds_nothing"
     ]
    },
    {
     "mutant": "m4-lowest-divergence",
     "query": "M4",
     "mistake": "the lowest divergence instead of the highest",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_m4_third_version_raises_the_highest_divergence"
     ]
    },
    {
     "mutant": "m4-tie-break-dropped",
     "query": "M4",
     "mistake": "the track_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M4]"
     ]
    },
    {
     "mutant": "m4-claims-union",
     "query": "M4",
     "mistake": "the comment claims requirement 3.3 (a set operation) instead of 3.4",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_meets_its_requirement[M4]",
      "test_each_requirement_is_met"
     ]
    },
    {
     "mutant": "m5-window-edges-excluded",
     "query": "M5",
     "mistake": "the window's edges left out (> and < instead of BETWEEN)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_m5_window_edges_are_inside"
     ]
    },
    {
     "mutant": "m5-status-filter-dropped",
     "query": "M5",
     "mistake": "rejected recordings allowed on stations (ingest status not checked)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_m5_rejected_recording_is_never_streamed",
      "test_declared_columns_are_read"
     ]
    },
    {
     "mutant": "m5-any-model",
     "query": "M5",
     "mistake": "scores from every model version used, not the station's own",
     "caught": true,
     "failed": 6,
     "first_failures": [
      "test_result_matches_oracle[M5]",
      "test_result_is_deterministic[M5]",
      "test_m5_window_edges_are_inside",
      "test_m5_rejected_recording_is_never_streamed"
     ]
    },
    {
     "mutant": "m5-blend-genre-ignored",
     "query": "M5",
     "mistake": "top genre not matched to the blend (any blend row joins)",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_result_matches_oracle[M5]",
      "test_result_is_deterministic[M5]",
      "test_m5_window_edges_are_inside",
      "test_m5_rejected_recording_is_never_streamed"
     ]
    },
    {
     "mutant": "m5-weight-ascending",
     "query": "M5",
     "mistake": "lowest blend weight first",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[M5]",
      "test_m5_window_edges_are_inside",
      "test_m5_rejected_recording_is_never_streamed",
      "test_m5_only_blend_genres_and_its_own_model_count"
     ]
    },
    {
     "mutant": "m5-tie-break-dropped",
     "query": "M5",
     "mistake": "the track_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M5]"
     ]
    },
    {
     "mutant": "m5-minutes-unrounded",
     "query": "M5",
     "mistake": "station running time not rounded",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[M5]",
      "test_m5_window_edges_are_inside",
      "test_m5_rejected_recording_is_never_streamed",
      "test_m5_only_blend_genres_and_its_own_model_count"
     ]
    },
    {
     "mutant": "m6-deployment-day-stale",
     "query": "M6",
     "mistake": "a result scored at midnight on the deployment day counted as out of date (<= instead of <)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_m6_deployment_day_is_the_boundary"
     ]
    },
    {
     "mutant": "m6-oldest-result",
     "query": "M6",
     "mistake": "the oldest result judged instead of the newest: rescored recordings stay listed",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[M6]",
      "test_m6_rescore_by_the_model_in_service_brings_a_recording_up_to_date",
      "test_m6_deployment_day_is_the_boundary",
      "test_m6_rejected_recording_is_never_rescored"
     ]
    },
    {
     "mutant": "m6-rejected-included",
     "query": "M6",
     "mistake": "rejected recordings queued for rescoring (release status not checked)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_m6_rejected_recording_is_never_rescored",
      "test_declared_columns_are_read"
     ]
    },
    {
     "mutant": "m6-days-from-first-deployment",
     "query": "M6",
     "mistake": "days counted from the first deployment instead of the newest one",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_result_matches_oracle[M6]",
      "test_m6_rescore_by_the_model_in_service_brings_a_recording_up_to_date",
      "test_m6_deployment_day_is_the_boundary",
      "test_m6_new_deployment_makes_every_recording_stale"
     ]
    },
    {
     "mutant": "m6-versions-alphabetical",
     "query": "M6",
     "mistake": "the versions listed alphabetically instead of oldest first",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_result_matches_oracle[M6]",
      "test_m6_rescore_by_the_model_in_service_brings_a_recording_up_to_date",
      "test_m6_deployment_day_is_the_boundary",
      "test_m6_new_deployment_makes_every_recording_stale"
     ]
    },
    {
     "mutant": "m6-tie-break-dropped",
     "query": "M6",
     "mistake": "the track_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M6]"
     ]
    },
    {
     "mutant": "m7-second-place-includes-top",
     "query": "M7",
     "mistake": "the top genre allowed as its own runner-up: every margin is 0",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[M7]",
      "test_m7_tie_for_second_place_takes_the_lower_genre_id",
      "test_m7_top_tie_is_exactly_between_genres",
      "test_m7_result_without_a_distribution_is_absent"
     ]
    },
    {
     "mutant": "m7-higher-genre-on-tie",
     "query": "M7",
     "mistake": "a tie for second place goes to the higher genre_id",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_m7_tie_for_second_place_takes_the_lower_genre_id"
     ]
    },
    {
     "mutant": "m7-largest-margin-first",
     "query": "M7",
     "mistake": "the most clearly placed recordings first",
     "caught": true,
     "failed": 4,
     "first_failures": [
      "test_result_matches_oracle[M7]",
      "test_m7_tie_for_second_place_takes_the_lower_genre_id",
      "test_m7_top_tie_is_exactly_between_genres",
      "test_m7_result_without_a_distribution_is_absent"
     ]
    },
    {
     "mutant": "m7-tie-break-dropped",
     "query": "M7",
     "mistake": "the model_id tie-break left out of ORDER BY",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_result_is_deterministic[M7]"
     ]
    },
    {
     "mutant": "m7-runner-up-optional",
     "query": "M7",
     "mistake": "results with no distribution kept, half empty (runner_up and its genre joined LEFT OUTER)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_m7_result_without_a_distribution_is_absent"
     ]
    }
   ],
   "caught": 39,
   "total": 39,
   "not_applicable": [],
   "real_file": "========================= 1 failed, 79 passed in 0.36s =========================",
   "already_failing": []
  }
 },
 "routines": {
  "file": "routines.sql",
  "task": "Task 4",
  "status": "tested",
  "title": "Routines",
  "lede": "How routines.sql is checked: MySQL's own catalogue must hold each routine exactly as its comment declares it; each routine is called on the crossfade database and must write, return and refuse exactly what an independent Python answer from data.csv says; the RA's rules (no derived values as input, a royalty computed once, plays in UTC) are tested directly; and the duplicate-upload handler is pushed to its edges: a duplicate answered, every other error passed on, a key clash re-raised.",
  "results": "routines_results.js",
  "resultsVar": "P2_ROUTINES",
  "pdf": "test_routines_guide.pdf",
  "pdfTitle": "Testing routines.sql locally",
  "mutator": "mutate_routines.py",
  "flowTo": "<b>each routine called in MySQL</b>, inside a transaction that is rolled back",
  "files": [
   {
    "file": "routines.sql",
    "role": "the file under test (Task 4)",
    "href": "../deliverables/routines.sql"
   },
   {
    "file": "routines_example_usage.sql",
    "role": "example usage, not a deliverable: calls each routine once and rolls back",
    "href": "../examples/routines_example_usage.sql"
   },
   {
    "file": "test_routines.py",
    "role": "the tests: contract, behaviour cases, file coverage",
    "href": "../tests/test_routines.py"
   },
   {
    "file": "oracle_routines.py",
    "role": "the independent answers: what each routine must write, return or refuse, in plain Python from data.csv",
    "href": "../tests/oracle_routines.py"
   },
   {
    "file": "conftest.py",
    "role": "shared set-up: finds the files, connects, splits routines.sql at its DELIMITER lines, writes the results snapshot",
    "href": "../tests/conftest.py"
   },
   {
    "file": "use_cases.json",
    "role": "the use cases: their RA evidence and the columns each routine may read or write (routineColumns)",
    "href": "../data/use_cases.json"
   },
   {
    "file": "data.csv",
    "role": "the Project 1 sample data the oracle reads",
    "href": "../../project1/data_export/data.csv"
   },
   {
    "file": "database_implementation.sql",
    "role": "builds the database the routines run on (--fresh)",
    "href": "../deliverables/database_implementation.sql"
   },
   {
    "file": "pytest.ini",
    "role": "pytest settings (verbose, no cache folder)",
    "href": "../tests/pytest.ini"
   },
   {
    "file": "requirements.txt",
    "role": "pytest, PyMySQL, cryptography (MySQL 8 sign-in)",
    "href": "../tests/requirements.txt"
   },
   {
    "file": "test_routines_guide.pdf",
    "role": "how to run the tests locally, what they cover and what they could miss",
    "href": "../docs/test_routines_guide.pdf"
   },
   {
    "file": "mutate_routines.py",
    "role": "tests the tests: breaks routines.sql 20 ways, one at a time, and checks every break is caught (repo only)",
    "href": "../scripts/mutate_routines.py"
   }
  ],
  "bundle": {
   "file": "crossfade_routines_tests.zip",
   "role": "the tests, the oracle, every input file and the guide, in one folder that runs as-is",
   "href": "../tests/crossfade_routines_tests.zip",
   "bytes": 179856,
   "contents": [
    "test_routines.py",
    "oracle_routines.py",
    "conftest.py",
    "pytest.ini",
    "requirements.txt",
    "routines.sql",
    "routines_example_usage.sql",
    "database_implementation.sql",
    "data.csv",
    "use_cases.json",
    "test_routines_guide.pdf",
    "rubric_routines.md",
    "use_case_reference.pdf",
    "README.txt"
   ]
  },
  "sources": [
   {
    "name": "Independent answers",
    "from": "oracle_routines.py + data.csv",
    "how": "What each routine must write, return or refuse, worked out in plain Python from data.csv and the RA's rules, no SQL. MySQL must agree value for value, including the error code of every refusal."
   },
   {
    "name": "MySQL's catalogue",
    "from": "information_schema.ROUTINES, PARAMETERS",
    "how": "Each routine's kind, parameters, return type and data-access characteristic, as MySQL stored them, compared with the comment."
   },
   {
    "name": "The RA's integrity rules",
    "from": "requirements_analysis.pdf",
    "how": "I7 (completed and royalty computed by the procedure that records a play, once, never updated), I6 (shared stations), the play key that keeps a double-counted royalty out of the ledger, and \"the procedures do not accept derived values as input\"."
   },
   {
    "name": "Live behaviour",
    "from": "rolled-back calls, two connections, a test trigger",
    "how": "Every call runs in a transaction that is rolled back; the race uses two connections; the RESIGNAL branch is forced with a temporary trigger, dropped afterwards."
   },
   {
    "name": "The brief and the slides",
    "from": "info579_project02.pdf, Unit 9",
    "how": "2 procedures + 1 function or 1 + 2, in one file; DELIMITER, DECLARE, IF, SIGNAL, handlers and IN / OUT parameters from Unit 9."
   }
  ],
  "groups": [
   {
    "group": "contract",
    "tests": 18,
    "passed": 18,
    "text": "Each routine is preceded by a purpose comment with its tag and name, use cases, business need, what it does step by step, the requirement, the Unit 9 features it uses, its tables, parameters, return type, errors and an example call. MySQL's own catalogue (information_schema.ROUTINES and PARAMETERS) holds it exactly as declared: its kind, every parameter in order with mode, name and type, and a function's return type. The characteristic tells the truth (a function that reads tables is READS SQL DATA and NOT DETERMINISTIC; a procedure that writes is MODIFIES SQL DATA). Every feature listed under Uses: is in the body. It names exactly the tables listed, counting those of a routine it calls, and every column it touches is declared by one of its use cases."
   },
   {
    "group": "behaviour",
    "tests": 24,
    "passed": 24,
    "text": "Each routine is called on the crossfade database and compared with an independent answer computed in plain Python from data.csv (oracle_routines.py): the row a procedure writes, its OUT values, a function's result, and the refusals it must give, both its own SIGNALs and the database's errors it must not swallow. Every call runs inside a transaction that is rolled back. Two cases go further: two connections upload at the same moment, and a temporary trigger forces a primary-key clash so the handler's RESIGNAL branch runs."
   },
   {
    "group": "coverage",
    "tests": 8,
    "passed": 8,
    "text": "The file as a whole: the brief's mix (2 procedures + 1 function, or 1 + 2); tags F1.., P1.. in order; every use case with routine columns served, and every declared column touched by a routine serving it; the RA's rule that procedures take no derived values as input; no transaction control inside a routine; and the script itself: it re-creates the routines when run again and only creates them; the example usage script (project2/examples/routines_example_usage.sql, not a deliverable) leaves the data unchanged and returns what its comments promise."
   }
  ],
  "coverage": {
   "columns": [
    {
     "key": "contract",
     "label": "Comment fields"
    },
    {
     "key": "catalogue",
     "label": "Catalogue (MySQL)"
    },
    {
     "key": "access",
     "label": "Data access"
    },
    {
     "key": "uses",
     "label": "Uses: features"
    },
    {
     "key": "tables",
     "label": "Tables"
    },
    {
     "key": "cols",
     "label": "Columns declared"
    },
    {
     "key": "cases",
     "label": "Behaviour cases"
    },
    {
     "key": "m_fn",
     "label": "Function",
     "mark": true
    },
    {
     "key": "m_proc",
     "label": "Procedure",
     "mark": true
    },
    {
     "key": "m_signal",
     "label": "SIGNAL",
     "mark": true
    },
    {
     "key": "m_handler",
     "label": "HANDLER",
     "mark": true
    }
   ],
   "rows": [
    {
     "key": "F1",
     "label": "F1",
     "sub": "play_royalty"
    },
    {
     "key": "P1",
     "label": "P1",
     "sub": "record_play"
    },
    {
     "key": "P2",
     "label": "P2",
     "sub": "upload_track"
    }
   ],
   "cells": {
    "F1": {
     "contract": [
      1,
      1
     ],
     "catalogue": [
      1,
      1
     ],
     "access": [
      1,
      1
     ],
     "uses": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "cases": [
      4,
      4
     ],
     "m_fn": [
      1,
      1
     ],
     "m_proc": [
      0,
      0
     ],
     "m_signal": [
      0,
      0
     ],
     "m_handler": [
      0,
      0
     ]
    },
    "P1": {
     "contract": [
      1,
      1
     ],
     "catalogue": [
      1,
      1
     ],
     "access": [
      1,
      1
     ],
     "uses": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "cases": [
      12,
      12
     ],
     "m_fn": [
      0,
      0
     ],
     "m_proc": [
      1,
      1
     ],
     "m_signal": [
      1,
      1
     ],
     "m_handler": [
      0,
      0
     ]
    },
    "P2": {
     "contract": [
      1,
      1
     ],
     "catalogue": [
      1,
      1
     ],
     "access": [
      1,
      1
     ],
     "uses": [
      1,
      1
     ],
     "tables": [
      1,
      1
     ],
     "cols": [
      1,
      1
     ],
     "cases": [
      8,
      8
     ],
     "m_fn": [
      0,
      0
     ],
     "m_proc": [
      1,
      1
     ],
     "m_signal": [
      1,
      1
     ],
     "m_handler": [
      1,
      1
     ]
    }
   },
   "whole": [
    {
     "test": "test_brief_routine_mix",
     "outcome": "passed"
    },
    {
     "test": "test_tags_are_unique_and_in_order",
     "outcome": "passed"
    },
    {
     "test": "test_every_routine_use_case_is_served",
     "outcome": "passed"
    },
    {
     "test": "test_declared_columns_are_touched",
     "outcome": "passed"
    },
    {
     "test": "test_no_derived_values_as_input",
     "outcome": "passed"
    },
    {
     "test": "test_no_transaction_control_inside",
     "outcome": "passed"
    },
    {
     "test": "test_script_reruns_and_leaves_data_unchanged",
     "outcome": "passed"
    },
    {
     "test": "test_example_usage_gives_the_documented_answers",
     "outcome": "passed"
    }
   ],
   "caption": "tests per routine and check; ✓ = what the routine is and uses"
  },
  "misses": [
   {
    "title": "Independent code, not an independent reading",
    "what": "The oracle was written from the same comments and RA rules as the routines. If a rule was misread (what 'released' means, whether 30 seconds exactly qualifies), the routine and its expected answer agree.",
    "cover": "Each comment quotes the RA rule it applies; a second reader."
   },
   {
    "title": "Columns found by name, not by plan",
    "what": "EXPLAIN cannot see inside a routine, so the column check counts the column names that appear in its body. A name shared by two tables it uses (track_id, artist_id) counts for both.",
    "cover": "The tables are checked separately; the behaviour cases check what is actually written."
   },
   {
    "title": "One interleaving of a race",
    "what": "The simultaneous-upload case runs one timing: A uploads, B waits, A commits. On MySQL 8 the second upload's ID lookup waits for the first, so B takes the next ID; other timings, and other servers, are not tried.",
    "cover": "The handler's RESIGNAL branch is tested directly with a forced key clash."
   },
   {
    "title": "A forced clash, not a natural one",
    "what": "The primary-key clash that RESIGNAL guards against is produced by a temporary trigger, because it does not happen on its own here. The test proves the branch works, not how often it is needed.",
    "cover": "The comment says the branch is defensive."
   },
   {
    "title": "Permissions not tested",
    "what": "The RA grants the application EXECUTE on the procedures and no direct writes, making them the only write path. The tests run as root and do not check grants (they are not part of the brief).",
    "cover": "Not required by the brief."
   },
   {
    "title": "One time zone",
    "what": "\"Recorded in UTC\" is tested with the session set to UTC-7 (Arizona). Other offsets and daylight-saving changes are not tried.",
    "cover": "UTC_TIMESTAMP ignores the session time zone by definition."
   },
   {
    "title": "Comments checked for shape, not truth",
    "what": "Every field must be present and agree with MySQL (kind, parameters, tables, features). Whether the business reasoning is sound is not testable.",
    "cover": "The comments cite the RA."
   }
  ],
  "findings": [
   {
    "title": "The deliberate-mistake run had a blind spot of its own (now fixed)",
    "text": "Its first run reported one mistake missed: catching every error instead of only 1062. The edit had landed in the file's header comment, where the same words appear, so the routine never changed. The edit now names the handler's own code line, and that mistake is caught. The other 19 edits were checked by hand to land where they mean to: 16 in code, 3 in the comment fields the contract tests read."
   },
   {
    "title": "Simultaneous uploads wait for each other on MySQL 8",
    "text": "The two-connection case showed that the second upload's lookup of the next track ID waits for the first upload to commit, then takes the next ID. The primary-key clash the handler re-raises (RESIGNAL) therefore does not occur on its own here; the branch is tested with a forced clash."
   }
  ],
  "run": [
   {
    "title": "What you need",
    "text": "A running MySQL Server 8.0.16 or later and its root password; Python 3.10 or later. --fresh builds the database; the tests create the routines themselves by running routines.sql.",
    "code": null
   },
   {
    "title": "Get the files",
    "text": "Download crossfade_routines_tests.zip with the button above and extract it. It holds one folder, crossfade_routines_tests, with the tests, the oracle, routines.sql, database_implementation.sql, data.csv, use_cases.json and the guide.",
    "code": "Expand-Archive -Force $HOME\\Downloads\\crossfade_routines_tests.zip .\ncd .\\crossfade_routines_tests"
   },
   {
    "title": "Set up Python (once)",
    "text": "A virtual environment with the three packages. macOS / Linux: python3 and .venv/bin/python.",
    "code": "python -m venv .venv\n.venv\\Scripts\\python -m pip install -r requirements.txt"
   },
   {
    "title": "Run the tests",
    "text": "--fresh rebuilds the crossfade database from database_implementation.sql first. The tests then run routines.sql (it drops and re-creates the three routines) and call each one; every write is rolled back, and the race and key-clash cases delete what they add.",
    "code": "$env:CROSSFADE_DB_PASSWORD = \"your-root-password\"\n.venv\\Scripts\\python -m pytest --fresh"
   },
   {
    "title": "Read the result",
    "text": "One line per test, then a summary. A failure names the comment field, catalogue entry, column, value or error code that differs from the oracle.",
    "code": "collected 50 items\ntest_routines.py::test_comment_contract[F1] PASSED   [  2%]\n...\n========== 50 passed in 1.0s =========="
   }
  ],
  "mutants": {
   "mutants": [
    {
     "mutant": "f1-thirty-seconds-excluded",
     "query": "F1",
     "mistake": "a play of exactly 30 seconds earns nothing (> instead of >=)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_f1_thirty_seconds_is_the_boundary",
      "test_f1_follows_a_rate_change",
      "test_example_usage_gives_the_documented_answers"
     ]
    },
    {
     "mutant": "f1-unknown-is-zero",
     "query": "F1",
     "mistake": "a recording that does not exist earns 0 instead of NULL",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_f1_unknown_recording_has_no_royalty"
     ]
    },
    {
     "mutant": "f1-one-rate-for-all",
     "query": "F1",
     "mistake": "every recording paid at one artist's rate (join condition wrong)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_f1_agrees_with_every_recorded_play",
      "test_p1_full_length_play_is_completed",
      "test_p1_shared_station_is_accepted"
     ]
    },
    {
     "mutant": "f1-declared-deterministic",
     "query": "F1",
     "mistake": "declared DETERMINISTIC, though the rate it reads can change",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_data_access_declared[F1]",
      "test_uses_what_it_lists[F1]"
     ]
    },
    {
     "mutant": "f1-declared-no-sql",
     "query": "F1",
     "mistake": "declared NO SQL, though it reads two tables",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_data_access_declared[F1]",
      "test_uses_what_it_lists[F1]"
     ]
    },
    {
     "mutant": "p1-completed-at-thirty",
     "query": "P1",
     "mistake": "completed means 30 seconds or more, not the whole recording",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_p1_records_an_abandoned_skip",
      "test_p1_ledger_survives_a_rate_change",
      "test_example_usage_gives_the_documented_answers"
     ]
    },
    {
     "mutant": "p1-awaiting-scoring-allowed",
     "query": "P1",
     "mistake": "only rejected recordings refused: one awaiting scoring can be streamed",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_p1_refuses_an_invalid_play[awaiting_scoring]"
     ]
    },
    {
     "mutant": "p1-full-play-refused",
     "query": "P1",
     "mistake": "a play as long as the recording refused (>= instead of >)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_p1_full_length_play_is_completed",
      "test_p1_shared_station_is_accepted",
      "test_p1_repeated_report_is_rejected"
     ]
    },
    {
     "mutant": "p1-fixed-royalty",
     "query": "P1",
     "mistake": "a fixed royalty instead of the artist's rate through play_royalty",
     "caught": true,
     "failed": 5,
     "first_failures": [
      "test_reads_declared_tables[P1]",
      "test_p1_full_length_play_is_completed",
      "test_p1_short_play_earns_nothing",
      "test_p1_shared_station_is_accepted"
     ]
    },
    {
     "mutant": "p1-local-time",
     "query": "P1",
     "mistake": "no time given: local time (NOW) instead of UTC",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_p1_no_time_given_records_utc_now"
     ]
    },
    {
     "mutant": "p1-station-dropped",
     "query": "P1",
     "mistake": "the station that surfaced the play not recorded",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_p1_shared_station_is_accepted"
     ]
    },
    {
     "mutant": "p1-swallows-repeats",
     "query": "P1",
     "mistake": "a repeated report of a play silently ignored (CONTINUE HANDLER FOR 1062)",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_p1_repeated_report_is_rejected"
     ]
    },
    {
     "mutant": "p1-uses-line-wrong",
     "query": "P1",
     "mistake": "the comment lists a feature the procedure does not use",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_uses_what_it_lists[P1]"
     ]
    },
    {
     "mutant": "p1-parameter-line-wrong",
     "query": "P1",
     "mistake": "the comment declares a parameter type MySQL does not have",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_created_as_declared[P1]"
     ]
    },
    {
     "mutant": "p2-handler-for-every-error",
     "query": "P2",
     "mistake": "the handler catches every error, not just 1062",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_uses_what_it_lists[P2]",
      "test_p2_handler_catches_only_duplicates"
     ]
    },
    {
     "mutant": "p2-no-resignal",
     "query": "P2",
     "mistake": "a key clash on the new track ID reported as a duplicate (RESIGNAL removed)",
     "caught": true,
     "failed": 2,
     "first_failures": [
      "test_uses_what_it_lists[P2]",
      "test_p2_key_clash_is_not_reported_as_a_duplicate"
     ]
    },
    {
     "mutant": "p2-enters-as-scored",
     "query": "P2",
     "mistake": "an upload enters the catalogue as scored, skipping the pipeline",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_p2_new_upload_awaits_scoring"
     ]
    },
    {
     "mutant": "p2-reuses-an-id",
     "query": "P2",
     "mistake": "the new track takes the highest existing ID instead of the next one",
     "caught": true,
     "failed": 35,
     "first_failures": [
      "test_comment_contract[F1]",
      "test_comment_contract[P1]",
      "test_comment_contract[P2]",
      "test_created_as_declared[F1]"
     ]
    },
    {
     "mutant": "p2-artist-not-checked",
     "query": "P2",
     "mistake": "an unregistered artist is not refused in words (left to the foreign key)",
     "caught": true,
     "failed": 3,
     "first_failures": [
      "test_reads_declared_tables[P2]",
      "test_p2_unregistered_artist_is_refused",
      "test_declared_columns_are_touched"
     ]
    },
    {
     "mutant": "p2-tables-line-wrong",
     "query": "P2",
     "mistake": "artist left off the comment's Tables line",
     "caught": true,
     "failed": 1,
     "first_failures": [
      "test_reads_declared_tables[P2]"
     ]
    }
   ],
   "caught": 20,
   "total": 20,
   "not_applicable": [],
   "real_file": "========================= 1 failed, 49 passed in 0.85s =========================",
   "already_failing": []
  }
 }
};
