/*
	FILE: single_table.sql
	.
	INFO 579 Project 2, Task 2: Single-table queries
	CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh)
	.
	***** FYI and project descriptions **********
	One query per question the business asks of a single table. The questions are
	the use cases (UC-xx) drawn from the Project 1 requirements analysis; every
	non-associative table (artist, track, genre, listener, scoring_model, station)
	is queried, and track twice, so that every use case a single table can answer
	is answered.

	BRIEF REQUIREMENTS ADDRESSED (Task 2: "Develop a variety of SQL queries
	following the requirements for single table queries"). The brief's wording is
	quoted; "2.1" is Task 2, requirement 1, and (a)-(e) are its sub-requirements.
	The minimum is one query per non-associative table for 2.1, and at least one
	query for each of (a)-(e). Each is met; where more than one query is listed,
	the extra queries go beyond the minimum.
	  2.1  "Write queries to retrieve data from each non-associative table
	       individually": artist S1, track S2 S7, genre S3, listener S4,
	       scoring_model S5, station S6. Each query reads one table only.
	  (a)  "At least one of the queries must use single row functions":
	       S1 S2 S3 S4 S5 S6 S7
	  (b)  "At least one of the queries must use aggregate functions":
	       S3 S4 S6 S7
	  (c)  "At least one of the queries must sort the results according to some
	       criteria": S1 S2 S3 S4 S5 S6 S7
	  (d)  "At least one of the queries must return just the first N results":
	       S2 (LIMIT 5), S5 (LIMIT 1)
	  (e)  "At least one of the queries must use a selection control function":
	       S1 S3 S6 S7
	  Each query's own comment repeats this: its Requirements field names the
	  requirements it meets and shows the SQL that meets each one.

	THE BRIEF'S GENERAL RULES, and how this file meets them:
	  "Every statement, query and routine should be justified within the logic of
	  your business plan and must be preceded by a comment explaining its
	  purpose": every query has its own comment directly above it; its
	  Business need field gives the purpose and ties it to the business plan
	  (the Project 1 requirements analysis, RA), and its Business question field
	  justifies how the query is written, citing the RA.
	  "Avoid trivial and generic solutions": each query answers a question
	  CROSSFADE actually asks (a use case, UC-xx, from the RA), never a generic
	  "show the whole table" listing.

	***** How to Run *********
	Run database_implementation.sql first, then this script. Each query reads only
	the `crossfade` database, changes nothing, and can be run on its own.

	***** NERD STUFF *********
	Report date: every "days since" figure is measured to 2026-09-30, the close of
	Q3 2026 and the reporting date of the sample data (the last event in it is a
	2026-09-22 upload). A fixed date keeps the results reproducible; a live report
	would use CURDATE() in its place.
	Comments: each statement is preceded by a comment with the same fields:
	  [S#] TABLE        tag and the one table the query reads
	  Use cases:        the use cases (UC-xx) it answers
	  Business need:    what the business plan (the Project 1 requirements
	                    analysis, RA) needs from this data
	  Business question: the question the query answers, then why it is written
	                    the way it is, citing the RA
	  Requirements:     the brief's requirements it meets (2.1 and (a)-(e), see
	                    the list above), on one line; then, indented, each
	                    one quoted from the brief with the SQL that meets it
	  Output:           its result columns, in order
	project2/tests/test_single_table.py reads these fields and checks each query
	against an independent answer computed from the Project 1 data.
	DISABLED CHECK: the last statement, [E1], is a write the database must refuse
	(UC-15, duplicate upload). It is commented out, so this file runs without
	error; it is not a brief requirement. The [E1] comment says how to run it.

	***** Re: Class notes and syntax *****
	"Selection control" follows the Unit 8 slides: CASE and IF. Arithmetic uses the
	Unit 6 operators (DIV, MOD).
	Course material: CONCAT, LPAD, ROUND, DATEDIFF and the aggregates from Unit 6;
	CASE, IF and scalar subqueries from Unit 8.
	Beyond the slides: CHAR_LENGTH (S3). Unit 6 shows LENGTH, which counts bytes;
	an accented letter takes two bytes in utf8mb4, and the RA's one-line limit
	for a description is 80 characters, so S3 counts characters.
	Branches: every CASE/IF branch fires on the sample data except one: S7's "on time"
	branch, the healthy state for an unscored upload, which the sample data does
	not contain (its one unscored upload is already late).
*/


