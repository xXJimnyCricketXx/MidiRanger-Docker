# Angelehnt an dev-modus/alt/src/utils/backup_worker.py. Original zippt das
# komplette App-Root-Verzeichnis (shutil.make_archive über get_root_dir()) -
# bei uns sinnvoll eingegrenzt auf die tatsächlich schützenswerten Daten
# (DB + midi/-Bibliothek), nicht den Code/venv. Fester Zielordner statt
# Ordnerauswahl, da der Docker-Container einen festen appdata-Mount nutzt.
import os
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings

from . import paths

# MR_DATA_DIR wird nur im Docker-Image gesetzt (fester Appdata-Mount, siehe
# Kommentar oben) - lokal unverändert BASE_DIR/data/backups.
_data_dir_env = os.environ.get('MR_DATA_DIR')
BACKUPS_DIR = (Path(_data_dir_env) / 'backups') if _data_dir_env else (settings.BASE_DIR / 'data' / 'backups')
DB_PATH = Path(settings.DATABASES['default']['NAME'])


def create_backup() -> str:
    paths.ensure(BACKUPS_DIR)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    zip_path = BACKUPS_DIR / f'MidiRanger_Backup_{timestamp}.zip'

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if DB_PATH.exists():
            zipf.write(DB_PATH, arcname='db.sqlite3')

        if paths.MIDI_DIR.exists():
            for file_path in paths.MIDI_DIR.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, arcname=str(Path('midi') / file_path.relative_to(paths.MIDI_DIR)))

    return str(zip_path)
