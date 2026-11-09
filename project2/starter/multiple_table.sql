/*
	STARTER KIT: blank slate. The comments are the specification; keep them.
	Write each statement under its comment and end it with ;
	The tests read these lines, so do not change them: the [M#] tag, Use cases,
	Requirements (the Task 3 number, 3.1 to 3.5, it must meet), Tables (exactly the
	tables your query reads), One row per (the columns that identify a result row;
	your ORDER BY must include them) and Output (your column names, in order).
	Business need and Business question say what the business plan needs the query
	for; the bullets under the question say how to meet it.
	Run the tests at any point: unwritten queries are reported by name.
	.
	FILE: multiple_table.sql
	.
	INFO 579 Project 2, Task 3: Multiple-table queries
	CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh)
	.
	***** FYI and project descriptions **********
	One query per question the business can only answer by combining tables. The
	questions are the use cases (UC-xx) drawn from the Project 1 requirements
	analysis that single_table.sql could not answer, or answered only in part:
	royalties owed, listener taste, station sharing, model disagreement, filling
	a station, results to recompute after a model redeployment, and where each
	recording sits between genres. Each of the five brief requirements is met by
	M1 to M5, one each; M6 and M7 meet 3.1 and 3.5 a second time, because their
	questions need that shape.

	BRIEF REQUIREMENTS ADDRESSED (Task 3: "Develop a variety of SQL queries
	following the requirements for multiple table queries"). The brief's wording
	is quoted; "3.n" is Task 3, requirement n. The minimum is one query per
	requirement: M1 to M5 meet it, one requirement each. M6 and M7 go beyond the
	minimum (a second 3.1 and a second 3.5) because their questions need that
	shape.
	  3.1  "Write a query involving an associative table and two other related
	       tables. You must use the INNER JOIN to connect with all three
	       tables": M1 (play, listener, track), M6 (track_score, track,
	       scoring_model)
	  3.2  "Write a query including two or more tables and using the LEFT OUTER
	       JOIN": M2 (artist, track, play)
	  3.3  "Write a query including some kind of set operation": M3 (UNION)
	  3.4  "Write a query including a subquery and some multi-row operation":
	       M4 (IN with a subquery)
	  3.5  "Write a query including a derived table using the WITH statement":
	       M5 (eligible, station_length), M7 (second_place, runner_up)
	  Each query's own comment repeats this: its Requirements field names the
	  requirement it meets, quotes the brief, and shows the SQL that meets it.

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
	Comments: each statement is preceded by a comment with the same fields:
	  [M#] title        tag and a short title
	  Use cases:        the use cases (UC-xx) it answers
	  Business need:    what the business plan (the Project 1 requirements
	                    analysis, RA) needs from this data
	  Business question: the question the query answers, then why it is written
	                    the way it is, citing the RA
	  Requirements:     the brief's requirement it meets (3.1-3.5, see the list
	                    above), on one line; then indented lines quoting the
	                    brief and naming the SQL that meets it
	  Tables:           every table it reads
	  One row per:      the column(s) that identify a result row; the ORDER BY
	                    always includes them, so no two rows can tie
	  Output:           its result columns, in order
	project2/tests/test_multiple_table.py reads these fields and checks each query
	against an independent answer computed from the Project 1 data.

	***** Re: Class notes and syntax *****
	Every join names its type (INNER JOIN, LEFT OUTER JOIN), as the course
	requires; there are no bare JOINs and no comma joins. Tables carry short
	aliases (AS p, AS t) so every column says which table it comes from.
	Course material: INNER JOIN and LEFT OUTER JOIN from Unit 7; UNION,
	subqueries with IN, scalar subqueries, WITH and CASE from Unit 8; DATEDIFF
	(M6, the days between two dates) from Unit 6. IFNULL (M2) is a NULL-handling
	function in the Unit 8 slides.
	Beyond the slides: GROUP_CONCAT (M6), MySQL's aggregate that joins a group's
	values into one string; it only formats the list of versions, so dropping it
	would not affect requirement 3.1.
	Branches: every CASE branch fires on the sample data (M1, M2, M3), and IFNULL in M2
	fires for Kestrel Ave, the artist with no uploads.
*/


