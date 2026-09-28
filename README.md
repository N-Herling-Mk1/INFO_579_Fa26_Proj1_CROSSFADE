# CROSSFADE

INFO 579 (SQL/NoSQL Databases), Fall 2026. **info579_group_1:** Herling, Nathan; Pabari, Nidhi Nilesh.

CROSSFADE is a streaming service for independent artists where the catalogue is indexed by where a track sits *between* genres, not by a single genre label. The course's three projects take the same business through three stages of database work.

**Site:** https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/

| Folder | Project | Due | Status |
|---|---|---|---|
| [`design/`](design/) | Top-level design shared by all three | | |
| [`project1/`](project1/) | Project 1: Database Design | Sep 27, 2026 | All 4 deliverables; submission zip in `project1/submission/` |
| [`project2/`](project2/) | Project 2: SQL Database | Nov 8, 2026 | Not started |
| [`project3/`](project3/) | Project 3: NoSQL Database | Dec 13, 2026 | Not started |

## Layout

```
index.html       project picker (site front page)
assets/          shared site.css, panel.js, logo, favicons, social card (og_card.png), CROSSFADE artwork
tools/           build_banner.py: writes the shared top banner into every top-level page
                 stamp_assets.py: tags every link to site.css / panel.js with a content hash
assets/vendor/   jszip.min.js (JSZip 3.10.1, MIT): builds the Project 1 submission zip in the browser
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

## Banner

Every top-level page shares one banner: the CROSSFADE wave and wordmark, a context line, and Home / Project 1 / Project 2 / Project 3 buttons with a hover effect. After changing it, run `python tools/build_banner.py` from the repository root; it rewrites the block between the `BANNER` markers in each page.

## After editing site.css or panel.js

Run `python tools/stamp_assets.py`. It tags each page's links as `site.css?v=<hash>`, so browsers fetch the new file instead of reusing a cached copy (GitHub Pages lets them cache for up to 10 minutes).

## Social preview

`assets/images/og_card.png` (1280 x 640) is the link card. Pages carry Open Graph tags pointing at it. GitHub's own repo card is set separately: Settings → General → Social preview → Upload an image.
