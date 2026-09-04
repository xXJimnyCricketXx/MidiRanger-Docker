# Einmaliger Import aus der alten PySide6-App (dev-modus/alt/src/models/db/*.py,
# Schema: sources/songs/playlists/playlist_songs). filename/lyrics_filename sind
# dort bereits relativ zu midi/ (siehe songs_model.py::_row_to_dict) - identisch
# zu unserem Song.filename/lyrics_filename, daher reine Feldübernahme ohne
# Pfad-Umrechnung.
import sqlite3
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from app.models import Playlist, PlaylistSong, Song, Source


def _parse_imported_at(value):
    if not value:
        return None
    try:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


class Command(BaseCommand):
    help = 'Importiert Sources/Songs/Playlists aus einer alten midiranger.db (PySide6-Version).'

    def add_arguments(self, parser):
        parser.add_argument('legacy_db_path', help='Pfad zur alten midiranger.db')

    def handle(self, *args, **options):
        db_path = options['legacy_db_path']

        try:
            con = sqlite3.connect(db_path)
        except sqlite3.Error as e:
            raise CommandError(f'Konnte {db_path} nicht öffnen: {e}')

        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # --- Sources ---
        source_id_map = {}
        cur.execute('SELECT id, name FROM sources')
        for row in cur.fetchall():
            obj, _ = Source.objects.get_or_create(name=row['name'])
            source_id_map[row['id']] = obj
        self.stdout.write(f'{len(source_id_map)} Quelle(n) übernommen.')

        # --- Songs ---
        # Upsert (nicht skip-if-exists): ein erneuter Lauf gegen eine
        # aktualisierte Legacy-DB soll bestehende Zeilen auf den dortigen
        # Stand bringen, nicht bei der ersten Übernahme stehen bleiben.
        song_id_map = {}
        created_count = 0
        updated_count = 0
        cur.execute('SELECT * FROM songs')
        for row in cur.fetchall():
            filename = row['filename']
            bpm = row['bpm']
            if bpm in ('', None):
                bpm = None
            else:
                try:
                    bpm = int(bpm)
                except (TypeError, ValueError):
                    bpm = None

            fields = dict(
                title=row['title'],
                artist=row['artist'],
                genre=row['genre'],
                collection=row['collection'],
                source=source_id_map.get(row['source_id']),
                duration=row['duration'],
                bpm=bpm,
                key=row['key'],
                time_sig=row['time_sig'],
                is_edited=bool(row['is_edited']),
                is_favorite=bool(row['is_favorite']),
                is_selected=bool(row['is_selected']),
                comment=row['comment'],
                lyrics_filename=row['lyrics_filename'],
                missing=bool(row['missing']),
            )

            song, created = Song.objects.update_or_create(filename=filename, defaults=fields)

            imported_at = _parse_imported_at(row['imported_at'])
            if imported_at:
                Song.objects.filter(pk=song.pk).update(imported_at=imported_at)

            song_id_map[row['id']] = song
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(f'{created_count} Song(s) neu angelegt, {updated_count} bestehende Song(s) aktualisiert.')

        # --- Playlists ---
        playlist_id_map = {}
        cur.execute('SELECT id, name FROM playlists')
        for row in cur.fetchall():
            obj, _ = Playlist.objects.get_or_create(name=row['name'])
            playlist_id_map[row['id']] = obj
        self.stdout.write(f'{len(playlist_id_map)} Playlist(s) übernommen.')

        # --- Playlist-Zuordnungen ---
        link_created = 0
        cur.execute('SELECT playlist_id, song_id FROM playlist_songs')
        for order, row in enumerate(cur.fetchall()):
            playlist = playlist_id_map.get(row['playlist_id'])
            song = song_id_map.get(row['song_id'])
            if not playlist or not song:
                continue
            _, created = PlaylistSong.objects.get_or_create(
                playlist=playlist, song=song, defaults={'order': order}
            )
            if created:
                link_created += 1
        self.stdout.write(f'{link_created} Playlist-Zuordnung(en) übernommen.')

        con.close()
        self.stdout.write(self.style.SUCCESS(
            'Migration abgeschlossen. Bitte anschließend "Datenbank prüfen" im Tools-Menü '
            'ausführen, um den Missing-Status gegen den aktuellen midi/-Ordner zu aktualisieren.'
        ))
