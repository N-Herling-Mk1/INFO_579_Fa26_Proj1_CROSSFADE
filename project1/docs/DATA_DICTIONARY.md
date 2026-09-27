# CROSSFADE — What every attribute is for

## How to read this

Every one of the 59 columns in CROSSFADE's ten tables, with the job it does and why it is typed or constrained that way. Keys are included, because each key choice answers a design question too.

The schema is the mk11 version: six entities, four associative entities. Each entry says what the column is for first, then what would break without it or with a different design. Rule numbers (I1 to I6) refer to the Integrity rules table in the requirements analysis.

## Artist

The party that uploads recordings and gets paid for them. Every column here serves either identity or royalties.

1. **Artist ID** (PK). Identifies the artist so tracks and royalty records can point to one row. MEDIUMINT UNSIGNED covers 16.7 million artists at three bytes, smaller than INT.
2. **Stage Name** (UNIQUE). The public name listeners see. Unique so two artists are never confused on a station, a share link or a royalty statement.
3. **Country** (optional). Decides which payment channels and tax treatment apply to royalties. Stored as a two-letter ISO code, so it is a controlled value, not free text. Optional because an artist may register before supplying it.
4. **Joined Date**. The day the direct streaming licence took effect. Nothing the artist uploads can be released before it.
5. **Payout Rate**. The price paid per qualifying stream. It is copied into every Play's Royalty Amount. DECIMAL(5,5) stores it exactly to one hundred-thousandth of a dollar, with no float rounding.
6. **Verified**. Whether the service has confirmed the artist's identity and right to license the material. It works alongside Audio Checksum to guard against people uploading work that is not theirs.

## Track

One uploaded recording. The table holds facts about the audio, never the audio itself. The file lives in an object store under a key computed from Track ID, so no column stores its location.

1. **Track ID** (PK). Identifies the recording across scores and plays. INT UNSIGNED, because the catalogue can grow past MEDIUMINT's 16.7 million.
2. **Artist ID** (FK to Artist). Names the one artist who uploaded the track and is paid for it. Non-identifying: the track has its own ID, so the artist is an attribute of it, not part of its key.
3. **Title**. What listeners see. Deliberately not unique, because two artists can release songs with the same name.
4. **Duration**. Length in whole seconds. A play is complete when Seconds Played equals it, and it caps Seconds Played. It also lets a station estimate running time.
5. **Release Date**. When listeners can first see the track. It cannot precede the artist's Joined Date or the track's first score, since a track is only streamable once scored.
6. **Audio Checksum** (UNIQUE). The SHA-256 digest of the file: 32 bytes, shown as 64 hex characters.
    1. Duplicate detection. Artists upload directly, so the same recording could be uploaded twice, by the same artist or by someone re-uploading another artist's work. Identical files give identical hashes, and because the column is UNIQUE, the database rejects the second upload by itself. That also blocks a simple royalty fraud: re-uploading someone else's track to collect its per-stream payments.
    2. Integrity. Every Track Score describes one specific audio file. If the stored file is later replaced or corrupted, re-hashing it no longer matches the checksum. That shows the file's scores and royalties now point at different audio.
    3. Limit. It catches only byte-identical copies. A re-encoded or trimmed copy hashes differently; catching those needs audio fingerprinting, which is out of scope.
7. **Ingest Status**. Where the track is in the upload pipeline: awaiting scoring, scored or rejected. It may read scored only if a Track Score exists (I5). Rejected tracks stay on record rather than vanishing, so the rejection is auditable.

## Genre

The ten fixed categories. They are the coordinate system for both model output and listener blends.

1. **Genre ID** (PK). Equal to the class index the models output (0 blues through 9 rock). A prediction is therefore stored with no translation step. The value is fixed by the design, not generated, so it never drifts from the model's output order.
2. **Name** (UNIQUE). The label listeners see, such as jazz. Unique so a blend can never name two different genres the same way. VARCHAR(9): the ten names are fixed by the models' output classes and the longest, classical, has nine characters.
3. **Description** (optional). A short account of the genre, shown while a listener composes a blend. Optional because it is presentation, not identity. VARCHAR(80) keeps it to one line.

## Listener

A subscriber. The columns cover sign-in, billing and how the listener appears to others.

