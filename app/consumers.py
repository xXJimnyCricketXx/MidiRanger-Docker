# Ersetzt Qt's Cross-Thread-Signal-Zustellung an die UI: der PlayerController
# (app/player.py) sendet bei playback_started/playback_stopped eine Nachricht
# an diese Gruppe, jeder verbundene Browser-Tab bekommt sie live zugestellt
# (Statusleiste + Play/Stop-Icon in der Songtabelle reagieren ohne Reload,
# insbesondere wenn ein Song von selbst zu Ende ist).
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class PlayerStatusConsumer(WebsocketConsumer):
    group_name = 'player_status'

    def connect(self):
        if not self.scope['user'].is_authenticated:
            self.close()
            return
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def player_event(self, event):
        self.send(text_data=json.dumps(event['data']))
