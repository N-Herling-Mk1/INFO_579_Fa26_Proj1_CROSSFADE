"""Independent answers for routines.sql, computed in plain Python from data.csv (no SQL, no database).

Each function takes the tables as load_bulk returns them ({table: {"columns", "rows"}}, values as text or None),
so a test can add rows to a copy and ask again. They follow the requirements analysis (RA) directly:

  royalty(t, track_id, seconds)   rule I7: the owning artist's payout rate for 30 seconds or more, else 0;
                                  None when the recording does not exist
  record_play(t, ...)             what record_play must do: the row it writes, or the refusal it must give
  upload(t, ...)                  what upload_track must do: a new track awaiting scoring, a duplicate answer,
                                  or a refusal
"""
from decimal import Decimal

D = Decimal


def _row(t, table, **key):
    for r in t[table]["rows"]:
        if all(str(r[k]) == str(v) for k, v in key.items()):
            return r
    return None


def royalty(t, track_id, seconds):
    """Rule I7 (RA): Royalty Amount equals the artist's Payout Rate for a play of 30 seconds or more, zero
    otherwise. DECIMAL(5,5), so the answer has five decimals."""
    tr = _row(t, "track", track_id=track_id)
    if tr is None or seconds is None:
        return None
    rate = D(_row(t, "artist", artist_id=tr["artist_id"])["payout_rate"])
    return (rate if int(seconds) >= 30 else D(0)).quantize(D("0.00001"))


def record_play(t, listener_id, track_id, station_id, seconds, reaction, played_at):
    """("row", {column: value}) for the play record_play must write, or ("refuse", code, words in the message).
    1644 = SIGNAL SQLSTATE '45000' (the procedure's own refusal); 1062 / 1452 = the database's (key, foreign key)."""
    tr = _row(t, "track", track_id=track_id)
    if tr is None:
        return ("refuse", 1644, f"track {track_id} does not exist")
    if tr["ingest_status"] != "scored":
        return ("refuse", 1644, f"track {track_id} is not released for streaming ({tr['ingest_status']})")
    if int(seconds) > int(tr["duration"]):
        return ("refuse", 1644, f"{seconds} seconds played, but track {track_id} is only {tr['duration']} seconds long")
    if _row(t, "listener", listener_id=listener_id) is None:
        return ("refuse", 1452, "fk_play_listener")
    if station_id is not None and _row(t, "station", station_id=station_id) is None:
        return ("refuse", 1452, "fk_play_station")
    if played_at is not None and _row(t, "play", listener_id=listener_id, track_id=track_id, played_at=played_at):
        return ("refuse", 1062, "PRIMARY")
    return ("row", {"listener_id": int(listener_id), "track_id": int(track_id), "played_at": played_at,
                    "station_id": None if station_id is None else int(station_id), "seconds_played": int(seconds),
                    "completed": int(int(seconds) == int(tr["duration"])), "reaction": reaction,
                    "royalty_amount": royalty(t, track_id, seconds)})


def upload(t, artist_id, title, duration, release_date, checksum_hex):
    """What upload_track must answer: ("uploaded", new track_id, row), ("duplicate", existing track_id, title),
    or ("refuse", code, words). checksum_hex is the 64-digit hexadecimal SHA-256 of the audio."""
    if _row(t, "artist", artist_id=artist_id) is None:
        return ("refuse", 1644, f"artist {artist_id} is not registered")
    if duration is not None and int(duration) <= 0:
        return ("refuse", 3819, "ck_track_duration")
    if title is None:
        return ("refuse", 1048, "title")
    want = "0x" + checksum_hex.upper()
    for r in t["track"]["rows"]:
        if str(r["audio_checksum"])[2:].upper() == checksum_hex.upper():
            return ("duplicate", int(r["track_id"]), r["title"])
    new_id = max(int(r["track_id"]) for r in t["track"]["rows"]) + 1
    return ("uploaded", new_id, {"track_id": new_id, "artist_id": int(artist_id), "title": title,
                                 "duration": int(duration), "release_date": release_date, "audio_checksum": want,
                                 "ingest_status": "awaiting scoring"})
