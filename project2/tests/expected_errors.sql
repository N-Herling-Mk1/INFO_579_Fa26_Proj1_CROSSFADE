/*
	FILE: expected_errors.sql
	.
	CROSSFADE, INFO 579 Project 2: statements that MUST fail.
	Not a deliverable. Each one tests a use case whose correct outcome is the database refusing a write.
	project2/tests/test_single_table.py runs each inside a transaction, checks that MySQL raises exactly
	the expected error, checks that nothing changed, and rolls back. Do not run this file by hand
	expecting success: every statement in it is supposed to error.
*/


/*
	[E1] TRACK: a duplicate upload is refused
	Use cases: UC-15
	Business question: What happens when an artist uploads an audio file that is already in the catalogue?
	- The RA says the audio checksum (SHA-256 of the file) is "used to detect duplicate uploads", and
	  the physical model makes it UNIQUE (uq_track_audio_checksum). A re-upload must never become a
	  second catalogue entry earning a second royalty stream.
	- The statement re-uploads Low Tide Signal (track 4817) under a new track_id by copying its checksum,
	  exactly what an upload of the same file computes.
	Expects: 1062 uq_track_audio_checksum
*/
INSERT INTO crossfade.track (track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)
SELECT 9999, artist_id, CONCAT(title, ' (re-upload)'), duration, '2026-09-30', audio_checksum, 'awaiting scoring'
FROM crossfade.track
WHERE track_id = 4817;
