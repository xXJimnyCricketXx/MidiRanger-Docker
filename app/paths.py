# Port von dev-modus/alt/src/utils/path_utils.py - dieselbe flache
# Verzeichnisstruktur (midi/ liegt wie im Original neben der App, nicht
# unter data/), damit spätere Docker-Volumes 1:1 übertragbar bleiben.
import os
from pathlib import Path

from django.conf import settings

# MR_MIDI_DIR wird nur im Docker-Image gesetzt (Mount auf den vom User
# gewählten Ordner, z.B. einen Netzwerk-Share). Lokal unverändert BASE_DIR/midi.
_midi_dir_env = os.environ.get('MR_MIDI_DIR')
MIDI_DIR = Path(_midi_dir_env) if _midi_dir_env else (settings.BASE_DIR / 'midi')
UPLOADS_DIR = MIDI_DIR / 'uploads'
LYRICS_DIR = MIDI_DIR / 'lyrics'
MIXER_OUTPUT_DIR = MIDI_DIR / 'mixer_output'
ORIGINALS_DIR = MIDI_DIR / 'originals'
TMP_DIR = settings.BASE_DIR / 'data' / 'tmp'

# Aus dev-modus/alt/src/assets kopiert (FluidSynth-Soundfont + native
# Windows-DLLs für die lokale Entwicklung, nicht Teil des Git-Repos - im
# Docker/Linux-Image kommen beide stattdessen aus apt-Paketen
# (libfluidsynth3 + fluid-soundfont-gm, siehe Dockerfile/MR_SOUNDFONT_PATH),
# u.a. weil die 142 MB des Soundfonts über GitHubs 100-MB-Push-Limit liegen.
ASSETS_DIR = settings.BASE_DIR / 'assets'
_soundfont_env = os.environ.get('MR_SOUNDFONT_PATH')
SOUNDFONT_PATH = Path(_soundfont_env) if _soundfont_env else (ASSETS_DIR / 'sf2' / 'FluidR3_GM.sf2')
FLUIDSYNTH_LIB_DIR = ASSETS_DIR / 'lib'


def ensure(path):
    path.mkdir(parents=True, exist_ok=True)
    return path
