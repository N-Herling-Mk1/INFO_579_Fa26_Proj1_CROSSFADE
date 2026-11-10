# CROSSFADE, Project 3: NoSQL Database

INFO 579 (SQL/NoSQL Databases), Fall 2026. info579_group_1: Herling, Nathan; Pabari, Nidhi Nilesh. Due **Dec 13, 2026, 11:59 PM**.

**Status: planning** (Nov 10, 2026). The brief has been read, a six-table aggregate boundary is agreed, and the queries, unit tests and a cluster "flair" are drafted. None of the graded files exist yet. The proposed flair runs on one Flask dashboard: a real MongoDB replica set driven from Flask (Tier 1) and Flask servers acting as peer-to-peer nodes (Tier 2). The full plan is [`docs/p3_plan.md`](docs/p3_plan.md); the site pages are under `#p3` on the [CROSSFADE site](https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/#p3).

## Deliverables (zipped as `project03_info579_group_1.zip`)

| Task | File | Status |
|---|---|---|
| 1 | `collection.json`, `collection.pdf` | Boundary agreed; example document built |
| 2 | `collection_creation.js` | Planned |
| 3 | `find_queries.js` | 6 queries drafted |
| 4 | `aggregate_pipelines.js` | 6 pipelines drafted |

Graded files go in `deliverables/`; the submission zip is built from that folder only and lands in `submission/`.

## Aggregate boundary

One document per track. Six tables joined by foreign keys in the Project 1 schema: `track` (root), `track_score` → `scores[]`, `genre_probability` → `scores[].probabilities[]`, plus `artist`, `scoring_model` and `genre` embedded as subdocuments. `play` stays out (it grows with every listen), and with it the listener-side tables. 15 documents, 27 scores, 270 probabilities.

## Layout

```
brief/info579_project03.pdf          the assignment brief
design/crossfade_p3_aggregate.svg    aggregate-boundary diagram (dark); _light.svg on white
design/example_document_4818.json    one real document of the proposed collection (Extended JSON)
docs/p3_plan.md                      the plan: boundary, draft queries, tests, flair, open decisions
scripts/build_aggregate_svg.py       rebuilds both diagrams
scripts/build_example_document.py    rebuilds the example document from the Project 1 data
panels/                              site pages: overview, aggregate, queries, tests, flair, brief
deliverables/  submission/           empty until the graded files exist
index.html                           redirect stub to ../#p3
```

## Rebuilding

From the repository root:

```
python project3/scripts/build_aggregate_svg.py        # both diagrams into project3/design/
python project3/scripts/build_example_document.py     # track 4818; pass another track_id to change it
```

`build_example_document.py` reads `project1/data_export/csv/` (written from the graded data.xlsx by `tools/export_p1_data.py`) and the column types in `project1/source/physical_model/crossfade_schema.sql`. If `pymongo` is installed it also parses the result with `bson.json_util`.
