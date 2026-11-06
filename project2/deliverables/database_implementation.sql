/*
	FILE: database_implementation.sql
	.
	INFO 579 Project 2, Task 1: Database Implementation
	CROSSFADE, info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh)
	.
	***** FYI and project descriptions **********
	CROSSFADE is a streaming service for independent artists whose catalogue is
	indexed by where a recording sits between genres. This script builds the
	Project 1 physical data model (physical_data_model.png) as the MySQL database
	`crossfade` and loads the Project 1 sample data (data.xlsx), unchanged:
	10 tables, 401 rows.
	
	***** How to Run *********
	Run the whole script (MySQL 8.0.16 or later, for CHECK constraints). It drops
	and rebuilds the database, so it can be run again at any time.

	***** NERD STUFF *********
	Order: parent tables are created and loaded before the tables that reference
	them, so every foreign key value already exists when its row is inserted.
		genre, artist, listener, scoring_model      (no foreign keys)
		track, station                              (reference the tables above)
		track_score, genre_probability,
		station_blend, play                         (associative tables)
	Data: located and stored at bottom of file, reproduced from the Project1 data file.

	***** Re: Class notes and syntax *****
	Conventions, following the course examples:
	- Every constraint is named: pk_<table>, fk_<child>_<parent>, uq_<table>_<column>,
	  ck_<table>_<rule>. MySQL names the index behind each foreign key after the
	  constraint, which reproduces the index names shown on the physical model.
	- Each associative table's primary key is formed from its foreign keys.
	- Fixed-length values use CHAR/BINARY, variable-length values VARCHAR, and each
	  numeric column the smallest type that holds its range (Project 1 data dictionary).
	- ON DELETE is left at the default (reject) wherever a child row is a business
	  record in its own right; CASCADE or SET NULL is used only where the comment
	  on that table says why.
*/


/*
	Remove any earlier copy of the CROSSFADE database so that the script always
	starts from an empty database and loads exactly the Project 1 sample data.
*/
DROP DATABASE IF EXISTS crossfade;


/*
	Create the CROSSFADE database. utf8mb4 stores any artist name, track title or
	listener display name, including accented letters and non-Latin scripts.
*/
CREATE DATABASE IF NOT EXISTS crossfade DEFAULT CHARACTER SET utf8mb4;


/* ======================================================================== */
/*                                 TABLES                                   */
/* ======================================================================== */

/*
	[GENRE]: the fixed set of ten musical categories every scoring model produces a
	probability for. It is the coordinate system listeners use to describe the
	blend a station should play, so every model output and every station blend
	refers to a row here instead of free text.
	- genre_id equals the class index the models output (0 to 9), so a prediction
	  is stored without translation; the CHECK keeps it inside the fixed set.
	- name is unique: two genres cannot share a label. VARCHAR(9) fits the longest
	  label, "classical".
*/
CREATE TABLE IF NOT EXISTS crossfade.genre (
	genre_id TINYINT UNSIGNED NOT NULL,
	name VARCHAR(9) NOT NULL,
	description VARCHAR(80),
	CONSTRAINT pk_genre PRIMARY KEY (genre_id),
	UNIQUE INDEX uq_genre_name (name),
	CONSTRAINT ck_genre_id CHECK (genre_id BETWEEN 0 AND 9)
);


/*
	[ARTIST]: an independent musician or group registered to upload recordings under
	a direct streaming licence and paid a per-stream royalty. An artist can exist
	before their first upload.
	- stage_name is unique because it is how listeners find the artist.
	- country is CHAR(2): every value is a two-letter ISO 3166-1 code. It is
	  optional because an artist may not have declared one yet.
	- payout_rate is in US dollars per qualifying stream, always below one dollar,
	  so DECIMAL(5,5) holds it exactly; it must be positive.
*/
CREATE TABLE IF NOT EXISTS crossfade.artist (
	artist_id MEDIUMINT UNSIGNED NOT NULL,
	stage_name VARCHAR(64) NOT NULL,
	country CHAR(2),
	joined_date DATE NOT NULL,
	payout_rate DECIMAL(5,5) NOT NULL,
	verified BIT(1) NOT NULL,
	CONSTRAINT pk_artist PRIMARY KEY (artist_id),
	UNIQUE INDEX uq_artist_stage_name (stage_name),
	CONSTRAINT ck_artist_payout_rate CHECK (payout_rate > 0)
);


/*
	[LISTENER]: a registered subscriber who streams recordings and creates the
	stations through which they discover new material.
	- email is the sign-in address, so it is unique, and the CHECK rejects a value
	  with no @. VARCHAR(254) is the longest address the email standard allows.
	- plan_tier is one of three fixed subscription levels, so it is an ENUM.
*/
CREATE TABLE IF NOT EXISTS crossfade.listener (
	listener_id INT UNSIGNED NOT NULL,
	email VARCHAR(254) NOT NULL,
	display_name VARCHAR(32) NOT NULL,
	plan_tier ENUM('free', 'standard', 'premium') NOT NULL,
	signup_date DATE NOT NULL,
	CONSTRAINT pk_listener PRIMARY KEY (listener_id),
	UNIQUE INDEX uq_listener_email (email),
	CONSTRAINT ck_listener_email CHECK (email LIKE '%@%')
);


