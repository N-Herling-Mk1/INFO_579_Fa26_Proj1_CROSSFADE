/*
	FILE: routines.sql
	.
	INFO 579 Project 2, Task 4: Routines
	CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh)
	.
	***** FYI and project descriptions **********
	Three routines: one function and two procedures. They are the write path the
	Project 1 requirements analysis (RA) gives the business for its two everyday
	events, a listener playing a recording and an artist uploading one:
	  F1 play_royalty   what one play earns the artist (RA rule I7)
	  P1 record_play    records a play, computing what the RA forbids the caller to
	                    supply (completed, royalty_amount), and refuses an invalid
	                    play with SIGNAL
	  P2 upload_track   adds an upload to the catalogue, and answers a duplicate
	                    upload with a message instead of an error, using a HANDLER
	                    for MySQL error 1062
	The RA: "the procedures do not accept derived values as input" (Integrity rules).

	***** How to Run *********
	Run database_implementation.sql first, then this whole script. It drops and
	re-creates the three routines, so it can be run again at any time. The "Try it"
	block at the end calls each routine inside a transaction and rolls it back, so
	the sample data is left exactly as it was.

	***** NERD STUFF *********
	Comments: each routine is preceded by a comment with the same fields:
	  [F#] / [P#] name  tag (F = function, P = procedure) and the routine's name
	  Use cases:        the use cases (UC-xx) it serves
	  Business need:    what the business plan (the RA) needs it for
	  What it does:     the steps, and why each is there, citing the RA
	  Requirements:     4 function or 4 procedure (the brief: 2 procedures and 1
	                    function, or 1 procedure and 2 functions)
	  Uses:             the routine features it uses (Class notes below says which
	                    come from Unit 9 and which go beyond the slides)
	  Tables:           every table it reads or writes
	  Parameters:       its parameters in order: [IN|OUT] name type
	  Returns:          the return type (functions only)
	  Errors:           what it refuses, and how
	  Example:          one call to the routine, with its result
	project2/tests/test_routines.py reads these fields, checks each routine against
	MySQL's own catalogue (information_schema), and runs it against an independent
	answer computed from the Project 1 data.
	No routine starts or ends a transaction itself: each makes exactly one write
	(one INSERT), which MySQL already applies whole or not at all, so the caller
	keeps control of the transaction (the tests roll every call back).

	***** Re: Class notes and syntax *****
	Course material: Unit 9: DELIMITER $$ lets each routine body contain ; without ending the
	CREATE statement. DECLARE (local variables and a handler), IF ... ELSEIF ...
	ELSE, SIGNAL SQLSTATE '45000' (a user-defined error), DECLARE EXIT HANDLER
	FOR 1062 (catch MySQL's duplicate-key error by its error code), IN / OUT
	parameters, and READS SQL DATA for a function that reads tables. Unit 10:
	START TRANSACTION and ROLLBACK (the "Try it" block).
	Beyond the slides: RESIGNAL (P2 re-raises a key clash that is not a
	duplicate file); NOT DETERMINISTIC (F1; the slides show DETERMINISTIC, and NOT
	DETERMINISTIC is MySQL's default, stated because the payout rate F1 reads can
	change); MODIFIES SQL DATA (P1, P2); UTC_TIMESTAMP() (P1, the RA's UTC play
	time); UNHEX(SHA2(...)) (P2's example call, to make a 32-byte checksum).
	Branches: the "Try it" block reaches F1's 29- and 30-second branches, P1's
	insert and P2's upload and duplicate paths. The guard branches, which refuse
	bad input, are reached only by the tests: F1's NULL for an unknown recording,
	P1's three SIGNALs, P2's unregistered-artist SIGNAL and its RESIGNAL for a
	key clash that is not a duplicate file.
*/
DELIMITER $$


