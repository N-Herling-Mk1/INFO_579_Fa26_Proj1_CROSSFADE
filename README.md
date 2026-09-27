# CROSSFADE

INFO 579 (SQL/NoSQL Databases), Fall 2026. **info579_group_1:** Herling, Nathan; Pabari, Nidhi Nilesh.

CROSSFADE is a streaming service for independent artists where the catalogue is indexed by where a track sits *between* genres, not by a single genre label. The course's three projects take the same business through three stages of database work.

**Site:** https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/

| Folder | Project | Due | Status |
|---|---|---|---|
| [`design/`](design/) | Top-level design shared by all three | | |
| [`project1/`](project1/) | Project 1: Database Design | Sep 27, 2026 | 3 of 4 deliverables |
| [`project2/`](project2/) | Project 2: SQL Database | Nov 8, 2026 | Not started |
| [`project3/`](project3/) | Project 3: NoSQL Database | Dec 13, 2026 | Not started |

## Layout

```
index.html       project picker (site front page)
assets/          shared site.css, panel.js, logo, favicons, social card (og_card.png)
design/          top-level design: the business and its ten entities
project1/        Database Design: deliverables, sources, docs, its own site
project2/        SQL Database
project3/        NoSQL Database
boot_site.ps1    local preview server for the whole repo
```

Each project's graded submission is built from that project's `deliverables/` folder only (for Project 1, `project01_<groupcode>.zip`).

## Local preview

```
.\boot_site.ps1
```

## Social preview

`assets/images/og_card.png` (1280 x 640) is the link card. Pages carry Open Graph tags pointing at it. GitHub's own repo card is set separately: Settings → General → Social preview → Upload an image.
