"""Independent answers to the multiple_table.sql questions, computed in plain Python from the Project 1 sample data
(data.csv). No SQL: joins are dictionary look-ups, UNION is a set, WITH is a list built first. If a query and its
oracle agree, the query means what its comment says.

Each function takes the tables as loaded by conftest.load_bulk (strings, None for NULL) and returns (columns, rows)
with values in conftest.canon form: Decimal for numbers, str for text, None for NULL.

MySQL rules reproduced on purpose:
- ROUND on exact (DECIMAL/integer) values rounds half away from zero.
- Dividing exact values keeps 4 extra decimal places (div_precision_increment = 4) before any ROUND.
- SUM over no rows is NULL; IFNULL(NULL, 0) is 0.
"""
from decimal import Decimal, ROUND_HALF_UP

from oracle import D, rnd


def div(a, b, extra=4):
    """MySQL exact division a / b: the result keeps the dividend's scale + 4 decimal places."""
    scale = max(0, -Decimal(a).as_tuple().exponent)
    return (Decimal(a) / Decimal(b)).quantize(Decimal(1).scaleb(-(scale + extra)), rounding=ROUND_HALF_UP)


def by(rows, key):
    return {r[key]: r for r in rows}


# ----------------------------------------------------------------------------- M1 listener taste (play, listener, track)
def m1(t):
    cols = ["listener_id", "display_name", "plays", "completed_plays", "saves", "skips", "pct_of_audio_heard"]
    listeners, tracks = by(t["listener"]["rows"], "listener_id"), by(t["track"]["rows"], "track_id")
    acc = {}
    for p in t["play"]["rows"]:
        if p["listener_id"] not in listeners or p["track_id"] not in tracks:
            continue                                                   # INNER JOIN: both sides must exist
        a = acc.setdefault(p["listener_id"], {"plays": 0, "done": 0, "saves": 0, "skips": 0, "heard": 0, "length": 0})
        a["plays"] += 1
        a["done"] += int(p["completed"]) == 1
        a["saves"] += p["reaction"] == "saved"
        a["skips"] += p["reaction"] == "skipped"
        a["heard"] += int(p["seconds_played"])
        a["length"] += int(tracks[p["track_id"]]["duration"])
    out = []
    for lid, a in acc.items():
        pct = rnd(div(100 * a["heard"], a["length"]), 1)
        out.append(((-pct, int(lid)), (D(lid), listeners[lid]["display_name"], D(a["plays"]), D(a["done"]),
                                       D(a["saves"]), D(a["skips"]), pct)))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- M2 royalty run (artist LEFT OUTER JOIN track, play)
def m2(t):
    cols = ["artist_id", "payee", "plays", "qualifying_plays", "usd_owed"]
    out = []
    for a in t["artist"]["rows"]:
        tracks = {x["track_id"] for x in t["track"]["rows"] if x["artist_id"] == a["artist_id"]}
        plays = [p for p in t["play"]["rows"] if p["track_id"] in tracks]
        owed = sum((D(p["royalty_amount"]) for p in plays), Decimal(0)) if plays else Decimal(0)   # IFNULL(SUM, 0)
        qualifying = sum(1 for p in plays if int(p["seconds_played"]) >= 30)
        out.append(((-owed, int(a["artist_id"])), (D(a["artist_id"]), a["stage_name"], D(len(plays)), D(qualifying), owed)))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- M3 station reach (UNION)
def m3(t):
    cols = ["station_id", "station", "created_by", "listeners_reached", "reach_status"]
    reach = {(s["station_id"], s["listener_id"]) for s in t["station"]["rows"]}                        # creators
    reach |= {(p["station_id"], p["listener_id"]) for p in t["play"]["rows"] if p["station_id"] is not None}  # UNION
    listeners = by(t["listener"]["rows"], "listener_id")
    out = []
    for s in t["station"]["rows"]:
        n = sum(1 for sid, _ in reach if sid == s["station_id"])
        if n == 0 or s["listener_id"] not in listeners:
            continue
        out.append(((-n, int(s["station_id"])), (D(s["station_id"]), s["name"], listeners[s["listener_id"]]["display_name"],
                                                 D(n), "shared" if n > 1 else "creator only")))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- M4 model disagreement (subquery + IN)
def m4(t):
    cols = ["track_id", "title", "models_scoring", "highest_divergence"]
    scores = {}
    for s in t["track_score"]["rows"]:
        scores.setdefault(s["track_id"], []).append(s)
    out = []
    for tr in t["track"]["rows"]:
        ss = scores.get(tr["track_id"], [])
        if len({s["genre_id"] for s in ss}) <= 1:
            continue
        divs = [D(s["model_divergence"]) for s in ss if s["model_divergence"] is not None]
        hi = max(divs) if divs else None
        out.append((((0, -hi) if hi is not None else (1, 0), int(tr["track_id"])),     # NULLs sort last in DESC
                    (D(tr["track_id"]), tr["title"], D(len(ss)), hi)))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- M5 filling each station (WITH)