/*
	[F1] play_royalty
	Use cases: UC-01, UC-14
	Business need: CROSSFADE pays each artist "a per stream royalty on plays of
	  those recordings" (RA: Artist), and the royalty ledger must be exact (RA:
	  Play). The payout rule lives in one place so every caller applies it the same
	  way: record_play (P1) when a play is recorded, and finance when it previews
	  what a play would earn.
	What it does:
	- Looks up the payout rate of the artist who owns the recording: "the amount
	  in United States dollars the artist is paid for a single qualifying stream"
	  (RA: Artist.payout_rate).
	- Applies rule I7: "Royalty Amount equals the artist's Payout Rate for a play
	  of 30 seconds or more and zero otherwise." 30 seconds exactly qualifies.
	- Returns NULL, not 0, when the recording does not exist: there is no rate to
	  apply, and 0 would read as "a short play" (P1 refuses such a play first).
	- NOT DETERMINISTIC: the same arguments can give a different answer after the
	  artist's rate changes, which is why P1 stores the result (a snapshot).
	Requirements: 4 function
	Uses: DECLARE, IF ... ELSEIF ... ELSE, READS SQL DATA, NOT DETERMINISTIC
	Tables: track, artist
	Parameters: IN input_track_id INT UNSIGNED, IN input_seconds_played SMALLINT UNSIGNED
	Returns: DECIMAL(5,5)
	Errors: none; NULL for a recording that does not exist or a missing length
	Example: SELECT crossfade.play_royalty(4817, 30);   -- 0.00400 (Velvet Static's rate)
*/
DROP FUNCTION IF EXISTS crossfade.play_royalty$$
CREATE FUNCTION crossfade.play_royalty (
	input_track_id INT UNSIGNED,
	input_seconds_played SMALLINT UNSIGNED)
	RETURNS DECIMAL(5,5)
	NOT DETERMINISTIC
	READS SQL DATA
BEGIN
	DECLARE artist_rate DECIMAL(5,5);

	-- The rate of the artist who owns the recording; NULL if there is no such recording.
	SET artist_rate = (SELECT a.payout_rate
					   FROM crossfade.track AS t
					   INNER JOIN crossfade.artist AS a ON a.artist_id = t.artist_id
					   WHERE t.track_id = input_track_id);

	IF artist_rate IS NULL OR input_seconds_played IS NULL THEN
		RETURN NULL;
	ELSEIF input_seconds_played >= 30 THEN
		RETURN artist_rate;
	ELSE
		RETURN 0;
	END IF;
END$$


/*
	[P1] record_play
	Use cases: UC-14, UC-13, UC-01, UC-07, UC-04
	Business need: Every play is both the taste signal (RA: Play, "the record from
	  which listener taste is inferred") and the billable event the royalty is paid
	  on. Rule I7: "The procedure that records a play computes both [Completed and
	  Royalty Amount] from the Track and Artist rows rather than accepting them as
	  input", and "Royalty Amount is computed once, when the play is recorded, and
	  never updated." This is that procedure.
	What it does:
	- Refuses, with SIGNAL SQLSTATE '45000' and a message naming the problem, a
	  play of a recording that does not exist, of one not released for streaming
	  (ingest status other than 'scored'; RA: a recording has no score "while it
	  is awaiting scoring, at least one before it is released"), or a play longer
	  than the recording.
	- Computes completed: true "exactly when Seconds Played equals the Duration of
	  the recording" (RA: Play.completed).
	- Computes royalty_amount with play_royalty (F1): the artist's rate as it
	  stands now, stored as a snapshot "so that a later rate change never rewrites
	  the royalty ledger" (RA: Play.royalty_amount).
	- Records the play at the UTC time given, or now in UTC when none is given:
	  "Played At is recorded in UTC" (RA: key of Play).
	- Does not catch the database's own refusals: a second report of the same play
	  (same listener, recording and start time) is rejected by the primary key,
	  "which is what keeps a double-counted royalty out of the ledger" (RA), and
	  an unknown listener or station by its foreign key. The station may belong to
	  another listener (rule I6: stations can be shared).
	- Hands completed and royalty_amount back through OUT parameters.
	Requirements: 4 procedure
	Uses: DECLARE, IF ... ELSEIF, SIGNAL SQLSTATE '45000', IN / OUT parameters, calls F1, MODIFIES SQL DATA
	Tables: track, artist, play
	Parameters: IN input_listener_id INT UNSIGNED, IN input_track_id INT UNSIGNED, IN input_station_id INT UNSIGNED, IN input_seconds_played SMALLINT UNSIGNED, IN input_reaction VARCHAR(7), IN input_played_at DATETIME, OUT output_completed TINYINT, OUT output_royalty_amount DECIMAL(5,5)
	Errors: SIGNAL 45000 for a recording that does not exist, is not released, or is shorter than the seconds played; MySQL refuses a repeated play (1062) and an unknown listener or station (1452)
	Example: CALL crossfade.record_play(20937, 4817, NULL, 107, 'skipped', '2026-11-01 20:15:00', @completed, @royalty);
*/
DROP PROCEDURE IF EXISTS crossfade.record_play$$
CREATE PROCEDURE crossfade.record_play (
	IN input_listener_id INT UNSIGNED,
	IN input_track_id INT UNSIGNED,
	IN input_station_id INT UNSIGNED,
	IN input_seconds_played SMALLINT UNSIGNED,
	IN input_reaction VARCHAR(7),
	IN input_played_at DATETIME,
	OUT output_completed TINYINT,
	OUT output_royalty_amount DECIMAL(5,5))
	MODIFIES SQL DATA