/*
	[S1] ARTIST: royalty run readiness
	Use cases: UC-02, UC-01
	Business need: CROSSFADE pays every artist a per-stream royalty (RA: Overview;
	  Artist). Two artist fields bear on whether a payment can go out: Verified,
	  "whether the service has confirmed the artist's identity and their right to
	  licence the material they upload", and Country, used "to determine which
	  royalty payment channels and tax treatments apply" (RA: Artist).
	Business question: Is each artist ready for this royalty run, and if not,
	which check is outstanding?
	- Hold rule (business policy, not stated in the RA): a payment needs a
	  confirmed licence right and a country to route it through, so an artist
	  missing either is held. The RA defines the two fields; using them to gate
	  payment is the policy built on them.
	- Each check has its own column and its own IF, so an artist failing both
	  shows both. A single CASE with ordered WHENs would report only the first
	  failure: Saltmarsh Tapes is unverified and has no country, so its missing
	  country would never be shown.
	- run_status (CASE) is 'ready' only when both checks pass.
	- Payout is quoted per 1,000 streams, the figure artists compare, from the
	  per-stream payout_rate. Days under licence counts from joined_date, the day
	  the artist's licence took effect (RA: Joined Date).
	- Ready artists first ('ready' sorts after 'held', so DESC), then by rate,
	  highest first; artist_id breaks ties.
	Requirements: 2.1, (a), (c), (e)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the artist table, and only artist
	  (a)  "use single row functions": ROUND (usd_per_1000_streams), DATEDIFF
	       (days_under_licence)
	  (c)  "sort the results according to some criteria": ORDER BY run_status
	       DESC, payout_rate DESC, artist_id
	  (e)  "use a selection control function": IF (licence_check,
	       payment_country), CASE (run_status)
	Output: artist_id, stage_name, usd_per_1000_streams, days_under_licence, licence_check, payment_country, run_status
*/
SELECT artist_id,
       stage_name,
       ROUND(payout_rate * 1000, 2) AS usd_per_1000_streams,
       DATEDIFF('2026-09-30', joined_date) AS days_under_licence,
       IF(verified = 1, 'confirmed', 'HOLD: not confirmed') AS licence_check,
       IF(country IS NULL, 'HOLD: no country', country) AS payment_country,
       CASE
           WHEN verified = 1 AND country IS NOT NULL THEN 'ready'
           ELSE 'held'
       END AS run_status
FROM crossfade.artist
ORDER BY run_status DESC,
         payout_rate DESC,
         artist_id;


/*
	[S2] TRACK: the new-uploads shelf
	Use cases: UC-03
	Business need: a recording uploaded an hour ago must be as recommendable as one
	  with a million plays (RA: Overview), and only scored recordings may be
	  streamed (RA: Track).
	Business question: What are the five newest recordings listeners can stream?
	- CROSSFADE's selling point is that a recording uploaded an hour ago is as
	  recommendable as a hit (RA: Overview), so the newest releases get a shelf.
	- Only scored recordings are streamable (RA: Track), so a newer recording still
	  awaiting scoring, or rejected, must stay off the shelf.
	- Playing time is shown as m:ss (whole minutes by DIV, seconds by MOD); ties on
	  release date go to the lower track_id.
	Requirements: 2.1, (a), (c), (d)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the track table, and only track
	  (a)  "use single row functions": CONCAT, LPAD, MOD (run_time), DATEDIFF
	       (days_since_release)
	  (c)  "sort the results according to some criteria": ORDER BY release_date
	       DESC, track_id
	  (d)  "return just the first N results": LIMIT 5, the five newest
	Output: track_id, title, run_time, release_date, days_since_release
*/
SELECT track_id,
       title,
       CONCAT(duration DIV 60, ':', LPAD(MOD(duration, 60), 2, '0')) AS run_time,
       release_date,
       DATEDIFF('2026-09-30', release_date) AS days_since_release
