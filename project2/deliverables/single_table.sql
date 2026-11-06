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
	Tags: each comment starts with a tag ([S1] to [S7]) and lists its use cases and
	the brief's requirements it meets; project2/tests/test_single_table.py reads
	them and checks each query against an independent answer computed from the
	Project 1 data.

	***** Re: Class notes and syntax *****
	Brief requirements (Task 2), and where each is met:
	  (a) single-row functions ........ S1 S2 S3 S4 S5 S6 S7
	  (b) aggregate functions ......... S4 S6 S7
	  (c) sorting ..................... S1 S2 S3 S4 S5 S6 S7
	  (d) first N results ............. S2 S5
	  (e) selection control (CASE, IF)  S1 S3 S6 S7
	"Selection control" follows the Unit 8 slides: CASE and IF. IFNULL is used too,
	but the slides class it as a NULL-handling function, so it is never the only
	selection control in a query.
*/


/*
	[S1] ARTIST: royalty payment run
	Use cases: UC-02, UC-01
	Business question: Who can be paid in this royalty run, who is on hold and why,
	and what does each artist earn per 1,000 qualifying streams?
	- Payments go out through a channel chosen by the artist's country, and only to
	  artists whose identity and licence rights are verified (RA: Country, Verified).
	  An artist failing either check is held; the CASE names the reason.
	- Payout is quoted per 1,000 streams, the figure artists compare, from the
	  per-stream payout_rate. Days under licence counts from joined_date.
	- Payable artists first, then by rate, highest first; artist_id breaks ties.
	Requirements: (a) CONCAT, IFNULL, ROUND, DATEDIFF  (c) ORDER BY  (e) CASE
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
	Business question: What are the five newest recordings listeners can stream?
	- CROSSFADE's selling point is that a recording uploaded an hour ago is as
	  recommendable as a hit (RA: Overview), so the newest releases get a shelf.
	- Only scored recordings are streamable (RA: Track), so a newer recording still
	  awaiting scoring, or rejected, must stay off the shelf.
	- Playing time is shown as m:ss; ties on release date go to the lower track_id.
	Requirements: (a) CONCAT, FLOOR, LPAD, MOD, DATEDIFF  (c) ORDER BY  (d) LIMIT
*/
SELECT track_id,
       title,
       CONCAT(FLOOR(duration / 60), ':', LPAD(MOD(duration, 60), 2, '0')) AS run_time,
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
	Business question: Is every genre ready to show in the blend composer, listed in
	the order the scoring models output them?
	- Listeners compose a station blend from this legend, and the RA says each
	  genre's description is shown to them while they do; description is the one
	  optional column, so a genre without one must be flagged before it reaches
	  the composer.
	- genre_id is the models' output class index (RA: Genre ID), so ordering by it
	  lists the genres exactly as every probability vector does.
	Requirements: (a) UPPER, IFNULL  (c) ORDER BY  (e) IF
*/
SELECT genre_id AS model_class_index,
       UPPER(name) AS label,
       IFNULL(description, '(no description)') AS legend_text,
       IF(description IS NULL, 'HIDE: no description for the composer', 'READY') AS composer_status
FROM crossfade.genre
ORDER BY genre_id;


/*
	[S4] LISTENER: subscriber mix by plan tier
	Use cases: UC-06
	Business question: How many subscribers does each plan tier have, when did the
	first and latest join, and how long has the average subscriber been billing?
	- Plan tier sets the monthly charge, and the signup date anchors each billing
	  cycle (RA: Plan Tier, Signup Date), so tier size and tenure are the revenue
	  picture.
	- ORDER BY plan_tier DESC sorts by the ENUM's declared order (free < standard <
	  premium), i.e. the most valuable tier first, not alphabetically.
	Requirements: (a) ROUND, DATEDIFF  (b) COUNT, MIN, MAX, AVG  (c) ORDER BY
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
	Business question: Which three model versions should a new station default to?
	- Holdout accuracy decides how much weight a version's output carries (RA:
	  Holdout Accuracy), so the most accurate versions are the candidates.
	- The architecture label includes the training corpus, because the RA keeps it
	  so that results from differently trained versions are never silently compared.
	- Two versions tie at 0.7600; deployed_on DESC prefers the newer of them.
	Requirements: (a) CONCAT, ROUND  (c) ORDER BY  (d) LIMIT
*/
SELECT version_label,
       CONCAT(fusion_type, ' / ', embedding_dimension, 'd / ', segment_length, 's / ', training_corpus) AS architecture,
       ROUND(holdout_accuracy * 100, 2) AS accuracy_pct,
       deployed_on
FROM crossfade.scoring_model
ORDER BY holdout_accuracy DESC,
         deployed_on DESC
LIMIT 3;


/*
	[S6] STATION: how stations rely on each model version
	Use cases: UC-10, UC-08
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
	Business question: How many recordings sit at each stage of the upload pipeline,
	and how long since the newest one reached each stage?
	- Every upload moves through awaiting scoring -> scored or rejected (RA: Ingest
	  Status); a growing "awaiting scoring" count means scoring is falling behind.
	- ORDER BY ingest_status follows the ENUM's declared order, which is the
	  pipeline order.
	- The IF states what each stage means to a listener: only scored recordings
	  are streamable (RA: Track).
	Requirements: (a) DATEDIFF  (b) COUNT, MAX  (c) ORDER BY  (e) IF
*/
SELECT ingest_status,
       COUNT(*) AS recordings,
       MAX(release_date) AS newest_release,
       DATEDIFF('2026-09-30', MAX(release_date)) AS days_since_newest,
       IF(ingest_status = 'scored', 'streamable', 'not streamable') AS listener_visibility
FROM crossfade.track
GROUP BY ingest_status
ORDER BY ingest_status;
