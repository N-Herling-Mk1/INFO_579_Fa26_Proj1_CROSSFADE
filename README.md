# CROSSFADE

INFO 579 (SQL/NoSQL Databases), Fall 2026. **info579_group_1:** Herling, Nathan; Pabari, Nidhi Nilesh.

CROSSFADE is a streaming service for independent artists where the catalogue is indexed by where a track sits *between* genres, not by a single genre label. The course's three projects take the same business through three stages of database work.

**Site:** https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/

| Folder | Project | Due | Status |
|---|---|---|---|
| [`design/`](design/) | Top-level design shared by all three | | |
| [`project1/`](project1/) | Project 1: Database Design | Sep 27, 2026 | All 4 deliverables; submission zip in `project1/submission/` |
| [`project2/`](project2/) | Project 2: SQL Database | Nov 8, 2026 | 1 of 4 `.sql` files (Task 1 ready to test), see [`project2/README.md`](project2/README.md) |
| [`project3/`](project3/) | Project 3: NoSQL Database | Dec 13, 2026 | Not started |

## Layout

The site is one page, `index.html`: a top bar (sections), a side rail (that section's pages) and one
iframe that every page loads into. Routes are hashes: `#<section>/<page>[/<anchor>]`.

| Route | Loads |
|---|---|
| `#home` (default), `#home/p1`, `#home/data[/tables]`, `#home/brief` | `home/overview.html`, `home/p1.html`, `home/data.html`, `home/brief.html` |
| `#p1/<panel>[/<anchor>]` | `project1/panels/<panel>.html` (unchanged) |
| `#p2/overview`, `#p2/usecases`, `#p2/brief` | `project2/panels/<panel>.html` |
| `#p2/implementation`, `#p2/single`, `#p2/multiple`, `#p2/routines` | `project2/panels/file.html?f=<id>` |
| `#p3`, `#design` | `project3/panel.html`, `design/panel.html` |

`project1/index.html`, `project2/index.html`, `project3/index.html` and `design/index.html` are now redirect
stubs (`project2/#usecases` → `#p2/usecases`), so old links and bookmarks still work. Links inside a panel that
point at those old pages are caught by the shell and turned into routes, so the panels did not need editing.
The shell chrome is dark TRON Ares (`assets/shell.css`, modelled on the HELIX view shell): each section has its own
accent colour, the top-right readout shows the current section and page, and Alt+1 to Alt+5 jump between sections.
The front panel `home/overview.html` is dark too (`assets/splash.css`); every other panel stays a light reading surface
(`site.css`). The ☰ button hides the rail for a full-width panel; the choice is remembered per browser. To add a page,
add one line to `SECTIONS` in the script at the bottom of `index.html`.

```
index.html       the site shell (top bar, rail, iframe, router)
home/            front-page panels: overview, Project 1 package, Project 1 data (bulk / per table), Project 2 brief
assets/          site.css (panels), shell.css (index.html chrome), splash.css (home/overview.html), panel.js,
                 logo, favicons, social card (og_crossfade_card.jpg), CROSSFADE artwork
tools/           stamp_assets.py: tags every link to site.css / shell.css / splash.css / panel.js with a content hash
                 export_p1_data.py: data.xlsx -> project1/data_export/ (data.csv + one CSV per table + zip)
assets/vendor/   jszip.min.js (JSZip 3.10.1, MIT): builds the Project 1 submission zip in the browser
design/          top-level design (panel.html)
project1/        Database Design: deliverables, sources, docs, panels
  data_export/   the graded data.xlsx as data.csv (whole sheet) and csv/<table>.csv, plus crossfade_project1_data.zip
  brief/         (to add) info579_project01.pdf; the Project 1 page shows it once it exists
project2/        SQL Database: deliverables, panels, use cases, scripts
project3/        NoSQL Database (panel.html)
course_materials/  course zips kept for transport only; not linked from the site (see below)
boot_site.ps1    local preview server for the whole repo
```

Each project's graded submission is built from that project's `deliverables/` folder only (for Project 1, `project01_<groupcode>.zip`).

## Project 1 data export

```
python tools/export_p1_data.py
```

Reads `project1/deliverables/data.xlsx` (the file handed in) and writes two views of it: `project1/data_export/data.csv`, the whole sheet laid out as in the workbook, and `project1/data_export/csv/<table>.csv` for each of the 10 tables (401 rows). Checks every cell of both against the workbook, then builds `crossfade_project1_data.zip` (data.xlsx + data.csv + CSVs + README.txt). Empty field = NULL; dates `yyyy-mm-dd`; timestamps `yyyy-mm-dd hh:mm:ss`; decimals exact.

## Course materials (transport only)

`course_materials/` holds the course zips as uploaded, so they travel with the repo. Nothing on the site links to them.

| File | Contents |
|---|---|
| `lectures.zip` | Lecture slides, units 1 to 10 plus the unit 8 exercises (PDF) |
| `0_unit_4.zip` | Homework units 4 to 10: submitted `.sql`/`.png`, instructor feedback screenshots, the assignment attachments |
| `project01_info579_group_1.zip` | The Project 1 submission as uploaded; same four files as `project1/submission/project01_info579_group_1.zip` |

The repository is public, so these files can be downloaded by anyone who browses it, whether or not the site links to them.

## Local preview

```
.\boot_site.ps1
```

## After editing site.css, shell.css, splash.css or panel.js

Run `python tools/stamp_assets.py`. It tags each page's links as `site.css?v=<hash>`, so browsers fetch the new file instead of reusing a cached copy (GitHub Pages lets them cache for up to 10 minutes).

## Social preview

`assets/images/og_crossfade_card.jpg` (1200 x 630, the size Facebook, LinkedIn, X, Slack and Discord crop to) is the link card. Every top-level page carries Open Graph and X (Twitter) tags pointing at it. GitHub's own repo card is set separately: Settings → General → Social preview → Upload an image, with `assets/images/github_social_preview.png` (1280 x 640, GitHub's size).
