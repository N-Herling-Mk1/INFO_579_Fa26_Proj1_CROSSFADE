/* Written by project2/tests (pytest) at the end of a run. Do not edit. */
window.P2_SINGLE = {
 "file": "single_table.sql",
 "generated": "2026-11-06T03:20:48",
 "passed": 64,
 "failed": 0,
 "queries": {
  "S1": {
   "table": "artist",
   "use_cases": [
    "UC-02",
    "UC-01"
   ],
   "question": "Who can be paid in this royalty run, who is on hold and why, and what does each artist earn per 1,000 qualifying streams?",
   "declared": [
    "a",
    "c",
    "e"
   ],
   "sql": "SELECT artist_id,\n       CONCAT(stage_name, ' (', IFNULL(country, '--'), ')') AS payee,\n       ROUND(payout_rate * 1000, 2) AS usd_per_1000_streams,\n       DATEDIFF('2026-09-30', joined_date) AS days_under_licence,\n       CASE\n           WHEN verified = 0 THEN 'HOLD: identity not verified'\n           WHEN country IS NULL THEN 'HOLD: no payment country'\n           ELSE 'PAYABLE'\n       END AS payment_status\nFROM crossfade.artist\nORDER BY CASE WHEN verified = 1 AND country IS NOT NULL THEN 0 ELSE 1 END,\n         payout_rate DESC,\n         artist_id",
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
    "payee",
    "usd_per_1000_streams",
    "days_under_licence",
    "payment_status"
   ],
   "rows": [
    [
     "1042",
     "Velvet Static (US)",
     "4.00",
     "200",
     "PAYABLE"
    ],
    [
     "1044",
     "Low Orbit Choir (CA)",
     "3.80",
     "239",
     "PAYABLE"
    ],
    [
     "1046",
     "Ochre Parade (MX)",
     "3.60",
     "172",
     "PAYABLE"
    ],
    [
     "1043",
     "Mara Quell (GB)",
     "3.50",
     "253",
     "PAYABLE"
    ],
    [
     "1047",
     "Juno Fleet (DE)",
     "3.00",
     "151",
     "PAYABLE"
    ],
    [
     "1049",
     "Kestrel Ave (JM)",
     "3.40",
     "33",
     "HOLD: identity not verified"
    ],
    [
     "1045",
     "Tin Harbour (AU)",
     "3.20",
     "215",
     "HOLD: identity not verified"
    ],
    [
     "1048",
     "Saltmarsh Tapes (--)",
     "3.00",
     "134",
     "HOLD: identity not verified"
    ]
   ]
  },
  "S2": {
   "table": "track",
   "use_cases": [
    "UC-03"
   ],
   "question": "What are the five newest recordings listeners can stream?",
   "declared": [
    "a",
    "c",
    "d"
   ],
   "sql": "SELECT track_id,\n       title,\n       CONCAT(FLOOR(duration / 60), ':', LPAD(MOD(duration, 60), 2, '0')) AS run_time,\n       release_date,\n       DATEDIFF('2026-09-30', release_date) AS days_since_release\nFROM crossfade.track\nWHERE ingest_status = 'scored'\nORDER BY release_date DESC,\n         track_id\nLIMIT 5",
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
   ]
  },
  "S3": {
   "table": "genre",
   "use_cases": [
    "UC-05"
   ],
   "question": "Is every genre ready to show in the blend composer, listed in the order the scoring models output them?",
   "declared": [
    "a",
    "c",
    "e"
   ],
   "sql": "SELECT genre_id AS model_class_index,\n       UPPER(name) AS label,\n       IFNULL(description, '(no description)') AS legend_text,\n       IF(description IS NULL, 'HIDE: no description for the composer', 'READY') AS composer_status\nFROM crossfade.genre\nORDER BY genre_id",
   "detected": [
    "a",
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
    "legend_text",
    "composer_status"
   ],
   "rows": [
    [
     "0",
     "BLUES",
     "Twelve-bar forms, blue notes and call-and-response phrasing",
     "READY"
    ],
    [
     "1",
     "CLASSICAL",
     "Orchestral and chamber writing in the Western art-music tradition",
     "READY"
    ],
    [
     "2",
     "COUNTRY",
     "Narrative songwriting with steel guitar, fiddle and twang",
     "READY"
    ],
    [
     "3",
     "DISCO",
     "Four-on-the-floor dance grooves with lush strings and bass",
     "READY"
    ],
    [
     "4",
     "HIPHOP",
     "Rhythmic vocal delivery over sampled or programmed beats",
     "READY"
    ],
    [
     "5",
     "JAZZ",
     "Swing, improvisation and extended harmony",
     "READY"
    ],
    [
     "6",
     "METAL",
     "Distorted guitars, heavy drums and aggressive dynamics",
     "READY"
    ],
    [
     "7",
     "POP",
     "Hook-driven songs built for broad appeal",
     "READY"
    ],
    [
     "8",
     "REGGAE",
     "Offbeat skank rhythm and prominent bass lines",
     "READY"
    ],
    [
     "9",
     "ROCK",
     "Guitar-led songs with a driving backbeat",
     "READY"
    ]
   ]
  },
  "S4": {
   "table": "listener",
   "use_cases": [
    "UC-06"
   ],
   "question": "How many subscribers does each plan tier have, when did the first and latest join, and how long has the average subscriber been billing?",
   "declared": [
    "a",
    "b",
    "c"
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
   ]
  },
  "S5": {
   "table": "scoring_model",
   "use_cases": [
    "UC-08"
   ],
   "question": "Which three model versions should a new station default to?",
   "declared": [
    "a",
    "c",
    "d"
   ],
   "sql": "SELECT version_label,\n       CONCAT(fusion_type, ' / ', embedding_dimension, 'd / ', segment_length, 's / ', training_corpus) AS architecture,\n       ROUND(holdout_accuracy * 100, 2) AS accuracy_pct,\n       deployed_on\nFROM crossfade.scoring_model\nORDER BY holdout_accuracy DESC,\n         deployed_on DESC\nLIMIT 3",
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
    ],
    [
     "beardown_rrm",
     "concat / 768d / 30s / GTZAN",
     "76.00",
     "2026-03-23"
    ],
    [
     "beardown_rrm_cfg17",
     "concat / 768d / 30s / GTZAN",
     "76.00",
     "2026-03-09"
    ]
   ]
  },
  "S6": {
   "table": "station",
   "use_cases": [
    "UC-10",
    "UC-08"
   ],
   "question": "How many stations does each model version serve, how wide are their ambiguity windows, and since when has each version been relied on?",
   "declared": [
    "a",
    "b",
    "c",
    "e"
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
   ]
  },
  "S7": {
   "table": "track",
   "use_cases": [
    "UC-04"
   ],
   "question": "How many recordings sit at each stage of the upload pipeline, and how long since the newest one reached each stage?",
   "declared": [
    "a",
    "b",
    "c",
    "e"
   ],
   "sql": "SELECT ingest_status,\n       COUNT(*) AS recordings,\n       MAX(release_date) AS newest_release,\n       DATEDIFF('2026-09-30', MAX(release_date)) AS days_since_newest,\n       IF(ingest_status = 'scored', 'streamable', 'not streamable') AS listener_visibility\nFROM crossfade.track\nGROUP BY ingest_status\nORDER BY ingest_status",
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
    "newest_release",
    "days_since_newest",
    "listener_visibility"
   ],
   "rows": [
    [
     "awaiting scoring",
     "1",
     "2026-09-21",
     "9",
     "not streamable"
    ],
    [
     "scored",
     "13",
     "2026-07-10",
     "82",
     "streamable"
    ],
    [
     "rejected",
     "1",
     "2026-09-22",
     "8",
     "not streamable"
    ]
   ]
  },
  "E1": {
   "table": "track",
   "use_cases": [
    "UC-15"
   ],
   "question": "What happens when an artist uploads an audio file that is already in the catalogue?",
   "sql": "INSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)\nSELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', audio_checksum, 'awaiting scoring'\nFROM crossfade.track\nWHERE track_id = 4817",
   "kind": "expected_error",
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
    "test": "test_s1_verified_artist_without_country_is_held",
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
    "test": "test_s3_genre_without_description_is_hidden",
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
    "test": "test_s6_window_of_exactly_half_is_not_wide",
    "outcome": "passed"
   },
   {
    "test": "test_s7_new_rejection_is_counted_in_pipeline_order",
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
    "test": "test_expected_error_is_raised[E1]",
    "outcome": "passed"
   }
  ]
 }
};
