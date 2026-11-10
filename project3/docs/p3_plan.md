# CROSSFADE · Project 3 plan (NoSQL Database)

INFO 579, Fall 2026 · info579_group_1 (Herling, Nathan; Pabari, Nidhi Nilesh) · due **Dec 13, 2026, 11:59 PM**
Status: **planning** (Nov 10, 2026). Nothing graded has been written yet; this is the map we build against.

## 1. What the brief asks

Migrate part of the Project 1 database to MongoDB and query it. Four tasks, 25% each, zipped as `project03_info579_group_1.zip`:

| Task | Deliverable | Requirement |
|---|---|---|
| 1 | `collection.json`, `collection.pdf` | An aggregate boundary over at least 3 related tables, denormalized into one collection of at least 5 documents. Every document and subdocument keeps all of its table's fields and primary keys; foreign keys are dropped. Stored as valid BSON (Extended JSON). `collection.pdf` is a short paragraph on why this boundary fits the business plan. |
| 2 | `collection_creation.js` | The MongoDB statements that create the collection, in one script. |
| 3 | `find_queries.js` | 5 to 7 `find` queries, each with a filter **and** a projection. Coverage: (a) `$regex`, (b) `$elemMatch`, (c) a query on embedded documents, (d) positional `$` returning the matching array element, (e) `$nor`. |
| 4 | `aggregate_pipelines.js` | 5 to 7 pipelines with at least 2 stages each, not counting `$limit`, `$skip` or `$sort`. Coverage: (a) `$unwind`, (b) `$group` with accumulators, (c) `$group` with `$push`, (d) `$project` with `$filter` on an array, (e) `$project` that reshapes the output. |

Every command is preceded by a comment that justifies it within the application; trivial or generic queries are marked down. Late work is capped at 70%.

The brief says to upload to "the assignment of project 1 Dropbox"; this looks like a copy-paste slip, so check the D2L assignment name before submitting.

## 2. Aggregate boundary: one document per track

**"Related" means joined by foreign keys in the Project 1 schema.** Every table in the boundary must reach the others through FK → PK links (the lines in the physical data model); denormalizing turns those joins into nesting.

Six tables, all reachable from `track`:

| Table | Joined by (crossfade_schema.sql) | Cardinality | Becomes |
|---|---|---|---|
| `track` | root | — | the document, `_id` = `track_id` |
| `artist` | `track.artist_id` → `artist.artist_id` (`fk_track_artist`) | N tracks : 1 artist | `artist{}` |
| `track_score` | `track_score.track_id` → `track.track_id` (`fk_track_score_track`) | 1 track : N scores | `scores[]` |
| `scoring_model` | `track_score.model_id` → `scoring_model.model_id` (`fk_track_score_scoring_model`) | N scores : 1 model | `scores[].model{}` |
| `genre_probability` | `(track_id, model_id)` → `track_score` (`fk_genre_probability_track_score`, composite) | 1 score : 10 probabilities | `scores[].probabilities[]` |
| `genre` | `track_score.genre_id` → `genre` (`fk_track_score_genre`) and `genre_probability.genre_id` → `genre` (`fk_genre_probability_genre`) | N : 1, joined twice | `scores[].top_genre{}` and `scores[].probabilities[].genre{}` |

Core chain (`track` → `track_score` → `genre_probability`) becomes nested arrays; the three reference tables are embedded as subdocuments.

```js
{ _id: 4818,                                   // track_id
  title, duration, release_date: Date, audio_checksum: BinData, ingest_status,
  artist: { artist_id, stage_name, country, joined_date: Date, payout_rate: Decimal128, verified: bool },
  scores: [{
    model:     { model_id, version_label, fusion_type, embedding_dimension, segment_length,
                 training_corpus, holdout_accuracy: Decimal128, deployed_on: Date },
    top_genre: { genre_id, name, description },
    top_probability, posterior_entropy, model_divergence, segment_variance,   // Decimal128
    scored_on: Date,
    probabilities: [ { genre: { genre_id, name, description }, probability: Decimal128 } ×10 ]
  }] }
```

A full example built from the real rows is `project3/design/example_document_4818.json` (`python project3/scripts/build_example_document.py`).

### Keys

| Project 1 column | Role | In MongoDB |
|---|---|---|
| `track.track_id` | PK | `_id` |
| `track.artist_id` | FK | dropped; `artist{}.artist_id` is the artist's own PK |
| `track_score.track_id` | PK·FK | dropped; implied by the parent document |
| `track_score.model_id` | PK·FK | dropped; `scores[].model.model_id` |
| `track_score.genre_id` | FK | dropped; `scores[].top_genre.genre_id` |
| `genre_probability.(track_id, model_id)` | PK·FK | dropped; implied by the enclosing score |
| `genre_probability.genre_id` | PK·FK | dropped; `probabilities[].genre.genre_id` |

### Why this boundary

- At ingest a track is written once with all its scores; station matching then reads a track together with its score under the station's model. One document read, no joins.
- `genre` (10 rows) and `scoring_model` (5 rows) are fixed reference tables that are never updated, so copying them into every document is safe.
- The aggregate is bounded: a track is scored by a handful of models, and each score has exactly 10 probabilities.

