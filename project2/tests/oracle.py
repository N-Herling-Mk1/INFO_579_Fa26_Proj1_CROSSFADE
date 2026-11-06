"""Independent answers to the single_table.sql questions, computed in plain Python from the Project 1
sample data (data.csv). No SQL and no code shared with the queries: if a query and its oracle agree,
the query means what its comment says.

Each function takes the tables as loaded by conftest.load_bulk (strings, None for NULL) and returns
(columns, rows) with values in conftest.canon form: Decimal for numbers, 'YYYY-MM-DD' for dates.

MySQL rules reproduced on purpose:
- ROUND on exact (DECIMAL/integer) values rounds half away from zero.
- AVG of exact values keeps 4 extra decimal places (div_precision_increment = 4) before any ROUND.
- ORDER BY on an ENUM sorts by the declared position, not alphabetically.
"""
import datetime
from decimal import Decimal, ROUND_HALF_UP

REPORT_DATE = datetime.date(2026, 9, 30)
PLAN_TIER = ["free", "standard", "premium"]                    # ENUM order in listener
INGEST = ["awaiting scoring", "scored", "rejected"]             # ENUM order in track


def D(x):
    return Decimal(str(x))


def day(s):
    return datetime.date.fromisoformat(s)


def rnd(x, places=0):
    q = Decimal(1).scaleb(-places)
    return x.quantize(q, rounding=ROUND_HALF_UP)


def avg(values, scale):
    """MySQL AVG over exact values: result scale = input scale + 4."""
    total = sum(values, Decimal(0))
    return (total / len(values)).quantize(Decimal(1).scaleb(-(scale + 4)), rounding=ROUND_HALF_UP)


def days_to_report(s):
    return D((REPORT_DATE - day(s)).days)


# ----------------------------------------------------------------------------- S1 artist
def s1(t):
    cols = ["artist_id", "payee", "usd_per_1000_streams", "days_under_licence", "payment_status"]
    out = []
    for a in t["artist"]["rows"]:
        verified, country, rate = int(a["verified"]), a["country"], D(a["payout_rate"])
        status = ("HOLD: identity not verified" if verified == 0 else
                  "HOLD: no payment country" if country is None else "PAYABLE")
        payable = 0 if verified == 1 and country is not None else 1
        row = (D(a["artist_id"]), f"{a['stage_name']} ({country if country is not None else '--'})",
               rnd(rate * 1000, 2), days_to_report(a["joined_date"]), status)
        out.append(((payable, -rate, int(a["artist_id"])), row))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- S2 track: new-uploads shelf
def s2(t):
    cols = ["track_id", "title", "run_time", "release_date", "days_since_release"]
    rows = [r for r in t["track"]["rows"] if r["ingest_status"] == "scored"]
    rows.sort(key=lambda r: (-day(r["release_date"]).toordinal(), int(r["track_id"])))
    out = []
    for r in rows[:5]:
        d = int(r["duration"])
        out.append((D(r["track_id"]), r["title"], f"{d // 60}:{d % 60:02d}", r["release_date"],
                    days_to_report(r["release_date"])))
    return cols, out


# ----------------------------------------------------------------------------- S3 genre: composer legend
def s3(t):
    cols = ["model_class_index", "label", "legend_line", "composer_status"]
    out = []
    for g in sorted(t["genre"]["rows"], key=lambda g: int(g["genre_id"])):
        desc = g["description"]
        out.append((D(g["genre_id"]), g["name"], g["name"] + ": " + (desc if desc is not None else "(no description)"),
                    "HIDE: no description for the composer" if desc is None else "READY"))
    return cols, out


# ----------------------------------------------------------------------------- S4 listener: mix by tier
def s4(t):
    cols = ["plan_tier", "listeners", "first_signup", "latest_signup", "avg_days_subscribed"]
    groups = {}
    for l in t["listener"]["rows"]:
        groups.setdefault(l["plan_tier"], []).append(l["signup_date"])
    out = []
    for tier in sorted(groups, key=lambda x: -PLAN_TIER.index(x)):
        ds = groups[tier]
        out.append((tier, D(len(ds)), min(ds), max(ds), rnd(avg([days_to_report(d) for d in ds], 0), 0)))
    return cols, out


# ----------------------------------------------------------------------------- S5 scoring_model: default model
def s5(t):
    cols = ["version_label", "architecture", "accuracy_pct", "deployed_on"]
    rows = sorted(t["scoring_model"]["rows"],
                  key=lambda m: (-D(m["holdout_accuracy"]), -day(m["deployed_on"]).toordinal()))
    out = []
    for m in rows[:1]:                                         # the one default
        out.append((m["version_label"],
                    f"{m['fusion_type']} / {m['embedding_dimension']}d / {m['segment_length']}s / {m['training_corpus']}",
                    rnd(D(m["holdout_accuracy"]) * 100, 2), m["deployed_on"]))
    return cols, out


# ----------------------------------------------------------------------------- S6 station: reliance per model
def s6(t):
    cols = ["model_id", "stations", "avg_window", "wide_stations", "oldest_station"]
    groups = {}
    for s in t["station"]["rows"]:
        groups.setdefault(int(s["model_id"]), []).append(s)
    out = []
    for mid, ss in groups.items():
        widths = [D(s["maximum_ambiguity"]) - D(s["minimum_ambiguity"]) for s in ss]
        out.append((D(mid), D(len(ss)), rnd(avg(widths, 2), 2), D(sum(1 for w in widths if w > D("0.5"))),
                    min(s["created_on"] for s in ss)))
    out.sort(key=lambda r: (-r[1], r[0]))
    return cols, out


# ----------------------------------------------------------------------------- S7 track: upload pipeline
def s7(t):
    cols = ["ingest_status", "recordings", "earliest_release", "days_to_earliest_release", "release_status"]
    groups = {}
    for r in t["track"]["rows"]:
        groups.setdefault(r["ingest_status"], []).append(r["release_date"])
    out = []
    for st in sorted(groups, key=INGEST.index):
        earliest = min(groups[st])
        status = ("streamable" if st == "scored" else
                  "never streamable: rejected" if st == "rejected" else
                  "LATE: release date reached, still unscored" if day(earliest) <= REPORT_DATE else
                  "on time: release date still ahead")
        out.append((st, D(len(groups[st])), earliest, -days_to_report(earliest), status))
    return cols, out


ORACLES = {"S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5, "S6": s6, "S7": s7}
