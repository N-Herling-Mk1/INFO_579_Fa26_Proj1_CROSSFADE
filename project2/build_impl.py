"""Build project2/deliverables/database_implementation.sql (Task 1).

Merges Project 1's generated schema and sample data into one script and puts a
purpose comment before every statement, as the brief requires. Nothing is typed
by hand into the SQL:
  * CREATE TABLE statements come verbatim from project1/source/physical_model/crossfade_schema.sql
  * INSERT statements come verbatim from project1/source/physical_model/crossfade_data.sql
  * each table's purpose comment is its entity description in the requirements analysis
  * each INSERT's comment states what the sample rows cover; row counts are counted, not typed

Project 1 stays frozen: this script only reads its outputs. Rerun after any change there:
    python project2/scripts/build_impl.py
"""
import os
import re
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P1 = os.path.join(ROOT, "project1")
SCHEMA = os.path.join(P1, "source", "physical_model", "crossfade_schema.sql")
DATA = os.path.join(P1, "source", "physical_model", "crossfade_data.sql")
TEX = os.path.join(P1, "source", "requirements_analysis", "requirements_analysis.tex")
OUT = os.path.join(ROOT, "project2", "deliverables", "database_implementation.sql")
STEPS = 5


def step(i, msg):
    print(f"[{i}/{STEPS}] {msg}", flush=True)


def comment(text, width=78):
    """Wrap prose into '-- ' lines."""
    out = []
    for para in text.strip().split("\n"):
        if not para.strip():
            out.append("--")
            continue
        out += ["-- " + l for l in textwrap.wrap(para.strip(), width - 3)]
    return "\n".join(out)


def snake(name):
    return re.sub(r"\W+", "_", name.strip().lower())


# What each table's sample rows were chosen to exercise. Facts checked against the
# loaded data on 2026-11-04 (MySQL 8.0.46). {n} is filled with the counted row total.
INSERT_NOTES = {
    "artist": "Sample artists ({n} rows). Kestrel Ave has registered but not yet uploaded "
              "anything, which the requirements allow; Saltmarsh Tapes has no country yet "
              "(Country is optional); three artists are unverified. Payout rates differ, so "
              "royalty totals differ per artist.",
    "track": "Sample catalogue ({n} rows). Thirteen tracks are scored and streamable; Brine "
             "is awaiting scoring and Untitled Loop 7 was rejected, so both ingest outcomes "
             "other than 'scored' are present. Audio checksums are SHA-256 digests stored as "
             "BINARY(32) through UNHEX.",
    "genre": "The ten GTZAN genres ({n} rows), IDs 0 to 9. These are the coordinates every "
             "probability distribution and every station blend is expressed in, so this "
             "table must be loaded before Track Score, Station Blend and Genre Probability.",
    "listener": "Sample subscribers ({n} rows) across all three plan tiers: three free, three "
                "standard, two premium. One listener (h.ito) owns no station and streams only "
                "through other listeners' stations or none.",
    "scoring_model": "The deployed BEARDOWN model versions ({n} rows). Both fusion types are "
                     "present. beardown_rrm_cfg17 is deployed but has produced no scores yet, "
                     "so a model can exist without results.",
    "station": "Sample stations ({n} rows) owned by seven listeners; amara_o owns two. Each "
               "pairs a scoring model with an ambiguity window, and windows range from narrow "
               "(0.35 to 0.80) to wide (0.10 to 0.70).",
    "track_score": "Scoring results ({n} rows) for the thirteen scored tracks, one row per "
                   "(track, model) pair. Harbour Lights Waltz was scored by one model only, so "
                   "its Model Divergence is NULL: there is no other result to diverge from.",
    "play": "Listening history and royalty ledger ({n} rows), May to August 2026. Nine plays "
            "happened outside any station; four used a station owned by a different listener "
            "(I6, shared stations). Five plays under 30 seconds earned no royalty (I7). Eight "
            "saves and five skips record listener reactions.",
    "station_blend": "Station recipes ({n} rows): one to three genres per station, weights in "
                     "hundredths summing to exactly 1.00 for every station (I1). Blue Hour is a "
                     "single-genre station at weight 1.00.",
    "genre_probability": "Full genre distributions ({n} rows): ten probabilities for each of "
                         "the scoring results, each set summing to 1 within 0.0010 (I2). "
                         "Track Score's top genre, top probability and entropy are derived "
                         "from these rows (I3).",
}


