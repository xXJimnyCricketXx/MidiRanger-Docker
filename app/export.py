# Angelehnt an dev-modus/alt/src/views/export_dialog.py (ExportWorker).
# Kein eigener Zielordner-Dialog - der Speicherort wird im Docker/Browser-
# Kontext vom Browser selbst bestimmt (Speichern-unter/Downloads-Ordner),
# genau wie im Original der Nutzer einen Ordner wählt. Die Originaldateien
# bleiben unangetastet, es werden nur Kopien ins ZIP gepackt.
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings

from . import paths

EXPORTS_DIR = settings.BASE_DIR / 'data' / 'exports'


class ExportError(Exception):
    pass


def create_export(songs):
    songs = list(songs)
    if not songs:
        raise ExportError('Es sind keine Songs ausgewählt. Bitte die Checkbox-Spalte verwenden.')

    paths.ensure(EXPORTS_DIR)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    zip_path = EXPORTS_DIR / f'MidiRanger_Export_{timestamp}.zip'

    added = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for song in songs:
            src = None

            if song.filename:
                candidate = paths.MIDI_DIR / song.filename
                if candidate.exists():
                    src = candidate

            # Fallback: rekursive Suche im midi/-Verzeichnis, falls der
            # gespeicherte Pfad veraltet ist (wie im Original).
            if src is None and song.filename:
                name = Path(song.filename).name
                matches = list(paths.MIDI_DIR.rglob(name)) or list(paths.MIDI_DIR.rglob(name.lower()))
                if matches:
                    src = matches[0]

            if not src or not src.exists():
                continue

            rel_path = src.relative_to(paths.MIDI_DIR)
            zipf.write(src, arcname=str(rel_path))
            added += 1

    if added == 0:
        zip_path.unlink(missing_ok=True)
        raise ExportError('Keine gültigen Dateien zum Export gefunden.')

    return str(zip_path), added
