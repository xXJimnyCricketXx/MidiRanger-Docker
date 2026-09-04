# Singleton-Zugriff auf DEN EINEN PlayerController-Prozess. Original hatte
# eine PlayerController-Instanz pro laufender Desktop-App (MainWindow.player);
# bei uns entsprechend eine pro Django-Prozess statt pro Fenster - für einen
# selbst gehosteten Single-User/Haushalt-Einsatz ohne horizontale Skalierung
# eine treue Entsprechung.
import logging

from .models import Settings
from .player_controller import PlayerController

logger = logging.getLogger('midiranger')

_player = None


def _broadcast(event, **data):
    """Ersetzt die Qt-Signal-Verbindung PlayerWidget<->PlayerController: statt
    eines direkten Methodenaufrufs im selben Prozess geht die Nachricht hier
    an alle per WebSocket verbundenen Browser-Tabs (channels/consumers.py)."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)('player_status', {
            'type': 'player_event',
            'data': {'event': event, **data},
        })
    except Exception:
        logger.exception('💥 Fehler beim Broadcast des Player-Status')


def get_player() -> PlayerController:
    global _player
    if _player is None:
        settings = Settings.load()
        logger.debug(f"🎧 Erzeuge PlayerController-Singleton (Backend={settings.backend})")
        _player = PlayerController(backend_name=settings.backend)
        _player.engine.set_volume(settings.master_volume / 100)

        _player.playback_started.connect(
            lambda song_data: _broadcast('started', id=song_data.get('id'), title=song_data.get('title'), artist=song_data.get('artist'))
        )
        _player.playback_stopped.connect(lambda: _broadcast('stopped'))
    return _player
