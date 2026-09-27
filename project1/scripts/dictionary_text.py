"""Prose for docs/DATA_DICTIONARY.md. Edit here, then run scripts/build_dictionary.py.

Types, byte counts and example values are NOT written here: the builder reads them
from the requirements analysis and data.xlsx so they cannot drift. Each column has
  why  - why its type is the smallest correct one (the parsimony argument)
  what - what the column holds and what would break without it
"""

INTRO = """Every one of the 59 columns in CROSSFADE's ten tables. Each entity opens with a table of its columns, types and the extreme values found in `data.xlsx`. Each column then leads with its type and values, says why that type is the smallest correct choice, and then what the column holds.

Types come from the requirements analysis and values from `data.xlsx`, both read by `scripts/build_dictionary.py` when it writes this page. Byte counts are the Unit 4 figures; DECIMAL, BIT and ENUM follow the MySQL manual, and string sizes assume one byte per character. Rule numbers (I1 to I6) refer to the Integrity rules table in the requirements analysis. *Derived* marks a column computed from other data; in `data.xlsx` its header is italic and carries a note saying how."""

ENTITIES = [
("Artist", "entity",
 "The party that uploads recordings and gets paid for them. Every column here serves either identity or royalties.", [
 ("Artist ID",
  "Three bytes cover 16.7 million artists. Independent artists number in the millions, not billions, so INT's fourth byte would never be used.",
  "Identifies the artist so tracks and royalty records can point to one row."),
 ("Stage Name",
  "Length varies by artist, so VARCHAR, which stores only the characters used plus one byte. 64 is a policy ceiling on input, not an allocation.",
  "The public name listeners see. Unique so two artists are never confused on a station, a share link or a royalty statement."),
 ("Country",
  "Every value is exactly two letters (an ISO 3166-1 code), so CHAR(2). VARCHAR(2) would spend a length byte on every row to record a length that never changes: the same point as the Unit 4 phone-number feedback.",
  "Decides which payment channels and tax treatment apply to royalties. A controlled code, not free text. Optional because an artist may register before supplying it."),
 ("Joined Date",
  "A calendar day with no time of day: DATE, 3 bytes. DATETIME would spend 5 more bytes on a time nobody uses.",
  "The day the direct streaming licence took effect. Nothing the artist uploads can be released before it."),
 ("Payout Rate",
  "Money must be exact, so DECIMAL, never FLOAT. Per-stream rates are fractions of a cent quoted to five decimals (for example 0.00318 USD), so five places after the point and none before: 3 bytes.",
  "The price paid per qualifying stream. It is copied into every Play's Royalty Amount."),
 ("Verified",
  "A yes/no flag: BIT(1), one byte, the smallest type that holds a boolean.",
  "Whether the service has confirmed the artist's identity and right to license the material. It works alongside Audio Checksum to guard against people uploading work that is not theirs."),
]),
("Track", "entity",
 "One uploaded recording. The table holds facts about the audio, never the audio itself. The file lives in an object store under a key computed from Track ID, so no column stores its location.", [
 ("Track ID",
  "The catalogue can pass MEDIUMINT's 16.7 million recordings, so INT UNSIGNED (4 bytes, 4.29 billion). Unsigned because an identifier is never negative, which doubles the range at no cost.",
  "Identifies the recording across scores and plays."),
 ("Artist ID",
  "A foreign key must have exactly the type of the key it references: Artist.Artist ID is MEDIUMINT UNSIGNED.",
  "The one artist who uploaded the track and is paid for it. Non-identifying: the track has its own ID, so the artist is an attribute of it, not part of its key."),
 ("Title",
  "Length varies widely, so VARCHAR. 128 is a policy ceiling for long titles; the row stores only the characters used.",
  "What listeners see. Deliberately not unique, because two artists can release songs with the same name."),
 ("Duration",
  "Whole seconds from a few seconds to well past an hour. TINYINT stops at 255 seconds (4 min 15 s), too short; SMALLINT UNSIGNED reaches 65,535 seconds (18 hours) in 2 bytes.",
  "Length in whole seconds. A play is complete when Seconds Played equals it, and it caps Seconds Played. It also lets a station estimate running time."),
 ("Release Date",
  "A calendar day: DATE, 3 bytes.",
  "When listeners can first see the track. It cannot precede the artist's Joined Date or the track's first score, since a track is only streamable once scored."),
 ("Audio Checksum",
  "A SHA-256 digest is always exactly 32 bytes, so BINARY(32). Stored as text it would take 64 hex characters, twice the space.",
  "The digest of the audio file. Duplicate detection: identical files give identical hashes, and because the column is UNIQUE the database rejects a second upload of the same file by itself, which also blocks re-uploading someone else's track to collect its royalties. Integrity: if the stored file is later replaced or corrupted, re-hashing no longer matches, so its scores and royalties are shown to point at different audio. Limit: it catches only byte-identical copies; a re-encoded copy needs audio fingerprinting, which is out of scope. It is kept, unlike the removed location key, because it cannot be computed without reading the file."),
 ("Ingest Status",
  "A closed list of three states the service defines: ENUM, one byte, and the database rejects any other value.",
  "Where the track is in the upload pipeline. It may read scored only if a Track Score exists (I5). Rejected tracks stay on record rather than vanishing, so the rejection is auditable."),
]),
("Genre", "entity",
 "The ten fixed categories. They are the coordinate system for both model output and listener blends.", [
 ("Genre ID",
  "Ten values (0 to 9): TINYINT UNSIGNED, one byte, the smallest integer type.",
  "Equal to the class index the models output (0 blues through 9 rock), so a prediction is stored with no translation step. Fixed by the design, not generated, so it never drifts from the models' output order."),
 ("Name",
  "The ten names are fixed by the models' output classes; the longest, classical, has nine characters, so VARCHAR(9) is exact. Lengths vary (3 to 9), so VARCHAR rather than CHAR(9), which would pad pop to nine characters.",
  "The label listeners see. Unique so a blend can never name two different genres the same way."),
 ("Description",
  "Display text of varying length: VARCHAR, kept to one 80-character line.",
  "A short account of the genre, shown while a listener composes a blend. Optional because it is presentation, not identity."),
]),
("Listener", "entity",
 "A subscriber. The columns cover sign-in, billing and how the listener appears to others.", [
 ("Listener ID",
  "Subscribers can pass 16.7 million, so INT UNSIGNED, 4 bytes.",
  "Ties stations and play history to one subscriber."),
 ("Email",
  "Length varies, so VARCHAR. 254 characters is the longest address the email standard allows, so no valid address is refused and none is truncated.",
  "Sign-in, account recovery and billing mail. Unique so one address is one account."),
 ("Display Name",
  "Short text of varying length: VARCHAR with a 32-character policy ceiling.",
  "The name shown when a listener's station is shared. Not unique, and it keeps the email private."),
 ("Plan Tier",
  "Three tiers the service defines: ENUM, one byte. Text would cost up to nine bytes and accept typos that change someone's bill.",
  "Free, standard or premium: sets the monthly charge and the limits on station creation and offline listening."),
 ("Signup Date",
  "A calendar day: DATE, 3 bytes.",
  "Anchors the monthly billing cycle. No station or play by the listener can predate it."),
]),
("Scoring Model", "entity",
 "One deployed version of the genre classifier. Its columns record what makes versions differ, so their disagreement can be read as a signal rather than noise.", [
 ("Model ID",
  "Deployed versions number in the tens: TINYINT UNSIGNED (up to 255) in one byte. It is repeated on every score and every probability row, so each byte saved here is saved hundreds of times over.",
  "Assigned in deployment order from 1 and carried on every score, so no result is ever separated from the model that produced it. Fixed by the design, like Genre ID."),
 ("Version Label",
  "Short text of varying length: VARCHAR with a 32-character ceiling.",
  "The human-readable release name, used in reports."),
 ("Fusion Type",
  "Two architectures, concat and gated: ENUM, one byte.",
  "How the model joins its spectrogram branch and its tabular branch. A principal architectural difference, and one reason two versions place a track differently."),
 ("Embedding Dimension",
  "Widths such as 384, 512 and 768 exceed TINYINT's 255, so SMALLINT UNSIGNED, 2 bytes.",
  "The width of the representation the model produces. Vectors of different widths are not comparable, so this tells the vector store which space a representation lives in."),
 ("Segment Length",
  "Seconds per audio window, 3 or 30: TINYINT UNSIGNED, one byte.",
  "The audio window scored at a time. Short windows show a track changing character partway through, which is what Segment Variance measures."),
 ("Training Corpus",
  "Dataset names are short identifiers of varying length (GTZAN is 5): VARCHAR(16).",
  "The labelled dataset the version learned from. Recorded so results from differently trained models are never silently compared."),
 ("Holdout Accuracy",
  "A proportion from 0 to 1 to four decimals. DECIMAL(5,4) rather than DECIMAL(4,4), because 1.0000 is a legitimate accuracy and DECIMAL(4,4) stops at 0.9999; exact, unlike FLOAT.",
  "The share of held-out recordings the version classified correctly. It sets how much weight that version's output carries in a blended placement."),
 ("Deployed On",
  "A calendar day: DATE, 3 bytes.",
  "The day the version began scoring uploads. No score can predate it, and it shows which results came before a redeployment."),
]),
("Station", "entity",
 "A saved description of a region of genre space, not a fixed playlist. Its contents change as the catalogue grows.", [
 ("Station ID",
  "Every listener can save several stations, so the count can pass 16.7 million: INT UNSIGNED, 4 bytes.",
  "Lets a play record which station surfaced it."),
 ("Listener ID",
  "Matches Listener.Listener ID, INT UNSIGNED.",
  "The creator, whose library the station belongs to. Stations can be shared, so this need not match the listener on a play the station surfaces (I6)."),
 ("Model ID",
  "Matches Scoring Model.Model ID, TINYINT UNSIGNED.",
  "The one model version the station is matched against. A station keeps its meaning when a new version is deployed, because it keeps reading the same model's scores."),
 ("Name",
  "Short text of varying length: VARCHAR with a 64-character policy ceiling.",
  "Shown in the library and the share link. Not unique: two listeners can both call a station Chill."),
 ("Minimum Ambiguity",
  "A threshold from 0 to 1 that listeners set in hundredths: DECIMAL(3,2), 2 bytes, which can hold 1.00.",
  "The lowest Posterior Entropy a track may have to qualify. Raising it excludes tracks that sit squarely inside one genre, which is the between-genres idea itself."),
 ("Maximum Ambiguity",
  "Same scale as the minimum: DECIMAL(3,2), 2 bytes.",
  "The highest Posterior Entropy allowed. Lowering it excludes tracks the model cannot place at all. It may not be below the minimum (I4)."),
 ("Created On",
  "A calendar day: DATE, 3 bytes.",
  "Orders the library and measures how long a station stays in use. No play credited to the station can predate it."),
]),
("Track Score", "associative entity",
 "The result of one model scoring one track, and the parent of that result's ten Genre Probability rows. The model's vector for the track lives in a vector store under a key computed from Track ID and Model ID, so no column stores it. Four columns are derived from the ten probability rows and stored so stations can filter without reading ten rows per track (I3).", [
 ("Track ID",
  "Matches Track.Track ID, INT UNSIGNED.",
  "Half of the key: the track that was scored."),
 ("Model ID",
  "Matches Scoring Model.Model ID, TINYINT UNSIGNED.",
  "The other half. Together they allow one result per track per model. A rescore by the same version replaces it; a retrained model gets a new Model ID instead."),
 ("Genre ID",
  "Matches Genre.Genre ID, TINYINT UNSIGNED. Stored though derived: one byte lets a station find tracks by top genre without reading ten probability rows.",
  "The genre the model ranked first: the one with the highest probability. Not in the key, because the pair of track and model already determines it."),
 ("Top Probability",
  "A probability to four decimals that can reach 1.0000: DECIMAL(5,4), 3 bytes, exact. Stored though derived, for the same filtering reason.",
  "How confident that single placement is: the largest of the ten probabilities."),
 ("Posterior Entropy",
  "Normalised to 0 to 1, and 1.0000 is reachable (a perfectly even distribution): DECIMAL(5,4), 3 bytes. Stored though derived, because stations filter on it and recomputing it would mean reading and aggregating ten rows per track per query.",
  "How spread the distribution is: Shannon entropy divided by its maximum. This is the ambiguity stations filter on, the core number of the business."),
 ("Model Divergence",
  "Base-2 Jensen-Shannon divergence is bounded by 0 and 1: DECIMAL(5,4), 3 bytes. Optional (NULL) rather than 0 when only one model has scored the track, because 0 would falsely claim agreement.",
  "How far this model's distribution sits from the other models' for the same track: the mean pairwise divergence. Recomputed for all of a track's results whenever any model scores it."),
 ("Segment Variance",
  "The variance of a proportion never exceeds 0.25, so no digit is needed before the point: DECIMAL(4,4), 2 bytes, one byte less than DECIMAL(5,4).",
  "How much the top probability moves between audio windows. It flags tracks that change character partway through. Not derived from stored data: it is measured at scoring time, because per-window output is not stored."),
 ("Scored On",
  "A moment, not just a day, because several runs can happen on one date: DATETIME. TIMESTAMP would save bytes but ends on 2038-01-19. The slides give 8 bytes; MySQL 5.6.4 and later stores DATETIME in 5, one more than TIMESTAMP.",
  "When the scoring run finished. It shows which results predate a redeployment and must be recomputed, and it cannot predate the model's Deployed On."),
]),
("Genre Probability", "associative entity",
 "The full distribution behind each Track Score: ten rows per result, one per genre. This is the table with the most rows per upload (ten per score), so its 9-byte row is kept as small as the types allow. Without it a station asking for 60% jazz and 40% hip hop would have nothing to match against.", [
 ("Track ID",
  "Matches Track Score.Track ID, INT UNSIGNED.",
  "With Model ID it names the parent result. The pair points at Track Score, not at Track and Scoring Model separately, so a probability can only exist for a pair that has actually been scored."),
 ("Model ID",
  "Matches Track Score.Model ID, TINYINT UNSIGNED.",
  "The model that produced the distribution."),
 ("Genre ID",
  "Matches Genre.Genre ID, TINYINT UNSIGNED.",
  "The genre this probability belongs to. As the last part of the key, it allows exactly one probability per genre per result, which makes the ten-row rule checkable (I2)."),
 ("Probability",
  "A probability to four decimals that can reach 1.0000: DECIMAL(5,4), 3 bytes. DECIMAL(4,4) would save a byte but could not store a certain prediction; FLOAT would save none (4 bytes) and would not add up exactly.",
  "The model's probability for this genre. A result's ten probabilities sum to 1 within 0.0010, the rounding allowance for four decimal places. Every derived column on Track Score is computed from these."),
]),
("Station Blend", "associative entity",
 "The genre mix a station asks for, one row per genre. A single text field such as \"jazz 0.6, hiphop 0.4\" would put several values in one cell and break first normal form.", [
 ("Station ID",
  "Matches Station.Station ID, INT UNSIGNED.",
  "The station whose blend this row belongs to."),
 ("Genre ID",
  "Matches Genre.Genre ID, TINYINT UNSIGNED.",
  "The genre being weighted. With Station ID it allows one weight per genre per station, so one weight can change without rewriting the rest."),
 ("Weight",
  "A share in hundredths that can be 1.00 for a single-genre station: DECIMAL(3,2), 2 bytes.",
  "The genre's share of the blend, above 0 and at most 1. A station's weights sum to exactly 1.00 and it has at least one row (I1). Weights are in hundredths, so a three-way blend is 0.34, 0.33 and 0.33, never three equal thirds."),
]),
("Play", "associative entity",
 "One streaming event, and the fastest-growing table: every stream adds a row. It is both the taste signal for the listener and the billable event for the artist.", [
 ("Listener ID",
  "Matches Listener.Listener ID, INT UNSIGNED.",
  "Who streamed."),
 ("Track ID",
  "Matches Track.Track ID, INT UNSIGNED.",
  "What was streamed."),
 ("Played At",
  "A moment to the second: DATETIME. This is the one knowing trade of bytes for correctness. TIMESTAMP is smaller (4 bytes) and Played At is in the key of the largest table, but TIMESTAMP ends on 2038-01-19 and a play after that must still be payable. The slides give DATETIME 8 bytes; MySQL 5.6.4 and later stores it in 5, so the real cost is one byte per play.",
  "When the stream began. A listener replays tracks, so the two foreign keys alone cannot identify a play; the start time completes the key, like a weak entity's partial key. It also orders listening history, assigns the play to a billing period, and exposes a duplicated event, which is how double-counted royalties get caught."),
 ("Station ID",
  "Matches Station.Station ID, INT UNSIGNED. Optional (NULL) when no station was involved.",
  "The station that surfaced the play, credited in station analytics. Empty when the listener picked the track directly, which is why it cannot be in the key. It may be another listener's shared station (I6)."),
 ("Seconds Played",
  "Same scale as Duration, which caps it: SMALLINT UNSIGNED, 2 bytes.",
  "How much was actually heard. It decides whether the play earns royalty (30 seconds or more) and how strong a taste signal it is."),
 ("Completed",
  "A yes/no flag: BIT(1), one byte. Derived from Seconds Played and the track's Duration, and stored because the one byte saves a join to Track every time listening history is filtered to finished plays.",
  "Whether the listener reached the end, separating a genuine listen from an abandoned one. True exactly when Seconds Played equals the track's Duration."),
 ("Reaction",
  "Two explicit signals the service defines: ENUM, one byte, NULL when the listener gave none.",
  "A saved or skipped, a stronger taste signal than duration alone."),
 ("Royalty Amount",
  "Money to five decimals, the same scale as Payout Rate: DECIMAL(5,5), 3 bytes, exact. A snapshot rather than a derived value: it copies the rate in force at play time, so it cannot be recomputed later if the rate changes.",
  "The money owed to the artist for this play: the artist's Payout Rate for a qualifying play, zero otherwise. A later rate change never rewrites the royalty ledger."),
]),
]

