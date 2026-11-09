/*
	FILE: routines_example_usage.sql
	.
	INFO 579 Project 2, Task 4: example usage of routines.sql
	CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh)
	.
	***** FYI and project descriptions **********
	EXAMPLE USAGE ONLY. This is not a deliverable and meets no brief requirement:
	Task 4 asks for the three routines, and they are all in routines.sql. This
	script calls each routine once on the sample data, so the reader can see them
	work: F1 play_royalty, P1 record_play and P2 upload_track (twice: a duplicate
	upload and a new one). It is kept in the repo and shown on the site; it is
	not in the submission zip.

	***** How to Run *********
	Run database_implementation.sql, then routines.sql, then this script. Every
	call runs inside one transaction that is rolled back, so the sample data is
	left exactly as it was and the script can be run again at any time. A call
	that SIGNALs stops a script, so the refused calls are left to the tests
	(project2/tests/test_routines.py).

	***** NERD STUFF *********
	project2/tests/test_routines.py runs this script after routines.sql, checks
	each result against an independent answer computed from the Project 1 data,
	and checks the data is unchanged afterwards. The site shows the results of
	the latest test run next to the script.

	***** Re: Class notes and syntax *****
	Course material: CALL and OUT parameters from Unit 9; START TRANSACTION and
	ROLLBACK from Unit 10.
	Beyond the slides: UNHEX(SHA2(...)) makes the 32-byte checksum of a new upload.
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