/*
	[SCORING_MODEL]: one trained and deployed version of the genre classifier.
	Several versions run at once because they disagree, and that disagreement is
	itself a signal CROSSFADE uses. The five rows are the real BEARDOWN/FORGE
	model versions.
	- version_label is unique: it names the version in reports.
	- holdout_accuracy is a proportion (0 to 1); embedding_dimension and
	  segment_length (seconds) must be positive.
*/
CREATE TABLE IF NOT EXISTS crossfade.scoring_model (
	model_id TINYINT UNSIGNED NOT NULL,
	version_label VARCHAR(32) NOT NULL,
	fusion_type ENUM('concat', 'gated') NOT NULL,
	embedding_dimension SMALLINT UNSIGNED NOT NULL,
	segment_length TINYINT UNSIGNED NOT NULL,
	training_corpus VARCHAR(16) NOT NULL,
	holdout_accuracy DECIMAL(5,4) NOT NULL,
	deployed_on DATE NOT NULL,
	CONSTRAINT pk_scoring_model PRIMARY KEY (model_id),
	UNIQUE INDEX uq_scoring_model_version_label (version_label),
	CONSTRAINT ck_scoring_model_holdout_accuracy CHECK (holdout_accuracy BETWEEN 0 AND 1),
	CONSTRAINT ck_scoring_model_embedding_dimension CHECK (embedding_dimension > 0),
	CONSTRAINT ck_scoring_model_segment_length CHECK (segment_length > 0)
);


/*
	[TRACK]: a single recording uploaded by an artist (Artist 1:N Track). It is
	streamable once at least one model has scored it.
	- artist_id is the artist the royalty is paid to. An artist who has tracks
	  cannot be deleted (default ON DELETE), because the royalty ledger needs them.
	- audio_checksum is the 32-byte SHA-256 digest of the audio file, so it is
	  BINARY(32), and it is unique to reject duplicate uploads.
	- duration is in whole seconds and must be positive.
*/
CREATE TABLE IF NOT EXISTS crossfade.track (
	track_id INT UNSIGNED NOT NULL,
	artist_id MEDIUMINT UNSIGNED NOT NULL,
	title VARCHAR(128) NOT NULL,
	duration SMALLINT UNSIGNED NOT NULL,
	release_date DATE NOT NULL,
	audio_checksum BINARY(32) NOT NULL,
	ingest_status ENUM('awaiting scoring', 'scored', 'rejected') NOT NULL,
	CONSTRAINT pk_track PRIMARY KEY (track_id),
	UNIQUE INDEX uq_track_audio_checksum (audio_checksum),
	CONSTRAINT fk_track_artist FOREIGN KEY (artist_id)
		REFERENCES crossfade.artist (artist_id),
	CONSTRAINT ck_track_duration CHECK (duration > 0)
);


/*
	[STATION]: a listener's standing description of a region of genre space. It
	stores a blend and an ambiguity window, not a fixed playlist, so its contents
	grow with the catalogue (Listener 1:N Station, Scoring Model 1:N Station).
	- model_id is the model version the station is evaluated against, so its
	  contents do not change meaning when another version scores the catalogue.
	- The ambiguity bounds are on the 0 to 1 posterior-entropy scale, and the
	  minimum may not exceed the maximum (integrity rule I4).
*/
CREATE TABLE IF NOT EXISTS crossfade.station (
	station_id INT UNSIGNED NOT NULL,
	listener_id INT UNSIGNED NOT NULL,
	model_id TINYINT UNSIGNED NOT NULL,
	name VARCHAR(64) NOT NULL,
	minimum_ambiguity DECIMAL(3,2) NOT NULL,
	maximum_ambiguity DECIMAL(3,2) NOT NULL,
	created_on DATE NOT NULL,
	CONSTRAINT pk_station PRIMARY KEY (station_id),
	CONSTRAINT fk_station_listener FOREIGN KEY (listener_id)
		REFERENCES crossfade.listener (listener_id),
	CONSTRAINT fk_station_scoring_model FOREIGN KEY (model_id)
		REFERENCES crossfade.scoring_model (model_id),
	CONSTRAINT ck_station_minimum_ambiguity CHECK (minimum_ambiguity BETWEEN 0 AND 1),
	CONSTRAINT ck_station_maximum_ambiguity CHECK (maximum_ambiguity BETWEEN 0 AND 1),
	CONSTRAINT ck_station_ambiguity_window CHECK (minimum_ambiguity <= maximum_ambiguity)
);


/*
	[TRACK_SCORE] (associative): the result one scoring model produced for one
	recording. It resolves Track M:N Scoring Model, so its primary key is the two
	foreign keys (track_id, model_id): at most one result per recording and model.
	- genre_id is the model's top genre (Genre 1:N Track Score). It stays outside
	  the key, because one recording and model pair has exactly one top genre.
	- genre_id, top_probability, posterior_entropy and model_divergence are
	  derived from the genre_probability rows (integrity rule I3).
	- model_divergence is NULL while only one model has scored the recording.
	  segment_variance is a variance of probabilities, so it never exceeds 0.25.
*/
CREATE TABLE IF NOT EXISTS crossfade.track_score (
	track_id INT UNSIGNED NOT NULL,
	model_id TINYINT UNSIGNED NOT NULL,
	genre_id TINYINT UNSIGNED NOT NULL,
	top_probability DECIMAL(5,4) NOT NULL,
	posterior_entropy DECIMAL(5,4) NOT NULL,
	model_divergence DECIMAL(5,4),
	segment_variance DECIMAL(4,4),
	scored_on DATETIME NOT NULL,
	CONSTRAINT pk_track_score PRIMARY KEY (track_id, model_id),
	CONSTRAINT fk_track_score_track FOREIGN KEY (track_id)
		REFERENCES crossfade.track (track_id),
	CONSTRAINT fk_track_score_scoring_model FOREIGN KEY (model_id)
		REFERENCES crossfade.scoring_model (model_id),
	CONSTRAINT fk_track_score_genre FOREIGN KEY (genre_id)
		REFERENCES crossfade.genre (genre_id),
	CONSTRAINT ck_track_score_top_probability CHECK (top_probability BETWEEN 0 AND 1),
	CONSTRAINT ck_track_score_posterior_entropy CHECK (posterior_entropy BETWEEN 0 AND 1),
	CONSTRAINT ck_track_score_model_divergence CHECK (model_divergence BETWEEN 0 AND 1),
	CONSTRAINT ck_track_score_segment_variance CHECK (segment_variance BETWEEN 0 AND 0.25)
);