BEGIN
	DECLARE track_duration SMALLINT UNSIGNED;
	DECLARE track_status VARCHAR(16);
	DECLARE error_message VARCHAR(128);

	-- The recording's length and upload stage; both NULL if there is no such recording.
	SET track_duration = (SELECT duration FROM crossfade.track WHERE track_id = input_track_id);
	SET track_status = (SELECT ingest_status FROM crossfade.track WHERE track_id = input_track_id);

	IF track_duration IS NULL THEN
		SET error_message = CONCAT('record_play: track ', input_track_id, ' does not exist');
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
	ELSEIF track_status <> 'scored' THEN
		SET error_message = CONCAT('record_play: track ', input_track_id, ' is not released for streaming (', track_status, ')');
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
	ELSEIF input_seconds_played > track_duration THEN
		SET error_message = CONCAT('record_play: ', input_seconds_played, ' seconds played, but track ', input_track_id,
								   ' is only ', track_duration, ' seconds long');
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
	END IF;

	-- Rule I7: both values are derived here, never taken from the caller.
	SET output_completed = (input_seconds_played = track_duration);
	SET output_royalty_amount = crossfade.play_royalty(input_track_id, input_seconds_played);

	INSERT INTO crossfade.play (listener_id, track_id, played_at, station_id, seconds_played,
								completed, reaction, royalty_amount)
	VALUES (input_listener_id, input_track_id, IFNULL(input_played_at, UTC_TIMESTAMP()), input_station_id,
			input_seconds_played, output_completed, input_reaction, output_royalty_amount);
END$$


/*
	[P2] upload_track
	Use cases: UC-15, UC-04
	Business need: Artists upload recordings "under a direct streaming licence"
	  (RA: Artist), and the audio checksum is "used to detect duplicate uploads"
	  (RA: Track.audio_checksum). A duplicate upload is an everyday event, not a
	  failure: the artist should be told which recording is already in the
	  catalogue, and a batch of uploads should carry on. [E1] in single_table.sql
	  (kept disabled there) shows the raw refusal (error 1062); this procedure is
	  the business answering it.
	What it does:
	- Refuses, with SIGNAL SQLSTATE '45000', an upload from an artist who is not
	  registered.
	- Gives the recording the next track ID and inserts it with ingest status
	  'awaiting scoring', the first stage of the upload pipeline (RA: a recording
	  has no score "while it is awaiting scoring"); scoring moves it on (rule I5).
	  The release date may be later than the upload (RA: Track.release_date).
	- Lets the UNIQUE index on audio_checksum detect the duplicate, rather than
	  looking first: a look-then-insert leaves a gap in which a second upload of
	  the same file could slip in, and the index has no gap.
	- DECLARE EXIT HANDLER FOR 1062 catches that duplicate: nothing is inserted,
	  and the OUT parameters name the recording already in the catalogue, with
	  status 'duplicate'. If the 1062 came from the primary key instead (two
	  uploads took the same new ID at the same moment), there is no recording with
	  this checksum, and the handler re-raises the error (RESIGNAL) rather than
	  report a duplicate that is not one.
	- Every other refusal (a length of 0 seconds, a missing title) is the
	  database's own, and is not caught.
	Requirements: 4 procedure
	Uses: DECLARE, DECLARE EXIT HANDLER FOR 1062, RESIGNAL, IF, SIGNAL SQLSTATE '45000', IN / OUT parameters, MODIFIES SQL DATA
	Tables: artist, track
	Parameters: IN input_artist_id MEDIUMINT UNSIGNED, IN input_title VARCHAR(128), IN input_duration SMALLINT UNSIGNED, IN input_release_date DATE, IN input_audio_checksum BINARY(32), OUT output_track_id INT UNSIGNED, OUT output_status VARCHAR(9), OUT output_message VARCHAR(128)
	Errors: SIGNAL 45000 for an unregistered artist; a duplicate upload is not an error (status 'duplicate'); the database refuses an invalid length or title (3819, 1048)
	Example: CALL crossfade.upload_track(1049, 'First Light', 201, '2026-12-01', UNHEX(SHA2('first light', 256)), @id, @status, @message);
*/
DROP PROCEDURE IF EXISTS crossfade.upload_track$$
CREATE PROCEDURE crossfade.upload_track (
	IN input_artist_id MEDIUMINT UNSIGNED,
	IN input_title VARCHAR(128),
	IN input_duration SMALLINT UNSIGNED,
	IN input_release_date DATE,
	IN input_audio_checksum BINARY(32),
	OUT output_track_id INT UNSIGNED,
	OUT output_status VARCHAR(9),
	OUT output_message VARCHAR(128))
	MODIFIES SQL DATA