FROM crossfade.track
WHERE ingest_status = 'scored'
ORDER BY release_date DESC,
         track_id
LIMIT 5;


/*
	[S3] GENRE: blend-composer legend layout
	Use cases: UC-05
	Business need: listeners compose station blends from the genre legend, which
	  shows each genre's label and its description (RA: Genre). The RA sizes both
	  for that display: the ten labels are fixed and "the longest, classical, has
	  nine characters" (RA: Name), and a description is "kept to one line of 80
	  characters" (RA: Description).
	Business question: How wide must the composer's label column be, which genre
	sets that width, and how much of its one 80-character line does each
	description use?
	- The label column must fit the longest label. The scalar subquery finds the
	  longest name in the table and IF marks the genre that sets the width, so the
	  width comes from the data rather than being hard-coded to classical.
	- chars_left_on_line = 80 minus the description's length: the room left on its
	  one line (RA: Description). A genre with no description (the column is
	  optional) shows NULL in both description columns.
	- genre_id is the models' output class index (RA: Genre ID), so ordering by it
	  lists the genres exactly as every probability vector does.
	Requirements: 2.1, (a), (b), (c), (e)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the genre table, and only genre (the subquery reads genre too)
	  (a)  "use single row functions": CHAR_LENGTH (label_chars,
	       description_chars, chars_left_on_line)
	  (b)  "use aggregate functions": MAX, in the subquery that finds the
	       longest label
	  (c)  "sort the results according to some criteria": ORDER BY genre_id,
	       the model's class index
	  (e)  "use a selection control function": IF (label_column)
	Output: model_class_index, label, label_chars, label_column, description_chars, chars_left_on_line
*/
SELECT genre_id AS model_class_index,
       name AS label,
       CHAR_LENGTH(name) AS label_chars,
       IF(CHAR_LENGTH(name) = (SELECT MAX(CHAR_LENGTH(name)) FROM crossfade.genre),
          'sets the column width', 'fits') AS label_column,
       CHAR_LENGTH(description) AS description_chars,
       80 - CHAR_LENGTH(description) AS chars_left_on_line
FROM crossfade.genre
ORDER BY genre_id;


/*
	[S4] LISTENER: subscriber mix by plan tier
	Use cases: UC-06
	Business need: subscribers are billed by plan tier, each from their own signup
	  date (RA: Listener: Plan Tier, Signup Date).
	Business question: How many subscribers does each plan tier have, when did the
	first and latest join, and how long has the average subscriber been billing?
	- Plan tier sets the monthly charge, and the signup date anchors each billing
	  cycle (RA: Plan Tier, Signup Date), so tier size and tenure are the revenue
	  picture.
	- ORDER BY plan_tier DESC sorts by the ENUM's declared order (free < standard <
	  premium), i.e. the most valuable tier first, not alphabetically.
	Requirements: 2.1, (a), (b), (c)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the listener table, and only listener
	  (a)  "use single row functions": ROUND, DATEDIFF (avg_days_subscribed)
	  (b)  "use aggregate functions": COUNT (listeners), MIN (first_signup),
	       MAX (latest_signup), AVG (avg_days_subscribed), per plan_tier
	  (c)  "sort the results according to some criteria": ORDER BY plan_tier
	       DESC
	Output: plan_tier, listeners, first_signup, latest_signup, avg_days_subscribed
*/
SELECT plan_tier,
       COUNT(*) AS listeners,
       MIN(signup_date) AS first_signup,
       MAX(signup_date) AS latest_signup,
       ROUND(AVG(DATEDIFF('2026-09-30', signup_date))) AS avg_days_subscribed