/*
	[GENRE_PROBABILITY] (associative): the probability one model assigned to one
	genre for one recording. It resolves Track Score M:N Genre and holds the full
	ten-genre distribution that stations are matched against.
	- Primary key: the two-part key of track_score followed by genre_id.
	- (track_id, model_id) is one composite foreign key to track_score, so a
	  probability can only exist for a recording and model that have a result.
	- ON DELETE CASCADE on that key: the ten probabilities are the parts of one
	  scoring result, so deleting the result deletes them with it.
*/
CREATE TABLE IF NOT EXISTS crossfade.genre_probability (
	track_id INT UNSIGNED NOT NULL,
	model_id TINYINT UNSIGNED NOT NULL,
	genre_id TINYINT UNSIGNED NOT NULL,
	probability DECIMAL(5,4) NOT NULL,
	CONSTRAINT pk_genre_probability PRIMARY KEY (track_id, model_id, genre_id),
	CONSTRAINT fk_genre_probability_track_score FOREIGN KEY (track_id, model_id)
		REFERENCES crossfade.track_score (track_id, model_id)
		ON DELETE CASCADE,
	CONSTRAINT fk_genre_probability_genre FOREIGN KEY (genre_id)
		REFERENCES crossfade.genre (genre_id),
	CONSTRAINT ck_genre_probability_probability CHECK (probability BETWEEN 0 AND 1)
);


/*
	[STATION_BLEND] (associative): the weight one station gives to one genre. It
	resolves Station M:N Genre, with one weight per row so each value is atomic.
	- Primary key (station_id, genre_id): one weight per genre per station.
	- A weight is greater than 0 and at most 1. The weights of one station sum to
	  1.00 (integrity rule I1), a rule across rows that a CHECK cannot express.
	- ON DELETE CASCADE on station: a blend is part of its station's definition
	  and means nothing without it.
*/
CREATE TABLE IF NOT EXISTS crossfade.station_blend (
	station_id INT UNSIGNED NOT NULL,
	genre_id TINYINT UNSIGNED NOT NULL,
	weight DECIMAL(3,2) NOT NULL,
	CONSTRAINT pk_station_blend PRIMARY KEY (station_id, genre_id),
	CONSTRAINT fk_station_blend_station FOREIGN KEY (station_id)
		REFERENCES crossfade.station (station_id)
		ON DELETE CASCADE,
	CONSTRAINT fk_station_blend_genre FOREIGN KEY (genre_id)
		REFERENCES crossfade.genre (genre_id),
	CONSTRAINT ck_station_blend_weight CHECK (weight > 0 AND weight <= 1)
);


/*
	[PLAY] (associative): one occasion on which a listener streamed a recording. It
	resolves Listener M:N Track and is both the taste signal and the billable
	event the artist royalty is paid on.
	- Primary key (listener_id, track_id, played_at): a listener streams the same
	  recording many times, so the UTC start time completes the key, and a
	  repeated report of the same play is rejected instead of being paid twice.
	- station_id is optional (NULL when the listener chose the recording
	  directly), so it is outside the key. ON DELETE SET NULL: if a station is
	  deleted, its plays stay in the royalty ledger with no station recorded.
	- completed and royalty_amount follow integrity rule I7: completed is 1
	  exactly when seconds_played equals the track's duration, and royalty_amount
	  is the artist's payout_rate at play time for a play of 30 seconds or more,
	  otherwise 0. Both depend on other tables, so they are set when the play is
	  recorded, not by a CHECK here.
*/
CREATE TABLE IF NOT EXISTS crossfade.play (
	listener_id INT UNSIGNED NOT NULL,
	track_id INT UNSIGNED NOT NULL,
	played_at DATETIME NOT NULL,
	station_id INT UNSIGNED,
	seconds_played SMALLINT UNSIGNED NOT NULL,
	completed BIT(1) NOT NULL,
	reaction ENUM('saved', 'skipped'),
	royalty_amount DECIMAL(5,5) NOT NULL,
	CONSTRAINT pk_play PRIMARY KEY (listener_id, track_id, played_at),
	CONSTRAINT fk_play_listener FOREIGN KEY (listener_id)
		REFERENCES crossfade.listener (listener_id),
	CONSTRAINT fk_play_track FOREIGN KEY (track_id)
		REFERENCES crossfade.track (track_id),
	CONSTRAINT fk_play_station FOREIGN KEY (station_id)
		REFERENCES crossfade.station (station_id)
		ON DELETE SET NULL,
	CONSTRAINT ck_play_royalty_amount CHECK (royalty_amount >= 0)
);


/* ======================================================================== */
/*                     SAMPLE DATA (Project 1, data.xlsx)                   */
/* ======================================================================== */

/*
	Load the ten genres. IDs 0 to 9 match the scoring models' output classes
	(the GTZAN genres); the descriptions are shown to listeners while they
	compose a station blend.
*/
INSERT INTO crossfade.genre
	(genre_id, name, description)
VALUES
	(0, 'blues',     'Twelve-bar forms, blue notes and call-and-response phrasing'),
	(1, 'classical', 'Orchestral and chamber writing in the Western art-music tradition'),
	(2, 'country',   'Narrative songwriting with steel guitar, fiddle and twang'),
	(3, 'disco',     'Four-on-the-floor dance grooves with lush strings and bass'),
	(4, 'hiphop',    'Rhythmic vocal delivery over sampled or programmed beats'),
	(5, 'jazz',      'Swing, improvisation and extended harmony'),
	(6, 'metal',     'Distorted guitars, heavy drums and aggressive dynamics'),
	(7, 'pop',       'Hook-driven songs built for broad appeal'),
	(8, 'reggae',    'Offbeat skank rhythm and prominent bass lines'),
	(9, 'rock',      'Guitar-led songs with a driving backbeat');