BEGIN
	DECLARE error_message VARCHAR(128);

	-- A duplicate upload is answered, not raised: name the recording already in the catalogue.
	DECLARE EXIT HANDLER FOR 1062
	BEGIN
		SET output_track_id = (SELECT track_id FROM crossfade.track WHERE audio_checksum = input_audio_checksum);
		IF output_track_id IS NULL THEN
			RESIGNAL;      -- the duplicate key was the new track ID, not the audio file
		END IF;
		SET output_status = 'duplicate';
		SET output_message = CONCAT('already in the catalogue as track ', output_track_id, ' (',
									(SELECT title FROM crossfade.track WHERE track_id = output_track_id), ')');
	END;

	IF (SELECT COUNT(*) FROM crossfade.artist WHERE artist_id = input_artist_id) = 0 THEN
		SET error_message = CONCAT('upload_track: artist ', input_artist_id, ' is not registered');
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
	END IF;

	SET output_track_id = (SELECT IFNULL(MAX(track_id), 0) + 1 FROM crossfade.track);
	INSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)
	VALUES (output_track_id, input_artist_id, input_title, input_duration, input_release_date,
			input_audio_checksum, 'awaiting scoring');

	SET output_status = 'uploaded';
	SET output_message = CONCAT('uploaded as track ', output_track_id, ', awaiting scoring');
END$$

DELIMITER ;


/*
	Try it: each routine called once, inside a transaction that is rolled back, so
	the sample data is unchanged. (A call that SIGNALs stops a script, so those are
	left to the tests: project2/tests/test_routines.py.)
*/
START TRANSACTION;

-- F1: a 29-second play earns nothing; 30 seconds earns Velvet Static's rate.
SELECT crossfade.play_royalty(4817, 29) AS royalty_29_seconds,
       crossfade.play_royalty(4817, 30) AS royalty_30_seconds;

-- P1: dokafor skips Low Tide after 107 of its 214 seconds.
CALL crossfade.record_play(20937, 4817, NULL, 107, 'skipped', '2026-11-01 20:15:00', @completed, @royalty);
SELECT @completed AS completed, @royalty AS royalty_amount;

-- P2: Velvet Static uploads Low Tide's audio again (same checksum as track 4817).
CALL crossfade.upload_track(1042, 'Low Tide (again)', 214, '2026-11-01',
	(SELECT audio_checksum FROM crossfade.track WHERE track_id = 4817), @track_id, @status, @message);
SELECT @track_id AS track_id, @status AS status, @message AS message;

-- P2: Kestrel Ave uploads a new recording.
CALL crossfade.upload_track(1049, 'First Light', 201, '2026-12-01', UNHEX(SHA2('first light', 256)),
	@track_id, @status, @message);
SELECT @track_id AS track_id, @status AS status, @message AS message;

ROLLBACK;