def main():
    step(1, "reading entity descriptions from the requirements analysis")
    tex = open(TEX, encoding="utf-8").read()
    desc = {}
    for m in re.finditer(r"\\entityhead\{([^}]*)\}\{(.*?)\\dictnote", tex, re.S):
        text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", m.group(2))
        desc[snake(m.group(1))] = re.sub(r"\s+", " ", text).strip()
    print(f"      {len(desc)} entity descriptions")

    step(2, "splitting Project 1 schema into statements")
    schema = open(SCHEMA, encoding="utf-8").read()
    creates = re.findall(r"(CREATE TABLE (\w+) \(.*?\) ENGINE=InnoDB;)", schema, re.S)
    order = [name for _, name in creates]
    print(f"      {len(creates)} CREATE TABLE statements: {', '.join(order)}")

    step(3, "splitting Project 1 data into statements")
    data = open(DATA, encoding="utf-8").read()
    inserts = re.findall(r"(INSERT INTO (\w+) \(.*?\) VALUES\n.*?\);)\n", data, re.S)
    counts = {name: len(re.findall(r"^\s+\(", stmt, re.M)) for stmt, name in inserts}
    print(f"      {len(inserts)} INSERT statements, {sum(counts.values())} rows")

    problems = []
    if len(creates) != 10 or len(inserts) != 10:
        problems.append("expected 10 tables and 10 INSERT statements")
    for t in order:
        if t not in desc:
            problems.append(f"no entity description for {t}")
        if t not in INSERT_NOTES:
            problems.append(f"no INSERT note for {t}")
    if problems:
        sys.exit("FAIL: " + "; ".join(problems))

    step(4, "writing database_implementation.sql")
    parts = [comment(
        "CROSSFADE database implementation (INFO 579 Project 2, Task 1), info579_group_1: "
        "Herling, Nathan; Pabari, Nidhi Nilesh.\n"
        "Purpose: create the ten tables of the Project 1 physical model, with every primary "
        "key, foreign key, UNIQUE and CHECK constraint, and load the Project 1 sample data "
        f"({sum(counts.values())} rows), so that single_table.sql, multiple_table.sql and "
        "routines.sql run against exactly the database designed in Project 1.\n"
        "Requires MySQL 8.0.16 or later, the first version that enforces CHECK constraints. "
        "Tested on 8.0.46.\n"
        "Run: mysql -u <user> -p < database_implementation.sql\n"
        "Generated by project2/scripts/build_impl.py from the Project 1 sources; do not edit "
        "by hand.")]

    parts.append(comment(
        "Start from a clean slate so the script can be rerun at any time and always yields "
        "the same database. WARNING: this drops any existing crossfade schema and its data.")
                 + "\nDROP SCHEMA IF EXISTS crossfade;")
    parts.append(comment(
        "utf8mb4 so artist names, stage names and track titles from any country store "
        "correctly, including accented and non-Latin characters.")
                 + "\nCREATE SCHEMA crossfade DEFAULT CHARACTER SET utf8mb4;")
    parts.append(comment("Every statement below applies to the crossfade schema.")
                 + "\nUSE crossfade;")

    parts.append("-- " + "=" * 72 + "\n-- Tables, created parents first so every foreign "
                 "key has a table to point at\n-- " + "=" * 72)
    for stmt, name in creates:
        parents = []
        for p in re.findall(r"REFERENCES (\w+) \(", stmt):
            if p not in parents:
                parents.append(p)
        note = f"Table {name}: {desc[name]}"
        if parents:
            note += "\nCreated after " + ", ".join(parents) + (
                ", which its foreign keys reference." if len(parents) > 1
                else ", which its foreign key references.")
        parts.append(comment(note) + "\n" + stmt)

    parts.append("-- " + "=" * 72 + "\n-- Sample data from Project 1 data.xlsx, inserted "
                 "parents first\n-- " + "=" * 72)
    for stmt, name in inserts:
        parts.append(comment(INSERT_NOTES[name].format(n=counts[name])) + "\n" + stmt)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n\n".join(parts) + "\n")

    step(5, "checking every statement is preceded by a comment")
    text = open(OUT, encoding="utf-8").read()
    bare = 0
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"(DROP|CREATE|USE|INSERT)\b", line):
            if i == 0 or not lines[i - 1].startswith("--"):
                bare += 1
                print(f"      no comment before line {i + 1}: {line[:60]}")
    if bare:
        sys.exit(f"FAIL: {bare} statement(s) without a purpose comment")
    print(f"      ok: {len(lines)} lines -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
