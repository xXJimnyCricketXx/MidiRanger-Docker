# Angelehnt an dev-modus/alt/src/services/missing_files_checker.py.
from . import paths
from .models import Song


def list_missing_songs():
    """Songs, deren Datei im midi/-Verzeichnis nicht (mehr) existiert."""
    existing = set()
    if paths.MIDI_DIR.exists():
        for path in paths.MIDI_DIR.rglob('*'):
            if path.is_file() and path.suffix.lower() in ('.mid', '.midi'):
                existing.add(str(path.relative_to(paths.MIDI_DIR)).replace('\\', '/'))

    return [song for song in Song.objects.all() if song.filename not in existing]
