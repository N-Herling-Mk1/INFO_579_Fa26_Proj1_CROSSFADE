/* Written by project2/tests (pytest) at the end of a run. Do not edit. */
window.P2_ROUTINES = {
 "file": "routines.sql",
 "generated": "2026-11-08T13:24:10",
 "passed": 50,
 "failed": 0,
 "queries": {
  "F1": {
   "name": "play_royalty",
   "kind": "FUNCTION",
   "title": "play_royalty",
   "use_cases": [
    "UC-01",
    "UC-14"
   ],
   "need": "CROSSFADE pays each artist \"a per stream royalty on plays of those recordings\" (RA: Artist), and the royalty ledger must be exact (RA: Play). The payout rule lives in one place so every caller applies it the same way: record_play (P1) when a play is recorded, and finance when it previews what a play would earn.",
   "does": [
    "Looks up the payout rate of the artist who owns the recording: \"the amount in United States dollars the artist is paid for a single qualifying stream\" (RA: Artist.payout_rate).",
    "Applies rule I7: \"Royalty Amount equals the artist's Payout Rate for a play of 30 seconds or more and zero otherwise.\" 30 seconds exactly qualifies.",
    "Returns NULL, not 0, when the recording does not exist: there is no rate to apply, and 0 would read as \"a short play\" (P1 refuses such a play first).",
    "NOT DETERMINISTIC: the same arguments can give a different answer after the artist's rate changes, which is why P1 stores the result (a snapshot)."
   ],
   "requirement": "4 function",
   "uses": [
    "DECLARE",
    "IF ... ELSEIF ... ELSE",
    "READS SQL DATA",
    "NOT DETERMINISTIC"
   ],
   "tables": [
    "track",
    "artist"
   ],
   "params": [
    "IN input_track_id INT UNSIGNED",
    "IN input_seconds_played SMALLINT UNSIGNED"
   ],
   "returns": "DECIMAL(5,5)",
   "errors": "none; NULL for a recording that does not exist or a missing length",
   "example": "SELECT crossfade.play_royalty(4817, 30);   -- 0.00400 (Velvet Static's rate)",
   "sql": "CREATE FUNCTION crossfade.play_royalty (\n\tinput_track_id INT UNSIGNED,\n\tinput_seconds_played SMALLINT UNSIGNED)\n\tRETURNS DECIMAL(5,5)\n\tNOT DETERMINISTIC\n\tREADS SQL DATA\nBEGIN\n\tDECLARE artist_rate DECIMAL(5,5);\n\n\t-- The rate of the artist who owns the recording; NULL if there is no such recording.\n\tSET artist_rate = (SELECT a.payout_rate\n\t\t\t\t\t   FROM crossfade.track AS t\n\t\t\t\t\t   INNER JOIN crossfade.artist AS a ON a.artist_id = t.artist_id\n\t\t\t\t\t   WHERE t.track_id = input_track_id);\n\n\tIF artist_rate IS NULL OR input_seconds_played IS NULL THEN\n\t\tRETURN NULL;\n\tELSEIF input_seconds_played >= 30 THEN\n\t\tRETURN artist_rate;\n\tELSE\n\t\tRETURN 0;\n\tEND IF;\nEND",
   "catalogue": {
    "type": "FUNCTION",
    "data_access": "READS SQL DATA",
    "deterministic": "NO",
    "parameters": [
     [
      "IN",
      "input_track_id",
      "int unsigned"
     ],
     [
      "IN",
      "input_seconds_played",
      "smallint unsigned"
     ]
    ]
   },
   "columns": {
    "artist": [
     "artist_id",
     "payout_rate"
    ],
    "track": [
     "artist_id",
     "track_id"
    ]
   }
  },
  "P1": {
   "name": "record_play",
   "kind": "PROCEDURE",
   "title": "record_play",
   "use_cases": [
    "UC-14",
    "UC-13",
    "UC-01",
    "UC-07",
    "UC-04"
   ],
   "need": "Every play is both the taste signal (RA: Play, \"the record from which listener taste is inferred\") and the billable event the royalty is paid on. Rule I7: \"The procedure that records a play computes both [Completed and Royalty Amount] from the Track and Artist rows rather than accepting them as input\", and \"Royalty Amount is computed once, when the play is recorded, and never updated.\" This is that procedure.",
   "does": [
    "Refuses, with SIGNAL SQLSTATE '45000' and a message naming the problem, a play of a recording that does not exist, of one not released for streaming (ingest status other than 'scored'; RA: a recording has no score \"while it is awaiting scoring, at least one before it is released\"), or a play longer than the recording.",
    "Computes completed: true \"exactly when Seconds Played equals the Duration of the recording\" (RA: Play.completed).",
    "Computes royalty_amount with play_royalty (F1): the artist's rate as it stands now, stored as a snapshot \"so that a later rate change never rewrites the royalty ledger\" (RA: Play.royalty_amount).",
    "Records the play at the UTC time given, or now in UTC when none is given: \"Played At is recorded in UTC\" (RA: key of Play).",
    "Does not catch the database's own refusals: a second report of the same play (same listener, recording and start time) is rejected by the primary key, \"which is what keeps a double-counted royalty out of the ledger\" (RA), and an unknown listener or station by its foreign key. The station may belong to another listener (rule I6: stations can be shared).",
    "Hands completed and royalty_amount back through OUT parameters."
   ],
   "requirement": "4 procedure",
   "uses": [
    "DECLARE",
    "IF ... ELSEIF",
    "SIGNAL SQLSTATE '45000'",
    "IN / OUT parameters",
    "calls F1",
    "MODIFIES SQL DATA"
   ],
   "tables": [
    "track",
    "artist",
    "play"
   ],
   "params": [
    "IN input_listener_id INT UNSIGNED",
    "IN input_track_id INT UNSIGNED",
    "IN input_station_id INT UNSIGNED",
    "IN input_seconds_played SMALLINT UNSIGNED",
    "IN input_reaction VARCHAR(7)",
    "IN input_played_at DATETIME",
    "OUT output_completed TINYINT",
    "OUT output_royalty_amount DECIMAL(5,5)"
   ],
   "returns": "",
   "errors": "SIGNAL 45000 for a recording that does not exist, is not released, or is shorter than the seconds played; MySQL refuses a repeated play (1062) and an unknown listener or station (1452)",
   "example": "CALL crossfade.record_play(20937, 4817, NULL, 107, 'skipped', '2026-11-01 20:15:00', @completed, @royalty);",
   "sql": "CREATE PROCEDURE crossfade.record_play (\n\tIN input_listener_id INT UNSIGNED,\n\tIN input_track_id INT UNSIGNED,\n\tIN input_station_id INT UNSIGNED,\n\tIN input_seconds_played SMALLINT UNSIGNED,\n\tIN input_reaction VARCHAR(7),\n\tIN input_played_at DATETIME,\n\tOUT output_completed TINYINT,\n\tOUT output_royalty_amount DECIMAL(5,5))\n\tMODIFIES SQL DATA\nBEGIN\n\tDECLARE track_duration SMALLINT UNSIGNED;\n\tDECLARE track_status VARCHAR(16);\n\tDECLARE error_message VARCHAR(128);\n\n\t-- The recording's length and upload stage; both NULL if there is no such recording.\n\tSET track_duration = (SELECT duration FROM crossfade.track WHERE track_id = input_track_id);\n\tSET track_status = (SELECT ingest_status FROM crossfade.track WHERE track_id = input_track_id);\n\n\tIF track_duration IS NULL THEN\n\t\tSET error_message = CONCAT('record_play: track ', input_track_id, ' does not exist');\n\t\tSIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;\n\tELSEIF track_status <> 'scored' THEN\n\t\tSET error_message = CONCAT('record_play: track ', input_track_id, ' is not released for streaming (', track_status, ')');\n\t\tSIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;\n\tELSEIF input_seconds_played > track_duration THEN\n\t\tSET error_message = CONCAT('record_play: ', input_seconds_played, ' seconds played, but track ', input_track_id,\n\t\t\t\t\t\t\t\t   ' is only ', track_duration, ' seconds long');\n\t\tSIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;\n\tEND IF;\n\n\t-- Rule I7: both values are derived here, never taken from the caller.\n\tSET output_completed = (input_seconds_played = track_duration);\n\tSET output_royalty_amount = crossfade.play_royalty(input_track_id, input_seconds_played);\n\n\tINSERT INTO crossfade.play (listener_id, track_id, played_at, station_id, seconds_played,\n\t\t\t\t\t\t\t\tcompleted, reaction, royalty_amount)\n\tVALUES (input_listener_id, input_track_id, IFNULL(input_played_at, UTC_TIMESTAMP()), input_station_id,\n\t\t\tinput_seconds_played, output_completed, input_reaction, output_royalty_amount);\nEND",
   "catalogue": {
    "type": "PROCEDURE",
    "data_access": "MODIFIES SQL DATA",
    "deterministic": "NO",
    "parameters": [
     [
      "IN",
      "input_listener_id",
      "int unsigned"
     ],
     [
      "IN",
      "input_track_id",
      "int unsigned"
     ],
     [
      "IN",
      "input_station_id",
      "int unsigned"
     ],
     [
      "IN",
      "input_seconds_played",
      "smallint unsigned"
     ],
     [
      "IN",
      "input_reaction",
      "varchar(7)"
     ],
     [
      "IN",
      "input_played_at",
      "datetime"
     ],
     [
      "OUT",
      "output_completed",
      "tinyint"
     ],
     [
      "OUT",
      "output_royalty_amount",
      "decimal(5,5)"
     ]
    ]
   },
   "columns": {
    "play": [
     "completed",
     "listener_id",
     "played_at",
     "reaction",
     "royalty_amount",
     "seconds_played",
     "station_id",
     "track_id"
    ],
    "track": [
     "artist_id",
     "duration",
     "ingest_status",
     "track_id"
    ],
    "artist": [
     "artist_id",
     "payout_rate"
    ]
   }
  },
  "P2": {
   "name": "upload_track",
   "kind": "PROCEDURE",
   "title": "upload_track",
   "use_cases": [
    "UC-15",
    "UC-04"
   ],
   "need": "Artists upload recordings \"under a direct streaming licence\" (RA: Artist), and the audio checksum is \"used to detect duplicate uploads\" (RA: Track.audio_checksum). A duplicate upload is an everyday event, not a failure: the artist should be told which recording is already in the catalogue, and a batch of uploads should carry on. [E1] in single_table.sql (kept disabled there) shows the raw refusal (error 1062); this procedure is the business answering it.",
   "does": [
    "Refuses, with SIGNAL SQLSTATE '45000', an upload from an artist who is not registered.",
    "Gives the recording the next track ID and inserts it with ingest status 'awaiting scoring', the first stage of the upload pipeline (RA: a recording has no score \"while it is awaiting scoring\"); scoring moves it on (rule I5). The release date may be later than the upload (RA: Track.release_date).",
    "Lets the UNIQUE index on audio_checksum detect the duplicate, rather than looking first: a look-then-insert leaves a gap in which a second upload of the same file could slip in, and the index has no gap.",
    "DECLARE EXIT HANDLER FOR 1062 catches that duplicate: nothing is inserted, and the OUT parameters name the recording already in the catalogue, with status 'duplicate'. If the 1062 came from the primary key instead (two uploads took the same new ID at the same moment), there is no recording with this checksum, and the handler re-raises the error (RESIGNAL) rather than report a duplicate that is not one.",
    "Every other refusal (a length of 0 seconds, a missing title) is the database's own, and is not caught."
   ],
   "requirement": "4 procedure",
   "uses": [
    "DECLARE",
    "DECLARE EXIT HANDLER FOR 1062",
    "RESIGNAL",
    "IF",
    "SIGNAL SQLSTATE '45000'",
    "IN / OUT parameters",
    "MODIFIES SQL DATA"
   ],
   "tables": [
    "artist",
    "track"
   ],
   "params": [
    "IN input_artist_id MEDIUMINT UNSIGNED",
    "IN input_title VARCHAR(128)",
    "IN input_duration SMALLINT UNSIGNED",
    "IN input_release_date DATE",
    "IN input_audio_checksum BINARY(32)",
    "OUT output_track_id INT UNSIGNED",
    "OUT output_status VARCHAR(9)",
    "OUT output_message VARCHAR(128)"
   ],
   "returns": "",
   "errors": "SIGNAL 45000 for an unregistered artist; a duplicate upload is not an error (status 'duplicate'); the database refuses an invalid length or title (3819, 1048)",
   "example": "CALL crossfade.upload_track(1049, 'First Light', 201, '2026-12-01', UNHEX(SHA2('first light', 256)), @id, @status, @message);",
   "sql": "CREATE PROCEDURE crossfade.upload_track (\n\tIN input_artist_id MEDIUMINT UNSIGNED,\n\tIN input_title VARCHAR(128),\n\tIN input_duration SMALLINT UNSIGNED,\n\tIN input_release_date DATE,\n\tIN input_audio_checksum BINARY(32),\n\tOUT output_track_id INT UNSIGNED,\n\tOUT output_status VARCHAR(9),\n\tOUT output_message VARCHAR(128))\n\tMODIFIES SQL DATA\nBEGIN\n\tDECLARE error_message VARCHAR(128);\n\n\t-- A duplicate upload is answered, not raised: name the recording already in the catalogue.\n\tDECLARE EXIT HANDLER FOR 1062\n\tBEGIN\n\t\tSET output_track_id = (SELECT track_id FROM crossfade.track WHERE audio_checksum = input_audio_checksum);\n\t\tIF output_track_id IS NULL THEN\n\t\t\tRESIGNAL;      -- the duplicate key was the new track ID, not the audio file\n\t\tEND IF;\n\t\tSET output_status = 'duplicate';\n\t\tSET output_message = CONCAT('already in the catalogue as track ', output_track_id, ' (',\n\t\t\t\t\t\t\t\t\t(SELECT title FROM crossfade.track WHERE track_id = output_track_id), ')');\n\tEND;\n\n\tIF (SELECT COUNT(*) FROM crossfade.artist WHERE artist_id = input_artist_id) = 0 THEN\n\t\tSET error_message = CONCAT('upload_track: artist ', input_artist_id, ' is not registered');\n\t\tSIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;\n\tEND IF;\n\n\tSET output_track_id = (SELECT IFNULL(MAX(track_id), 0) + 1 FROM crossfade.track);\n\tINSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)\n\tVALUES (output_track_id, input_artist_id, input_title, input_duration, input_release_date,\n\t\t\tinput_audio_checksum, 'awaiting scoring');\n\n\tSET output_status = 'uploaded';\n\tSET output_message = CONCAT('uploaded as track ', output_track_id, ', awaiting scoring');\nEND",
   "catalogue": {
    "type": "PROCEDURE",
    "data_access": "MODIFIES SQL DATA",
    "deterministic": "NO",
    "parameters": [
     [
      "IN",
      "input_artist_id",
      "mediumint unsigned"
     ],
     [
      "IN",
      "input_title",
      "varchar(128)"
     ],
     [
      "IN",
      "input_duration",
      "smallint unsigned"
     ],
     [
      "IN",
      "input_release_date",
      "date"
     ],
     [
      "IN",
      "input_audio_checksum",
      "binary(32)"
     ],
     [
      "OUT",
      "output_track_id",
      "int unsigned"
     ],
     [
      "OUT",
      "output_status",
      "varchar(9)"
     ],
     [
      "OUT",
      "output_message",
      "varchar(128)"
     ]
    ]
   },
   "columns": {
    "artist": [
     "artist_id"
    ],
    "track": [
     "artist_id",
     "audio_checksum",
     "duration",
     "ingest_status",
     "release_date",
     "title",
     "track_id"
    ]
   }
  }
 },
 "tests": {
  "F1": [
   {
    "test": "test_comment_contract[F1]",
    "outcome": "passed"
   },
   {
    "test": "test_created_as_declared[F1]",
    "outcome": "passed"
   },
   {
    "test": "test_data_access_declared[F1]",
    "outcome": "passed"
   },
   {
    "test": "test_uses_what_it_lists[F1]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_declared_tables[F1]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_are_declared[F1]",
    "outcome": "passed"
   },
   {
    "test": "test_f1_agrees_with_every_recorded_play",
    "outcome": "passed"
   },
   {
    "test": "test_f1_thirty_seconds_is_the_boundary",
    "outcome": "passed"
   },
   {
    "test": "test_f1_unknown_recording_has_no_royalty",
    "outcome": "passed"
   },
   {
    "test": "test_f1_follows_a_rate_change",
    "outcome": "passed"
   }
  ],
  "P1": [
   {
    "test": "test_comment_contract[P1]",
    "outcome": "passed"
   },
   {
    "test": "test_created_as_declared[P1]",
    "outcome": "passed"
   },
   {
    "test": "test_data_access_declared[P1]",
    "outcome": "passed"
   },
   {
    "test": "test_uses_what_it_lists[P1]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_declared_tables[P1]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_are_declared[P1]",
    "outcome": "passed"
   },
   {
    "test": "test_p1_records_an_abandoned_skip",
    "outcome": "passed"
   },
   {
    "test": "test_p1_full_length_play_is_completed",
    "outcome": "passed"
   },
   {
    "test": "test_p1_short_play_earns_nothing",
    "outcome": "passed"
   },
   {
    "test": "test_p1_shared_station_is_accepted",
    "outcome": "passed"
   },
   {
    "test": "test_p1_refuses_an_invalid_play[unknown_track]",
    "outcome": "passed"
   },
   {
    "test": "test_p1_refuses_an_invalid_play[awaiting_scoring]",
    "outcome": "passed"
   },
   {
    "test": "test_p1_refuses_an_invalid_play[rejected]",
    "outcome": "passed"
   },
   {
    "test": "test_p1_refuses_an_invalid_play[longer_than_the_recording]",
    "outcome": "passed"
   },
   {
    "test": "test_p1_repeated_report_is_rejected",
    "outcome": "passed"
   },
   {
    "test": "test_p1_unknown_listener_is_refused_by_the_database",
    "outcome": "passed"
   },
   {
    "test": "test_p1_ledger_survives_a_rate_change",
    "outcome": "passed"
   },
   {
    "test": "test_p1_no_time_given_records_utc_now",
    "outcome": "passed"
   }
  ],
  "P2": [
   {
    "test": "test_comment_contract[P2]",
    "outcome": "passed"
   },
   {
    "test": "test_created_as_declared[P2]",
    "outcome": "passed"
   },
   {
    "test": "test_data_access_declared[P2]",
    "outcome": "passed"
   },
   {
    "test": "test_uses_what_it_lists[P2]",
    "outcome": "passed"
   },
   {
    "test": "test_reads_declared_tables[P2]",
    "outcome": "passed"
   },
   {
    "test": "test_columns_are_declared[P2]",
    "outcome": "passed"
   },
   {
    "test": "test_p2_new_upload_awaits_scoring",
    "outcome": "passed"
   },
   {
    "test": "test_p2_duplicate_is_answered_not_raised",
    "outcome": "passed"
   },
   {
    "test": "test_p2_duplicate_of_another_artists_audio",
    "outcome": "passed"
   },
   {
    "test": "test_p2_batch_carries_on_after_a_duplicate",
    "outcome": "passed"
   },
   {
    "test": "test_p2_unregistered_artist_is_refused",
    "outcome": "passed"
   },
   {
    "test": "test_p2_handler_catches_only_duplicates",
    "outcome": "passed"
   },
   {
    "test": "test_p2_simultaneous_uploads_never_report_a_false_duplicate",
    "outcome": "passed"
   },
   {
    "test": "test_p2_key_clash_is_not_reported_as_a_duplicate",
    "outcome": "passed"
   }
  ],
  "file": [
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
    "test": "test_try_it_block_gives_the_documented_answers",
    "outcome": "passed"
   }
  ]
 },
 "demo": [
  {
   "label": "F1: a 29-second play earns nothing; 30 seconds earns Velvet Static's rate.",
   "sql": "SELECT crossfade.play_royalty(4817, 29) AS royalty_29_seconds,\n       crossfade.play_royalty(4817, 30) AS royalty_30_seconds",
   "columns": [
    "royalty_29_seconds",
    "royalty_30_seconds"
   ],
   "rows": [
    [
     "0.00000",
     "0.00400"
    ]
   ]
  },
  {
   "label": "P1: dokafor skips Low Tide after 107 of its 214 seconds.",
   "sql": "CALL crossfade.record_play(20937, 4817, NULL, 107, 'skipped', '2026-11-01 20:15:00', @completed, @royalty)"
  },
  {
   "label": "",
   "sql": "SELECT @completed AS completed, @royalty AS royalty_amount",
   "columns": [
    "completed",
    "royalty_amount"
   ],
   "rows": [
    [
     "0",
     "0.00400"
    ]
   ]
  },
  {
   "label": "P2: Velvet Static uploads Low Tide's audio again (same checksum as track 4817).",
   "sql": "CALL crossfade.upload_track(1042, 'Low Tide (again)', 214, '2026-11-01',\n\t(SELECT audio_checksum FROM crossfade.track WHERE track_id = 4817), @track_id, @status, @message)"
  },
  {
   "label": "",
   "sql": "SELECT @track_id AS track_id, @status AS status, @message AS message",
   "columns": [
    "track_id",
    "status",
    "message"
   ],
   "rows": [
    [
     "4817",
     "duplicate",
     "already in the catalogue as track 4817 (Low Tide Signal)"
    ]
   ]
  },
  {
   "label": "P2: Kestrel Ave uploads a new recording.",
   "sql": "CALL crossfade.upload_track(1049, 'First Light', 201, '2026-12-01', UNHEX(SHA2('first light', 256)),\n\t@track_id, @status, @message)"
  },
  {
   "label": "",
   "sql": "SELECT @track_id AS track_id, @status AS status, @message AS message",
   "columns": [
    "track_id",
    "status",
    "message"
   ],
   "rows": [
    [
     "4832",
     "uploaded",
     "uploaded as track 4832, awaiting scoring"
    ]
   ]
  }
 ],
 "cases": [
  {
   "tag": "F1",
   "inputs": [
    {
     "kind": "call",
     "sql": "SELECT crossfade.play_royalty(track_id, seconds_played) -- for each of the 31 sample plays"
    }
   ],
   "columns": [
    "track_id",
    "seconds_played",
    "oracle",
    "play_royalty"
   ],
   "expected": [
    [
     "4820",
     "187",
     "0.00350",
     "0.00350"
    ],
    [
     "4821",
     "201",
     "0.00380",
     "0.00380"
    ],
    [
     "4821",
     "83",
     "0.00380",
     "0.00380"
    ],
    [
     "4821",
     "312",
     "0.00380",
     "0.00380"
    ],
    [
     "4821",
     "24",
     "0.00000",
     "0.00000"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4827",
     "23",
     "0.00000",
     "0.00000"
    ],
    [
     "4823",
     "205",
     "0.00320",
     "0.00320"
    ],
    [
     "4818",
     "187",
     "0.00400",
     "0.00400"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4823",
     "10",
     "0.00000",
     "0.00000"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4829",
     "189",
     "0.00300",
     "0.00300"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4825",
     "188",
     "0.00360",
     "0.00360"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4824",
     "151",
     "0.00320",
     "0.00320"
    ],
    [
     "4823",
     "205",
     "0.00320",
     "0.00320"
    ],
    [
     "4828",
     "221",
     "0.00300",
     "0.00300"
    ],
    [
     "4817",
     "214",
     "0.00400",
     "0.00400"
    ],
    [
     "4826",
     "104",
     "0.00360",
     "0.00360"
    ],
    [
     "4817",
     "20",
     "0.00000",
     "0.00000"
    ],
    [
     "4817",
     "214",
     "0.00400",
     "0.00400"
    ],
    [
     "4829",
     "189",
     "0.00300",
     "0.00300"
    ],
    [
     "4817",
     "214",
     "0.00400",
     "0.00400"
    ],
    [
     "4829",
     "189",
     "0.00300",
     "0.00300"
    ],
    [
     "4817",
     "210",
     "0.00400",
     "0.00400"
    ],
    [
     "4824",
     "14",
     "0.00000",
     "0.00000"
    ]
   ],
   "got": [
    [
     "4820",
     "187",
     "0.00350",
     "0.00350"
    ],
    [
     "4821",
     "201",
     "0.00380",
     "0.00380"
    ],
    [
     "4821",
     "83",
     "0.00380",
     "0.00380"
    ],
    [
     "4821",
     "312",
     "0.00380",
     "0.00380"
    ],
    [
     "4821",
     "24",
     "0.00000",
     "0.00000"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4827",
     "23",
     "0.00000",
     "0.00000"
    ],
    [
     "4823",
     "205",
     "0.00320",
     "0.00320"
    ],
    [
     "4818",
     "187",
     "0.00400",
     "0.00400"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4823",
     "10",
     "0.00000",
     "0.00000"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4829",
     "189",
     "0.00300",
     "0.00300"
    ],
    [
     "4825",
     "233",
     "0.00360",
     "0.00360"
    ],
    [
     "4825",
     "188",
     "0.00360",
     "0.00360"
    ],
    [
     "4827",
     "254",
     "0.00300",
     "0.00300"
    ],
    [
     "4824",
     "151",
     "0.00320",
     "0.00320"
    ],
    [
     "4823",
     "205",
     "0.00320",
     "0.00320"
    ],
    [
     "4828",
     "221",
     "0.00300",
     "0.00300"
    ],
    [
     "4817",
     "214",
     "0.00400",
     "0.00400"
    ],
    [
     "4826",
     "104",
     "0.00360",
     "0.00360"
    ],
    [
     "4817",
     "20",
     "0.00000",
     "0.00000"
    ],
    [
     "4817",
     "214",
     "0.00400",
     "0.00400"
    ],
    [
     "4829",
     "189",
     "0.00300",
     "0.00300"
    ],
    [
     "4817",
     "214",
     "0.00400",
     "0.00400"
    ],
    [
     "4829",
     "189",
     "0.00300",
     "0.00300"
    ],
    [
     "4817",
     "210",
     "0.00400",
     "0.00400"
    ],
    [
     "4824",
     "14",
     "0.00000",
     "0.00000"
    ]
   ],
   "doc": "play_royalty gives the royalty already recorded on every sample play.\nWhy: rule I7 says the stored amount is the artist's rate for 30 seconds or more, else 0; the function must\nreproduce the 31 sample plays exactly (the rates have not changed since).\nExpect: for each play, play_royalty(track, seconds) = its royalty_amount = the oracle.",
   "test": "test_f1_agrees_with_every_recorded_play",
   "outcome": "passed"
  },
  {
   "tag": "F1",
   "inputs": [
    {
     "kind": "call",
     "sql": "SELECT crossfade.play_royalty(4817, 0), crossfade.play_royalty(4817, 29), crossfade.play_royalty(4817, 30), crossfade.play_royalty(4817, 214)"
    }
   ],
   "columns": [
    "0 s",
    "29 s",
    "30 s",
    "214 s"
   ],
   "expected": [
    [
     "0.00000",
     "0.00000",
     "0.00400",
     "0.00400"
    ]
   ],
   "got": [
    [
     "0.00000",
     "0.00000",
     "0.00400",
     "0.00400"
    ]
   ],
   "doc": "29 seconds earns nothing; 30 seconds earns the artist's rate; a full play earns the same rate.\nWhy: rule I7's boundary is \"30 seconds or more\"; the sample's shortest play is 10 seconds and none is 29 or 30.\nExpect: play_royalty(4817, s) for s = 0, 29, 30, 214 gives 0, 0, 0.00400, 0.00400 (Velvet Static's rate).",
   "test": "test_f1_thirty_seconds_is_the_boundary",
   "outcome": "passed"
  },
  {
   "tag": "F1",
   "inputs": [
    {
     "kind": "call",
     "sql": "SELECT crossfade.play_royalty(9999, 200), crossfade.play_royalty(4817, NULL)"
    }
   ],
   "columns": [
    "track 9999",
    "no length"
   ],
   "expected": [
    [
     null,
     null
    ]
   ],
   "got": [
    [
     null,
     null
    ]
   ],
   "doc": "A recording that does not exist has no royalty: NULL, not 0.\nWhy: 0 would read as \"a short play\"; there is simply no rate to apply.\nExpect: play_royalty(9999, 200) is NULL; play_royalty(4817, NULL) is NULL.",
   "test": "test_f1_unknown_recording_has_no_royalty",
   "outcome": "passed"
  },
  {
   "tag": "F1",
   "inputs": [
    {
     "kind": "call",
     "sql": "UPDATE artist SET payout_rate = 0.00450 WHERE artist_id = 1042"
    },
    {
     "kind": "call",
     "sql": "SELECT crossfade.play_royalty(4817, 30)"
    }
   ],
   "columns": [
    "royalty"
   ],
   "expected": [
    [
     "0.00450"
    ]
   ],
   "got": [
    [
     "0.00450"
    ]
   ],
   "doc": "After an artist's rate changes, the function applies the new rate.\nWhy: this is why play_royalty is NOT DETERMINISTIC, and why record_play stores its answer as a snapshot.\nExpect: Velvet Static's rate set to 0.00450: play_royalty(4817, 30) gives 0.00450.",
   "test": "test_f1_follows_a_rate_change",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4817, NULL, 107, 'skipped', '2026-11-01 20:15:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "listener_id",
    "track_id",
    "played_at",
    "station_id",
    "seconds_played",
    "completed",
    "reaction",
    "royalty_amount",
    "OUT completed",
    "OUT royalty"
   ],
   "expected": [
    [
     "20937",
     "4817",
     "2026-11-01 20:15:00",
     null,
     "107",
     "0",
     "skipped",
     "0.00400",
     "0",
     "0.00400"
    ]
   ],
   "got": [
    [
     "20937",
     "4817",
     "2026-11-01 20:15:00",
     null,
     "107",
     "0",
     "skipped",
     "0.00400",
     "0",
     "0.00400"
    ]
   ],
   "doc": "A skipped play of half a recording is recorded as not completed, and still earns the rate.\nWhy: rule I7 computes both completed and royalty_amount from the Track and Artist rows.\nExpect: dokafor (20937) skips Low Tide (4817, 214 s) after 107 s: completed 0, royalty 0.00400; the OUT\nparameters return the same two values.",
   "test": "test_p1_records_an_abandoned_skip",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4829, NULL, 189, 'saved', '2026-11-01 21:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "listener_id",
    "track_id",
    "played_at",
    "station_id",
    "seconds_played",
    "completed",
    "reaction",
    "royalty_amount",
    "OUT completed",
    "OUT royalty"
   ],
   "expected": [
    [
     "20937",
     "4829",
     "2026-11-01 21:00:00",
     null,
     "189",
     "1",
     "saved",
     "0.00300",
     "1",
     "0.00300"
    ]
   ],
   "got": [
    [
     "20937",
     "4829",
     "2026-11-01 21:00:00",
     null,
     "189",
     "1",
     "saved",
     "0.00300",
     "1",
     "0.00300"
    ]
   ],
   "doc": "A play as long as the recording is a completed play.\nWhy: completed is true \"exactly when Seconds Played equals the Duration\" (RA).\nExpect: 189 s of Ember Count (4829, 189 s), saved: completed 1, royalty 0.00300.",
   "test": "test_p1_full_length_play_is_completed",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4817, NULL, 29, NULL, '2026-11-01 22:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "listener_id",
    "track_id",
    "played_at",
    "station_id",
    "seconds_played",
    "completed",
    "reaction",
    "royalty_amount",
    "OUT completed",
    "OUT royalty"
   ],
   "expected": [
    [
     "20937",
     "4817",
     "2026-11-01 22:00:00",
     null,
     "29",
     "0",
     null,
     "0.00000",
     "0",
     "0.00000"
    ]
   ],
   "got": [
    [
     "20937",
     "4817",
     "2026-11-01 22:00:00",
     null,
     "29",
     "0",
     null,
     "0.00000",
     "0",
     "0.00000"
    ]
   ],
   "doc": "A play under 30 seconds is recorded, earns nothing, and is not completed.\nWhy: the royalty rule's boundary inside the procedure, through play_royalty.\nExpect: 29 s of 4817: completed 0, royalty 0.00000.",
   "test": "test_p1_short_play_earns_nothing",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4819, 7710, 241, NULL, '2026-11-02 08:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "listener_id",
    "track_id",
    "played_at",
    "station_id",
    "seconds_played",
    "completed",
    "reaction",
    "royalty_amount",
    "OUT completed",
    "OUT royalty"
   ],
   "expected": [
    [
     "20937",
     "4819",
     "2026-11-02 08:00:00",
     "7710",
     "241",
     "1",
     null,
     "0.00350",
     "1",
     "0.00350"
    ]
   ],
   "got": [
    [
     "20937",
     "4819",
     "2026-11-02 08:00:00",
     "7710",
     "241",
     "1",
     null,
     "0.00350",
     "1",
     "0.00350"
    ]
   ],
   "doc": "A listener may play through a station another listener created.\nWhy: rule I6: \"A play's Station ID may refer to a station created by another listener.\"\nExpect: dokafor (20937) plays 4819 through Late Jazz Hop (7710, created by 20931): recorded with station 7710.",
   "test": "test_p1_shared_station_is_accepted",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 9999, NULL, 100, NULL, '2026-11-03 09:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "error",
    "message",
    "plays"
   ],
   "expected": [
    [
     "1644",
     "record_play: track 9999 does not exist",
     "31"
    ]
   ],
   "got": [
    [
     "1644",
     "record_play: track 9999 does not exist",
     "31"
    ]
   ],
   "doc": "record_play refuses an invalid play with SIGNAL SQLSTATE '45000' and a message naming the problem, and\nwrites nothing.\nWhy: only released recordings can be streamed, and a play cannot outlast its recording; none of these is in\nthe sample data.\nExpect: MySQL error 1644 (SQLSTATE 45000) with the oracle's message; the play table is unchanged.",
   "test": "test_p1_refuses_an_invalid_play[unknown_track]",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4830, NULL, 100, NULL, '2026-11-03 09:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "error",
    "message",
    "plays"
   ],
   "expected": [
    [
     "1644",
     "record_play: track 4830 is not released for streaming (awaiting scoring)",
     "31"
    ]
   ],
   "got": [
    [
     "1644",
     "record_play: track 4830 is not released for streaming (awaiting scoring)",
     "31"
    ]
   ],
   "doc": "record_play refuses an invalid play with SIGNAL SQLSTATE '45000' and a message naming the problem, and\nwrites nothing.\nWhy: only released recordings can be streamed, and a play cannot outlast its recording; none of these is in\nthe sample data.\nExpect: MySQL error 1644 (SQLSTATE 45000) with the oracle's message; the play table is unchanged.",
   "test": "test_p1_refuses_an_invalid_play[awaiting_scoring]",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4831, NULL, 40, NULL, '2026-11-03 09:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "error",
    "message",
    "plays"
   ],
   "expected": [
    [
     "1644",
     "record_play: track 4831 is not released for streaming (rejected)",
     "31"
    ]
   ],
   "got": [
    [
     "1644",
     "record_play: track 4831 is not released for streaming (rejected)",
     "31"
    ]
   ],
   "doc": "record_play refuses an invalid play with SIGNAL SQLSTATE '45000' and a message naming the problem, and\nwrites nothing.\nWhy: only released recordings can be streamed, and a play cannot outlast its recording; none of these is in\nthe sample data.\nExpect: MySQL error 1644 (SQLSTATE 45000) with the oracle's message; the play table is unchanged.",
   "test": "test_p1_refuses_an_invalid_play[rejected]",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4817, NULL, 215, NULL, '2026-11-03 09:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "error",
    "message",
    "plays"
   ],
   "expected": [
    [
     "1644",
     "record_play: 215 seconds played, but track 4817 is only 214 seconds long",
     "31"
    ]
   ],
   "got": [
    [
     "1644",
     "record_play: 215 seconds played, but track 4817 is only 214 seconds long",
     "31"
    ]
   ],
   "doc": "record_play refuses an invalid play with SIGNAL SQLSTATE '45000' and a message naming the problem, and\nwrites nothing.\nWhy: only released recordings can be streamed, and a play cannot outlast its recording; none of these is in\nthe sample data.\nExpect: MySQL error 1644 (SQLSTATE 45000) with the oracle's message; the play table is unchanged.",
   "test": "test_p1_refuses_an_invalid_play[longer_than_the_recording]",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4829, NULL, 189, 'saved', '2026-08-19 13:32:05', @completed, @royalty)"
    }
   ],
   "columns": [
    "error",
    "ledger total"
   ],
   "expected": [
    [
     "1062",
     "0.09010"
    ]
   ],
   "got": [
    [
     "1062",
     "0.09010"
    ]
   ],
   "doc": "A second report of a play already recorded is rejected by the database, not paid twice.\nWhy: the key (listener, recording, start time) \"is what keeps a double-counted royalty out of the ledger\"\n(RA); record_play must not catch or hide that error.\nExpect: re-reporting dokafor's sample play of 4829 at 2026-08-19 13:32:05 fails with 1062; the ledger total\nis unchanged.",
   "test": "test_p1_repeated_report_is_rejected",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(99999, 4817, NULL, 60, NULL, '2026-11-03 10:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "error"
   ],
   "expected": [
    [
     "1452"
    ]
   ],
   "got": [
    [
     "1452"
    ]
   ],
   "doc": "A play by a listener who does not exist is refused by the foreign key, and nothing is written.\nWhy: the procedure leaves the database's own checks in place rather than duplicating them.\nExpect: listener 99999: MySQL error 1452 (fk_play_listener).",
   "test": "test_p1_unknown_listener_is_refused_by_the_database",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4817, NULL, 120, NULL, '2026-11-04 10:00:00', @completed, @royalty)"
    },
    {
     "kind": "call",
     "sql": "UPDATE artist SET payout_rate = 0.00450 WHERE artist_id = 1042"
    },
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4817, NULL, 120, NULL, '2026-11-05 10:00:00', @completed, @royalty)"
    }
   ],
   "columns": [
    "first play",
    "second play"
   ],
   "expected": [
    [
     "0.00400",
     "0.00450"
    ]
   ],
   "got": [
    [
     "0.00400",
     "0.00450"
    ]
   ],
   "doc": "A royalty already recorded keeps its amount when the artist's rate later changes; the next play earns the\nnew rate.\nWhy: rule I7: \"Royalty Amount is computed once, when the play is recorded, and never updated.\"\nExpect: play of 4817 recorded at 0.00400; rate raised to 0.00450; that play still holds 0.00400, a new play\nholds 0.00450.",
   "test": "test_p1_ledger_survives_a_rate_change",
   "outcome": "passed"
  },
  {
   "tag": "P1",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.record_play(20937, 4818, NULL, 60, NULL, NULL, @completed, @royalty)"
    }
   ],
   "columns": [
    "from",
    "played_at",
    "to"
   ],
   "expected": [
    [
     "2026-11-08 20:24:09",
     "between",
     "2026-11-08 20:24:09"
    ]
   ],
   "got": [
    [
     "2026-11-08 20:24:09",
     "2026-11-08 20:24:09",
     "2026-11-08 20:24:09"
    ]
   ],
   "doc": "With no start time given, the play is recorded at the current UTC time, whatever the session's time zone.\nWhy: \"Played At is recorded in UTC\" (RA), so a daylight-saving change can never repeat a key. The session is\nput in Arizona time (UTC-7) first, so local time and UTC differ by seven hours.\nExpect: played_at falls between UTC_TIMESTAMP() just before and just after the call.",
   "test": "test_p1_no_time_given_records_utc_now",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1049, 'First Light', 201, '2026-12-01', 0x307B1B3807FD9902D48158A2880C2CEDEDEF17BDAAA6558443E2EE9C885303CD, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "OUT track_id",
    "OUT status",
    "OUT message"
   ],
   "expected": [
    [
     "4832",
     "uploaded",
     "uploaded as track 4832, awaiting scoring"
    ]
   ],
   "got": [
    [
     "4832",
     "uploaded",
     "uploaded as track 4832, awaiting scoring"
    ]
   ],
   "doc": "A new recording enters the catalogue awaiting scoring, under the next track ID.\nWhy: the first stage of the upload pipeline (RA: no score \"while it is awaiting scoring\").\nExpect: Kestrel Ave (1049) uploads First Light: track 4832, status 'uploaded', and the row holds the upload\nwith ingest_status 'awaiting scoring'.",
   "test": "test_p2_new_upload_awaits_scoring",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1042, 'Low Tide (again)', 214, '2026-11-01', 0xBD675D48363DAAFDCEF52552ABD98D2302AE34C58A6AEBE32A13ABF4A14ED8B4, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "OUT track_id",
    "OUT status",
    "OUT message"
   ],
   "expected": [
    [
     "4817",
     "duplicate",
     "already in the catalogue as track 4817 (Low Tide Signal)"
    ]
   ],
   "got": [
    [
     "4817",
     "duplicate",
     "already in the catalogue as track 4817 (Low Tide Signal)"
    ]
   ],
   "doc": "Uploading audio already in the catalogue is answered, not raised: nothing is inserted and the uploader is\ntold which recording it is.\nWhy: the UNIQUE index on audio_checksum detects the duplicate (error 1062), and the EXIT HANDLER turns it\ninto an answer.\nExpect: Velvet Static re-uploads Low Tide's audio: no error, status 'duplicate', track 4817 named; the track\ncount is unchanged.",
   "test": "test_p2_duplicate_is_answered_not_raised",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1049, 'Ember Count', 189, '2026-11-01', 0x4F9FF37AD95773DCD6CADECE159F4EB187B0110E3B7F056B01B9CCC94773AE90, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "OUT track_id",
    "OUT status",
    "OUT message"
   ],
   "expected": [
    [
     "4829",
     "duplicate",
     "already in the catalogue as track 4829 (Tapeworm Blues)"
    ]
   ],
   "got": [
    [
     "4829",
     "duplicate",
     "already in the catalogue as track 4829 (Tapeworm Blues)"
    ]
   ],
   "doc": "The same audio uploaded by a different artist is still a duplicate.\nWhy: the checksum identifies the audio, whoever uploads it; a second licence for the same file is refused.\nExpect: Kestrel Ave (1049) uploads Ember Count's audio (4829, by 1048): status 'duplicate', track 4829.",
   "test": "test_p2_duplicate_of_another_artists_audio",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1049, 'First Light', 200, '2026-12-01', 0x307B1B3807FD9902D48158A2880C2CEDEDEF17BDAAA6558443E2EE9C885303CD, @track_id, @status, @message)"
    },
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1042, 'Low Tide (again)', 200, '2026-12-01', 0xBD675D48363DAAFDCEF52552ABD98D2302AE34C58A6AEBE32A13ABF4A14ED8B4, @track_id, @status, @message)"
    },
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1049, 'Second Light', 200, '2026-12-01', 0xD9FB4927C55FBF08034B71386E6EBD70870F366E0C3F6331B7F4A7EC2EFD4441, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "OUT track_id",
    "OUT status"
   ],
   "expected": [
    [
     "4832",
     "uploaded"
    ],
    [
     "4817",
     "duplicate"
    ],
    [
     "4833",
     "uploaded"
    ]
   ],
   "got": [
    [
     "4832",
     "uploaded"
    ],
    [
     "4817",
     "duplicate"
    ],
    [
     "4833",
     "uploaded"
    ]
   ],
   "doc": "A run of uploads carries on past a duplicate: new, duplicate, new.\nWhy: this is why the duplicate is caught: an uncaught 1062 would stop a script at the second upload.\nExpect: tracks 4832 'uploaded', 4817 'duplicate', 4833 'uploaded'.",
   "test": "test_p2_batch_carries_on_after_a_duplicate",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(9999, 'Nobody', 120, '2026-12-01', 0x6382B3CC881412B77BFCAEED026001C00D9E3025E66C20F6E7E92F079851462A, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "error",
    "message",
    "tracks"
   ],
   "expected": [
    [
     "1644",
     "upload_track: artist 9999 is not registered",
     "15"
    ]
   ],
   "got": [
    [
     "1644",
     "upload_track: artist 9999 is not registered",
     "15"
    ]
   ],
   "doc": "An upload from an artist who is not registered is refused with SIGNAL, and nothing is inserted.\nWhy: artists upload \"under a direct streaming licence\" (RA); the procedure says so in words.\nExpect: artist 9999: MySQL error 1644 (SQLSTATE 45000), \"artist 9999 is not registered\".",
   "test": "test_p2_unregistered_artist_is_refused",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1049, 'Silence', 0, '2026-12-01', 0xE6C18FDBE59783DFEFEF3595CD288BCB7CE912D36854B5E8FAAEF31235D9031B, @track_id, @status, @message)"
    },
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1042, 'Low Tide (silent)', 0, '2026-12-01', 0xBD675D48363DAAFDCEF52552ABD98D2302AE34C58A6AEBE32A13ABF4A14ED8B4, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "new audio",
    "known audio"
   ],
   "expected": [
    [
     "3819",
     "3819"
    ]
   ],
   "got": [
    [
     "3819",
     "3819"
    ]
   ],
   "doc": "Only error 1062 is caught: an invalid length is still refused by the database, even for audio that is\nalready in the catalogue.\nWhy: an EXIT HANDLER for every error would hide real problems (here it would answer 'duplicate' and hide the\ninvalid length); this one names 1062 alone.\nExpect: a 0-second upload of new audio, and of Low Tide's audio, both fail with 3819 (ck_track_duration).",
   "test": "test_p2_handler_catches_only_duplicates",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "-- connection A\nCALL crossfade.upload_track(1049, 'Race A', 200, '2026-12-01', 0x4A74D55F450E2021C247CDADC2BFF6DA86B3F22A8D23791E8DB42D2252BC4CF2, @track_id, @status, @message)"
    },
    {
     "kind": "call",
     "sql": "-- connection B, at the same moment\nCALL crossfade.upload_track(1048, 'Race B', 200, '2026-12-01', 0x3AD110375ADF07CF2FDF7EB89C4D46B9B52015062EE0ED9F79808284A02975AE, @track_id, @status, @message)"
    },
    {
     "kind": "call",
     "sql": "-- connection A\nCOMMIT"
    }
   ],
   "columns": [
    "A",
    "B"
   ],
   "expected": [
    [
     "4832 uploaded",
     "4833 uploaded, or error 1062 PRIMARY"
    ]
   ],
   "got": [
    [
     "4832 uploaded",
     "4833 uploaded"
    ]
   ],
   "doc": "Two uploads of different audio at the same moment both get an honest answer, never 'duplicate'.\nWhy: both compute the next track ID. Two connections reproduce it: A uploads and holds its new row, B uploads\ndifferent audio, A commits. On MySQL 8 the second upload's ID lookup waits for the first, so B takes the next\nID; if a server let both take the same ID, B would get the primary-key clash (1062 on PRIMARY), which the\nhandler re-raises (see the next case). What must never happen is B being told its new audio is a duplicate.\nExpect: A gets track 4832; B gets track 4833 'uploaded', or error 1062 on PRIMARY. Both rows are deleted again\nafterwards.",
   "test": "test_p2_simultaneous_uploads_never_report_a_false_duplicate",
   "outcome": "passed"
  },
  {
   "tag": "P2",
   "inputs": [
    {
     "kind": "call",
     "sql": "CREATE TRIGGER test_take_used_id BEFORE INSERT ON track FOR EACH ROW SET NEW.track_id = 4817   -- test only, dropped afterwards"
    },
    {
     "kind": "call",
     "sql": "CALL crossfade.upload_track(1049, 'Clash', 200, '2026-12-01', 0x15A5A49734B740AD0226AB916B0441BE97E8F6F0732BD8344F03624117CF9F1D, @track_id, @status, @message)"
    }
   ],
   "columns": [
    "error",
    "on",
    "tracks"
   ],
   "expected": [
    [
     "1062",
     "PRIMARY",
     "15"
    ]
   ],
   "got": [
    [
     "1062",
     "PRIMARY",
     "15"
    ]
   ],
   "doc": "A 1062 that is not about the audio (the new track ID already taken) is re-raised, not answered as a\nduplicate.\nWhy: the handler catches every 1062, but only a clash on audio_checksum is a duplicate upload; for any other\nit finds no recording with the new checksum and must RESIGNAL. To make the new ID clash on demand, a\ntemporary trigger rewrites it to 4817, an ID already in use (the trigger is dropped again afterwards).\nExpect: uploading new audio fails with 1062 on PRIMARY; nothing is inserted.",
   "test": "test_p2_key_clash_is_not_reported_as_a_duplicate",
   "outcome": "passed"
  }
 ]
};
