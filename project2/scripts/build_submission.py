"""Build the Project 2 submission zip, as the brief asks: "Compress all the deliverables into a single zip file ...
The name file must follow the format: project02_groupcode.zip".

    python project2/scripts/build_submission.py

Reads the zip name and the four files from project2/data/deliverables.js (the one list the site uses), checks each
file is there, warns if a file changed after its last test run or its last run had failures, then writes

    project2/deliverables/project02_info579_group_1.zip   the four .sql files at the top level, nothing else
    project2/data/submission.js                           what is in it (sizes, SHA-256), for the Deliverables page

The zip is reproducible: fixed file dates and order, so the same four files always give the same bytes.
"""
import datetime, hashlib, json, pathlib, re, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
P2 = ROOT / "project2"
DATA = P2 / "data"
FIXED = (2026, 11, 8, 12, 0, 0)          # every entry's date in the zip, so the bytes depend only on the contents
RESULTS = {"database_implementation.sql": "implementation_results.json", "single_table.sql": "single_table_results.json",
           "multiple_table.sql": "multiple_table_results.json", "routines.sql": "routines_results.json"}


def say(k, n, text):
    print(f"[{k}/{n}] {text}", flush=True)


def main():
    src = (DATA / "deliverables.js").read_text(encoding="utf-8")
    zip_name = re.search(r'zip:\s*"([^"]+)"', src).group(1)
    files = re.findall(r'file:\s*"([^"]+\.sql)"', src)
    if not re.fullmatch(r"project02_\w+\.zip", zip_name):
        sys.exit(f"zip name {zip_name!r} does not follow project02_groupcode.zip")

    say(1, 4, f"checking the {len(files)} deliverables")
    entries, warnings = [], []
    for f in files:
        p = P2 / "deliverables" / f
        if not p.is_file():
            sys.exit(f"      missing: project2/deliverables/{f}")
        b = p.read_bytes()
        res = DATA / RESULTS.get(f, "")
        note = "no test results"
        if res.is_file():
            r = json.loads(res.read_text(encoding="utf-8"))
            run = datetime.datetime.fromisoformat(r["generated"])
            changed = datetime.datetime.fromtimestamp(p.stat().st_mtime)
            note = f"last test run {r['generated'].replace('T', ' ')}: {r['passed']} passed, {r['failed']} failed"
            if r["failed"]:
                warnings.append(f"{f}: its last test run had {r['failed']} failures")
            if changed > run + datetime.timedelta(seconds=5):
                warnings.append(f"{f}: changed after its last test run ({changed:%Y-%m-%d %H:%M})")
        else:
            warnings.append(f"{f}: no test results")
        entries.append({"file": f, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "tests": note, "data": b})
        print(f"      {f:<30} {len(b):>7,} bytes   {note}", flush=True)
    for w in warnings:
        print(f"      warning: {w}", flush=True)

    out = P2 / "deliverables" / zip_name
    say(2, 4, f"writing project2/deliverables/{zip_name}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for e in entries:
            info = zipfile.ZipInfo(e["file"], date_time=FIXED)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(info, e["data"])

    say(3, 4, "checking the zip")
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        names = z.namelist()
        same = all(z.read(e["file"]) == e["data"] for e in entries)
    if bad or names != files or not same:
        sys.exit(f"      the zip does not hold exactly the {len(files)} files: {names} (bad entry: {bad})")
    zb = out.read_bytes()
    print(f"      {len(names)} files, {len(zb):,} bytes, SHA-256 {hashlib.sha256(zb).hexdigest()[:16]}...", flush=True)

    say(4, 4, "writing project2/data/submission.js")
    info = {"zip": zip_name, "bytes": len(zb), "sha256": hashlib.sha256(zb).hexdigest(),
            "built": datetime.datetime.now().isoformat(timespec="seconds"), "warnings": warnings,
            "files": [{k: v for k, v in e.items() if k != "data"} for e in entries]}
    (DATA / "submission.js").write_text(
        "/* Written by project2/scripts/build_submission.py. Do not edit. */\nwindow.P2_SUBMISSION = " +
        json.dumps(info, indent=1) + ";\n", encoding="utf-8")
    print(f"done: {zip_name}" + (f" ({len(warnings)} warnings above)" if warnings else ""), flush=True)


if __name__ == "__main__":
    main()
