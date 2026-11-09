/* Written by project2/tests (pytest) at the end of a run. Do not edit. */
window.P2_SINGLE = {
 "file": "single_table.sql",
 "generated": "2026-11-08T20:01:18",
 "passed": 71,
 "failed": 0,
 "queries": {
  "S1": {
   "table": "artist",
   "use_cases": [
    "UC-02",
    "UC-01"
   ],
   "question": "Is each artist ready for this royalty run, and if not, which check is outstanding?",
   "need": "CROSSFADE pays every artist a per-stream royalty (RA: Overview; Artist). Two artist fields bear on whether a payment can go out: Verified, \"whether the service has confirmed the artist's identity and their right to licence the material they upload\", and Country, used \"to determine which royalty payment channels and tax treatments apply\" (RA: Artist).",
   "declared": [
    "a",
    "c",
    "e"
   ],
   "output": [
    "artist_id",
    "stage_name",
    "usd_per_1000_streams",
    "days_under_licence",
    "licence_check",
    "payment_country",
    "run_status"
   ],
   "sql": "SELECT artist_id,\n       stage_name,\n       ROUND(payout_rate * 1000, 2) AS usd_per_1000_streams,\n       DATEDIFF('2026-09-30', joined_date) AS days_under_licence,\n       IF(verified = 1, 'confirmed', 'HOLD: not confirmed') AS licence_check,\n       IF(country IS NULL, 'HOLD: no country', country) AS payment_country,\n       CASE\n           WHEN verified = 1 AND country IS NOT NULL THEN 'ready'\n           ELSE 'held'\n       END AS run_status\nFROM crossfade.artist\nORDER BY run_status DESC,\n         payout_rate DESC,\n         artist_id",
   "detected": [
    "a",
    "c",
    "e"
   ],
   "columns": [
    "artist_id",
    "country",
    "joined_date",
    "payout_rate",
    "stage_name",
    "verified"
   ],
   "columns_out": [
    "artist_id",
    "stage_name",
    "usd_per_1000_streams",
    "days_under_licence",
    "licence_check",
    "payment_country",
    "run_status"
   ],
   "rows": [
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "expected": {
    "columns": [
     "artist_id",
     "stage_name",
     "usd_per_1000_streams",
     "days_under_licence",
     "licence_check",
     "payment_country",
     "run_status"
    ],
    "rows": [
     [
      "1042",
      "Velvet Static",
      "4.00",
      "200",
      "confirmed",
      "US",
      "ready"
     ],
     [
      "1044",
      "Low Orbit Choir",
      "3.80",
      "239",
      "confirmed",
      "CA",
      "ready"
     ],
     [
      "1046",
      "Ochre Parade",
      "3.60",
      "172",
      "confirmed",
      "MX",
      "ready"
     ],
     [
      "1043",
      "Mara Quell",
      "3.50",
      "253",
      "confirmed",
      "GB",
      "ready"
     ],
     [
      "1047",
      "Juno Fleet",
      "3.00",
      "151",
      "confirmed",
      "DE",
      "ready"
     ],
     [
      "1049",
      "Kestrel Ave",
      "3.40",
      "33",
      "HOLD: not confirmed",
      "JM",
      "held"
     ],
     [
      "1045",
      "Tin Harbour",
      "3.20",
      "215",
      "HOLD: not confirmed",
      "AU",
      "held"
     ],
     [
      "1048",
      "Saltmarsh Tapes",
      "3.00",
      "134",
      "HOLD: not confirmed",
      "HOLD: no country",
      "held"
     ]
    ]
   }
  },
  "S2": {
   "table": "track",
   "use_cases": [
    "UC-03"
   ],
   "question": "What are the five newest recordings listeners can stream?",
   "need": "a recording uploaded an hour ago must be as recommendable as one with a million plays (RA: Overview), and only scored recordings may be streamed (RA: Track).",
   "declared": [
    "a",
    "c",
    "d"
   ],
   "output": [
    "track_id",
    "title",
    "run_time",
    "release_date",
    "days_since_release"
   ],
   "sql": "SELECT track_id,\n       title,\n       CONCAT(duration DIV 60, ':', LPAD(MOD(duration, 60), 2, '0')) AS run_time,\n       release_date,\n       DATEDIFF('2026-09-30', release_date) AS days_since_release\nFROM crossfade.track\nWHERE ingest_status = 'scored'\nORDER BY release_date DESC,\n         track_id\nLIMIT 5",
   "detected": [
    "a",
    "c",
    "d"
   ],
   "columns": [
    "duration",
    "ingest_status",
    "release_date",
    "title",
    "track_id"
   ],
   "columns_out": [
    "track_id",
    "title",
    "run_time",
    "release_date",
    "days_since_release"
   ],
   "rows": [
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ],
    [
     "4829",
     "Tapeworm Blues",
     "3:09",
     "2026-06-05",
     "117"
    ],
    [
     "4827",
     "Stahlwerk",
     "4:14",
     "2026-05-25",
     "128"
    ],
    [
     "4822",
     "Hymn for a Server Room",
     "4:28",
     "2026-05-15",
     "138"
    ]
   ],
   "expected": {
    "columns": [
     "track_id",
     "title",
     "run_time",
     "release_date",
     "days_since_release"
    ],
    "rows": [
     [
      "4828",
      "Afterimage Club",
      "3:41",
      "2026-07-10",
      "82"
     ],
     [
      "4826",
      "Plaza at Noon",
      "3:18",
      "2026-06-30",
      "92"
     ],
     [
      "4829",
      "Tapeworm Blues",
      "3:09",
      "2026-06-05",
      "117"
     ],
     [
      "4827",
      "Stahlwerk",
      "4:14",
      "2026-05-25",
      "128"
     ],
     [
      "4822",
      "Hymn for a Server Room",
      "4:28",
      "2026-05-15",
      "138"
     ]
    ]
   }
  },
  "S3": {
   "table": "genre",
   "use_cases": [
    "UC-05"
   ],
   "question": "How wide must the composer's label column be, which genre sets that width, and how much of its one 80-character line does each description use?",
   "need": "listeners compose station blends from the genre legend, which shows each genre's label and its description (RA: Genre). The RA sizes both for that display: the ten labels are fixed and \"the longest, classical, has nine characters\" (RA: Name), and a description is \"kept to one line of 80 characters\" (RA: Description).",
   "declared": [
    "a",
    "b",
    "c",
    "e"
   ],
   "output": [
    "model_class_index",
    "label",
    "label_chars",
    "label_column",
    "description_chars",
    "chars_left_on_line"
   ],
   "sql": "SELECT genre_id AS model_class_index,\n       name AS label,\n       CHAR_LENGTH(name) AS label_chars,\n       IF(CHAR_LENGTH(name) = (SELECT MAX(CHAR_LENGTH(name)) FROM crossfade.genre),\n          'sets the column width', 'fits') AS label_column,\n       CHAR_LENGTH(description) AS description_chars,\n       80 - CHAR_LENGTH(description) AS chars_left_on_line\nFROM crossfade.genre\nORDER BY genre_id",
   "detected": [
    "a",
    "b",
    "c",
    "e"
   ],
   "columns": [
    "description",
    "genre_id",
    "name"
   ],
   "columns_out": [
    "model_class_index",
    "label",
    "label_chars",
    "label_column",
    "description_chars",
    "chars_left_on_line"
   ],
   "rows": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classical",
     "9",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "fits",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "41",
     "39"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     "40",
     "40"
    ]
   ],
   "expected": {
    "columns": [
     "model_class_index",
     "label",
     "label_chars",
     "label_column",
     "description_chars",
     "chars_left_on_line"
    ],
    "rows": [
     [
      "0",
      "blues",
      "5",
      "fits",
      "59",
      "21"
     ],
     [
      "1",
      "classical",
      "9",
      "sets the column width",
      "65",
      "15"
     ],
     [
      "2",
      "country",
      "7",
      "fits",
      "57",
      "23"
     ],
     [
      "3",
      "disco",
      "5",
      "fits",
      "58",
      "22"
     ],
     [
      "4",
      "hiphop",
      "6",
      "fits",
      "56",
      "24"
     ],
     [
      "5",
      "jazz",
      "4",
      "fits",
      "41",
      "39"
     ],
     [
      "6",
      "metal",
      "5",
      "fits",
      "54",
      "26"
     ],
     [
      "7",
      "pop",
      "3",
      "fits",
      "40",
      "40"
     ],
     [
      "8",
      "reggae",
      "6",
      "fits",
      "45",
      "35"
     ],
     [
      "9",
      "rock",
      "4",
      "fits",
      "40",
      "40"
     ]
    ]
   }
  },
  "S4": {
   "table": "listener",
   "use_cases": [
    "UC-06"
   ],
   "question": "How many subscribers does each plan tier have, when did the first and latest join, and how long has the average subscriber been billing?",
   "need": "subscribers are billed by plan tier, each from their own signup date (RA: Listener: Plan Tier, Signup Date).",
   "declared": [
    "a",
    "b",
    "c"
   ],
   "output": [
    "plan_tier",
    "listeners",
    "first_signup",
    "latest_signup",
    "avg_days_subscribed"
   ],
   "sql": "SELECT plan_tier,\n       COUNT(*) AS listeners,\n       MIN(signup_date) AS first_signup,\n       MAX(signup_date) AS latest_signup,\n       ROUND(AVG(DATEDIFF('2026-09-30', signup_date))) AS avg_days_subscribed\nFROM crossfade.listener\nGROUP BY plan_tier\nORDER BY plan_tier DESC",
   "detected": [
    "a",
    "b",
    "c"
   ],
   "columns": [
    "plan_tier",
    "signup_date"
   ],
   "columns_out": [
    "plan_tier",
    "listeners",
    "first_signup",
    "latest_signup",
    "avg_days_subscribed"
   ],
   "rows": [
    [
     "premium",
     "2",
     "2026-04-02",
     "2026-05-27",
     "154"
    ],
    [
     "standard",
     "3",
     "2026-05-09",
     "2026-07-08",
     "116"
    ],
    [
     "free",
     "3",
     "2026-04-18",
     "2026-08-15",
     "104"
    ]
   ],
   "expected": {
    "columns": [
     "plan_tier",
     "listeners",
     "first_signup",
     "latest_signup",
     "avg_days_subscribed"
    ],
    "rows": [
     [
      "premium",
      "2",
      "2026-04-02",
      "2026-05-27",
      "154"
     ],
     [
      "standard",
      "3",
      "2026-05-09",
      "2026-07-08",
      "116"
     ],
     [
      "free",
      "3",
      "2026-04-18",
      "2026-08-15",
      "104"
     ]
    ]
   }
  },
  "S5": {
   "table": "scoring_model",
   "use_cases": [
    "UC-08"
   ],
   "question": "Which model version should a new station default to?",
   "need": "each scoring model version is weighted by its measured holdout accuracy, and versions trained on different corpora are never silently compared (RA: Scoring Model).",
   "declared": [
    "a",
    "c",
    "d"
   ],
   "output": [
    "version_label",
    "architecture",
    "accuracy_pct",
    "deployed_on"
   ],
   "sql": "SELECT version_label,\n       CONCAT(fusion_type, ' / ', embedding_dimension, 'd / ', segment_length, 's / ', training_corpus) AS architecture,\n       ROUND(holdout_accuracy * 100, 2) AS accuracy_pct,\n       deployed_on\nFROM crossfade.scoring_model\nORDER BY holdout_accuracy DESC,\n         deployed_on DESC,\n         model_id\nLIMIT 1",
   "detected": [
    "a",
    "c",
    "d"
   ],
   "columns": [
    "deployed_on",
    "embedding_dimension",
    "fusion_type",
    "holdout_accuracy",
    "model_id",
    "segment_length",
    "training_corpus",
    "version_label"
   ],
   "columns_out": [
    "version_label",
    "architecture",
    "accuracy_pct",
    "deployed_on"
   ],
   "rows": [
    [
     "beardown_3sec",
     "concat / 384d / 3s / GTZAN",
     "78.87",
     "2026-06-23"
    ]
   ],
   "expected": {
    "columns": [
     "version_label",
     "architecture",
     "accuracy_pct",
     "deployed_on"
    ],
    "rows": [
     [
      "beardown_3sec",
      "concat / 384d / 3s / GTZAN",
      "78.87",
      "2026-06-23"
     ]
    ]
   }
  },
  "S6": {
   "table": "station",
   "use_cases": [
    "UC-10",
    "UC-08"
   ],
   "question": "How many stations does each model version serve, how wide are their ambiguity windows, and since when has each version been relied on?",
   "need": "every station is evaluated against one nominated model version inside an ambiguity window (RA: Station; Scoring Model 1:N Station), so retiring or redeploying a version changes the stations that rely on it.",
   "declared": [
    "a",
    "b",
    "c",
    "e"
   ],
   "output": [
    "model_id",
    "stations",
    "avg_window",
    "wide_stations",
    "oldest_station"
   ],
   "sql": "SELECT model_id,\n       COUNT(*) AS stations,\n       ROUND(AVG(maximum_ambiguity - minimum_ambiguity), 2) AS avg_window,\n       SUM(CASE WHEN maximum_ambiguity - minimum_ambiguity > 0.5 THEN 1 ELSE 0 END) AS wide_stations,\n       MIN(created_on) AS oldest_station\nFROM crossfade.station\nGROUP BY model_id\nORDER BY stations DESC,\n         model_id",
   "detected": [
    "a",
    "b",
    "c",
    "e"
   ],
   "columns": [
    "created_on",
    "maximum_ambiguity",
    "minimum_ambiguity",
    "model_id"
   ],
   "columns_out": [
    "model_id",
    "stations",
    "avg_window",
    "wide_stations",
    "oldest_station"
   ],
   "rows": [
    [
     "4",
     "3",
     "0.57",
     "2",
     "2026-06-10"
    ],
    [
     "2",
     "2",
     "0.60",
     "2",
     "2026-05-02"
    ],
    [
     "5",
     "2",
     "0.50",
     "1",
     "2026-07-20"
    ],
    [
     "1",
     "1",
     "0.60",
     "1",
     "2026-05-20"
    ]
   ],
   "expected": {
    "columns": [
     "model_id",
     "stations",
     "avg_window",
     "wide_stations",
     "oldest_station"
    ],
    "rows": [
     [
      "4",
      "3",
      "0.57",
      "2",
      "2026-06-10"
     ],
     [
      "2",
      "2",
      "0.60",
      "2",
      "2026-05-02"
     ],
     [
      "5",
      "2",
      "0.50",
      "1",
      "2026-07-20"
     ],
     [
      "1",
      "1",
      "0.60",
      "1",
      "2026-05-20"
     ]
    ]
   }
  },
  "S7": {
   "table": "track",
   "use_cases": [
    "UC-04"
   ],
   "question": "How many recordings sit at each stage of the upload pipeline, and is scoring keeping up with their release dates?",
   "need": "every upload is scored before it can be streamed (RA: Track; its stages: Ingest Status), so a backlog in the upload pipeline must be visible.",
   "declared": [
    "a",
    "b",
    "c",
    "e"
   ],
   "output": [
    "ingest_status",
    "recordings",
    "earliest_release",
    "days_to_earliest_release",
    "release_status"
   ],
   "sql": "SELECT ingest_status,\n       COUNT(*) AS recordings,\n       MIN(release_date) AS earliest_release,\n       DATEDIFF(MIN(release_date), '2026-09-30') AS days_to_earliest_release,\n       CASE\n           WHEN ingest_status = 'scored' THEN 'streamable'\n           WHEN ingest_status = 'rejected' THEN 'never streamable: rejected'\n           WHEN MIN(release_date) <= '2026-09-30' THEN 'LATE: release date reached, still unscored'\n           ELSE 'on time: release date still ahead'\n       END AS release_status\nFROM crossfade.track\nGROUP BY ingest_status\nORDER BY ingest_status",
   "detected": [
    "a",
    "b",
    "c",
    "e"
   ],
   "columns": [
    "ingest_status",
    "release_date"
   ],
   "columns_out": [
    "ingest_status",
    "recordings",
    "earliest_release",
    "days_to_earliest_release",
    "release_status"
   ],
   "rows": [
    [
     "awaiting scoring",
     "1",
     "2026-09-21",
     "-9",
     "LATE: release date reached, still unscored"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "1",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "expected": {
    "columns": [
     "ingest_status",
     "recordings",
     "earliest_release",
     "days_to_earliest_release",
     "release_status"
    ],
    "rows": [
     [
      "awaiting scoring",
      "1",
      "2026-09-21",
      "-9",
      "LATE: release date reached, still unscored"
     ],
     [
      "scored",
      "13",
      "2026-02-25",
      "-217",
      "streamable"
     ],
     [
      "rejected",
      "1",
      "2026-09-22",
      "-8",
      "never streamable: rejected"
     ]
    ]
   }
  },
  "E1": {
   "table": "track",
   "use_cases": [
    "UC-15"
   ],
   "question": "What happens when an artist uploads an audio file that is already in the catalogue?",
   "need": "a re-upload of the same audio file must never become a second catalogue entry earning a second royalty stream; the RA keeps the audio checksum (SHA-256 of the file) to \"detect duplicate uploads\" (RA: Track: Audio Checksum).",
   "sql": "INSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)\nSELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', audio_checksum, 'awaiting scoring'\nFROM crossfade.track\nWHERE track_id = 4817",
   "kind": "expected_error",
   "disabled": true,
   "expects": "1062 uq_track_audio_checksum",
   "got": "1062 Duplicate entry '\\xBDg]H6=\\xAA\\xFD\\xCE\\xF5%R\\xAB\\xD9\\x8D#\\x02\\xAE4\\xC5\\x8Aj\\xEB\\x' for key 'track.uq_track_audio_checksum'"
  }
 },
 "tests": {
  "S1": [
   {
    "test": "test_comment_contract[S1]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S1]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S1]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S1]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S1]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S1]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S1]",
    "outcome": "passed"
   }
  ],
  "S2": [
   {
    "test": "test_comment_contract[S2]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S2]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S2]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S2]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S2]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S2]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S2]",
    "outcome": "passed"
   }
  ],
  "S3": [
   {
    "test": "test_comment_contract[S3]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S3]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S3]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S3]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S3]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S3]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S3]",
    "outcome": "passed"
   }
  ],
  "S4": [
   {
    "test": "test_comment_contract[S4]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S4]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S4]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S4]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S4]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S4]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S4]",
    "outcome": "passed"
   }
  ],
  "S5": [
   {
    "test": "test_comment_contract[S5]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S5]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S5]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S5]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S5]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S5]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S5]",
    "outcome": "passed"
   }
  ],
  "S6": [
   {
    "test": "test_comment_contract[S6]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S6]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S6]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S6]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S6]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S6]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S6]",
    "outcome": "passed"
   }
  ],
  "S7": [
   {
    "test": "test_comment_contract[S7]",
    "outcome": "passed"
   },
   {
    "test": "test_read_only_select[S7]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_exactly_one_table[S7]",
    "outcome": "passed"
   },
   {
    "test": "test_requirements_match_declared[S7]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_match_use_cases[S7]",
    "outcome": "passed"
   },
   {
    "test": "test_result_matches_oracle[S7]",
    "outcome": "passed"
   },
   {
    "test": "test_result_is_deterministic[S7]",
    "outcome": "passed"
   }
  ],
  "file": [
   {
    "test": "test_s1_verified_artist_without_country_is_held_for_country_alone",
    "outcome": "passed"
   },
   {
    "test": "test_s1_held_artist_never_outranks_a_ready_one",
    "outcome": "passed"
   },
   {
    "test": "test_s1_equal_rates_break_ties_on_artist_id",
    "outcome": "passed"
   },
   {
    "test": "test_s2_unscored_new_release_stays_off_the_shelf",
    "outcome": "passed"
   },
   {
    "test": "test_s2_same_day_releases_order_by_track_id",
    "outcome": "passed"
   },
   {
    "test": "test_s2_shelf_never_holds_more_than_five",
    "outcome": "passed"
   },
   {
    "test": "test_s3_genre_without_description_has_no_line_figures",
    "outcome": "passed"
   },
   {
    "test": "test_s3_label_width_follows_the_data_and_ties_share_it",
    "outcome": "passed"
   },
   {
    "test": "test_s3_description_length_counts_characters_not_bytes",
    "outcome": "passed"
   },
   {
    "test": "test_s4_tier_with_no_listeners_is_absent",
    "outcome": "passed"
   },
   {
    "test": "test_s5_accuracy_tie_prefers_the_newer_version",
    "outcome": "passed"
   },
   {
    "test": "test_s5_full_tie_goes_to_the_lower_model_id",
    "outcome": "passed"
   },
   {
    "test": "test_s6_window_of_exactly_half_is_not_wide",
    "outcome": "passed"
   },
   {
    "test": "test_s7_new_rejection_is_counted_in_pipeline_order",
    "outcome": "passed"
   },
   {
    "test": "test_s7_unscored_recording_before_its_release_is_on_time",
    "outcome": "passed"
   },
   {
    "test": "test_s7_release_due_on_the_report_date_is_late",
    "outcome": "passed"
   },
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
  "E1": [
   {
    "test": "test_error_statement_is_disabled[E1]",
    "outcome": "passed"
   },
   {
    "test": "test_expected_error_is_raised[E1]",
    "outcome": "passed"
   }
  ]
 },
 "cases": [
  {
   "tag": "S1",
   "inputs": [
    {
     "kind": "insert",
     "table": "artist",
     "row": {
      "artist_id": "9001",
      "stage_name": "Zero Country",
      "country": null,
      "joined_date": "2026-09-01",
      "payout_rate": "0.0020",
      "verified": "1"
     }
    }
   ],
   "columns": [
    "artist_id",
    "stage_name",
    "usd_per_1000_streams",
    "days_under_licence",
    "licence_check",
    "payment_country",
    "run_status"
   ],
   "expected": [
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ],
    [
     "9001",
     "Zero Country",
     "2.00",
     "29",
     "confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "got": [
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ],
    [
     "9001",
     "Zero Country",
     "2.00",
     "29",
     "confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "doc": "A verified artist with no payment country is held, and the country is the only reason shown.\nWhy: the sample's one artist with no country (Saltmarsh Tapes) is also unverified, so the data never shows a\nlicence that passes while the country fails. A run_status that ignored country would pass the sample data.\nExpect: artist 9001 reads licence 'confirmed', payment_country 'HOLD: no country', run_status 'held'.",
   "test": "test_s1_verified_artist_without_country_is_held_for_country_alone",
   "outcome": "passed"
  },
  {
   "tag": "S1",
   "inputs": [
    {
     "kind": "insert",
     "table": "artist",
     "row": {
      "artist_id": "9002",
      "stage_name": "Top Rate Unverified",
      "country": "US",
      "joined_date": "2026-09-01",
      "payout_rate": "0.0090",
      "verified": "0"
     }
    }
   ],
   "columns": [
    "artist_id",
    "stage_name",
    "usd_per_1000_streams",
    "days_under_licence",
    "licence_check",
    "payment_country",
    "run_status"
   ],
   "expected": [
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "9002",
     "Top Rate Unverified",
     "9.00",
     "29",
     "HOLD: not confirmed",
     "US",
     "held"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "got": [
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "9002",
     "Top Rate Unverified",
     "9.00",
     "29",
     "HOLD: not confirmed",
     "US",
     "held"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "doc": "A held artist with the highest rate in the catalogue is still listed after every ready artist.\nWhy: ready-first must decide the order before rate does; in the sample data no held artist out-earns them all.\nExpect: artist 9002 (unverified, 0.0090 per stream, the top rate) comes after all five ready artists, first\namong the held.",
   "test": "test_s1_held_artist_never_outranks_a_ready_one",
   "outcome": "passed"
  },
  {
   "tag": "S1",
   "inputs": [
    {
     "kind": "insert",
     "table": "artist",
     "row": {
      "artist_id": "900",
      "stage_name": "Aardvark Tie",
      "country": "US",
      "joined_date": "2026-01-01",
      "payout_rate": "0.0040",
      "verified": "1"
     }
    }
   ],
   "columns": [
    "artist_id",
    "stage_name",
    "usd_per_1000_streams",
    "days_under_licence",
    "licence_check",
    "payment_country",
    "run_status"
   ],
   "expected": [
    [
     "900",
     "Aardvark Tie",
     "4.00",
     "272",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "got": [
    [
     "900",
     "Aardvark Tie",
     "4.00",
     "272",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1042",
     "Velvet Static",
     "4.00",
     "200",
     "confirmed",
     "US",
     "ready"
    ],
    [
     "1044",
     "Low Orbit Choir",
     "3.80",
     "239",
     "confirmed",
     "CA",
     "ready"
    ],
    [
     "1046",
     "Ochre Parade",
     "3.60",
     "172",
     "confirmed",
     "MX",
     "ready"
    ],
    [
     "1043",
     "Mara Quell",
     "3.50",
     "253",
     "confirmed",
     "GB",
     "ready"
    ],
    [
     "1047",
     "Juno Fleet",
     "3.00",
     "151",
     "confirmed",
     "DE",
     "ready"
    ],
    [
     "1049",
     "Kestrel Ave",
     "3.40",
     "33",
     "HOLD: not confirmed",
     "JM",
     "held"
    ],
    [
     "1045",
     "Tin Harbour",
     "3.20",
     "215",
     "HOLD: not confirmed",
     "AU",
     "held"
    ],
    [
     "1048",
     "Saltmarsh Tapes",
     "3.00",
     "134",
     "HOLD: not confirmed",
     "HOLD: no country",
     "held"
    ]
   ],
   "doc": "Two payable artists on the same rate are ordered by artist_id.\nWhy: without a tie-break the order of equal rates is up to MySQL and could change between runs.\nExpect: artist 900 (rate 0.0040, same as 1042) is listed first, 1042 second.",
   "test": "test_s1_equal_rates_break_ties_on_artist_id",
   "outcome": "passed"
  },
  {
   "tag": "S2",
   "inputs": [
    {
     "kind": "insert",
     "table": "track",
     "row": {
      "track_id": "9100",
      "artist_id": "1042",
      "title": "Fresh But Unscored",
      "duration": "200",
      "release_date": "2026-09-29",
      "audio_checksum": "0x0101010101010101010101010101010101010101010101010101010101010101",
      "ingest_status": "awaiting scoring"
     }
    }
   ],
   "columns": [
    "track_id",
    "title",
    "run_time",
    "release_date",
    "days_since_release"
   ],
   "expected": [
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ],
    [
     "4829",
     "Tapeworm Blues",
     "3:09",
     "2026-06-05",
     "117"
    ],
    [
     "4827",
     "Stahlwerk",
     "4:14",
     "2026-05-25",
     "128"
    ],
    [
     "4822",
     "Hymn for a Server Room",
     "4:28",
     "2026-05-15",
     "138"
    ]
   ],
   "got": [
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ],
    [
     "4829",
     "Tapeworm Blues",
     "3:09",
     "2026-06-05",
     "117"
    ],
    [
     "4827",
     "Stahlwerk",
     "4:14",
     "2026-05-25",
     "128"
    ],
    [
     "4822",
     "Hymn for a Server Room",
     "4:28",
     "2026-05-15",
     "138"
    ]
   ],
   "doc": "The newest upload stays off the shelf until it is scored.\nWhy: only scored recordings can be streamed, so date alone must not put a track on the shelf.\nExpect: track 9100 (released 2026-09-29, awaiting scoring) is not in the result.",
   "test": "test_s2_unscored_new_release_stays_off_the_shelf",
   "outcome": "passed"
  },
  {
   "tag": "S2",
   "inputs": [
    {
     "kind": "insert",
     "table": "track",
     "row": {
      "track_id": "4800",
      "artist_id": "1043",
      "title": "Same Day",
      "duration": "61",
      "release_date": "2026-07-10",
      "audio_checksum": "0x0202020202020202020202020202020202020202020202020202020202020202",
      "ingest_status": "scored"
     }
    }
   ],
   "columns": [
    "track_id",
    "title",
    "run_time",
    "release_date",
    "days_since_release"
   ],
   "expected": [
    [
     "4800",
     "Same Day",
     "1:01",
     "2026-07-10",
     "82"
    ],
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ],
    [
     "4829",
     "Tapeworm Blues",
     "3:09",
     "2026-06-05",
     "117"
    ],
    [
     "4827",
     "Stahlwerk",
     "4:14",
     "2026-05-25",
     "128"
    ]
   ],
   "got": [
    [
     "4800",
     "Same Day",
     "1:01",
     "2026-07-10",
     "82"
    ],
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ],
    [
     "4829",
     "Tapeworm Blues",
     "3:09",
     "2026-06-05",
     "117"
    ],
    [
     "4827",
     "Stahlwerk",
     "4:14",
     "2026-05-25",
     "128"
    ]
   ],
   "doc": "Two releases on the same day are ordered by track_id, and run time is shown as m:ss.\nWhy: same-day releases tie on the date; 61 seconds checks the seconds are zero-padded.\nExpect: 4800 then 4828 at the top; 4800's run_time is '1:01'.",
   "test": "test_s2_same_day_releases_order_by_track_id",
   "outcome": "passed"
  },
  {
   "tag": "S2",
   "inputs": [
    {
     "kind": "insert",
     "table": "track",
     "row": {
      "track_id": "9200",
      "artist_id": "1044",
      "title": "New 0",
      "duration": "120",
      "release_date": "2026-09-20",
      "audio_checksum": "0x1010101010101010101010101010101010101010101010101010101010101010",
      "ingest_status": "scored"
     }
    },
    {
     "kind": "insert",
     "table": "track",
     "row": {
      "track_id": "9201",
      "artist_id": "1044",
      "title": "New 1",
      "duration": "120",
      "release_date": "2026-09-21",
      "audio_checksum": "0x1111111111111111111111111111111111111111111111111111111111111111",
      "ingest_status": "scored"
     }
    },
    {
     "kind": "insert",
     "table": "track",
     "row": {
      "track_id": "9202",
      "artist_id": "1044",
      "title": "New 2",
      "duration": "120",
      "release_date": "2026-09-22",
      "audio_checksum": "0x1212121212121212121212121212121212121212121212121212121212121212",
      "ingest_status": "scored"
     }
    }
   ],
   "columns": [
    "track_id",
    "title",
    "run_time",
    "release_date",
    "days_since_release"
   ],
   "expected": [
    [
     "9202",
     "New 2",
     "2:00",
     "2026-09-22",
     "8"
    ],
    [
     "9201",
     "New 1",
     "2:00",
     "2026-09-21",
     "9"
    ],
    [
     "9200",
     "New 0",
     "2:00",
     "2026-09-20",
     "10"
    ],
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ]
   ],
   "got": [
    [
     "9202",
     "New 2",
     "2:00",
     "2026-09-22",
     "8"
    ],
    [
     "9201",
     "New 1",
     "2:00",
     "2026-09-21",
     "9"
    ],
    [
     "9200",
     "New 0",
     "2:00",
     "2026-09-20",
     "10"
    ],
    [
     "4828",
     "Afterimage Club",
     "3:41",
     "2026-07-10",
     "82"
    ],
    [
     "4826",
     "Plaza at Noon",
     "3:18",
     "2026-06-30",
     "92"
    ]
   ],
   "doc": "The shelf never shows more than five recordings.\nWhy: the sample data has exactly enough scored tracks that LIMIT 5 is never pushed.\nExpect: 5 rows, newest first: track 9202 (released 2026-09-22).",
   "test": "test_s2_shelf_never_holds_more_than_five",
   "outcome": "passed"
  },
  {
   "tag": "S3",
   "inputs": [
    {
     "kind": "update",
     "sql": "UPDATE genre SET description = NULL WHERE genre_id = 9",
     "rows": 1
    }
   ],
   "columns": [
    "model_class_index",
    "label",
    "label_chars",
    "label_column",
    "description_chars",
    "chars_left_on_line"
   ],
   "expected": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classical",
     "9",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "fits",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "41",
     "39"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     null,
     null
    ]
   ],
   "got": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classical",
     "9",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "fits",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "41",
     "39"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     null,
     null
    ]
   ],
   "doc": "A genre with no description shows NULL for its description length and room left, and keeps its label row.\nWhy: description is the one optional genre column, and every genre in the sample data has one.\nExpect: genre 9 (rock) reads label_chars 4, 'fits', then NULL, NULL.",
   "test": "test_s3_genre_without_description_has_no_line_figures",
   "outcome": "passed"
  },
  {
   "tag": "S3",
   "inputs": [
    {
     "kind": "update",
     "sql": "UPDATE genre SET name = 'classic' WHERE genre_id = 1",
     "rows": 1
    }
   ],
   "columns": [
    "model_class_index",
    "label",
    "label_chars",
    "label_column",
    "description_chars",
    "chars_left_on_line"
   ],
   "expected": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classic",
     "7",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "sets the column width",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "41",
     "39"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     "40",
     "40"
    ]
   ],
   "got": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classic",
     "7",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "sets the column width",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "41",
     "39"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     "40",
     "40"
    ]
   ],
   "doc": "The genre that sets the label column width is found from the data, and genres tied on length all set it.\nWhy: in the sample data classical (9) is the one longest label, so a width hard-coded to 9, or a query that\nmarks only one row, would pass.\nExpect: with classical renamed 'classic' (7), the widest label is 7 and both classic and country set the width.",
   "test": "test_s3_label_width_follows_the_data_and_ties_share_it",
   "outcome": "passed"
  },
  {
   "tag": "S3",
   "inputs": [
    {
     "kind": "update",
     "sql": "UPDATE genre SET description = 'Bossa nova, samba-canção and música popular brasileira' WHERE genre_id = 5",
     "rows": 1
    }
   ],
   "columns": [
    "model_class_index",
    "label",
    "label_chars",
    "label_column",
    "description_chars",
    "chars_left_on_line"
   ],
   "expected": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classical",
     "9",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "fits",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "54",
     "26"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     "40",
     "40"
    ]
   ],
   "got": [
    [
     "0",
     "blues",
     "5",
     "fits",
     "59",
     "21"
    ],
    [
     "1",
     "classical",
     "9",
     "sets the column width",
     "65",
     "15"
    ],
    [
     "2",
     "country",
     "7",
     "fits",
     "57",
     "23"
    ],
    [
     "3",
     "disco",
     "5",
     "fits",
     "58",
     "22"
    ],
    [
     "4",
     "hiphop",
     "6",
     "fits",
     "56",
     "24"
    ],
    [
     "5",
     "jazz",
     "4",
     "fits",
     "54",
     "26"
    ],
    [
     "6",
     "metal",
     "5",
     "fits",
     "54",
     "26"
    ],
    [
     "7",
     "pop",
     "3",
     "fits",
     "40",
     "40"
    ],
    [
     "8",
     "reggae",
     "6",
     "fits",
     "45",
     "35"
    ],
    [
     "9",
     "rock",
     "4",
     "fits",
     "40",
     "40"
    ]
   ],
   "doc": "Description length is counted in characters, the unit of the RA's 80-character line, not in bytes.\nWhy: every sample description is plain ASCII, where characters and bytes agree; utf8mb4 stores an accented\nletter in two bytes, so LENGTH() would over-count.\nExpect: a jazz description with three accented letters reads 54 characters (57 bytes), 26 left on the line.",
   "test": "test_s3_description_length_counts_characters_not_bytes",
   "outcome": "passed"
  },
  {
   "tag": "S4",
   "inputs": [
    {
     "kind": "update",
     "sql": "UPDATE listener SET plan_tier = 'standard' WHERE plan_tier = 'premium'",
     "rows": 2
    }
   ],
   "columns": [
    "plan_tier",
    "listeners",
    "first_signup",
    "latest_signup",
    "avg_days_subscribed"
   ],
   "expected": [
    [
     "standard",
     "5",
     "2026-04-02",
     "2026-07-08",
     "131"
    ],
    [
     "free",
     "3",
     "2026-04-18",
     "2026-08-15",
     "104"
    ]
   ],
   "got": [
    [
     "standard",
     "5",
     "2026-04-02",
     "2026-07-08",
     "131"
    ],
    [
     "free",
     "3",
     "2026-04-18",
     "2026-08-15",
     "104"
    ]
   ],
   "doc": "A plan tier nobody is on does not appear in the subscriber mix.\nWhy: every tier has listeners in the sample data; GROUP BY must not invent an empty tier.\nExpect: only standard and free, in tier order, standard with 5 listeners.",
   "test": "test_s4_tier_with_no_listeners_is_absent",
   "outcome": "passed"
  },
  {
   "tag": "S5",
   "inputs": [
    {
     "kind": "insert",
     "table": "scoring_model",
     "row": {
      "model_id": "6",
      "version_label": "tie_newer",
      "fusion_type": "gated",
      "embedding_dimension": "256",
      "segment_length": "10",
      "training_corpus": "GTZAN",
      "holdout_accuracy": "0.7887",
      "deployed_on": "2026-09-01"
     }
    }
   ],
   "columns": [
    "version_label",
    "architecture",
    "accuracy_pct",
    "deployed_on"
   ],
   "expected": [
    [
     "tie_newer",
     "gated / 256d / 10s / GTZAN",
     "78.87",
     "2026-09-01"
    ]
   ],
   "got": [
    [
     "tie_newer",
     "gated / 256d / 10s / GTZAN",
     "78.87",
     "2026-09-01"
    ]
   ],
   "doc": "On equal holdout accuracy the more recently deployed version becomes the default.\nWhy: the sample's top version has no tie, so the deployed_on tie-break is never used for the default.\nExpect: tie_newer (accuracy 0.7887 like beardown_3sec, but deployed later, 2026-09-01) is the one default.",
   "test": "test_s5_accuracy_tie_prefers_the_newer_version",
   "outcome": "passed"
  },
  {
   "tag": "S5",
   "inputs": [
    {
     "kind": "insert",
     "table": "scoring_model",
     "row": {
      "model_id": "7",
      "version_label": "tie_high",
      "fusion_type": "concat",
      "embedding_dimension": "384",
      "segment_length": "3",
      "training_corpus": "GTZAN",
      "holdout_accuracy": "0.9000",
      "deployed_on": "2026-09-01"
     }
    },
    {
     "kind": "insert",
     "table": "scoring_model",
     "row": {
      "model_id": "6",
      "version_label": "tie_low",
      "fusion_type": "concat",
      "embedding_dimension": "384",
      "segment_length": "3",
      "training_corpus": "GTZAN",
      "holdout_accuracy": "0.9000",
      "deployed_on": "2026-09-01"
     }
    }
   ],
   "columns": [
    "version_label",
    "architecture",
    "accuracy_pct",
    "deployed_on"
   ],
   "expected": [
    [
     "tie_low",
     "concat / 384d / 3s / GTZAN",
     "90.00",
     "2026-09-01"
    ]
   ],
   "got": [
    [
     "tie_low",
     "concat / 384d / 3s / GTZAN",
     "90.00",
     "2026-09-01"
    ]
   ],
   "doc": "Two versions tied on both accuracy and deployment date: the lower model_id is the default, every time.\nWhy: without a last tie-break, LIMIT 1 would return whichever tied row MySQL found first.\nExpect: tie_low (model_id 6) wins over tie_high (model_id 7); both at 0.9000, both deployed 2026-09-01, above\nevery sample version. tie_high is inserted first, so insertion order cannot be what decides.",
   "test": "test_s5_full_tie_goes_to_the_lower_model_id",
   "outcome": "passed"
  },
  {
   "tag": "S6",
   "inputs": [
    {
     "kind": "insert",
     "table": "station",
     "row": {
      "station_id": "7799",
      "listener_id": "20938",
      "model_id": "3",
      "name": "Edge Window",
      "minimum_ambiguity": "0.25",
      "maximum_ambiguity": "0.75",
      "created_on": "2026-09-01"
     }
    }
   ],
   "columns": [
    "model_id",
    "stations",
    "avg_window",
    "wide_stations",
    "oldest_station"
   ],
   "expected": [
    [
     "4",
     "3",
     "0.57",
     "2",
     "2026-06-10"
    ],
    [
     "2",
     "2",
     "0.60",
     "2",
     "2026-05-02"
    ],
    [
     "5",
     "2",
     "0.50",
     "1",
     "2026-07-20"
    ],
    [
     "1",
     "1",
     "0.60",
     "1",
     "2026-05-20"
    ],
    [
     "3",
     "1",
     "0.50",
     "0",
     "2026-09-01"
    ]
   ],
   "got": [
    [
     "4",
     "3",
     "0.57",
     "2",
     "2026-06-10"
    ],
    [
     "2",
     "2",
     "0.60",
     "2",
     "2026-05-02"
    ],
    [
     "5",
     "2",
     "0.50",
     "1",
     "2026-07-20"
    ],
    [
     "1",
     "1",
     "0.60",
     "1",
     "2026-05-20"
    ],
    [
     "3",
     "1",
     "0.50",
     "0",
     "2026-09-01"
    ]
   ],
   "doc": "An ambiguity window of exactly 0.50 is not counted as wide.\nWhy: 'wide' means more than half the range; the boundary itself is not in the sample data.\nExpect: model 3 (only station 7799, window 0.25 to 0.75): 1 station, avg_window 0.50, 0 wide.",
   "test": "test_s6_window_of_exactly_half_is_not_wide",
   "outcome": "passed"
  },
  {
   "tag": "S7",
   "inputs": [
    {
     "kind": "insert",
     "table": "track",
     "row": {
      "track_id": "9300",
      "artist_id": "1049",
      "title": "Clipped Master",
      "duration": "30",
      "release_date": "2026-09-28",
      "audio_checksum": "0x0303030303030303030303030303030303030303030303030303030303030303",
      "ingest_status": "rejected"
     }
    }
   ],
   "columns": [
    "ingest_status",
    "recordings",
    "earliest_release",
    "days_to_earliest_release",
    "release_status"
   ],
   "expected": [
    [
     "awaiting scoring",
     "1",
     "2026-09-21",
     "-9",
     "LATE: release date reached, still unscored"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "2",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "got": [
    [
     "awaiting scoring",
     "1",
     "2026-09-21",
     "-9",
     "LATE: release date reached, still unscored"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "2",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "doc": "A new rejection is counted, and statuses stay in pipeline order, not alphabetical.\nWhy: ingest_status is an ENUM; ORDER BY must follow awaiting scoring, scored, rejected.\nExpect: rejected shows 2 recordings, earliest release 2026-09-22 (8 days ago), 'never streamable: rejected'.",
   "test": "test_s7_new_rejection_is_counted_in_pipeline_order",
   "outcome": "passed"
  },
  {
   "tag": "S7",
   "inputs": [
    {
     "kind": "update",
     "sql": "UPDATE track SET release_date = '2026-10-15' WHERE ingest_status = 'awaiting scoring'",
     "rows": 1
    }
   ],
   "columns": [
    "ingest_status",
    "recordings",
    "earliest_release",
    "days_to_earliest_release",
    "release_status"
   ],
   "expected": [
    [
     "awaiting scoring",
     "1",
     "2026-10-15",
     "15",
     "on time: release date still ahead"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "1",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "got": [
    [
     "awaiting scoring",
     "1",
     "2026-10-15",
     "15",
     "on time: release date still ahead"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "1",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "doc": "An unscored recording whose release date is still ahead is on time, not late.\nWhy: the sample's one unscored recording is already past its release date (LATE), so the on-time branch is\nnever reached.\nExpect: with its release moved to 2026-10-15, awaiting scoring reads 15 days ahead, 'on time: release date still ahead'.",
   "test": "test_s7_unscored_recording_before_its_release_is_on_time",
   "outcome": "passed"
  },
  {
   "tag": "S7",
   "inputs": [
    {
     "kind": "update",
     "sql": "UPDATE track SET release_date = '2026-09-30' WHERE ingest_status = 'awaiting scoring'",
     "rows": 1
    }
   ],
   "columns": [
    "ingest_status",
    "recordings",
    "earliest_release",
    "days_to_earliest_release",
    "release_status"
   ],
   "expected": [
    [
     "awaiting scoring",
     "1",
     "2026-09-30",
     "0",
     "LATE: release date reached, still unscored"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "1",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "got": [
    [
     "awaiting scoring",
     "1",
     "2026-09-30",
     "0",
     "LATE: release date reached, still unscored"
    ],
    [
     "scored",
     "13",
     "2026-02-25",
     "-217",
     "streamable"
    ],
    [
     "rejected",
     "1",
     "2026-09-22",
     "-8",
     "never streamable: rejected"
    ]
   ],
   "doc": "A release due on the report date itself, still unscored, is already late.\nWhy: the boundary: on its release day the recording must already be streamable, so 'reached' includes the day.\nExpect: with its release moved to 2026-09-30, awaiting scoring reads 0 days, 'LATE: release date reached, still unscored'.",
   "test": "test_s7_release_due_on_the_report_date_is_late",
   "outcome": "passed"
  }
 ]
};
