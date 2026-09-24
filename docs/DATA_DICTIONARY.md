# CROSSFADE — What every attribute is for

## How to read this

Every one of the 61 columns in CROSSFADE's ten tables, with the job it does and why it is typed or constrained that way. Keys are included, because each key choice answers a design question too.

The schema is the mk6 version: six entities, four associative entities. Each entry says what the column is for first, then what would break without it or with a different design. Rule numbers (I1 to I6) refer to the Integrity rules table in the requirements analysis.

## Artist

The party that uploads recordings and gets paid for them. Every column here serves either identity or royalties.

1. **Artist ID** (PK). Identifies the artist so tracks and royalty records can point to one row. MEDIUMINT UNSIGNED covers 16.7 million artists at three bytes, smaller than INT.
2. **Stage Name** (UNIQUE). The public name listeners see. Unique so two artists are never confused on a station, a share link or a royalty statement.
3. **Country** (optional). Decides which payment channels and tax treatment apply to royalties. Stored as a two-letter ISO code, so it is a controlled value, not free text. Optional because an artist may register before supplying it.
4. **Joined Date**. The day the direct streaming licence took effect. Nothing the artist uploads can be released before it.
5. **Payout Rate**. The price paid per qualifying stream. It is copied into every Play's Royalty Amount. DECIMAL(5,5) stores it exactly to one hundred-thousandth of a dollar, with no float rounding.
6. **Verified**. Whether the service has confirmed the artist's identity and right to license the material. It works alongside Audio Checksum to guard against people uploading work that is not theirs.

## Track

One uploaded recording. The table holds references to the audio, never the audio itself.

1. **Track ID** (PK). Identifies the recording across scores and plays. INT UNSIGNED, because the catalogue can grow past MEDIUMINT's 16.7 million.
2. **Artist ID** (FK to Artist). Names the one artist who uploaded the track and is paid for it. Non-identifying: the track has its own ID, so the artist is an attribute of it, not part of its key.
3. **Title**. What listeners see. Deliberately not unique, because two artists can release songs with the same name.
4. **Duration**. Length in whole seconds. A play is complete when Seconds Played equals it, and it caps Seconds Played. It also lets a station estimate running time.
5. **Release Date**. When listeners can first see the track. It cannot precede the artist's Joined Date or the track's first score, since a track is only streamable once scored.
6. **Audio URI** (UNIQUE). The key of the audio file in the object store. The database stores this pointer, not megabytes of audio. Unique so two rows never claim the same file.
7. **Audio Checksum** (UNIQUE). The SHA-256 digest of the file: 32 bytes, shown as 64 hex characters.
    1. Duplicate detection. Artists upload directly, so the same recording could be uploaded twice, by the same artist or by someone re-uploading another artist's work. Identical files give identical hashes, and because the column is UNIQUE, the database rejects the second upload by itself. That also blocks a simple royalty fraud: re-uploading someone else's track to collect its per-stream payments.
    2. Integrity. Every Track Score describes one specific audio file. If the stored file is later replaced or corrupted, re-hashing it no longer matches the checksum. That shows the file's scores and royalties now point at different audio.
    3. Limit. It catches only byte-identical copies. A re-encoded or trimmed copy hashes differently; catching those needs audio fingerprinting, which is out of scope.
8. **Ingest Status**. Where the track is in the upload pipeline: awaiting scoring, scored or rejected. It may read scored only if a Track Score exists (I5). Rejected tracks stay on record rather than vanishing, so the rejection is auditable.

## Genre

The ten fixed categories. They are the coordinate system for both model output and listener blends.

1. **Genre ID** (PK). Equal to the class index the models output (0 blues through 9 rock). A prediction is therefore stored with no translation step. The value is fixed by the design, not generated, so it never drifts from the model's output order.
2. **Name** (UNIQUE). The label listeners see, such as jazz. Unique so a blend can never name two different genres the same way.
3. **Description** (optional). A short account of the genre, shown while a listener composes a blend. Optional because it is presentation, not identity.

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
2. **Version Label** (UNIQUE). The human-readable release name, used in reports and in each Embedding Reference key.
3. **Fusion Type**. How the model joins its spectrogram branch and its tabular branch: concat or gated. It is a principal architectural difference, and one reason two versions place a track differently.
4. **Embedding Dimension**. The width of the representation the model produces. Vectors of different widths are not comparable, so this tells the vector store which space a representation lives in.
5. **Segment Length**. The audio window scored at a time: 30 or 3 seconds. Short windows show a track changing character partway through, which is what Segment Variance measures.
6. **Training Corpus**. The labelled dataset the version learned from. Recorded so results from differently trained models are never silently compared.
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

The result of one model scoring one track, and the parent of that result's ten Genre Probability rows. Four of its columns are derived from those rows and stored so stations can filter without reading ten rows per track (I3).

1. **Track ID** (PK, FK to Track). Half of the key: the track that was scored.
2. **Model ID** (PK, FK to Scoring Model). The other half. Together they allow one result per track per model. A rescore by the same version replaces it; a retrained model gets a new Model ID instead.
3. **Genre ID** (FK to Genre, not in the key). The genre the model ranked first. Derived: the genre with the highest probability. Not in the key, because the pair of track and model already determines it.
4. **Top Probability**. How confident that single placement is. Derived: the largest of the ten probabilities.
5. **Posterior Entropy**. How spread the distribution is, scaled to 0 to 1. This is the ambiguity that stations filter on, so it is the core number of the business. Derived from the ten probabilities.
6. **Model Divergence** (optional). How far this model's distribution sits from the other models' for the same track: the mean pairwise Jensen-Shannon divergence. Empty while only one model has scored the track, since 0 would falsely claim agreement. Recomputed for all of a track's results whenever any model scores it.
7. **Segment Variance** (optional). How much the top probability moves between audio windows, capped at 0.25. It flags tracks that change character partway through. Unlike the four above, it is measured at scoring time, because the per-window output is not stored.
8. **Embedding Reference** (UNIQUE). The key of this track's vector in the vector store. The vector is hundreds of numbers, too large and unlike a scalar to belong in a relational table.
9. **Scored On**. When the scoring run finished. It shows which results predate a redeployment and must be recomputed, and it cannot predate the model's Deployed On.

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
- **Pointers, not payloads.** Audio URI and Embedding Reference point to data held elsewhere, and Audio Checksum proves the audio behind the pointer is unchanged. The relational tables hold only what is small and queried.
- **Exact, bounded types.** Fractions use DECIMAL, never FLOAT, so money and probabilities are exact. Moments use DATETIME, because TIMESTAMP ends in January 2038. Identifiers are unsigned integers sized to the largest count each can reach.
