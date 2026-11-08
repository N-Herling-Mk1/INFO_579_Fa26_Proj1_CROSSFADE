/*
	STARTER KIT: blank slate. The comments are the specification; keep them.
	Write each statement under its comment and end it with ;
	The tests read these lines, so do not change them: the [S#] or [E#] tag and the
	table word after it, Use cases, Requirements, Output (your column names, in
	order) and Expects. Business need and Business question say what the business
	plan needs the query for; the bullets under the question say how to meet it.
	Run the tests at any point: unwritten queries are reported by name.
	.
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
	  Requirements:     the brief's requirements (a)-(e) it meets
	  Output:           its result columns, in order
	project2/tests/test_single_table.py reads these fields and checks each query
	against an independent answer computed from the Project 1 data.
	DISABLED CHECK: the last statement, [E1], is a write the database must refuse
	(UC-15, duplicate upload). It is commented out, so this file runs without
	error; it is not a brief requirement. The [E1] comment says how to run it.

	***** Re: Class notes and syntax *****
	Brief requirements (Task 2), and where each is met:
	  (a) single-row functions ........ S1 S2 S3 S4 S5 S6 S7
	  (b) aggregate functions ......... S3 S4 S6 S7
	  (c) sorting ..................... S1 S2 S3 S4 S5 S6 S7
	  (d) first N results ............. S2 S5
	  (e) selection control (CASE, IF)  S1 S3 S6 S7
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
	Requirements: (a) ROUND, DATEDIFF  (c) ORDER BY  (e) IF, CASE
	Output: artist_id, stage_name, usd_per_1000_streams, days_under_licence, licence_check, payment_country, run_status
*/
-- [S1] write one SELECT that reads crossfade.artist only, with the Output columns in order; end it with ;


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
	Requirements: (a) CONCAT, LPAD, MOD, DATEDIFF  (c) ORDER BY  (d) LIMIT
	Output: track_id, title, run_time, release_date, days_since_release
*/
-- [S2] write one SELECT that reads crossfade.track only, with the Output columns in order; end it with ;


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
	Requirements: (a) CHAR_LENGTH  (b) MAX  (c) ORDER BY  (e) IF
	Output: model_class_index, label, label_chars, label_column, description_chars, chars_left_on_line
*/
-- [S3] write one SELECT that reads crossfade.genre only, with the Output columns in order; end it with ;


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
	Requirements: (a) ROUND, DATEDIFF  (b) COUNT, MIN, MAX, AVG  (c) ORDER BY
	Output: plan_tier, listeners, first_signup, latest_signup, avg_days_subscribed
*/
-- [S4] write one SELECT that reads crossfade.listener only, with the Output columns in order; end it with ;


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
	Requirements: (a) CONCAT, ROUND  (c) ORDER BY  (d) LIMIT
	Output: version_label, architecture, accuracy_pct, deployed_on
*/
-- [S5] write one SELECT that reads crossfade.scoring_model only, with the Output columns in order; end it with ;


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
	Requirements: (a) ROUND  (b) COUNT, AVG, SUM, MIN  (c) ORDER BY  (e) CASE
	Output: model_id, stations, avg_window, wide_stations, oldest_station
*/
-- [S6] write one SELECT that reads crossfade.station only, with the Output columns in order; end it with ;


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
	Requirements: (a) DATEDIFF  (b) COUNT, MIN  (c) ORDER BY  (e) CASE
	Output: ingest_status, recordings, earliest_release, days_to_earliest_release, release_status
*/
-- [S7] write one SELECT that reads crossfade.track only, with the Output columns in order; end it with ;


/*
	[E1] TRACK: a duplicate upload is refused -- DISABLED (commented out)
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
-- [E1] write the statement on crossfade.track that MySQL must refuse (see Expects) here, inside this block comment, ending it with a semicolon; keep both comment markers
*/