DERIVED = {("Track Score", "Genre ID"), ("Track Score", "Top Probability"), ("Track Score", "Posterior Entropy"),
           ("Track Score", "Model Divergence"), ("Play", "Completed")}
SNAPSHOT = {("Play", "Royalty Amount")}

PATTERNS = """## Patterns that recur

Five design choices explain most of the columns above.

- **Two kinds of key.** Entities have single integer keys; Genre ID and Model ID are fixed by the design, the other four are generated. Associative entities have composite keys made of the keys they connect, per the professor's feedback.
- **Stored but derived.** Genre ID, Top Probability, Posterior Entropy and Model Divergence on Track Score repeat what Genre Probability already implies, and Completed on Play repeats what Seconds Played and Duration imply. They are stored for fast filtering, written only by the procedure that computes them, and marked in `data.xlsx` (I3).
- **Snapshots.** Royalty Amount copies the rate at the time of the play. History must stay fixed even when the source value later changes.
- **Payloads live elsewhere, and so do their addresses.** Audio files and model vectors sit in an object store and a vector store. Their keys are computed from primary keys already in the tables, so storing them would add bytes and a chance to disagree. Audio Checksum stays, because it cannot be computed without reading the file.
- **Exact, bounded types.** Fractions use DECIMAL, never FLOAT. Strings are CHAR or BINARY when every value has the same length, VARCHAR otherwise. Identifiers are unsigned integers sized to the largest count each can reach."""

PARSIMONY = """## Data types and parsimony

Unit 4's rule for SQL types is "allocate just the space required". Every column was sized against that rule, against the Unit 4 assignment feedback (a value that always has the same length is CHAR, not VARCHAR), and against the values in `data.xlsx`.

- **Integers** are unsigned and sized to the largest count they can reach: TINYINT for genres and model versions, SMALLINT for seconds and embedding widths, MEDIUMINT for artists, INT for tracks, listeners and stations.
- **Fractions** are DECIMAL with exactly the digits the value needs. A leading digit is kept only where 1 is a legitimate value.
- **Fixed-length values are CHAR or BINARY**: Country, Audio Checksum.
- **Closed sets the service owns are ENUM**, one byte: Ingest Status, Plan Tier, Fusion Type, Reaction.
- **Free text people type** gets a VARCHAR ceiling set by policy or standard. VARCHAR stores only the characters used plus one length byte, so the ceiling limits input without costing space.
- **Values computable from the key are not stored.** The audio's object-store key and the model vector's key were removed in mk11.
- **Two knowing exceptions:** the five stored-but-derived columns, which save aggregation or a join on every filtering query, and DATETIME for Played At and Scored On, which survives 2038 at one extra byte (MySQL 5.6.4+)."""