### What stays outside

- `play`: one row per listen, growing forever. Embedding it would be the unbounded-array anti-pattern.
- `listener`, `station`, `station_blend`: reached through the listener, and only joined to `track` through `play`. They belong to a separate, listener-centred aggregate.
- Rows that no track uses drop out: artist 1049 (Kestrel Ave, no tracks) and scoring model 3 (`beardown_rrm_cfg17`, scored nothing).

### Size and types

15 documents, 27 embedded scores, 270 probability subdocuments. Tracks 4830 (awaiting scoring) and 4831 (rejected) have an empty `scores` array. BSON types follow the Project 1 column types: DECIMAL → Decimal128 (scale kept), DATE/DATETIME → Date, BINARY(32) → BinData, BIT(1) → boolean. `collection_creation.js` will create the collection with a `$jsonSchema` validator carrying the Project 1 CHECK constraints and ENUMs, insert the documents and create indexes.

## 3. Draft queries

Expected hits are worked out from the Project 1 sample data. Thresholds may still move.

### find (Task 3)

| ID | Use case | Filter → projection | Expected | Covers |
|---|---|---|---|---|
| F1 | Catalogue search box | `title` or `artist.stage_name` matches `/static/i` → title, stage name | 4817, 4818, 4821 | (a) `$regex`, (c) |
| F2 | Station candidates: genuinely between genres under the station's model | `scores` `$elemMatch` {`model.version_label`: `beardown_rrm`, `posterior_entropy` ≥ 0.6} → title, `scores.$` | 4825, 4826 (that score only) | (b) `$elemMatch`, (d) `$` |
| F3 | Jazz–hip-hop crossovers | `scores` `$elemMatch` {`probabilities` `$elemMatch` {`genre.name`: hiphop, `probability` ≥ 0.30}} → title, artist | 4817 | (b) nested `$elemMatch` |
| F4 | Payout console: verified artists in given countries | `artist.verified`: true, `artist.country` in [GB, DE] → stage name, payout rate, title | 4819, 4820, 4827, 4828 | (c) embedded |
| F5 | Featured shelf: nothing rejected, unscored or from an unverified artist | `$nor` [rejected, awaiting scoring, `artist.verified`: false] → title, stage name | 10 tracks | (e) `$nor`, (c) |
| F6 | Scoring backlog | `scores` `$size` 0 → title, `ingest_status` | 4830, 4831 | — |

### aggregate (Task 4)

| ID | Use case | Stages | Expected | Covers |
|---|---|---|---|---|
| A1 | Compare BEARDOWN versions | `$unwind` scores → `$group` by model: count, `$avg` entropy, `$avg` top probability, `$first` holdout accuracy | 4 models (model 3 scored nothing) | (a), (b) |
| A2 | Genre shelves | `$unwind` → `$match` `beardown_rrm` → `$group` by top genre, `$push` title | 8 shelves, 10 tracks | (a), (c) `$push` |
| A3 | Genre "fingerprint" chips | `$match` scored → `$project` with `$map` over scores and `$filter` probabilities ≥ 0.10 | 13 tracks | (d) `$filter` |
| A4 | Artist-facing track card | `$match` scored → `$project` reshape: artist, track, minutes, models scored, release month | 13 cards | (e) reshape |
| A5 | Review queue: models disagree on the top genre | `$unwind` → `$group` by track, `$addToSet` top genre, `$max` divergence → `$match` more than one genre | 4818, 4821, 4828 | (a), (b) |
| A6 | Artists whose tracks sit most between genres | `$unwind` → `$group` by artist, `$avg` entropy, `$addToSet` titles → `$project` reshape | 7 artists | (b), (e) |

Every requirement letter is covered at least twice except find (d) and (e), each covered once; we can add a second if wanted.

## 4. Unit tests (our own QC; the brief does not ask for them)

pytest + pymongo against a real `mongod`. The expected answers are computed **separately, straight from data.xlsx** (plain Python, no MongoDB), so a failing test means a migration bug or a query bug.

1. **collection.json**: parses as Extended JSON; 15 documents; every column of the 6 tables present with the right BSON type; no FK fields remain; every value equals data.xlsx.
2. **collection_creation.js**: runs in `mongosh` on an empty database and produces exactly collection.json; the validator rejects bad documents (probability 1.2, an unknown `ingest_status`); the indexes exist.
3. **find_queries.js / aggregate_pipelines.js**: a mongosh shim wraps `find` and `aggregate`, recording each call's filter, projection or pipeline and its result as JSON. Python checks each result against the data.xlsx answer and checks the rubric: (a)–(e) covered, filter and projection present, at least 2 counted stages, 5–7 commands per file.
4. **Static**: every command preceded by a comment carrying a test-sync tag (`// F2 · UC-…`).
5. **Planted bugs** (as in Project 2): break each file one way at a time and confirm a test that passed now fails.

Running the tests needs MongoDB locally (Docker `mongo:8` or MongoDB Community + mongosh). The build sandbox can't download MongoDB, so test runs happen on the local machine.