/*
	Load the eight registered artists: the people royalties are paid to. Three are
	not yet verified, and Saltmarsh Tapes has not declared a country (NULL).
*/
INSERT INTO crossfade.artist
	(artist_id, stage_name, country, joined_date, payout_rate, verified)
VALUES
	(1042, 'Velvet Static',   'US', '2026-03-14', 0.004,  1),
	(1043, 'Mara Quell',      'GB', '2026-01-20', 0.0035, 1),
	(1044, 'Low Orbit Choir', 'CA', '2026-02-03', 0.0038, 1),
	(1045, 'Tin Harbour',     'AU', '2026-02-27', 0.0032, 0),
	(1046, 'Ochre Parade',    'MX', '2026-04-11', 0.0036, 1),
	(1047, 'Juno Fleet',      'DE', '2026-05-02', 0.003,  1),
	(1048, 'Saltmarsh Tapes', NULL, '2026-05-19', 0.003,  0),
	(1049, 'Kestrel Ave',     'JM', '2026-08-28', 0.0034, 0);

/*
	Load the eight listeners, covering all three plan tiers, so stations and play
	history can be tied to subscribers.
*/
INSERT INTO crossfade.listener
	(listener_id, email, display_name, plan_tier, signup_date)
VALUES
	(20931, 'j.rivera@example.com',    'jrivera', 'standard', '2026-05-09'),
	(20932, 'amara.o@example.com',     'amara_o', 'premium',  '2026-04-02'),
	(20933, 'k.lindqvist@example.com', 'klind',   'free',     '2026-04-18'),
	(20934, 'priya.m@example.com',     'priyam',  'premium',  '2026-05-27'),
	(20935, 'tomas.b@example.com',     'tbarros', 'standard', '2026-06-03'),
	(20936, 'wen.zhao@example.com',    'wenz',    'free',     '2026-06-20'),
	(20937, 'd.okafor@example.com',    'dokafor', 'standard', '2026-07-08'),
	(20938, 'h.ito@example.com',       'hito',    'free',     '2026-08-15');

/*
	Load the five deployed scoring model versions (the BEARDOWN/FORGE models),
	which differ in fusion type, embedding width and audio segment length.
*/
INSERT INTO crossfade.scoring_model
	(model_id, version_label, fusion_type, embedding_dimension, segment_length, training_corpus, holdout_accuracy, deployed_on)
VALUES
	(1, 'beardown',           'gated',  512, 30, 'GTZAN', 0.7,    '2026-01-12'),
	(2, 'beardown_rrm_cfg12', 'concat', 384, 30, 'GTZAN', 0.68,   '2026-02-16'),
	(3, 'beardown_rrm_cfg17', 'concat', 768, 30, 'GTZAN', 0.76,   '2026-03-09'),
	(4, 'beardown_rrm',       'concat', 768, 30, 'GTZAN', 0.76,   '2026-03-23'),
	(5, 'beardown_3sec',      'concat', 384, 3,  'GTZAN', 0.7887, '2026-06-23');

/*
	Load the fifteen recordings in the catalogue. Thirteen are scored; one is
	awaiting scoring and one was rejected, so the catalogue shows every stage of
	the upload pipeline. Checksums are written as hexadecimal literals, which
	MySQL stores as the 32 raw bytes of each SHA-256 digest.
*/
INSERT INTO crossfade.track
	(track_id, artist_id, title, duration, release_date, audio_checksum, ingest_status)
VALUES
	(4817, 1042, 'Low Tide Signal',        214, '2026-04-02', 0xBD675D48363DAAFDCEF52552ABD98D2302AE34C58A6AEBE32A13ABF4A14ED8B4, 'scored'),
	(4818, 1042, 'Copper Lanterns',        187, '2026-04-20', 0x5983C502A7DC729DE1309DB3472114C928E90E2E71279EDB90A32798A3091884, 'scored'),
	(4819, 1043, 'Glass Meridian',         241, '2026-02-25', 0x9E0DADD51ACFB2BFCFDCE10D63542D6F6C8B83DFCCF5FB602CA46A54419090E0, 'scored'),
	(4820, 1043, 'Second Weather',         199, '2026-03-30', 0x957C70149E1299D5F80FD0662D0FE441DEA2F2CF3A794F01723649800FF79578, 'scored'),
	(4821, 1044, 'Cathedral Static',       312, '2026-03-01', 0x2555040D4C50FDD2636C8FD581A3D89945DDBF766A1CFD23D1C4E4A6A3F4D4B8, 'scored'),
	(4822, 1044, 'Hymn for a Server Room', 268, '2026-05-15', 0xD276CB55DFBBAC0965C4BBE6FD22644E4204016CB93E774BCA56AF5DCFA61122, 'scored'),
	(4823, 1045, 'Dust on the Dial',       205, '2026-03-18', 0xC06597DE02EBD6D6AC031CB28019E44E4E5C12CDE2C78769A224FBFD1501C1C0, 'scored'),
	(4824, 1045, 'Harbour Lights Waltz',   176, '2026-05-06', 0x0648B585C6E9879E6C9673AB19090CBDF80BE8028F36134983CD256603CA5FE1, 'scored'),
	(4825, 1046, 'Marigold Dub',           233, '2026-05-01', 0xD13AB16A153AC5FD800A4A10B9C8D8965BC0E1C4DB91898EFDE205E2ECD49DDC, 'scored'),
	(4826, 1046, 'Plaza at Noon',          198, '2026-06-30', 0x84385F82766187C8310ADBC23C28FB91EC47264C49137ABB45819B77E5708698, 'scored'),
	(4827, 1047, 'Stahlwerk',              254, '2026-05-25', 0xB20784242490346AE77A68D7538C9AEC54488DF7B8F373C4FAC8835C0FA878CD, 'scored'),
	(4828, 1047, 'Afterimage Club',        221, '2026-07-10', 0x8B03F255CE532E687B4D146692737F2135AEF1B2AABB7C8DBE3AF0349EFB4B77, 'scored'),
	(4829, 1048, 'Tapeworm Blues',         189, '2026-06-05', 0x4F9FF37AD95773DCD6CADECE159F4EB187B0110E3B7F056B01B9CCC94773AE90, 'scored'),
	(4830, 1048, 'Brine',                  163, '2026-09-21', 0x7D19F53A1DAF42AD0CF5F5891779E666A137A68AD890F95356FDDBA2F8E39417, 'awaiting scoring'),
	(4831, 1048, 'Untitled Loop 7',        48,  '2026-09-22', 0x9261DDFAF151557C46D8A3DFB862D09D196E0BC6A34CFCEA97B5041AAE9D96F7, 'rejected');