/*
	[M1] listener taste profile
	Use cases: UC-13
	Business need: CROSSFADE learns listener taste from what they actually play:
	  how much of each recording they hear, whether they finish it, and whether
	  they save or skip it (RA: Overview, "learning listener taste"; Play).
	Business question: For each listener, how many recordings did they start,
	finish, save and skip, and how much of the audio they started did they hear?
	- Play is the associative entity that resolves Listener M:N Track, and the RA
	  calls it "the record from which listener taste is inferred". It is joined
	  to both of the tables it connects: listener, to name whose taste it is, and
	  track, because the share of audio heard needs each recording's duration.
	- Seconds played carries "how strong a taste signal it carries", completed
	  distinguishes "a genuine listen from an abandoned one", and a reaction is
	  "treated as a stronger signal than duration alone" (RA: Play), so all three
	  are counted. CASE turns completed and reaction into counts.
	- Share of audio heard = total seconds played / total duration of the
	  recordings started, as a percentage: one number for how far a listener
	  stays with what they start.
	- Most engaged listeners first; listener_id breaks ties.
	Requirements: 3.1  (brief: requirements for multiple table queries, item 1)
	  "Write a query involving an associative table and two other related
	  tables. You must use the INNER JOIN to connect with all three tables":
	  play is the associative table (Listener M:N Track); INNER JOIN play to
	  listener and INNER JOIN play to track connect all three
	Tables: play, listener, track
	One row per: listener_id
	Output: listener_id, display_name, plays, completed_plays, saves, skips, pct_of_audio_heard
*/
-- [M1] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;


/*
	[M2] royalty run: what each artist is owed
	Use cases: UC-01, UC-14
	Business need: CROSSFADE pays every artist a per-stream royalty from an exact
	  ledger: each play keeps the royalty it earned when it was recorded, so a
	  later rate change never rewrites what is owed (RA: Overview; Play: Royalty
	  Amount; rule I7).
	Business question: In this royalty run, how much does each artist earn from
	the plays of their recordings, and how many of those plays qualified?
	- The run must list every artist, including one with no uploads or no plays
	  yet, so the statement shows them a zero rather than leaving them out. That
	  is why the joins from artist to track to play are LEFT OUTER JOINs: an
	  INNER JOIN would drop exactly those artists.
	- The amount owed adds up the royalty each play recorded (RA: Royalty Amount,
	  "copied so that a later rate change never rewrites the royalty ledger"),
	  not today's payout rate times a count.
	- A play qualifies when it lasted 30 seconds or more (RA: rule I7); shorter
	  plays are counted as plays but earn nothing.
	- IFNULL turns the empty sum of an artist with no plays into 0.
	- Highest amount first; artist_id breaks ties.
	Requirements: 3.2  (brief: requirements for multiple table queries, item 2)
	  "Write a query including two or more tables and using the LEFT OUTER
	  JOIN": three tables, artist LEFT OUTER JOIN track LEFT OUTER JOIN play,
	  so an artist with no uploads or no plays still gets a row
	Tables: artist, track, play
	One row per: artist_id
	Output: artist_id, payee, plays, qualifying_plays, usd_owed
*/
-- [M2] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;