1. **Listener ID** (PK). Ties stations and play history to one subscriber.
2. **Email** (UNIQUE). Sign-in, account recovery and billing mail. Unique so one address is one account. VARCHAR(254) is the longest valid email address.
3. **Display Name**. The name shown when a listener's station is shared. Not unique, and it keeps the email private.
4. **Plan Tier**. Free, standard or premium: sets the monthly charge and the limits on station creation and offline listening. An ENUM, because the set is closed and a typo would change someone's billing.
5. **Signup Date**. Anchors the monthly billing cycle. No station or play by the listener can predate it.

## Scoring Model

One deployed version of the genre classifier. Its columns record what makes versions differ, so their disagreement can be read as a signal rather than noise.

1. **Model ID** (PK). Assigned in deployment order from 1 and carried on every score, so no result is ever separated from the model that produced it. Fixed by the design, like Genre ID.
2. **Version Label** (UNIQUE). The human-readable release name, used in reports.
3. **Fusion Type**. How the model joins its spectrogram branch and its tabular branch: concat or gated. It is a principal architectural difference, and one reason two versions place a track differently.
4. **Embedding Dimension**. The width of the representation the model produces. Vectors of different widths are not comparable, so this tells the vector store which space a representation lives in.
5. **Segment Length**. The audio window scored at a time: 30 or 3 seconds. Short windows show a track changing character partway through, which is what Segment Variance measures.
6. **Training Corpus**. The labelled dataset the version learned from. Recorded so results from differently trained models are never silently compared. VARCHAR(16): corpus names are short identifiers such as GTZAN.
7. **Holdout Accuracy**. The share of held-out recordings the version classified correctly. It sets how much weight that version's output carries in a blended placement.
8. **Deployed On**. The day the version began scoring uploads. No score can predate it, and it shows which results came before a redeployment.

## Station

A saved description of a region of genre space, not a fixed playlist. Its contents change as the catalogue grows.

1. **Station ID** (PK). Lets a play record which station surfaced it.
2. **Listener ID** (FK to Listener). The creator, whose library the station belongs to. Stations can be shared, so this need not match the listener on a play the station surfaces (I6).
3. **Model ID** (FK to Scoring Model). The one model version the station is matched against. A station keeps its meaning when a new version is deployed, because it keeps reading the same model's scores.
4. **Name**. Shown in the library and the share link. Not unique: two listeners can both call a station Chill.
5. **Minimum Ambiguity**. The lowest Posterior Entropy a track may have to qualify. Raising it excludes tracks that sit squarely inside one genre, which is the between-genres idea itself.
6. **Maximum Ambiguity**. The highest Posterior Entropy allowed. Lowering it excludes tracks the model cannot place at all. It may not be below the minimum (I4).
7. **Created On**. Orders the library and measures how long a station stays in use. No play credited to the station can predate it.

## Track Score

The result of one model scoring one track, and the parent of that result's ten Genre Probability rows. The model's vector for the track lives in a vector store under a key computed from Track ID and Model ID, so no column stores it. Four of its columns are derived from those rows and stored so stations can filter without reading ten rows per track (I3).

1. **Track ID** (PK, FK to Track). Half of the key: the track that was scored.
2. **Model ID** (PK, FK to Scoring Model). The other half. Together they allow one result per track per model. A rescore by the same version replaces it; a retrained model gets a new Model ID instead.
3. **Genre ID** (FK to Genre, not in the key). The genre the model ranked first. Derived: the genre with the highest probability. Not in the key, because the pair of track and model already determines it.
4. **Top Probability**. How confident that single placement is. Derived: the largest of the ten probabilities.
5. **Posterior Entropy**. How spread the distribution is, scaled to 0 to 1. This is the ambiguity that stations filter on, so it is the core number of the business. Derived from the ten probabilities.
6. **Model Divergence** (optional). How far this model's distribution sits from the other models' for the same track: the mean pairwise Jensen-Shannon divergence. Empty while only one model has scored the track, since 0 would falsely claim agreement. Recomputed for all of a track's results whenever any model scores it.
7. **Segment Variance** (optional). How much the top probability moves between audio windows, capped at 0.25. It flags tracks that change character partway through. Unlike the four above, it is measured at scoring time, because the per-window output is not stored.
8. **Scored On**. When the scoring run finished. It shows which results predate a redeployment and must be recomputed, and it cannot predate the model's Deployed On.

## Genre Probability

The full distribution behind each Track Score: ten rows per result, one per genre. Without it a station asking for 60% jazz and 40% hip hop would have nothing to match against.

