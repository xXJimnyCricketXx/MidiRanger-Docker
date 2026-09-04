# Port von dev-modus/alt/src/services/metadata_extractor.py - unverändert,
# das Original hatte keinerlei Qt-Abhängigkeit (reines mido + Mathe).
#
# Rückgabeformat (immer gleich):
# {
#     "filename": "Song.mid",
#     "bpm": int | None,
#     "key": str | None,
#     "time_sig": "4/4" | None,
#     "duration_sec": float | None,
#     "duration_formatted": "MM:SS" | None,
#     "tracks": int,
#     "channels": int,
#     "instruments": ["Program 0", ...],
#     "error": None | "Fehlermeldung"
# }

import os
from math import sqrt
from typing import Optional, Dict, Any, List
from mido import MidiFile

MAJOR_PROFILE = [
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
    2.52, 5.19, 2.39, 3.66, 2.29, 2.88
]

MINOR_PROFILE = [
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
    2.54, 4.75, 3.98, 2.69, 3.34, 3.17
]

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]


def _correlation(a: List[float], b: List[float]) -> float:
    sum_ab = sum(x * y for x, y in zip(a, b))
    sum_a2 = sum(x * x for x in a)
    sum_b2 = sum(x * x for x in b)

    if sum_a2 == 0 or sum_b2 == 0:
        return 0.0

    return sum_ab / (sqrt(sum_a2) * sqrt(sum_b2))


def _detect_key_from_histogram(hist: List[int]) -> Optional[str]:
    if not hist or sum(hist) == 0:
        return None

    h = [float(x) for x in hist]
    best_score = -1.0
    best_key = None

    for root in range(12):
        major_profile = [MAJOR_PROFILE[(i - root) % 12] for i in range(12)]
        score_major = _correlation(h, major_profile)
        if score_major > best_score:
            best_score = score_major
            best_key = NOTE_NAMES[root]

        minor_profile = [MINOR_PROFILE[(i - root) % 12] for i in range(12)]
        score_minor = _correlation(h, minor_profile)
        if score_minor > best_score:
            best_score = score_minor
            best_key = NOTE_NAMES[root] + "m"

    return best_key


def _pitch_class_histogram(mid: MidiFile) -> List[int]:
    hist = [0] * 12

    for track in mid.tracks:
        for msg in track:
            if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                ch = getattr(msg, "channel", 0)
                if ch == 9:
                    continue
                hist[msg.note % 12] += 1

    return hist


def _extract_bpm(mid: MidiFile) -> Optional[int]:
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return int(60000000 / msg.tempo)
    return None


def _extract_time_signature(mid: MidiFile) -> Optional[str]:
    for track in mid.tracks:
        for msg in track:
            if msg.type == "time_signature":
                return f"{msg.numerator}/{msg.denominator}"
    return "4/4"


def _extract_duration(mid: MidiFile) -> float:
    return mid.length


def _extract_mixer_data(mid: MidiFile):
    tracks_count = len(mid.tracks)
    channel_set = set()
    instruments = set()

    for track in mid.tracks:
        for msg in track:
            if hasattr(msg, "channel"):
                channel_set.add(msg.channel)

            if msg.type == "program_change":
                instruments.add(f"Program {msg.program}")

    return tracks_count, len(channel_set), sorted(instruments)


def analyze_midi(path: str) -> Dict[str, Any]:
    filename = os.path.basename(path)

    try:
        mid = MidiFile(path)

        bpm = _extract_bpm(mid)
        duration_sec = _extract_duration(mid)
        time_sig = _extract_time_signature(mid)

        minutes = int(duration_sec // 60)
        seconds = int(duration_sec % 60)
        duration_formatted = f"{minutes:02}:{seconds:02}"

        hist = _pitch_class_histogram(mid)
        key = _detect_key_from_histogram(hist)

        tracks, channels, instruments = _extract_mixer_data(mid)

        return {
            "filename": filename,
            "bpm": bpm,
            "key": key,
            "time_sig": time_sig,
            "duration_sec": duration_sec,
            "duration_formatted": duration_formatted,
            "tracks": tracks,
            "channels": channels,
            "instruments": instruments,
            "error": None,
        }

    except Exception as e:
        return {
            "filename": filename,
            "bpm": None,
            "key": None,
            "time_sig": None,
            "duration_sec": None,
            "duration_formatted": None,
            "tracks": 0,
            "channels": 0,
            "instruments": [],
            "error": str(e),
        }