/*
	[M3] station reach
	Use cases: UC-07
	Business need: stations can be shared, and a shared station appears under its
	  creator's display name (RA: Listener: Display Name; Station: Name; rule I6,
	  "A play's Station ID may refer to a station created by another listener").
	Business question: How many listeners does each station reach, its creator
	included, and which stations have been shared beyond their creator?
	- A listener is reached by a station if they created it or played a
	  recording through it (RA: Play: Station ID). The two lists come from
	  different tables, station and play, so they are combined with UNION.
	- UNION, not UNION ALL: it removes duplicates, so a creator who also plays
	  their own station, or a listener who plays it many times, is counted once.
	  Plays with no station (chosen directly) are not station reach.
	- The station is shown by its name and its creator's display name, as a
	  shared station is (RA: Display Name, "shown by when a station they created
	  is shared").
	- CASE labels a station reaching more than its creator as shared.
	- Widest reach first; station_id breaks ties.
	Requirements: 3.3  (brief: requirements for multiple table queries, item 3)
	  "Write a query including some kind of set operation": UNION of station
	  creators (station) and station players (play), with duplicates removed
	Tables: station, play, listener
	One row per: station_id
	Output: station_id, station, created_by, listeners_reached, reach_status
*/
-- [M3] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;


/*
	[M4] recordings the models disagree on
	Use cases: UC-11
	Business need: CROSSFADE places every recording between genres; each model
	  version returns a distribution with measures of how uncertain and how
	  inconsistent it is, and model divergence records how far one version sits
	  from the others that scored the same recording (RA: Overview; Track Score:
	  Model Divergence).
	Business question: Which recordings do the model versions place in different
	top genres, and how far apart are their distributions?
	- When two versions name different top genres for the same recording, the
	  recording sits between those genres: this is the inconsistency the RA
	  keeps model divergence for, at its plainest.
	- The subquery groups the scoring results by recording and keeps those with
	  more than one distinct top genre; IN, a multi-row operator, then selects
	  those recordings from track. A recording scored by one version only can
	  never qualify.
	- Two correlated subqueries add how many versions scored the recording and
	  the highest divergence among them (RA: Model Divergence).
	- Largest disagreement first; track_id breaks ties.
	Requirements: 3.4  (brief: requirements for multiple table queries, item 4)
	  "Write a query including a subquery and some multi-row operation":
	  an IN test against a subquery over track_score that groups by recording
	  and filters with HAVING; the subquery returns many rows and IN tests
	  each recording against all of them
	Tables: track, track_score
	One row per: track_id
	Output: track_id, title, models_scoring, highest_divergence
*/
-- [M4] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;


/*
	[M5] filling each station
	Use cases: UC-12, UC-10
	Business need: a station stores a genre blend and an ambiguity window, not a
	  fixed list, and the service "returns recordings that genuinely occupy that
	  region" (RA: Overview; Station). Which recordings belong on a station has to
	  be worked out from the business plan's own rules, so the query applies each
	  of them in turn:
	  1. only scored recordings can be streamed (RA: Track);
	  2. a station is evaluated against its one nominated model version, "so that
	     a station's contents do not change meaning when a different version
	     scores the catalogue" (RA: Scoring Model 1:N Station);
	  3. the recording's posterior entropy must lie inside the station's window:
	     the minimum excludes recordings "that sit squarely inside a single
	     genre", the maximum those "the models cannot place with any confidence"
	     (RA: Minimum and Maximum Ambiguity);
	  4. its top genre must be one of the station's blend genres (RA: Station
	     Blend). The RA stores the top genre and the entropy on the scoring
	     result "so that stations can filter without reading ten rows per score"
	     (RA: Track Score), so the filter reads track_score, not the ten
	     genre_probability rows.
	  The RA does not rank qualifying recordings, so the query orders them by the
	  station's own preference: the blend weight of their top genre, highest
	  first (RA: Weight, "the share of the station's blend given to this genre"),
	  then the higher posterior entropy, the recording further between genres,
	  which is the service's selling point; track_id breaks ties.
	Business question: For each station, which recordings qualify under its
	model, window and blend, in what order, and how long would the station run?
	- WITH defines two derived tables: eligible applies rules 1 to 4, and
	  station_length totals each station's qualifying recordings and running
	  time in minutes (RA: Duration, "to estimate station running time").
	- The final SELECT joins the two, so every recording carries its station's
	  totals.
	Requirements: 3.5  (brief: requirements for multiple table queries, item 5)
	  "Write a query including a derived table using the WITH statement":
	  WITH defines two derived tables, eligible and station_length, and the
	  final SELECT joins them
	Tables: station, track_score, track, station_blend, genre
	One row per: station_id, track_id
	Output: station_id, station, track_id, title, top_genre, genre_weight, posterior_entropy, station_recordings, station_run_minutes
*/
-- [M5] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;