1. **Track ID** (PK, part of a composite FK to Track Score). With Model ID it names the parent result. The pair points at Track Score, not at Track and Scoring Model separately, so a probability can only exist for a pair that has actually been scored.
2. **Model ID** (PK, part of the same composite FK). The model that produced the distribution.
3. **Genre ID** (PK, FK to Genre). The genre this probability belongs to. As the last part of the key, it allows exactly one probability per genre per result, which makes the ten-row rule checkable (I2).
4. **Probability**. The model's probability for this genre, 0 to 1 to four decimals. A result's ten probabilities sum to 1 within 0.0010, the rounding allowance for four decimal places. Every derived column on Track Score is computed from these.

## Station Blend

The genre mix a station asks for, one row per genre. A single text field such as "jazz 0.6, hiphop 0.4" would put several values in one cell and break first normal form.

1. **Station ID** (PK, FK to Station). The station whose blend this row belongs to.
2. **Genre ID** (PK, FK to Genre). The genre being weighted. With Station ID it allows one weight per genre per station, so one weight can change without rewriting the rest.
3. **Weight**. The genre's share of the blend, above 0 and at most 1. A station's weights sum to exactly 1.00 and it has at least one row (I1). Weights are in hundredths, so a three-way blend is 0.34, 0.33 and 0.33, never three equal thirds.

## Play

One streaming event. It does two jobs at once: it is the taste signal for the listener and the billable event for the artist.

1. **Listener ID** (PK, FK to Listener). Who streamed.
2. **Track ID** (PK, FK to Track). What was streamed.
3. **Played At** (PK). When the stream began. A listener replays tracks, so the two foreign keys alone cannot identify a play; the start time completes the key, like a weak entity's partial key. It also orders listening history, assigns the play to a billing period, and exposes a duplicated event, which is how double-counted royalties get caught.
4. **Station ID** (optional, FK to Station). The station that surfaced the play, credited in station analytics. Empty when the listener picked the track directly, which is why it cannot be in the key. It may be another listener's shared station (I6).
5. **Seconds Played**. How much was actually heard. It decides whether the play earns royalty and how strong a taste signal it is. The sample data treats 30 seconds as the qualifying threshold.
6. **Completed**. Whether the listener reached the end, separating a genuine listen from an abandoned one. It is true exactly when Seconds Played equals the track's Duration.
7. **Reaction** (optional). An explicit saved or skipped, a stronger taste signal than duration alone. Empty when the listener gave none.
8. **Royalty Amount**. The money owed to the artist for this play: the artist's Payout Rate at the time, or zero for a non-qualifying play. It is a snapshot, not a lookup, so a later rate change never rewrites the royalty ledger.

## Patterns that recur

Five design choices explain most of the columns above.

- **Two kinds of key.** Entities have single integer keys; Genre ID and Model ID are fixed by the design, the other four are generated. Associative entities have composite keys made of the keys they connect, per the professor's feedback.
- **Stored but derived.** Genre ID, Top Probability, Posterior Entropy and Model Divergence on Track Score repeat what Genre Probability already implies. They are stored for fast filtering and written only by the scoring procedure, so they cannot drift (I3).
- **Snapshots.** Royalty Amount copies the rate at the time of the play. History must stay fixed even when the source value later changes.
- **Payloads live elsewhere, and so do their addresses.** Audio files and model vectors sit in an object store and a vector store. Their keys are computed from primary keys already in the tables, so storing them would add bytes and a chance to disagree. Audio Checksum stays, because it cannot be computed without reading the file.
- **Exact, bounded types.** Fractions use DECIMAL, never FLOAT, so money and probabilities are exact. Strings are CHAR or BINARY when every value has the same length (Country, Audio Checksum), a VARCHAR sized to the longest member of a closed set (Genre Name), and a policy or standard ceiling only for free text people type. Moments use DATETIME, because TIMESTAMP ends in January 2038. Identifiers are unsigned integers sized to the largest count each can reach.

## Data types and parsimony

Unit 4's rule for SQL types is "allocate just the space required". Every column here was sized against that rule, against the Unit 4 assignment feedback (a value that always has the same length is CHAR, not VARCHAR), and against the values in `data.xlsx`.

### The rules applied

