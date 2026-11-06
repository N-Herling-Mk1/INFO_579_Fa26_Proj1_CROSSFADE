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
	EXPECTED TO FAIL: the last statement, [E1], is a write the database must
	refuse (UC-15, duplicate upload). Running this file ends with that error, by
	design; every query above it has already run. See the [E1] comment.

	***** Re: Class notes and syntax *****
	Brief requirements (Task 2), and where each is met:
	  (a) single-row functions ........ S1 S2 S3 S4 S5 S6 S7
	  (b) aggregate functions ......... S4 S6 S7
	  (c) sorting ..................... S1 S2 S3 S4 S5 S6 S7
	  (d) first N results ............. S2 S5
	  (e) selection control (CASE, IF)  S1 S3 S6 S7
	"Selection control" follows the Unit 8 slides: CASE and IF. IFNULL is used too,
	but the slides class it as a NULL-handling function, so it is listed apart
	([IFNULL: NULL handling]) and never counted as (a) or (e). Arithmetic uses the
	Unit 6 operators (DIV, MOD).
*/


/*
	[S1] ARTIST: royalty payment run
	Use cases: UC-02, UC-01
	Business need: CROSSFADE pays independent artists a per-stream royalty, and pays
	  only verified artists through a channel chosen by their country (RA: Overview;
	  Artist: Payout Rate, Country, Verified).
	Business question: Who can be paid in this royalty run, who is on hold and why,
	and what does each artist earn per 1,000 qualifying streams?
	- Payments go out through a channel chosen by the artist's country, and only to
	  artists whose identity and licence rights are verified (RA: Country, Verified).
	  An artist failing either check is held; the CASE names the reason.
	- Payout is quoted per 1,000 streams, the figure artists compare, from the
	  per-stream payout_rate. Days under licence counts from joined_date, the day
	  the artist's licence took effect (RA: Joined Date).
	- Payable artists first, then by rate, highest first; artist_id breaks ties.
	Requirements: (a) CONCAT, ROUND, DATEDIFF  (c) ORDER BY  (e) CASE  [IFNULL: NULL handling]
	Output: artist_id, payee, usd_per_1000_streams, days_under_licence, payment_status
*/
SELECT artist_id,
       CONCAT(stage_name, ' (', IFNULL(country, '--'), ')') AS payee,
       ROUND(payout_rate * 1000, 2) AS usd_per_1000_streams,
       DATEDIFF('2026-09-30', joined_date) AS days_under_licence,
       CASE
           WHEN verified = 0 THEN 'HOLD: identity not verified'
           WHEN country IS NULL THEN 'HOLD: no payment country'
           ELSE 'PAYABLE'
       END AS payment_status
FROM crossfade.artist
ORDER BY CASE WHEN verified = 1 AND country IS NOT NULL THEN 0 ELSE 1 END,
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
	Requirements: (a) CONCAT, LPAD, MOD, DATEDIFF  (c) ORDER BY  (d) LIMIT
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
	[S3] GENRE: the blend-composer legend
	Use cases: UC-05
	Business need: listeners compose station blends from the genre legend, which
	  shows them each genre's description (RA: Genre).
	Business question: Is every genre ready to show in the blend composer, listed in
	the order the scoring models output them?
	- Listeners compose a station blend from this legend, and the RA says each
	  genre's description is shown to them while they do; description is the one
	  optional column, so a genre without one must be flagged before it reaches
	  the composer.
	- The legend line is the label followed by its description, as the composer
	  shows a genre; labels keep the form listeners know them by (RA: Name, e.g.
	  "jazz, metal or reggae").
	- genre_id is the models' output class index (RA: Genre ID), so ordering by it
	  lists the genres exactly as every probability vector does.
	Requirements: (a) CONCAT  (c) ORDER BY  (e) IF  [IFNULL: NULL handling]
	Output: model_class_index, label, legend_line, composer_status
*/
SELECT genre_id AS model_class_index,
       name AS label,
       CONCAT(name, ': ', IFNULL(description, '(no description)')) AS legend_line,
       IF(description IS NULL, 'HIDE: no description for the composer', 'READY') AS composer_status
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
	Requirements: (a) ROUND, DATEDIFF  (b) COUNT, MIN, MAX, AVG  (c) ORDER BY
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
	  scoring incoming uploads most recently (RA: Deployed On).
	Requirements: (a) CONCAT, ROUND  (c) ORDER BY  (d) LIMIT
	Output: version_label, architecture, accuracy_pct, deployed_on
*/
SELECT version_label,
       CONCAT(fusion_type, ' / ', embedding_dimension, 'd / ', segment_length, 's / ', training_corpus) AS architecture,
       ROUND(holdout_accuracy * 100, 2) AS accuracy_pct,
       deployed_on
FROM crossfade.scoring_model
ORDER BY holdout_accuracy DESC,
         deployed_on DESC
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
	Requirements: (a) ROUND  (b) COUNT, AVG, SUM, MIN  (c) ORDER BY  (e) CASE
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
	Business need: every upload is scored before it can be streamed (RA: Track:
	  Ingest Status), so a backlog in the upload pipeline must be visible.
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
	[E1] TRACK: a duplicate upload is refused -- EXPECTED TO FAIL
	EXPECTED RESULT: MySQL refuses this statement with
	  Error Code: 1062. Duplicate entry '...' for key 'track.uq_track_audio_checksum'
	and crossfade.track keeps its 15 rows. That error is the correct answer. This
	is the last statement in the file because an error stops a script run; every
	query above has already run. Not a retrieval query, so it counts toward none
	of (a)-(e); it shows the database itself enforcing a business rule.
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
	- Error handling (catching 1062 and answering the uploader) belongs to
	  routines.sql: see the plan in project2/README.md.
	Expects: 1062 uq_track_audio_checksum
*/
INSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)
SELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', audio_checksum, 'awaiting scoring'
FROM crossfade.track
WHERE track_id = 4817;