/*
	[M6] results to recompute
	Use cases: UC-09
	Business need: several model versions are in service at once, and newer
	  versions are deployed over time (RA: Scoring Model: the date a version
	  "was placed in service and began scoring incoming uploads"). The RA gives
	  Scored On one use: "to establish which results predate a model
	  redeployment and must be recomputed" (RA: Track Score: Scored On).
	Business question: Which released recordings have not been scored since the
	newest model version was deployed, and how far out of date is their newest
	result?
	- Track Score is the associative entity that resolves Track M:N Scoring
	  Model. It is joined to both: track, for the title and the release status
	  (a rejected recording is never rescored), and scoring_model, to name the
	  versions that did score the recording.
	- Several versions are in service at once (RA: Scoring Model), so "out of
	  date" is measured against the newest one, the version deployed last. A
	  recording needs rescoring when its newest result was scored before that
	  deployment; a recording scored at or after it is up to date, whichever
	  version scored it, so its older results do not count. A scalar subquery
	  finds the latest deployment date; HAVING compares the newest result with it.
	- GROUP_CONCAT lists the versions that scored the recording, oldest first.
	  DATEDIFF gives how many days the newest result predates the deployment.
	- Most out of date first; track_id breaks ties.
	Requirements: 3.1  (brief: requirements for multiple table queries, item 1)
	  "Write a query involving an associative table and two other related
	  tables. You must use the INNER JOIN to connect with all three tables":
	  track_score is the associative table (Track M:N Scoring Model); INNER
	  JOIN track_score to track and INNER JOIN track_score to scoring_model
	  connect all three
	Tables: track_score, track, scoring_model
	One row per: track_id
	Output: track_id, title, results, scored_by, last_scored_on, days_out_of_date
*/
-- [M6] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;


/*
	[M7] where each recording sits between genres
	Use cases: UC-11
	Business need: the catalogue "is indexed by where a recording sits between
	  genres rather than by a single genre label" (RA: Overview). Genre
	  Probability "holds the full distribution that stations match against,
	  which the single top genre on Track Score cannot express" (RA: Genre
	  Probability), so placing a recording between genres means reading past
	  its top genre to the genre it sits closest to next.
	Business question: For each scoring result, which genre is the runner-up to
	the top genre, how close is it, and does the recording change character
	partway through?
	- WITH defines two derived tables. second_place finds, for each result, the
	  highest probability among the genres other than its top genre. runner_up
	  finds the genre holding that probability; if two genres share it, the
	  lower genre_id is taken, so each result has exactly one runner-up.
	- Margin = top probability (RA: Top Probability, "how confident that single
	  placement is") minus the runner-up's probability: the smaller the margin,
	  the more truly the recording sits between the two genres. A margin of 0
	  means the model could not separate them.
	- Segment variance (RA: Segment Variance) "identifies tracks that change
	  character partway through", the other way a recording can sit between
	  genres.
	- Smallest margin first; track_id, then model_id, break ties.
	Requirements: 3.5  (brief: requirements for multiple table queries, item 5)
	  "Write a query including a derived table using the WITH statement":
	  WITH defines two derived tables, second_place and runner_up (runner_up
	  reads second_place), and the final SELECT joins runner_up
	Tables: genre_probability, track_score, track, genre
	One row per: track_id, model_id
	Output: track_id, title, model_id, top_genre, top_probability, runner_up_genre, runner_up_probability, margin, segment_variance
*/
-- [M7] write one SELECT (or WITH ... SELECT) that reads exactly the Tables listed, meets its Requirement and returns the Output columns in order; end it with ;