- **Integers** are unsigned and sized to the largest count the identifier or quantity can reach: TINYINT for the ten genres and the model versions, SMALLINT for seconds and embedding widths, MEDIUMINT for artists, INT for tracks, listeners and stations.
- **Fractions** are DECIMAL with exactly the digits the value needs. Probabilities, entropy and accuracy are DECIMAL(5,4) rather than DECIMAL(4,4), because 1.0000 is a legitimate value and DECIMAL(4,4) stops at 0.9999. Money is DECIMAL(5,5), because per-stream rates are quoted to five decimals (for example 0.00318 USD).
- **Fixed-length values are CHAR or BINARY**: Country is always two letters, Audio Checksum always 32 bytes. This saves VARCHAR's length byte on every row.
- **Closed sets are ENUM** (one byte) when the service owns the list: Ingest Status, Plan Tier, Fusion Type, Reaction. Genre Name is a VARCHAR(9) instead, because it is the display label of a lookup table, sized to its longest member, classical.
- **Free text people type** (names, titles, email) gets a ceiling set by policy or by the email standard's 254 characters. VARCHAR stores only the characters used plus one length byte, so the ceiling limits input without costing space.
- **Values that can be computed are not stored.** The object-store key of a track's audio and the vector-store key of a model's representation are both built from primary keys. Both columns were removed in mk11.

### Deliberate exceptions

- **Four stored-but-derived columns on Track Score** (Genre ID, Top Probability, Posterior Entropy, Model Divergence) repeat what the ten Genre Probability rows imply. They cost 10 bytes per score. They stay because stations filter on Posterior Entropy: without it every station query would read and aggregate ten rows per track. Unlike the removed keys, they cannot be computed from the primary key alone. Only the scoring procedure writes them (I3).
- **DATETIME, not TIMESTAMP**, for Played At and Scored On. The slides give 8 bytes against 4, and Played At is part of Play's key, the fastest-growing table. TIMESTAMP ends on 2038-01-19, and a play recorded after that must still be payable. MySQL 5.6.4 and later stores DATETIME in 5 bytes, so the real cost is 1 byte per row.

<!-- TYPES:BEGIN -->
### Type reference

Byte counts are the Unit 4 figures; DECIMAL, BIT and ENUM follow the MySQL manual. String sizes assume one byte per character.

| Type | Bytes | Range | Columns using it |
|---|---|---|---|
| TINYINT UNSIGNED | 1 | 0 to 255 | 9 |
| SMALLINT UNSIGNED | 2 | 0 to 65,535 | 3 |
| MEDIUMINT UNSIGNED | 3 | 0 to 16,777,215 | 2 |
| INT UNSIGNED | 4 | 0 to 4,294,967,295 | 10 |
| DECIMAL(M,D) | digits packed 9 per 4 bytes | M digits, D after the point | 11 |
| CHAR(n) | n | exactly n characters | 1 |
| VARCHAR(n) | length + 1 | 0 to n characters | 9 |
| BINARY(n) | n | exactly n bytes | 1 |
| ENUM(...) | 1 | one listed value (up to 255 values) | 4 |
| BIT(1) | 1 | 0 or 1 | 2 |
| DATE | 3 | 1000-01-01 to 9999-12-31 | 5 |
| DATETIME | 8 (slides; 5 in MySQL 5.6.4+) | years 1000 to 9999 | 2 |
| TIMESTAMP (not used) | 4 | 1970-01-01 to 2038-01-19 | 0 |

### Every column

Declared range is what the design allows; typical values are taken from `data.xlsx`.

#### Artist

Row size: 77 bytes at most, about 25 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Artist ID (PK) | MEDIUMINT UNSIGNED | 3 | generated, up to 16,777,215; sample 1042 to 1049 | `1042`, `1046`, `1049` |
| Stage Name | VARCHAR(64) | length + 1 (max 65) | up to 64 characters; sample 10 to 15 characters | `Velvet Static`, `Ochre Parade`, `Kestrel Ave` |
| Country | CHAR(2) | 2 | ISO 3166-1 alpha-2 code; sample always 2 characters | `US`, `AU`, `JM` |
| Joined Date | DATE | 3 | calendar date; sample 2026-01-20 to 2026-08-28 | `2026-03-14`, `2026-04-11`, `2026-08-28` |
| Payout Rate | DECIMAL(5,5) | 3 | 0.00000 to 0.99999 USD; sample 0.00300 to 0.00400 | `0.00400`, `0.00320`, `0.00340` |
| Verified | BIT(1) | 1 | 0 or 1 | `1`, `0` |

#### Track

