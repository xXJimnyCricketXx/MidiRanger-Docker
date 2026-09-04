# Port von dev-modus/alt/src/audio/backends/fluidsynth_backend.py.
# QThread -> threading.Thread (Signal/QObject -> Signal aus qt_signal.py),
# self.msleep(n) -> time.sleep(n/1000), .isRunning() -> .is_alive(),
# .wait(ms) -> .join(ms/1000). Ablauf/Werte ansonsten unverändert.
#
# Unter Windows wird das native libfluidsynth (aus dev-modus/alt kopiert,
# siehe assets/lib/) über PATH auffindbar gemacht, BEVOR das fluidsynth-
# Modul importiert wird - im Docker/Linux-Image kommt libfluidsynth
# stattdessen aus dem apt-Paket libfluidsynth3 und braucht das nicht.
import logging
import os
import platform
import threading
import time
import traceback

from . import paths

if platform.system() == 'Windows' and paths.FLUIDSYNTH_LIB_DIR.exists():
    lib_dir = str(paths.FLUIDSYNTH_LIB_DIR)
    if lib_dir not in os.environ.get('PATH', ''):
        os.environ['PATH'] = lib_dir + os.pathsep + os.environ.get('PATH', '')

import fluidsynth

from .qt_signal import Signal

logger = logging.getLogger('midiranger')


class MidiPlayerThread(threading.Thread):

    def __init__(self, midi_path: str, soundfont_path: str, initial_gain: float = 1.0):
        super().__init__(daemon=True)
        self.playback_started = Signal()
        self.playback_finished = Signal()
        self.playback_error = Signal()
        self.driver_detected = Signal()

        self.midi_path = midi_path
        self.soundfont_path = soundfont_path
        self.initial_gain = initial_gain
        self._stop_requested = False
        self.fs = None
        self.sfid = None
        self.active_driver = None

    def _detect_audio_driver(self):
        system = platform.system().lower()
        if system == "windows":
            return ["wasapi", "dsound", "portaudio", "winmm"]
        elif system == "linux":
            return ["pulseaudio", "alsa", "jack"]
        elif system == "darwin":
            return ["coreaudio"]
        return ["portaudio"]

    def run(self):
        try:
            logger.info(f"🎵 Starte Wiedergabe: {self.midi_path}")

            self.fs = fluidsynth.Synth()

            # Grund-Einstellungen
            self.fs.setting("synth.threadsafe-api", 1)
            self.fs.setting("synth.verbose", 0)
            self.fs.setting("midi.driver", "")
            self.fs.setting("midi.autoconnect", 0)

            # --- Versuche Audio-Treiber ---
            for driver in self._detect_audio_driver():
                try:
                    self.fs.setting("audio.driver", driver)
                    self.fs.start()
                    self.active_driver = driver

                    self.driver_detected.emit(driver)

                    logger.info(f"✅ Audio-Treiber gestartet: {driver}")
                    break
                except Exception as e:
                    logger.debug(f"⚠️ Audio-Treiber '{driver}' fehlgeschlagen: {e}")
            else:
                raise RuntimeError("Kein funktionierender Audio-Treiber gefunden!")

            try:
                self.fs.setting("synth.gain", float(self.initial_gain))
                logger.debug(f"🔊 Initial Gain übernommen: {self.initial_gain}")
            except Exception as e:
                logger.error(f"⚠️ Gain konnte nicht gesetzt werden: {e}")

            if not os.path.exists(self.soundfont_path):
                raise FileNotFoundError(f"SoundFont nicht gefunden: {self.soundfont_path}")

            self.sfid = self.fs.sfload(self.soundfont_path)
            self.fs.sfont_select(0, self.sfid)
            logger.debug(f"🎹 SoundFont geladen: {self.soundfont_path}")

            self.playback_started.emit(self.midi_path)

            status = self.fs.play_midi_file(self.midi_path)
            if status != fluidsynth.FLUID_OK:
                raise RuntimeError(f"FluidSynth-Fehler: Status={status}")

            while not self._stop_requested:
                try:
                    state = fluidsynth.fluid_player_get_status(self.fs.player)
                    if state == fluidsynth.FLUID_PLAYER_DONE:
                        break
                except Exception:
                    break
                time.sleep(0.1)

            self.playback_finished.emit(self.midi_path)

        except Exception as e:
            err_text = f"{e}\n{traceback.format_exc()}"
            logger.error(f"💥 Fehler bei Wiedergabe: {err_text}")
            self.playback_error.emit(str(e))

        finally:
            self.cleanup()

    def stop(self):
        self._stop_requested = True
        if not self.fs:
            return
        try:
            self.fs.play_midi_stop()
            for chan in range(16):
                try:
                    self.fs.cc(chan, 7, 0)
                except Exception:
                    pass
            time.sleep(0.12)
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Stoppen: {e}")

    def cleanup(self):
        try:
            if self.fs:
                try:
                    self.fs.all_notes_off(0)
                except Exception:
                    pass
                try:
                    self.fs.delete()
                except Exception:
                    pass
                logger.info("🧹 FluidSynth-Instanz beendet.")
                self.fs = None
        except Exception as e:
            logger.warning(f"⚠️ Cleanup-Fehler: {e}")
        finally:
            logger.debug("🔚 MidiPlayerThread vollständig beendet.")


# ============================================================

class FluidSynthBackend:

    def __init__(self):
        self.playback_started = Signal()
        self.playback_finished = Signal()
        self.playback_error = Signal()
        self.audio_driver_changed = Signal()

        self.thread = None
        self.sf2_path = str(paths.SOUNDFONT_PATH)
        self.pending_volume = 1.0
        logger.debug(f"🎼 FluidSynth Backend bereit – SF2: {self.sf2_path}")

    def set_volume(self, gain: float):
        """Setzt Master-Gain persistent und live."""
        gain = max(0.0, min(2.0, gain))
        self.pending_volume = gain

        if self.thread and self.thread.fs:
            try:
                self.thread.fs.setting("synth.gain", gain)
            except Exception as e:
                logger.warning(f"⚠️ Gain konnte nicht live gesetzt werden: {e}")

    def play(self, midi_path: str):
        self.stop()
        self.thread = MidiPlayerThread(
            midi_path,
            self.sf2_path,
            initial_gain=self.pending_volume
        )

        # Signale durchreichen
        self.thread.playback_started.connect(self.playback_started.emit)
        self.thread.playback_finished.connect(self.playback_finished.emit)
        self.thread.playback_error.connect(self.playback_error.emit)

        # Audio Driver weiterreichen
        self.thread.driver_detected.connect(self.audio_driver_changed.emit)

        self.thread.start()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.thread.stop()
            # Absicherung: .join() auf den eigenen (aktuell ausführenden)
            # Thread würde crashen statt nur RuntimeError zu werfen, siehe
            # player_controller.py::_on_backend_finished.
            if threading.current_thread() is not self.thread:
                self.thread.join(0.3)
        self.thread = None

    def is_playing(self):
        return bool(self.thread and self.thread.is_alive())

    def cleanup(self):
        self.stop()