## 5. Flair (proposed): a small cluster on Flask, and its conflicts

Not part of the graded zip; it lives in the repo and on the site.

**Two data nodes are not enough on their own.** A replica set of 2 data nodes cannot elect a new primary when one fails (1 of 2 is not a majority). The fix is the arbiter from the Unit 12 slides: 2 data nodes + 1 arbiter. That limit is itself one of the demos.

### One Flask dashboard, two backends

| | What the nodes are | What Flask does | What it proves |
|---|---|---|---|
| Tier 1 | Three real `mongod` processes (node A, node B, arbiter) on local ports, `--replSet rs-crossfade`; Docker optional | **Control panel only**: start/stop nodes, step down the primary, send writes with `w:1` or `w:"majority"`, show `rs.status()` live | MongoDB's own elections, oplog, write concern and rollback |
| Tier 2 | **Flask servers, one per node**, each with its own copy of the documents | **Is the network**: nodes talk over HTTP through a Flask proxy that can cut the link, add delay or drop requests | Multi-primary replication as taught (vector stamps, revisions, conflicts, merges); a simulation, labelled as one |

We do not mimic the replica set in Flask: a Flask copy of elections and rollback would show our own model of MongoDB, not MongoDB. Every scenario page says which tier it runs on.

### Tier 1: real MongoDB replica set, driven from Flask

| Scenario | CROSSFADE story | Shows | Fix |
|---|---|---|---|
| Replication | Insert a new upload on the primary | Write lands in the oplog, appears on the secondary | — |
| Stale read (read-write conflict) | Moderation rejects track 4831; a station reading a delayed secondary (`secondaryDelaySecs`) still serves it | Eventual consistency | `readConcern: "majority"`, read from primary, causally consistent sessions |
| Lost update (write-write conflict) | Two scoring workers read-modify-write track 4830; one model's score disappears | Lost update | Atomic `$push`; optimistic version stamp + conditional update (retry when nothing matched); pessimistic lock field with expiry |
| Failover | Stop node A | Arbiter + node B elect node B; node A rejoins as secondary | — |
| Rollback | With node B stopped, a `w:1` write lands on node A only; stop A, start B (B + arbiter = majority, B elected, takes writes); restart A | Node A rolls back the write it acknowledged | `w: "majority"`: acknowledged writes survive or the client sees a timeout |
| Two nodes, no arbiter | Same failover without the arbiter | No primary, writes stop | Add the arbiter |

No scenario needs a real network split, so Tier 1 runs on plain local `mongod` processes.

### Tier 2: peer-to-peer simulator on Flask servers

MongoDB has one primary per replica set, so multi-primary replication (Unit 11) is simulated, following CouchDB (Unit 12), which is driven entirely over REST.

- **Nodes**: each Flask server (`:5001`, `:5002`) holds its own copy of the `tracks` documents, seeded from `collection.json`, and accepts reads and writes. Every document carries a revision `_rev` and a vector stamp `{a: n, b: m}`.
- **API from the slides**: `GET`/`PUT /tracks/<id>` with `_rev`, and `GET /_changes?since=n`, so the Unit 12 curl commands work almost unchanged. A `PUT` with a stale `_rev` is refused: read again, then write.
- **Replication**: a background loop on each node pulls the other's `_changes`. A stamp ahead on every counter wins outright; stamps ahead on different counters are a conflict: a deterministic winner is kept and the losing revision goes into `_conflicts`.
- **Per-field merges**: a stage-name edit on one node and a `verified` change on the other merge cleanly; two different `title` edits are flagged for a person.
- **Network**: all node-to-node traffic goes through a Flask proxy (`:5000`) that the dashboard can cut (partition), delay or make drop requests, then heal.
- **Tests**: pytest drives several nodes in one process with Flask's `test_client`; scripted orderings make each conflict reproducible. No MongoDB or Docker needed.

Both tiers print status and progress as they run. Tier 1 tests are marked `@pytest.mark.cluster` and skipped when no `mongod` is available; Tier 2 tests run anywhere. Version-stamp, revision and lock fields exist only in the flair, never in `collection.json`.

## 6. Open decisions

1. **Boundary**: six tables, track-centric — agreed Nov 10.
2. **`_id`**: `_id = track_id` alone (lecture: custom identifiers need no extra field), or also keep a literal `track_id` field so a grader sees it?
3. **Flair scope**: Tier 1 only, or Tiers 1 and 2. Either way it runs from one Flask dashboard and stays out of the graded zip.
4. **Project 2 pattern**: carry over the answer key, starter kit and the two PDFs (testing guide, use-case reference)?

## Files

```
project3/
  brief/info579_project03.pdf          the assignment brief
  design/crossfade_p3_aggregate.svg    aggregate-boundary diagram (dark); _light.svg on white
  design/example_document_4818.json    one real document of the proposed collection
  docs/p3_plan.md                      this plan
  scripts/build_aggregate_svg.py       rebuilds both diagrams
  scripts/build_example_document.py    rebuilds the example document from the Project 1 data
  panels/                              the Project 3 pages of the site
  deliverables/  submission/           empty until the graded files exist
```
