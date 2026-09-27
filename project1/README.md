# CROSSFADE, Project 1: Database Design

INFO 579 (SQL/NoSQL Databases), Fall 2026. info579_group_1: Herling, Nathan; Pabari, Nidhi Nilesh. Due Sep 27, 2026.

This folder is Project 1 of the [CROSSFADE repository](../README.md). Paths below are relative to `project1/`.

CROSSFADE is a streaming service for independent artists where the catalogue is indexed by where a track sits *between* genres, not by a single genre label. Every upload is scored by several versions of the BEARDOWN genre classifier; listeners build stations from a target genre blend and an allowed range of ambiguity.

**Documentation site:** https://n-herling-mk1.github.io/INFO_579_Fa26_Proj1_CROSSFADE/project1/

## Deliverables

| File | Status |
|---|---|
| `deliverables/requirements_analysis.pdf` | Done |
| `deliverables/conceptual_data_model.png` | Done |
| `deliverables/data.xlsx` | Done |
| `deliverables/physical_data_model.png` | Next |

The graded submission is `project01_<groupcode>.zip`, built from `deliverables/` only.

## Layout

```
index.html               Project 1 site shell (nav rail + panel iframe)
panels/                  one page per rail button
data/site_data.js        generated: tables, dictionary, change log, file list
deliverables/            the four graded files
docs/DATA_DICTIONARY.md  what every column is for
source/                  LaTeX, diagram and data-generator sources
scripts/build_site.py    rebuilds data/site_data.js
CHANGES.md               mk1 → mk9 history
```

## Rebuilding

From the repository root:

```
pdflatex requirements_analysis.tex          # in source/requirements_analysis/, run twice
python source/conceptual_model/build_cdm.py  # draft conceptual model only; the deliverable is hand-drawn (needs graphviz)
python source/data/gen_data.py               # data.xlsx, with integrity self-checks
python scripts/build_site.py                 # refresh the site after any of the above
```

`build_site.py` needs `openpyxl` and `markdown` (`pip install openpyxl markdown`). The site itself has no runtime dependencies.

## Local preview

```
..\boot_site.ps1
```

Run from the repository root. Serves the whole repo on the first free port in 8000–8020 and opens the browser. Opening `index.html` directly also works.

## Related

- BEARDOWN genre classifier (INFO 510): https://github.com/N-Herling-Mk1/INFO_510_Fa25_Final_Proj
- FORGE posterior observatory (INFO 698): https://n-herling-mk1.github.io/INFO_698_documentation/
