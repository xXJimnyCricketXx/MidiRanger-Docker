# Port von dev-modus/alt/src/models/player_state.py. current_view/current_row
# gab im Original das Icon der auslösenden Tabellenzeile direkt zurück (Qt-
# Objektreferenz) - im Browser übernimmt das der Client selbst anhand der
# Song-ID aus der Start/Stop/Finished-Antwort, deshalb hier current_song_id
# statt einer View-Referenz.
class PlayerState:
    def __init__(self):
        self.current_song = None       # dict mit: path, title, artist, id
        self.current_song_id = None
        self.is_playing = False

    def reset(self):
        self.current_song = None
        self.current_song_id = None
        self.is_playing = False