FROM crossfade.listener
GROUP BY plan_tier
ORDER BY plan_tier DESC;


/*
	[S5] SCORING_MODEL: default model for a new station
	Use cases: UC-08
	Business need: each scoring model version is weighted by its measured holdout
	  accuracy, and versions trained on different corpora are never silently
	  compared (RA: Scoring Model).
	Business question: Which model version should a new station default to?
	- A station is evaluated against exactly one model version (RA: Station: Model
	  ID), so a new station needs one default: the version whose output carries the
	  most weight, i.e. the highest holdout accuracy (RA: Holdout Accuracy).
	- The architecture label includes the training corpus, because the RA keeps it
	  so that results from differently trained versions are never silently compared.
	- On equal accuracy the newer deployment wins (deployed_on DESC): it began
	  scoring incoming uploads most recently (RA: Deployed On). If both tie, the
	  lower model_id wins, so LIMIT 1 always picks the same version.
	Requirements: 2.1, (a), (c), (d)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the scoring_model table, and only scoring_model
	  (a)  "use single row functions": CONCAT (architecture), ROUND
	       (accuracy_pct)
	  (c)  "sort the results according to some criteria": ORDER BY
	       holdout_accuracy DESC, deployed_on DESC, model_id
	  (d)  "return just the first N results": LIMIT 1, the one default version
	Output: version_label, architecture, accuracy_pct, deployed_on
*/
SELECT version_label,
       CONCAT(fusion_type, ' / ', embedding_dimension, 'd / ', segment_length, 's / ', training_corpus) AS architecture,
       ROUND(holdout_accuracy * 100, 2) AS accuracy_pct,
       deployed_on
FROM crossfade.scoring_model
ORDER BY holdout_accuracy DESC,
         deployed_on DESC,
         model_id
LIMIT 1;


/*
	[S6] STATION: how stations rely on each model version
	Use cases: UC-10, UC-08
	Business need: every station is evaluated against one nominated model version
	  inside an ambiguity window (RA: Station; Scoring Model 1:N Station), so
	  retiring or redeploying a version changes the stations that rely on it.
	Business question: How many stations does each model version serve, how wide
	are their ambiguity windows, and since when has each version been relied on?
	- A station is evaluated against one nominated model version (RA: Scoring Model
	  1:N Station), so this is the impact of retiring or redeploying a version.
	- The window (maximum - minimum ambiguity) is how adventurous a station is: the
	  RA says raising the minimum excludes single-genre recordings and lowering the
	  maximum excludes ones no model can place. A window wider than 0.50, more than
	  half the 0-1 scale, is counted as wide (a reporting band, not an RA rule).
	- Most-used versions first; model_id breaks ties.
	Requirements: 2.1, (a), (b), (c), (e)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the station table, and only station
	  (a)  "use single row functions": ROUND (avg_window)
	  (b)  "use aggregate functions": COUNT (stations), AVG (avg_window), SUM
	       (wide_stations), MIN (oldest_station), per model_id
	  (c)  "sort the results according to some criteria": ORDER BY stations
	       DESC, model_id
	  (e)  "use a selection control function": CASE, inside SUM, counts the
	       wide stations (wide_stations)
	Output: model_id, stations, avg_window, wide_stations, oldest_station
*/
SELECT model_id,
       COUNT(*) AS stations,
       ROUND(AVG(maximum_ambiguity - minimum_ambiguity), 2) AS avg_window,
       SUM(CASE WHEN maximum_ambiguity - minimum_ambiguity > 0.5 THEN 1 ELSE 0 END) AS wide_stations,
       MIN(created_on) AS oldest_station
FROM crossfade.station
GROUP BY model_id
ORDER BY stations DESC,
         model_id;