/*
	Load the eight stations: each listener's saved region of genre space, with
	the model version it is evaluated against and its ambiguity window.
*/
INSERT INTO crossfade.station
	(station_id, listener_id, model_id, name, minimum_ambiguity, maximum_ambiguity, created_on)
VALUES
	(7710, 20931, 5, 'Late Jazz Hop',     0.35, 0.8,  '2026-08-01'),
	(7711, 20932, 4, 'Porch and Pedal',   0.2,  0.7,  '2026-06-10'),
	(7712, 20932, 2, 'Neon Waltz',        0.3,  0.9,  '2026-05-02'),
	(7713, 20933, 1, 'Iron Choir',        0.25, 0.85, '2026-05-20'),
	(7714, 20934, 4, 'Harbour Dub',       0.3,  0.9,  '2026-06-12'),
	(7715, 20935, 5, 'Glitterball Drift', 0.2,  0.75, '2026-07-20'),
	(7716, 20936, 4, 'Rust Belt Radio',   0.1,  0.7,  '2026-07-01'),
	(7717, 20937, 2, 'Blue Hour',         0.2,  0.8,  '2026-08-05');

/*
	Load the 27 scoring results: one row per recording and model that scored it.
	Model divergence is NULL where only one model has scored the recording.
*/
INSERT INTO crossfade.track_score
	(track_id, model_id, genre_id, top_probability, posterior_entropy, model_divergence, segment_variance, scored_on)
VALUES
	(4817, 1, 5, 0.5438, 0.4908, 0.0124, 0.0243, '2026-03-15 21:31:57'),
	(4817, 2, 5, 0.6131, 0.4421, 0.0103, 0.0058, '2026-04-03 14:02:14'),
	(4817, 4, 5, 0.6002, 0.4843, 0.0156, 0.0289, '2026-04-05 16:12:38'),
	(4817, 5, 5, 0.58,   0.4619, 0.0198, 0.0051, '2026-07-01 09:14:52'),
	(4818, 1, 5, 0.4819, 0.5463, 0.0283, 0.0111, '2026-03-15 18:53:49'),
	(4818, 4, 0, 0.5077, 0.4628, 0.0283, 0.0109, '2026-04-26 10:47:01'),
	(4819, 1, 1, 0.489,  0.531,  0.0452, 0.0105, '2026-01-21 00:20:40'),
	(4819, 2, 1, 0.5562, 0.4114, 0.0452, 0.0233, '2026-03-01 10:35:49'),
	(4820, 2, 7, 0.4357, 0.5158, 0.0386, 0.0057, '2026-02-17 18:45:56'),
	(4820, 4, 7, 0.4671, 0.5621, 0.0386, 0.0256, '2026-03-31 19:48:26'),
	(4821, 1, 6, 0.4799, 0.57,   0.1025, 0.0081, '2026-02-04 18:53:48'),
	(4821, 2, 1, 0.5556, 0.4998, 0.1025, 0.0288, '2026-03-06 16:35:42'),
	(4822, 4, 1, 0.7354, 0.4455, 0.0227, 0.0276, '2026-03-24 10:44:57'),
	(4822, 5, 1, 0.6804, 0.5081, 0.0227, 0.0121, '2026-06-26 05:51:40'),
	(4823, 2, 2, 0.5153, 0.5194, 0.0423, 0.0128, '2026-02-28 23:04:33'),
	(4823, 4, 2, 0.6131, 0.5065, 0.0423, 0.0179, '2026-03-24 15:58:35'),
	(4824, 4, 2, 0.7401, 0.4276, NULL,   0.0089, '2026-03-24 17:19:44'),
	(4825, 1, 8, 0.4964, 0.6745, 0.0454, 0.0273, '2026-04-12 03:12:26'),
	(4825, 4, 8, 0.5743, 0.6107, 0.0454, 0.0246, '2026-05-07 22:13:19'),
	(4826, 4, 3, 0.4338, 0.6721, 0.0341, 0.018,  '2026-04-12 11:41:13'),
	(4826, 5, 3, 0.4943, 0.5503, 0.0341, 0.0193, '2026-07-03 17:38:51'),
	(4827, 1, 6, 0.6295, 0.4784, 0.0565, 0.0117, '2026-05-03 14:55:16'),
	(4827, 4, 6, 0.4514, 0.5906, 0.0565, 0.0072, '2026-05-31 03:30:19'),
	(4828, 2, 7, 0.4461, 0.5261, 0.0421, 0.0054, '2026-05-03 13:59:30'),
	(4828, 5, 3, 0.5516, 0.5417, 0.0421, 0.0246, '2026-07-15 10:06:28'),
	(4829, 2, 0, 0.4947, 0.522,  0.0258, 0.0265, '2026-05-20 16:00:44'),
	(4829, 4, 0, 0.5363, 0.4989, 0.0258, 0.0036, '2026-06-09 19:02:52');

