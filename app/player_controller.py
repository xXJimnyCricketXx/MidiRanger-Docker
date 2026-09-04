# Port von dev-modus/alt/src/controllers/player_controller.py. QObject/Signal
# -> Signal aus qt_signal.py. source_view/row (Qt-Tabellenzeilen-Referenz für
# das Play/Stop-Icon) entfällt - der Browser aktualisiert sein eigenes Icon
# anhand der Song-ID aus der Antwort/dem Live-Status, siehe player_state.py.
import logging
from pathlib import Path
from typing import Optional

from .midi_engine import MidiEngine
from .player_state import PlayerState
from .qt_signal import Signal
from .session_log import SessionLog

logger = logging.getLogger('midiranger')


class PlayerController:

    def __init__(self, engine: Optional[MidiEngine] = None, backend_name: str = "fluidsynth"):
        self.playback_started = Signal()
        self.playback_stopped = Signal()
        self.playback_error = Signal()
        self.audio_output_changed = Signal()

        if engine is not None:
            self.engine = engine
            logger.debug("🎧 PlayerController initialisiert → bestehende Engine übernommen")
        else:
            logger.debug(f"🎧 PlayerController initialisiert → Backend={backend_name}")
            self.engine = MidiEngine(backend_name)

        # Backend-Signale verbinden
        try:
            self.engine.backend.playback_started.connect(self._on_backend_started)
            self.engine.backend.playback_finished.connect(self._on_backend_finished)
            self.engine.backend.playback_error.connect(self._on_backend_error)

            # Wird von FluidSynth beim Driver-Detect und vom Roland-Backend beim Port-Open emittiert
            if hasattr(self.engine.backend, "audio_driver_changed"):
                self.engine.backend.audio_driver_changed.connect(self.audio_output_changed.emit)
        except Exception as e:
            logger.debug(f"ℹ Backend-Signalverkabelung übersprungen: {e}")

        self.state = PlayerState()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def play(self, song_data: dict):
        """
        song_data erwartet mindestens:
            {"path": <voller_midi_pfad>, "id": int?, "title": str?, "artist": str?}
        """
        try:
            midi_path = song_data.get("path")
            if not midi_path:
                msg = "Songdaten unvollständig (kein Pfad)."
                logger.error(f"❌ {msg}")
                self.playback_error.emit(msg)
                return

            midi_path = Path(midi_path)

            if not midi_path.exists():
                msg = f"❌ Datei nicht gefunden: {midi_path}"
                logger.error(msg)
                self.playback_error.emit(msg)
                return

            if self.engine.is_playing():
                logger.debug("🔁 Stoppe vorherige Wiedergabe …")
                self.stop()

            logger.info(f"▶️ Starte Song: {song_data.get('title')}")

            self.state.current_song = song_data
            self.state.current_song_id = song_data.get("id")
            self.state.is_playing = True

            # WICHTIG: FluidSynth benötigt einen String, nicht Path!
            self.engine.play(str(midi_path))

            self.playback_started.emit(song_data)

            try:
                title = song_data.get("title") or midi_path.stem or "(ohne Titel)"
                SessionLog().add_recent_play(title=title)
            except Exception as e:
                logger.debug(f"SessionLog add_recent_play übersprungen: {e}")

        except Exception as e:
            logger.exception(f"💥 Fehler in PlayerController.play(): {e}")
            self.playback_error.emit(str(e))

    def stop(self):
        if not self.state.is_playing:
            return

        logger.info("⏹ Stoppe Wiedergabe …")

        # State ZUERST zurücksetzen, noch bevor engine.stop() blockierend auf
        # den Wiedergabe-Thread wartet: erreicht dessen eigene "von selbst
        # beendet"-Meldung (_on_backend_finished) uns währenddessen aus dem
        # anderen Thread, sieht deren is_playing-Check bereits False und
        # bricht ab, statt ein zweites playback_stopped zu emittieren.
        self.state.reset()

        try:
            self.engine.stop()
        except Exception as e:
            logger.debug(f"⚠️ Engine.stop() meldete: {e}")

        self.playback_stopped.emit()

    def emit_error(self, msg: str):
        logger.error(f"❌ Playback Error: {msg}")
        self.playback_error.emit(msg)

    # ---------------------------------------------------------------------
    # Live CC (nur sinnvoll, wenn FluidSynth aktiv ist)
    # ---------------------------------------------------------------------
    def _send_cc(self, channel: int, control: int, value: int):
        try:
            backend = getattr(self.engine, "backend", None)
            if backend and hasattr(backend, "thread") and backend.thread and getattr(backend.thread, "fs", None):
                backend.thread.fs.cc(channel, control, value)
        except Exception as e:
            logger.debug(f"⚠️ CC konnte nicht gesendet werden: ch={channel}, cc={control}, value={value} ({e})")

    def set_expression_live(self, ch: int, value: int):
        vol = max(0, min(127, int(value)))
        self._send_cc(ch, 11, vol)

    def set_pan_live(self, ch: int, pan: int):
        cc_val = max(0, min(127, 64 + int(pan)))
        self._send_cc(ch, 10, cc_val)

    # ---------------------------------------------------------------------
    # Backend Events
    # ---------------------------------------------------------------------
    def _on_backend_started(self, midi_path: str):
        logger.debug("🔊 Backend meldet: Wiedergabe gestartet")

    def _on_backend_finished(self, midi_path: str):
        # Original bekommt dieses Signal per Qt-Cross-Thread-Queued-Connection
        # erst im Haupt-Thread zugestellt, NACHDEM der Worker-Thread bereits
        # fertig ist - dort ist self.stop() (das den Worker-Thread joint)
        # unproblematisch. Unsere Signal-Klasse ruft Callbacks synchron im
        # EMITTIERENDEN Thread auf; hier ist das der Worker-Thread selbst,
        # der sich damit gerade selbst joinen würde (Absturz). Deshalb hier
        # nur den State zurücksetzen statt engine.stop() erneut aufzurufen.
        logger.debug("⏹ Backend meldet: Wiedergabe beendet")
        if not self.state.is_playing:
            return
        self.state.reset()
        self.playback_stopped.emit()

    def _on_backend_error(self, msg: str):
        logger.error(f"💥 Backend Error: {msg}")
        self.playback_error.emit(msg)
