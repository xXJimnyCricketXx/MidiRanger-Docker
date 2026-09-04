# Singleton-Zugriff auf den aktuell geöffneten Mixer (entspricht: im Original
# wird bei jedem Öffnen des MixerDialog ein frischer MixerService erzeugt und
# neu analysiert; Regler-Änderungen leben nur so lange, wie der Dialog offen
# ist). Bei uns: jeder GET auf /mixer/<song_id> erzeugt eine frische Instanz,
# nachfolgende AJAX-Regler-Aufrufe für dieselbe Song-ID nutzen dieselbe.
import logging

from .mixer_service import MixerService
from .player import get_player

logger = logging.getLogger('midiranger')

_current_song_id = None
_current_service: MixerService | None = None


def open_mixer(song_id: int, midi_path: str) -> MixerService:
    global _current_song_id, _current_service
    logger.debug(f"🎚 MixerService neu geladen für Song-ID {song_id}")
    _current_service = MixerService(midi_path, player=get_player())
    _current_service.load()
    _current_song_id = song_id
    return _current_service


def get_mixer_service(song_id: int) -> MixerService | None:
    if _current_song_id == song_id:
        return _current_service
    return None
