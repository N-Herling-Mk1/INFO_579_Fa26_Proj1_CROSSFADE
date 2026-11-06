"""Build crossfade_p2_test_kit.zip: everything needed to run the Project 2 tests outside the repo,
except the two files you download from the site yourself (data.csv and database_implementation.sql).

    python project2/tests/build_kit.py
"""
import os, pathlib, zipfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / "crossfade_p2_test_kit.zip"
FILES = [(HERE / n, n) for n in ("conftest.py", "oracle.py", "test_single_table.py", "pytest.ini",
                                 "requirements.txt", "README.md")]
FILES += [(REPO / "project2/data/use_cases.json", "use_cases.json"),
          (REPO / "project2/deliverables/single_table.sql", "single_table.sql"),
          (REPO / "project2/docs/run_tests_locally.pdf", "run_tests_locally.pdf"),        # python project2/scripts/build_docs.py
          (REPO / "project2/docs/use_case_reference.pdf", "use_case_reference.pdf")]
STAMP = (2026, 11, 6, 0, 0, 0)        # fixed entry time, so an unchanged kit rebuilds byte-identical

with zipfile.ZipFile(OUT, "w") as z:
    for i, (src, name) in enumerate(FILES, 1):
        zi = zipfile.ZipInfo("crossfade_p2_tests/" + name, STAMP)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16          # rw-r--r-- when unzipped
        z.writestr(zi, src.read_bytes())
        print(f"[{i}/{len(FILES)}] {name}", flush=True)
print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size:,} bytes); add data.csv and database_implementation.sql from the site")
