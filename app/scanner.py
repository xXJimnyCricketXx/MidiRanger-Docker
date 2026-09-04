# Angelehnt an dev-modus/alt/src/services/scanner_service.py.
from . import paths
from .models import Song


def list_all_midi_files():
    if not paths.MIDI_DIR.exists():
        return []
    return list(paths.MIDI_DIR.rglob('*.mid')) + list(paths.MIDI_DIR.rglob('*.midi'))


def compare_with_database():
    """Liefert (new_files, missing_files) als relative Pfade zu MIDI_DIR.
    new_files = Dateien auf der Platte, die noch nicht in der DB stehen.
    missing_files = DB-Einträge ohne Datei (hier wie im Original ungenutzt,
    dafür ist "Datenbank prüfen" zuständig)."""
    db_files = set(Song.objects.values_list('filename', flat=True))

    fs_files = {
        str(f.relative_to(paths.MIDI_DIR)).replace('\\', '/')
        for f in list_all_midi_files()
    }

    new_files = sorted(fs_files - db_files)
    missing_files = sorted(db_files - fs_files)
    return new_files, missing_files