/*
	Load the 270 genre probabilities: ten per scoring result, one for each genre,
	summing to one within rounding (integrity rule I2). These are the full
	distributions that place each recording between genres.
*/
INSERT INTO crossfade.genre_probability
	(track_id, model_id, genre_id, probability)
VALUES
	(4817, 1, 0, 0.0482),
	(4817, 1, 1, 0.0252),
	(4817, 1, 2, 0.0087),
	(4817, 1, 3, 0.0035),
	(4817, 1, 4, 0.3426),
	(4817, 1, 5, 0.5438),
	(4817, 1, 6, 0.0044),
	(4817, 1, 7, 0.0039),
	(4817, 1, 8, 0.0164),
	(4817, 1, 9, 0.0033),
	(4817, 2, 0, 0.0563),
	(4817, 2, 1, 0.0111),
	(4817, 2, 2, 0.0101),
	(4817, 2, 3, 0.0025),
	(4817, 2, 4, 0.2898),
	(4817, 2, 5, 0.6131),
	(4817, 2, 6, 0.004),
	(4817, 2, 7, 0.0022),
	(4817, 2, 8, 0.0107),
	(4817, 2, 9, 0.0002),
	(4817, 4, 0, 0.0469),
	(4817, 4, 1, 0.0126),
	(4817, 4, 2, 0.0065),
	(4817, 4, 3, 0.0115),
	(4817, 4, 4, 0.2859),
	(4817, 4, 5, 0.6002),
	(4817, 4, 6, 0.0047),
	(4817, 4, 7, 0.0149),
	(4817, 4, 8, 0.0087),
	(4817, 4, 9, 0.0081),
	(4817, 5, 0, 0.0949),
	(4817, 5, 1, 0.0285),
	(4817, 5, 2, 0.0085),
	(4817, 5, 3, 0.0026),
	(4817, 5, 4, 0.2843),
	(4817, 5, 5, 0.58),
	(4817, 5, 6, 0.0008),
	(4817, 5, 7, 0.0002),
	(4817, 5, 8, 0.0001),
	(4817, 5, 9, 0.0001),
	(4818, 1, 0, 0.3774),
	(4818, 1, 1, 0.0133),
	(4818, 1, 2, 0.0211),
	(4818, 1, 3, 0.0146),
	(4818, 1, 4, 0.0132),
	(4818, 1, 5, 0.4819),
	(4818, 1, 6, 0.049),
	(4818, 1, 7, 0.0036),
	(4818, 1, 8, 0.0131),
	(4818, 1, 9, 0.0128),
	(4818, 4, 0, 0.5077),
	(4818, 4, 1, 0.0119),
	(4818, 4, 2, 0.0089),
	(4818, 4, 3, 0.006),
	(4818, 4, 4, 0.0144),
	(4818, 4, 5, 0.4133),
	(4818, 4, 6, 0.0049),
	(4818, 4, 7, 0.0058),
	(4818, 4, 8, 0.0195),
	(4818, 4, 9, 0.0076),
	(4819, 1, 0, 0.0279),
	(4819, 1, 1, 0.489),
	(4819, 1, 2, 0.0498),
	(4819, 1, 3, 0.0028),
	(4819, 1, 4, 0.0015),
	(4819, 1, 5, 0.0111),
	(4819, 1, 6, 0.0226),
	(4819, 1, 7, 0.3745),
	(4819, 1, 8, 0.0136),
	(4819, 1, 9, 0.0072),
	(4819, 2, 0, 0.001),
	(4819, 2, 1, 0.5562),
	(4819, 2, 2, 0.0024),
	(4819, 2, 3, 0.0026),
	(4819, 2, 4, 0.015),
	(4819, 2, 5, 0.009),
	(4819, 2, 6, 0.0086),
	(4819, 2, 7, 0.3888),
	(4819, 2, 8, 0.0008),
	(4819, 2, 9, 0.0156),
	(4820, 2, 0, 0.0218),
	(4820, 2, 1, 0.0079),
	(4820, 2, 2, 0.0083),
	(4820, 2, 3, 0.4304),
	(4820, 2, 4, 0.0001),
	(4820, 2, 5, 0.0231),
	(4820, 2, 6, 0.0671),
	(4820, 2, 7, 0.4357),
	(4820, 2, 8, 0.0041),
	(4820, 2, 9, 0.0015),
	(4820, 4, 0, 0.0136),
	(4820, 4, 1, 0.0156),
	(4820, 4, 2, 0.0643),
	(4820, 4, 3, 0.3764),
	(4820, 4, 4, 0.0092),
	(4820, 4, 5, 0.0129),
	(4820, 4, 6, 0.021),
	(4820, 4, 7, 0.4671),
	(4820, 4, 8, 0.0129),
	(4820, 4, 9, 0.007),
	(4821, 1, 0, 0.0039),
	(4821, 1, 1, 0.3612),
	(4821, 1, 2, 0.0435),
	(4821, 1, 3, 0.022),
	(4821, 1, 4, 0.0304),
	(4821, 1, 5, 0.0238),
	(4821, 1, 6, 0.4799),
	(4821, 1, 7, 0.0072),
	(4821, 1, 8, 0.0129),
	(4821, 1, 9, 0.0152),
	(4821, 2, 0, 0.011),
	(4821, 2, 1, 0.5556),
	(4821, 2, 2, 0.0034),
	(4821, 2, 3, 0.0018),
	(4821, 2, 4, 0.0107),
	(4821, 2, 5, 0.0003),
	(4821, 2, 6, 0.2865),
	(4821, 2, 7, 0.0016),
	(4821, 2, 8, 0.1063),
	(4821, 2, 9, 0.0228),
	(4822, 4, 0, 0.0126),
	(4822, 4, 1, 0.7354),
	(4822, 4, 2, 0.0103),
	(4822, 4, 3, 0.0092),
	(4822, 4, 4, 0.0114),
	(4822, 4, 5, 0.1269),
	(4822, 4, 6, 0.0419),
	(4822, 4, 7, 0.0117),
	(4822, 4, 8, 0.0264),
	(4822, 4, 9, 0.0142),
	(4822, 5, 0, 0.0158),
	(4822, 5, 1, 0.6804),
	(4822, 5, 2, 0.0146),
	(4822, 5, 3, 0.0178),
	(4822, 5, 4, 0.0161),
	(4822, 5, 5, 0.1499),
	(4822, 5, 6, 0.0089),
	(4822, 5, 7, 0.0168),
	(4822, 5, 8, 0.0209),
	(4822, 5, 9, 0.0588),
	(4823, 2, 0, 0.0196),
	(4823, 2, 1, 0.0122),
	(4823, 2, 2, 0.5153),
	(4823, 2, 3, 0.0402),
	(4823, 2, 4, 0.004),
	(4823, 2, 5, 0.0264),
	(4823, 2, 6, 0.005),
	(4823, 2, 7, 0.0007),
	(4823, 2, 8, 0.0196),
	(4823, 2, 9, 0.357),
	(4823, 4, 0, 0.0017),
	(4823, 4, 1, 0.035),
	(4823, 4, 2, 0.6131),
	(4823, 4, 3, 0.0189),
	(4823, 4, 4, 0.0279),
	(4823, 4, 5, 0.0121),
	(4823, 4, 6, 0.0236),
	(4823, 4, 7, 0.0087),
	(4823, 4, 8, 0.0065),
	(4823, 4, 9, 0.2525),
	(4824, 4, 0, 0.1002),
	(4824, 4, 1, 0.0053),
	(4824, 4, 2, 0.7401),
	(4824, 4, 3, 0.0131),
	(4824, 4, 4, 0.0128),
	(4824, 4, 5, 0.0074),
	(4824, 4, 6, 0.0006),
	(4824, 4, 7, 0.0482),
	(4824, 4, 8, 0.0688),
	(4824, 4, 9, 0.0035),
	(4825, 1, 0, 0.014),
	(4825, 1, 1, 0.0493),
	(4825, 1, 2, 0.0275),
	(4825, 1, 3, 0.0261),
	(4825, 1, 4, 0.2332),
	(4825, 1, 5, 0.0261),
	(4825, 1, 6, 0.0756),
	(4825, 1, 7, 0.0068),
	(4825, 1, 8, 0.4964),
	(4825, 1, 9, 0.045),
	(4825, 4, 0, 0.0525),
	(4825, 4, 1, 0.0054),
	(4825, 4, 2, 0.065),
	(4825, 4, 3, 0.02),
	(4825, 4, 4, 0.194),
	(4825, 4, 5, 0.031),
	(4825, 4, 6, 0.031),
	(4825, 4, 7, 0.0113),
	(4825, 4, 8, 0.5743),
	(4825, 4, 9, 0.0155),
	(4826, 4, 0, 0.0182),
	(4826, 4, 1, 0.0253),
	(4826, 4, 2, 0.0362),
	(4826, 4, 3, 0.4338),
	(4826, 4, 4, 0.0731),
	(4826, 4, 5, 0.0343),
	(4826, 4, 6, 0.0213),
	(4826, 4, 7, 0.0224),
	(4826, 4, 8, 0.3212),
	(4826, 4, 9, 0.0142),
	(4826, 5, 0, 0.0128),
	(4826, 5, 1, 0.0301),
	(4826, 5, 2, 0.0209),
	(4826, 5, 3, 0.4943),
	(4826, 5, 4, 0.0039),
	(4826, 5, 5, 0.0367),
	(4826, 5, 6, 0.0108),
	(4826, 5, 7, 0.0123),
	(4826, 5, 8, 0.3632),
	(4826, 5, 9, 0.015),
	(4827, 1, 0, 0.0021),
	(4827, 1, 1, 0.0144),
	(4827, 1, 2, 0.0013),
	(4827, 1, 3, 0.0146),
	(4827, 1, 4, 0.0437),
	(4827, 1, 5, 0.0116),
	(4827, 1, 6, 0.6295),
	(4827, 1, 7, 0.0293),
	(4827, 1, 8, 0.0054),
	(4827, 1, 9, 0.2481),
	(4827, 4, 0, 0.0139),
	(4827, 4, 1, 0.0268),
	(4827, 4, 2, 0.0413),
	(4827, 4, 3, 0.0376),
	(4827, 4, 4, 0.0533),
	(4827, 4, 5, 0.0051),
	(4827, 4, 6, 0.4514),
	(4827, 4, 7, 0.0016),
	(4827, 4, 8, 0.0054),
	(4827, 4, 9, 0.3636),
	(4828, 2, 0, 0.0281),
	(4828, 2, 1, 0.004),
	(4828, 2, 2, 0.007),
	(4828, 2, 3, 0.4273),
	(4828, 2, 4, 0.0049),
	(4828, 2, 5, 0.0419),
	(4828, 2, 6, 0.0083),
	(4828, 2, 7, 0.4461),
	(4828, 2, 8, 0.0211),
	(4828, 2, 9, 0.0113),
	(4828, 5, 0, 0.0181),
	(4828, 5, 1, 0.0059),
	(4828, 5, 2, 0.0149),
	(4828, 5, 3, 0.5516),
	(4828, 5, 4, 0.0417),
	(4828, 5, 5, 0.0177),
	(4828, 5, 6, 0.0197),
	(4828, 5, 7, 0.3023),
	(4828, 5, 8, 0.0034),
	(4828, 5, 9, 0.0247),
	(4829, 2, 0, 0.4947),
	(4829, 2, 1, 0.031),
	(4829, 2, 2, 0.02),
	(4829, 2, 3, 0.0304),
	(4829, 2, 4, 0.0032),
	(4829, 2, 5, 0.0041),
	(4829, 2, 6, 0.0154),
	(4829, 2, 7, 0.0001),
	(4829, 2, 8, 0.0234),
	(4829, 2, 9, 0.3777),
	(4829, 4, 0, 0.5363),
	(4829, 4, 1, 0.0178),
	(4829, 4, 2, 0.0331),
	(4829, 4, 3, 0.006),
	(4829, 4, 4, 0.0271),
	(4829, 4, 5, 0.0078),
	(4829, 4, 6, 0.0097),
	(4829, 4, 7, 0.0051),
	(4829, 4, 8, 0.0045),
	(4829, 4, 9, 0.3526);