def m5(t):
    cols = ["station_id", "station", "track_id", "title", "top_genre", "genre_weight", "posterior_entropy",
            "station_recordings", "station_run_minutes"]
    tracks, genres = by(t["track"]["rows"], "track_id"), by(t["genre"]["rows"], "genre_id")
    blend = {(b["station_id"], b["genre_id"]): D(b["weight"]) for b in t["station_blend"]["rows"]}
    eligible = []                                                     # the first derived table
    for st in t["station"]["rows"]:
        lo, hi = D(st["minimum_ambiguity"]), D(st["maximum_ambiguity"])
        for s in t["track_score"]["rows"]:
            tr = tracks.get(s["track_id"])
            if s["model_id"] != st["model_id"] or tr is None or tr["ingest_status"] != "scored":
                continue
            w = blend.get((st["station_id"], s["genre_id"]))
            if w is None or not (lo <= D(s["posterior_entropy"]) <= hi) or s["genre_id"] not in genres:
                continue
            eligible.append({"station_id": st["station_id"], "station": st["name"], "track_id": tr["track_id"],
                             "title": tr["title"], "duration": int(tr["duration"]), "top_genre": genres[s["genre_id"]]["name"],
                             "w": w, "h": D(s["posterior_entropy"])})
    length = {}                                                       # the second derived table
    for e in eligible:
        n, secs = length.get(e["station_id"], (0, 0))
        length[e["station_id"]] = (n + 1, secs + e["duration"])
    out = []
    for e in eligible:
        n, secs = length[e["station_id"]]
        out.append(((int(e["station_id"]), -e["w"], -e["h"], int(e["track_id"])),
                    (D(e["station_id"]), e["station"], D(e["track_id"]), e["title"], e["top_genre"], e["w"], e["h"],
                     D(n), rnd(div(secs, 60), 1))))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- M6 results to recompute (track_score, track, scoring_model)
def m6(t):
    import datetime
    cols = ["track_id", "title", "results", "scored_by", "last_scored_on", "days_out_of_date"]
    tracks, models = by(t["track"]["rows"], "track_id"), by(t["scoring_model"]["rows"], "model_id")
    in_service = max(datetime.date.fromisoformat(m["deployed_on"]) for m in t["scoring_model"]["rows"])
    groups = {}
    for s in t["track_score"]["rows"]:
        tr, m = tracks.get(s["track_id"]), models.get(s["model_id"])
        if tr is None or m is None or tr["ingest_status"] != "scored":       # INNER JOINs, WHERE
            continue
        groups.setdefault(s["track_id"], []).append((s, m))
    out = []
    for tid, rs in groups.items():
        last = max(s["scored_on"] for s, _ in rs)                            # ISO text sorts as time
        last_dt = datetime.datetime.fromisoformat(last)
        if not last_dt < datetime.datetime.combine(in_service, datetime.time()):   # HAVING
            continue
        days = (in_service - last_dt.date()).days                            # DATEDIFF ignores the time of day
        versions = ", ".join(m["version_label"] for _, m in sorted(rs, key=lambda x: (x[1]["deployed_on"], int(x[1]["model_id"]))))
        out.append(((-days, int(tid)), (D(tid), tracks[tid]["title"], D(len(rs)), versions, last, D(days))))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


# ----------------------------------------------------------------------------- M7 between genres (WITH over genre_probability)
def m7(t):
    cols = ["track_id", "title", "model_id", "top_genre", "top_probability", "runner_up_genre", "runner_up_probability",
            "margin", "segment_variance"]
    tracks, genres = by(t["track"]["rows"], "track_id"), by(t["genre"]["rows"], "genre_id")
    dist = {}
    for g in t["genre_probability"]["rows"]:
        dist.setdefault((g["track_id"], g["model_id"]), []).append(g)
    out = []
    for s in t["track_score"]["rows"]:
        others = [g for g in dist.get((s["track_id"], s["model_id"]), []) if g["genre_id"] != s["genre_id"]]
        if not others or s["track_id"] not in tracks or s["genre_id"] not in genres:
            continue
        second = max(D(g["probability"]) for g in others)                                     # second_place
        runner = min(int(g["genre_id"]) for g in others if D(g["probability"]) == second)      # runner_up
        if str(runner) not in genres:
            continue
        top = D(s["top_probability"])
        margin = top - second
        out.append(((margin, int(s["track_id"]), int(s["model_id"])),
                    (D(s["track_id"]), tracks[s["track_id"]]["title"], D(s["model_id"]), genres[s["genre_id"]]["name"], top,
                     genres[str(runner)]["name"], second, margin,
                     None if s["segment_variance"] is None else D(s["segment_variance"]))))
    return cols, [r for _, r in sorted(out, key=lambda x: x[0])]


ORACLES = {"M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5, "M6": m6, "M7": m7}