Row size: 174 bytes at most, about 60 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Track ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 4817 to 4831 | `4817`, `4824`, `4831` |
| Artist ID | MEDIUMINT UNSIGNED | 3 | generated, up to 16,777,215; sample 1042 to 1048 | `1042`, `1045`, `1048` |
| Title | VARCHAR(128) | length + 1 (max 129) | up to 128 characters; sample 5 to 22 characters | `Low Tide Signal`, `Harbour Lights Waltz`, `Untitled Loop 7` |
| Duration | SMALLINT UNSIGNED | 2 | 0 to 65,535 s; sample 48 to 312 | `214`, `176`, `48` |
| Release Date | DATE | 3 | calendar date; sample 2026-02-25 to 2026-09-22 | `2026-04-02`, `2026-05-06`, `2026-09-22` |
| Audio Checksum | BINARY(32) | 32 | 32-byte SHA-256 digest | `0xBD675D48...D8B4`, `0x0648B585...5FE1`, `0x9261DDFA...96F7` |
| Ingest Status | ENUM('awaiting scoring', 'scored', 'rejected') | 1 | one of 3 values | `scored`, `awaiting scoring`, `rejected` |

#### Genre

Row size: 92 bytes at most, about 60 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Genre ID (PK) | TINYINT UNSIGNED | 1 | 0 to 9, one per genre (the models' class index); sample 0 to 9 | `0`, `5`, `9` |
| Name | VARCHAR(9) | length + 1 (max 10) | one of 10 names, longest 'classical' (9); sample 3 to 9 characters | `blues`, `jazz`, `rock` |
| Description | VARCHAR(80) | length + 1 (max 81) | up to 80 characters; sample 40 to 65 characters | `Twelve-bar forms, blue notes and call-and-response phrasing`, `Swing, improvisation and extended harmony`, `Guitar-led songs with a driving backbeat` |

#### Listener

Row size: 296 bytes at most, about 36 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Listener ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 20931 to 20938 | `20931`, `20935`, `20938` |
| Email | VARCHAR(254) | length + 1 (max 255) | up to 254 characters; sample 17 to 23 characters | `j.rivera@example.com`, `tomas.b@example.com`, `h.ito@example.com` |
| Display Name | VARCHAR(32) | length + 1 (max 33) | up to 32 characters; sample 4 to 7 characters | `jrivera`, `tbarros`, `hito` |
| Plan Tier | ENUM('free', 'standard', 'premium') | 1 | one of 3 values | `standard`, `premium`, `free` |
| Signup Date | DATE | 3 | calendar date; sample 2026-04-02 to 2026-08-15 | `2026-05-09`, `2026-06-03`, `2026-08-15` |

#### Scoring Model

Row size: 61 bytes at most, about 32 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Model ID (PK) | TINYINT UNSIGNED | 1 | 1 upward, in deployment order (up to 255); sample 1 to 5 | `1`, `3`, `5` |
| Version Label | VARCHAR(32) | length + 1 (max 33) | up to 32 characters; sample 8 to 18 characters | `beardown`, `beardown_rrm_cfg17`, `beardown_3sec` |
| Fusion Type | ENUM('concat', 'gated') | 1 | one of 2 values | `gated`, `concat` |
| Embedding Dimension | SMALLINT UNSIGNED | 2 | 0 to 65,535; sample 384 to 768 | `512`, `384`, `768` |
| Segment Length | TINYINT UNSIGNED | 1 | 0 to 255 s; sample 3 to 30 | `30`, `3` |
| Training Corpus | VARCHAR(16) | length + 1 (max 17) | up to 16 characters; sample always 5 characters | `GTZAN` |
| Holdout Accuracy | DECIMAL(5,4) | 3 | 0.0000 to 1.0000; sample 0.6800 to 0.7887 | `0.7000`, `0.7600`, `0.7887` |
| Deployed On | DATE | 3 | calendar date; sample 2026-01-12 to 2026-06-23 | `2026-01-12`, `2026-03-09`, `2026-06-23` |

#### Station

Row size: 81 bytes at most, about 30 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Station ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 7710 to 7717 | `7710`, `7714`, `7717` |
| Listener ID | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 20931 to 20937 | `20931`, `20934`, `20937` |
| Model ID | TINYINT UNSIGNED | 1 | 1 upward, in deployment order (up to 255); sample 1 to 5 | `5`, `2`, `1` |
| Name | VARCHAR(64) | length + 1 (max 65) | up to 64 characters; sample 9 to 17 characters | `Late Jazz Hop`, `Harbour Dub`, `Blue Hour` |
| Minimum Ambiguity | DECIMAL(3,2) | 2 | 0.00 to 1.00; sample 0.10 to 0.35 | `0.35`, `0.30`, `0.10` |
| Maximum Ambiguity | DECIMAL(3,2) | 2 | 0.00 to 1.00; sample 0.70 to 0.90 | `0.80`, `0.90`, `0.75` |
| Created On | DATE | 3 | calendar date; sample 2026-05-02 to 2026-08-05 | `2026-08-01`, `2026-06-12`, `2026-08-05` |

#### Track Score

Row size: 25 bytes at most, about 25 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Track ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 4817 to 4829 | `4817`, `4823`, `4829` |
| Model ID (PK) | TINYINT UNSIGNED | 1 | 1 upward, in deployment order (up to 255); sample 1 to 5 | `1`, `4`, `5` |
| Genre ID | TINYINT UNSIGNED | 1 | 0 to 9, one per genre (the models' class index); sample 0 to 8 | `5`, `6`, `3` |
| Top Probability | DECIMAL(5,4) | 3 | 0.0000 to 1.0000; sample 0.4338 to 0.7401 | `0.5438`, `0.6804`, `0.5363` |
| Posterior Entropy | DECIMAL(5,4) | 3 | 0.0000 to 1.0000; sample 0.4114 to 0.6745 | `0.4908`, `0.5081`, `0.4989` |
| Model Divergence | DECIMAL(5,4) | 3 | 0.0000 to 1.0000, or empty; sample 0.0103 to 0.1025 | `0.0124`, `0.1025`, `0.0258` |
| Segment Variance | DECIMAL(4,4) | 2 | 0.0000 to 0.2500; sample 0.0036 to 0.0289 | `0.0243`, `0.0121`, `0.0036` |
| Scored On | DATETIME | 8 (slides; 5 in MySQL 5.6.4+) | date and time; sample 2026-01-21 00:20:40 to 2026-07-15 10:06:28 | `2026-03-15 21:31:57`, `2026-06-26 05:51:40`, `2026-06-09 19:02:52` |

#### Play

Row size: 27 bytes at most, about 27 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Listener ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 20931 to 20938 | `20932`, `20935`, `20938` |
| Track ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 4817 to 4829 | `4820`, `4825`, `4826` |
| Played At (PK) | DATETIME | 8 (slides; 5 in MySQL 5.6.4+) | date and time the stream began; sample 2026-05-18 02:17:16 to 2026-08-29 06:44:37 | `2026-05-18 02:17:16`, `2026-06-28 06:05:04`, `2026-08-29 06:44:37` |
| Station ID | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 7710 to 7717 | `7712`, `7716`, `7717` |
| Seconds Played | SMALLINT UNSIGNED | 2 | 0 to 65,535 s; sample 10 to 312 | `187`, `10`, `14` |
| Completed | BIT(1) | 1 | 0 or 1 | `0`, `1` |
| Reaction | ENUM('saved', 'skipped') | 1 | one of 2 values | `saved`, `skipped` |
| Royalty Amount | DECIMAL(5,5) | 3 | 0.00000 to 0.99999 USD; sample 0.00000 to 0.00400 | `0.00350`, `0.00300`, `0.00360` |

#### Station Blend

Row size: 7 bytes at most, about 7 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Station ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 7710 to 7717 | `7710`, `7714`, `7717` |
| Genre ID (PK) | TINYINT UNSIGNED | 1 | 0 to 9, one per genre (the models' class index); sample 0 to 9 | `4`, `3`, `8` |
| Weight | DECIMAL(3,2) | 2 | 0.01 to 1.00; sample 0.16 to 1.00 | `0.40`, `0.34`, `1.00` |

#### Genre Probability

Row size: 9 bytes at most, about 9 bytes for the sample rows.

| Column | Type | Bytes | Declared range | Typical values |
|---|---|---|---|---|
| Track ID (PK) | INT UNSIGNED | 4 | generated, up to 4,294,967,295; sample 4817 to 4829 | `4817`, `4823`, `4829` |
| Model ID (PK) | TINYINT UNSIGNED | 1 | 1 upward, in deployment order (up to 255); sample 1 to 5 | `1`, `4`, `5` |
| Genre ID (PK) | TINYINT UNSIGNED | 1 | 0 to 9, one per genre (the models' class index); sample 0 to 9 | `0`, `5`, `9` |
| Probability | DECIMAL(5,4) | 3 | 0.0000 to 1.0000; sample 0.0001 to 0.7401 | `0.0482`, `0.7354`, `0.3526` |
<!-- TYPES:END -->