/*
	Load the 19 station blend weights. The weights of each station sum to 1.00
	(integrity rule I1).
*/
INSERT INTO crossfade.station_blend
	(station_id, genre_id, weight)
VALUES
	(7710, 4, 0.4),
	(7710, 5, 0.6),
	(7711, 0, 0.3),
	(7711, 2, 0.7),
	(7712, 1, 0.2),
	(7712, 3, 0.3),
	(7712, 7, 0.5),
	(7713, 1, 0.34),
	(7713, 6, 0.5),
	(7713, 9, 0.16),
	(7714, 4, 0.4),
	(7714, 8, 0.6),
	(7715, 3, 0.34),
	(7715, 7, 0.33),
	(7715, 8, 0.33),
	(7716, 0, 0.25),
	(7716, 2, 0.2),
	(7716, 9, 0.55),
	(7717, 0, 1);

/*
	Load the 31 plays: the listening history and royalty ledger. Station is NULL
	where the listener chose the recording directly; reaction is NULL where no
	explicit save or skip was given; royalty is 0 for plays under 30 seconds.
*/
INSERT INTO crossfade.play
	(listener_id, track_id, played_at, station_id, seconds_played, completed, reaction, royalty_amount)
VALUES
	(20932, 4820, '2026-05-18 02:17:16', 7712, 187, 0, NULL,      0.0035),
	(20932, 4821, '2026-05-20 07:43:07', 7712, 201, 0, NULL,      0.0038),
	(20931, 4821, '2026-05-21 21:23:06', NULL, 83,  0, NULL,      0.0038),
	(20933, 4821, '2026-05-23 04:55:58', 7713, 312, 1, 'saved',   0.0038),
	(20933, 4821, '2026-05-24 02:14:55', 7713, 24,  0, 'skipped', 0),
	(20933, 4827, '2026-05-26 18:17:40', 7713, 254, 1, NULL,      0.003),
	(20933, 4827, '2026-05-30 00:32:12', NULL, 254, 1, NULL,      0.003),
	(20931, 4827, '2026-06-02 15:59:47', NULL, 23,  0, 'skipped', 0),
	(20934, 4823, '2026-06-04 20:49:12', NULL, 205, 1, NULL,      0.0032),
	(20934, 4818, '2026-06-07 05:05:41', NULL, 187, 1, NULL,      0.004),
	(20935, 4825, '2026-06-13 09:52:53', 7714, 233, 1, NULL,      0.0036),
	(20932, 4823, '2026-06-14 21:38:17', 7711, 10,  0, 'skipped', 0),
	(20934, 4825, '2026-06-15 00:53:19', 7714, 233, 1, NULL,      0.0036),
	(20935, 4825, '2026-06-21 00:15:47', 7714, 233, 1, 'saved',   0.0036),
	(20936, 4827, '2026-06-26 16:41:48', NULL, 254, 1, NULL,      0.003),
	(20932, 4829, '2026-06-28 06:05:04', 7711, 189, 1, NULL,      0.003),
	(20934, 4825, '2026-06-29 07:30:15', 7714, 233, 1, 'saved',   0.0036),
	(20934, 4825, '2026-06-30 23:59:39', 7714, 188, 0, 'saved',   0.0036),
	(20936, 4827, '2026-07-07 11:50:35', NULL, 254, 1, NULL,      0.003),
	(20936, 4824, '2026-07-09 01:21:31', 7716, 151, 0, 'saved',   0.0032),
	(20936, 4823, '2026-07-20 23:26:48', 7716, 205, 1, NULL,      0.0032),
	(20935, 4828, '2026-07-26 09:03:48', 7715, 221, 1, NULL,      0.003),
	(20931, 4817, '2026-08-02 21:47:05', 7710, 214, 1, 'saved',   0.004),
	(20935, 4826, '2026-08-04 21:19:42', 7715, 104, 0, NULL,      0.0036),
	(20931, 4817, '2026-08-05 18:27:34', 7710, 20,  0, 'skipped', 0),
	(20931, 4817, '2026-08-09 15:06:38', 7710, 214, 1, 'saved',   0.004),
	(20937, 4829, '2026-08-19 13:32:05', 7717, 189, 1, NULL,      0.003),
	(20938, 4817, '2026-08-23 13:07:35', 7710, 214, 1, NULL,      0.004),
	(20938, 4829, '2026-08-25 23:34:24', NULL, 189, 1, NULL,      0.003),
	(20938, 4817, '2026-08-27 15:19:13', 7710, 210, 0, 'saved',   0.004),
	(20938, 4824, '2026-08-29 06:44:37', NULL, 14,  0, 'skipped', 0);
