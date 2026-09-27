# CROSSFADE top-level design

Shared by all three INFO 579 projects (info579_group_1: Herling, Nathan; Pabari, Nidhi Nilesh).

CROSSFADE is a streaming service for independent artists, indexed by where a track sits between genres. Every upload is scored by several versions of the BEARDOWN genre classifier; listeners build stations from a target genre blend and an allowed range of ambiguity.

## Entities (fixed in Project 1)

| Kind | Entities |
|---|---|
| Entity (6) | Artist, Track, Genre, Listener, Scoring Model, Station |
| Associative entity (4) | Track Score, Genre Probability, Station Blend, Play |

Definitions: [project1/docs/DATA_DICTIONARY.md](../project1/docs/DATA_DICTIONARY.md). Diagram: [project1/deliverables/conceptual_data_model.png](../project1/deliverables/conceptual_data_model.png).

## One design, three databases

| Project | Role | Due |
|---|---|---|
| 1. Database Design | Defines the design | Sep 27, 2026 |
| 2. SQL Database | Builds it as a relational database | Nov 8, 2026 |
| 3. NoSQL Database | Models the same business in a NoSQL database | Dec 13, 2026 |
