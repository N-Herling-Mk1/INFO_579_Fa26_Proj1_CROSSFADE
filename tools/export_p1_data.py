"""Export the graded Project 1 sample data (data.xlsx) as one CSV per table.

Reads project1/deliverables/data.xlsx, the file handed in for Project 1, and writes
    project1/data_export/data.csv               bulk: the whole sheet, laid out as in data.xlsx
    project1/data_export/csv/<table>.csv        one file per table, header = xlsx column names
    project1/data_export/crossfade_project1_data.zip   data.xlsx + data.csv + the 10 CSVs + README.txt
then reads every CSV back and checks it cell-for-cell against the workbook.

Value rules (no rounding, no rebuilding):
    integers        as written (1042)
    decimals        shortest exact form of the stored value (0.0035)
    dates           yyyy-mm-dd            (cells formatted yyyy-mm-dd)
    timestamps      yyyy-mm-dd hh:mm:ss   (cells formatted yyyy-mm-dd hh:mm:ss)
    empty cell      empty field = NULL

Run from the repository root:
    python tools/export_p1_data.py
"""
import csv, datetime, io, os, sys, zipfile

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, "project1", "deliverables", "data.xlsx")
OUT = os.path.join(ROOT, "project1", "data_export")
CSV_DIR = os.path.join(OUT, "csv")
ZIP = os.path.join(OUT, "crossfade_project1_data.zip")
FIXED_TIME = datetime.datetime(2026, 9, 27, 0, 0, 0)  # zip entry time, so rebuilds are byte-identical


def bar(i, n, label):
    w = 30
    k = int(w * i / n)
    sys.stdout.write(f"\r      [{'#' * k}{'.' * (w - k)}] {i}/{n} {label:<22}")
    sys.stdout.flush()
    if i == n:
        sys.stdout.write("\n")


def fmt(cell):
    v = cell.value
    if v is None:
        return ""
    if isinstance(v, datetime.datetime):
        if "h" in cell.number_format.lower():
            return v.strftime("%Y-%m-%d %H:%M:%S")
        if v.time() != datetime.time(0):
            sys.exit(f"  {cell.coordinate}: date-formatted cell carries a time ({v})")
        return v.strftime("%Y-%m-%d")
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() and "." not in cell.number_format else repr(v)
    return str(v)


def slug(name):
    return name.strip().lower().replace(" ", "_")


print("[1/4] reading " + os.path.relpath(XLSX, ROOT), flush=True)
ws = openpyxl.load_workbook(XLSX).active
rows = list(ws.iter_rows())

# The sheet stacks the tables: a title row (one cell), a header row, data rows, a blank row.
tables, i = [], 0
while i < len(rows):
    vals = [c.value for c in rows[i]]
    if vals[0] is not None and all(v is None for v in vals[1:]):
        title, header_cells = vals[0], rows[i + 1]
        ncol = max(j for j, c in enumerate(header_cells) if c.value is not None) + 1
        header = [c.value for c in header_cells[:ncol]]
        data, j = [], i + 2
        while j < len(rows) and any(c.value is not None for c in rows[j]):
            data.append(rows[j][:ncol])
            j += 1
        tables.append((title, header, data))
        i = j
    else:
        i += 1
print(f"      {len(tables)} tables, {sum(len(t[2]) for t in tables)} rows", flush=True)

print("[2/4] writing CSVs to " + os.path.relpath(CSV_DIR, ROOT), flush=True)
os.makedirs(CSV_DIR, exist_ok=True)
written = []
for n, (title, header, data) in enumerate(tables, 1):
    path = os.path.join(CSV_DIR, slug(title) + ".csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in data:
            w.writerow([fmt(c) for c in r])
    written.append((title, path, header, data))
    bar(n, len(tables), slug(title))

BULK = os.path.join(OUT, "data.csv")
ncol_sheet = ws.max_column
with open(BULK, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    for r in rows:
        w.writerow([fmt(c) for c in r[:ncol_sheet]])
print(f"      bulk: data.csv, the whole sheet as laid out in data.xlsx ({len(rows)} rows x {ncol_sheet} columns)", flush=True)

print("[3/4] checking every CSV against the workbook", flush=True)
bad = 0
with open(BULK, encoding="utf-8", newline="") as f:
    bulk_back = list(csv.reader(f))
if len(bulk_back) != len(rows):
    print("      data.csv: row count mismatch"); bad += 1
for r_cells, r_back in zip(rows, bulk_back):
    for c, s in zip(r_cells[:ncol_sheet], r_back):
        if s != fmt(c):
            print(f"      data.csv {c.coordinate}: {c.value!r} -> {s!r}"); bad += 1
for n, (title, path, header, data) in enumerate(written, 1):
    with open(path, encoding="utf-8", newline="") as f:
        back = list(csv.reader(f))
    if back[0] != header or len(back) - 1 != len(data):
        print(f"\n      {title}: header or row count mismatch")
        bad += 1
    for r_cells, r_back in zip(data, back[1:]):
        for c, s in zip(r_cells, r_back):
            v = c.value
            ok = (s == "") if v is None else (
                s == fmt(c) and (
                    not isinstance(v, (int, float)) or isinstance(v, bool) or float(s) == float(v)))
            if not ok:
                print(f"\n      {c.coordinate}: {v!r} -> {s!r}")
                bad += 1
    bar(n, len(written), slug(title))
if bad:
    sys.exit(f"      {bad} mismatches; nothing zipped")
print("      all cells match", flush=True)

print("[4/4] building " + os.path.relpath(ZIP, ROOT), flush=True)
readme = """CROSSFADE - INFO 579 Project 1 sample data (info579_group_1)

data.xlsx        the sample data exactly as handed in for Project 1
data.csv         bulk: the whole sheet as one CSV, laid out as in data.xlsx
                 (each table = title row, header row, data rows, blank row)
csv/<table>.csv  the same data, one file per table

CSV conventions
  header row     the column names used in data.xlsx
  empty field    NULL
  dates          yyyy-mm-dd
  timestamps     yyyy-mm-dd hh:mm:ss (Play.Played At)
  decimals       exact stored value, no rounding

Tables and rows
""" + "".join(f"  {slug(t):<20}{len(d):>4}\n" for t, _, _, d in written)


def add(z, arcname, data):
    zi = zipfile.ZipInfo(arcname, FIXED_TIME.timetuple()[:6])
    zi.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(zi, data)


with zipfile.ZipFile(ZIP, "w") as z:
    add(z, "README.txt", readme)
    add(z, "data.xlsx", open(XLSX, "rb").read())
    add(z, "data.csv", open(BULK, "rb").read())
    for title, path, _, _ in written:
        add(z, "csv/" + os.path.basename(path), open(path, "rb").read())
print(f"      {os.path.getsize(ZIP):,} bytes, {len(written) + 3} files", flush=True)
for t, _, _, d in written:
    print(f"      {slug(t):<20}{len(d):>4} rows")
