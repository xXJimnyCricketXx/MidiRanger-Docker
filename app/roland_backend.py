# Port von dev-modus/alt/src/audio/backends/roland_backend.py. Nutzte im
# Original bereits threading.Thread (keine QThread) - einzige Änderung ist
# QObject/Signal -> Signal aus qt_signal.py (reine Callback-Liste statt
# Qt-Event-Mechanik, s. dort).
import logging
import os
import threading
import time
from typing import Optional, List, Set

import mido

from .qt_signal import Signal

logger = logging.getLogger('midiranger')


class RolandBackend:

    # ---------------------------------------------------------------------
    # Hardware-MIDI-Ausgabe
    #
    # Spielt SMF-Dateien über den gewählten MIDI-Out-Port.
    # ---------------------------------------------------------------------

    def __init__(self, device_name: Optional[str] = None, init_mode: str = "auto"):
        self.playback_started = Signal()
        self.playback_finished = Signal()
        self.playback_error = Signal()
        self.audio_driver_changed = Signal()

        self.outport: Optional[mido.ports.BaseOutput] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.device_name = device_name
        self.current_midi: Optional[str] = None
        self._pending_volume: float = 1.0
        self._init_mode = (init_mode or "auto").lower()

        logger.debug("🎹 RolandBackend initialisiert.")
        self._open_port()

    # ---------------------------------------------------------------------
    # Ports
    # ---------------------------------------------------------------------
    @staticmethod
    def list_output_ports() -> List[str]:
        try:
            return mido.get_output_names()
        except Exception as e:
            logger.error(f"💥 Auslesen der MIDI-Out-Ports fehlgeschlagen: {e}")
            return []

    def _choose_port_name(self) -> Optional[str]:
        outputs = self.list_output_ports()
        logger.debug(f"🎛 Verfügbare MIDI-Out Ports: {outputs}")
        if not outputs:
            return None

        if self.device_name and self.device_name in outputs:
            return self.device_name

        umone = [n for n in outputs if "um-one" in n.lower()]
        if umone:
            return umone[-1]

        roland = [n for n in outputs if "roland" in n.lower()]
        if roland:
            return roland[-1]

        generic = [n for n in outputs if all(s not in n.lower() for s in ["microsoft gs", "virtualmidisynth"])]
        if generic:
            return generic[0]

        return outputs[0]

    def _open_port(self):
        try:
            chosen = self._choose_port_name()
            if not chosen:
                logger.error("❌ Keine MIDI-Out-Ports gefunden!")
                self.outport = None
                return
            self.outport = mido.open_output(chosen)
            self.device_name = chosen
            logger.info(f"🔌 MIDI-Out geöffnet: {self.device_name}")
            self.audio_driver_changed.emit(self.device_name)
        except Exception as e:
            logger.error(f"💥 Fehler beim Öffnen des MIDI-Out Ports: {e}")
            self.outport = None

    # ---------------------------------------------------------------------
    # Resets & Preludes
    # ---------------------------------------------------------------------
    def _send_gm_reset(self):
        if not self.outport:
            return
        try:
            self.outport.send(mido.Message('sysex', data=[0x7E, 0x7F, 0x09, 0x01]))
            logger.debug("♻️ GM Reset gesendet.")
        except Exception:
            pass

    def _send_gs_reset(self):
        if not self.outport:
            return
        try:
            self.outport.send(mido.Message('sysex', data=[0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00, 0x41]))
            logger.debug("♻️ GS Reset gesendet.")
        except Exception:
            pass

    def _send_xg_reset(self):
        if not self.outport:
            return
        try:
            self.outport.send(mido.Message('sysex', data=[0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00]))
            logger.debug("♻️ XG Reset gesendet.")
        except Exception:
            pass

    def _all_notes_off(self):
        if not self.outport:
            return
        for ch in range(16):
            for cc in (120, 121, 123, 64):
                try:
                    self.outport.send(mido.Message('control_change', channel=ch, control=cc, value=0))
                except Exception:
                    pass

    def _apply_initial_mix(self, used_channels: Set[int], gentle: bool = False):
        if not self.outport:
            return

        channels = used_channels or set(range(16))

        if gentle:
            for ch in channels:
                for cc in (121, 123, 64):
                    try:
                        self.outport.send(mido.Message('control_change', channel=ch, control=cc, value=0))
                    except Exception:
                        pass
            logger.debug("🪶 Gentle-Prelude gesendet.")
            return

        vol = max(0, min(127, int(round(self._pending_volume * 127))))
        for ch in channels:
            for (cc, val) in ((7, vol), (11, 127), (10, 64)):
                try:
                    self.outport.send(mido.Message('control_change', channel=ch, control=cc, value=val))
                except Exception:
                    pass
        for ch in channels:
            for (cc, val) in ((125, 0), (127, 0)):
                try:
                    self.outport.send(mido.Message('control_change', channel=ch, control=cc, value=val))
                except Exception:
                    pass
        logger.debug(f"🎚 Full-Prelude gesetzt (Channels: {sorted(list(channels))})")

    # ---------------------------------------------------------------------
    # Helpers / Detection / Diagnose
    # ---------------------------------------------------------------------
    @staticmethod
    def _scan_file_usage(mid: mido.MidiFile) -> Set[int]:
        used = set()
        for tr in mid.tracks:
            for msg in tr:
                if not msg.is_meta and hasattr(msg, "channel"):
                    used.add(int(msg.channel))
        return used

    @staticmethod
    def _detect_reset_from_sysex(mid: mido.MidiFile) -> Optional[str]:
        for tr in mid.tracks:
            for msg in tr:
                if msg.type == 'sysex':
                    data = list(msg.data)
                    if len(data) >= 4 and data[:4] == [0x7E, 0x7F, 0x09, 0x01]:
                        return "gm"
                    if data[:9] == [0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00, 0x41]:
                        return "gs"
                    if data[:7] == [0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00]:
                        return "xg"
        return None

    def _log_initial_programs(self, mid: mido.MidiFile):
        seen = {}
        for tr in mid.tracks:
            for msg in tr:
                if msg.is_meta:
                    continue
                if msg.type == "program_change":
                    ch = int(getattr(msg, "channel", -1))
                    if ch not in seen:
                        seen[ch] = msg.program
        if seen:
            items = ", ".join(f"ch{ch+1}:{prg}" for ch, prg in sorted(seen.items()))
            logger.info(f"🎛 Initiale Program Changes: {items}")
        else:
            logger.info("🎛 Keine Program Changes im File gefunden (früh).")

    def _count_notes(self, mid: mido.MidiFile) -> dict:
        counts = {ch: 0 for ch in range(16)}
        for tr in mid.tracks:
            for msg in tr:
                if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                    ch = int(getattr(msg, "channel", -1))
                    if 0 <= ch < 16:
                        counts[ch] += 1
        return counts

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def set_init_mode(self, mode: str):
        mode = (mode or "").lower()
        if mode in ("gm", "gs", "xg", "auto", "none"):
            self._init_mode = mode
            logger.info(f"🎛 Reset-Init-Mode gesetzt auf: {mode}")
        else:
            logger.warning(f"Unbekannter init_mode '{mode}', unverändert gelassen.")

    def set_volume(self, value: float):
        self._pending_volume = max(0.0, min(1.0, float(value)))
        if self.outport is None:
            return
        try:
            cc_val = int(round(self._pending_volume * 127))
            for ch in range(16):
                try:
                    self.outport.send(mido.Message('control_change', channel=ch, control=7, value=cc_val))
                except Exception:
                    pass
            logger.debug(f"🔊 CC7 Master-Volume live gesetzt: {cc_val}")
        except Exception as e:
            logger.warning(f"⚠️ Volume konnte nicht live gesetzt werden: {e}")

    def play(self, midi_path: str):
        self.stop()

        if not self.outport:
            msg = "Kein MIDI-Out verfügbar."
            logger.error(f"❌ {msg}")
            self.playback_error.emit(msg)
            return

        if not os.path.exists(midi_path):
            msg = f"MIDI-Datei nicht gefunden: {midi_path}"
            logger.error(f"❌ {msg}")
            self.playback_error.emit(msg)
            return

        logger.info(f"▶️ Roland: Spiele {os.path.basename(midi_path)}")
        self.current_midi = midi_path
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._play_thread, daemon=True)
        self._thread.start()

    def _play_thread(self):
        try:
            mid = mido.MidiFile(self.current_midi)

            used_ch = self._scan_file_usage(mid)
            logger.info(f"🎯 Kanäle im File: {sorted(list(used_ch)) or '—'}")
            self._log_initial_programs(mid)
            note_counts = self._count_notes(mid)
            nonzero = {ch + 1: c for ch, c in note_counts.items() if c > 0}
            logger.info(f"🎹 Note-On pro Kanal: {nonzero if nonzero else '—'}")

            detected_mode = self._detect_reset_from_sysex(mid) if self._init_mode == "auto" else None
            mode = detected_mode or (self._init_mode if self._init_mode in ("gm", "gs", "xg", "none") else "gs")

            # Startsignal
            self.playback_started.emit(self.current_midi or "")

            # Reset/Prelude-Logik
            if mode == "none":
                logger.info("🚫 Kein Reset/Prelude (init_mode=none).")
            elif detected_mode:
                logger.info(f"🧠 File-Init erkannt: {detected_mode.upper()} – kein eigener Reset, gentle-Prelude.")
                self._apply_initial_mix(used_ch, gentle=True)
            else:
                if mode == "gm":
                    self._send_gm_reset()
                elif mode == "xg":
                    self._send_xg_reset()
                else:
                    self._send_gs_reset()
                time.sleep(0.05)
                self._apply_initial_mix(used_ch, gentle=False)

            # Playback in Echtzeit
            for msg in mid.play():
                if self._stop_event.is_set():
                    break
                try:
                    if not msg.is_meta:
                        self.outport.send(msg)
                except Exception as e:
                    logger.debug(f"⚠️ Sendefehler: {e}")

        except Exception as e:
            logger.error(f"💥 Fehler beim Senden von MIDI-Events: {e}")
            self.playback_error.emit(str(e))
        finally:
            self.playback_finished.emit(self.current_midi or "")

    def stop(self):
        if self._thread and self._thread.is_alive():
            logger.debug("🛑 Roland: Stoppe Wiedergabe...")
            self._stop_event.set()
            # Absicherung: .join() auf den eigenen (aktuell ausführenden)
            # Thread würde crashen statt nur RuntimeError zu werfen, siehe
            # player_controller.py::_on_backend_finished.
            if threading.current_thread() is not self._thread:
                self._thread.join(timeout=1.0)

        try:
            self._all_notes_off()
        except Exception:
            pass

        self._thread = None
        self._stop_event.clear()

    def is_playing(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def cleanup(self):
        self.stop()
        if self.outport:
            try:
                self.outport.close()
                logger.debug("🎛 Roland MIDI-Out geschlossen.")
            except Exception:
                pass
        self.outport = None