/*
	[S7] TRACK: the upload pipeline
	Use cases: UC-04
	Business need: every upload is scored before it can be streamed (RA: Track;
	  its stages: Ingest Status), so a backlog in the upload pipeline must be
	  visible.
	Business question: How many recordings sit at each stage of the upload pipeline,
	and is scoring keeping up with their release dates?
	- Every upload moves through awaiting scoring -> scored or rejected (RA: Ingest
	  Status); ORDER BY ingest_status follows the ENUM's declared order, which is the
	  pipeline order.
	- Release date is when listeners get the recording and may be later than its
	  upload (RA: Release Date), and only scored recordings can be streamed (RA:
	  Track). So the earliest release date in each stage, and the days until it
	  (negative: already passed), show whether scoring keeps ahead of releases.
	- The CASE says what each stage means for those releases: scored is streamable,
	  rejected never will be, and an unscored recording whose release date has
	  arrived is late.
	Requirements: 2.1, (a), (b), (c), (e)  (brief: requirements for single table queries)
	  2.1  "retrieve data from each non-associative table individually":
	       the track table, and only track
	  (a)  "use single row functions": DATEDIFF (days_to_earliest_release)
	  (b)  "use aggregate functions": COUNT (recordings), MIN
	       (earliest_release), per ingest_status
	  (c)  "sort the results according to some criteria": ORDER BY
	       ingest_status, the pipeline order
	  (e)  "use a selection control function": CASE (release_status)
	Output: ingest_status, recordings, earliest_release, days_to_earliest_release, release_status
*/
SELECT ingest_status,
       COUNT(*) AS recordings,
       MIN(release_date) AS earliest_release,
       DATEDIFF(MIN(release_date), '2026-09-30') AS days_to_earliest_release,
       CASE
           WHEN ingest_status = 'scored' THEN 'streamable'
           WHEN ingest_status = 'rejected' THEN 'never streamable: rejected'
           WHEN MIN(release_date) <= '2026-09-30' THEN 'LATE: release date reached, still unscored'
           ELSE 'on time: release date still ahead'
       END AS release_status
FROM crossfade.track
GROUP BY ingest_status
ORDER BY ingest_status;


/*
	[E1] TRACK: a duplicate upload is refused -- DISABLED (commented out)
	>>>>
	Note: We wanted a use case/test that was designed to throw an error.
	This has been tested and performs as designed, but since nothing about a test like this
	was in the requirements. It's left in the deliverable but, commented out.
	>>>>>
	STATUS: the INSERT below sits inside its own block comment, so running this
	file does not execute it and the file finishes without error. It is kept
	because it shows the database itself enforcing a business rule; it is not a
	brief requirement and counts toward none of (a)-(e).
	TO RUN IT: delete the comment-marker lines directly above and below the
	INSERT, then run that statement on its own.
	EXPECTED RESULT: MySQL refuses the statement with
	  Error Code: 1062. Duplicate entry '...' for key 'track.uq_track_audio_checksum'
	and crossfade.track keeps its 15 rows. That error is the correct answer.
	Use cases: UC-15
	Business need: a re-upload of the same audio file must never become a second
	  catalogue entry earning a second royalty stream; the RA keeps the audio
	  checksum (SHA-256 of the file) to "detect duplicate uploads" (RA: Track:
	  Audio Checksum).
	Business question: What happens when an artist uploads an audio file that is
	already in the catalogue?
	- The physical model makes audio_checksum UNIQUE (uq_track_audio_checksum), so
	  the refusal comes from the database, not from application code.
	- The statement re-uploads Low Tide Signal (track 4817) under a new track_id by
	  copying its checksum, exactly what an upload of the same file computes.
	- Error handling (catching 1062 and answering the uploader) is done by
	  upload_track (P2) in routines.sql.
	Expects: 1062 uq_track_audio_checksum
*/
/*
INSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)
SELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', audio_checksum, 'awaiting scoring'
FROM crossfade.track
WHERE track_id = 4817;
*/
