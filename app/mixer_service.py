# Port von dev-modus/alt/src/services/mixer_service.py - reine mido-Logik,
# keine Qt-Abhängigkeit außer der optionalen player-Referenz für Live-CC
# (PlayerController.set_expression_live/set_pan_live/_send_cc, unverändert).
import os
from pathlib import Path
from typing import Dict, List

from mido import MidiFile, MidiTrack, Message

import logging

from . import paths
from .midi_channel_state import MidiChannelState
from .gm_instruments import get_instrument_name, get_drumkit_name

logger = logging.getLogger('midiranger')


class MixerService:

    def __init__(self, midi_path: str, player=None):
        self.midi_path = midi_path
        self.mid: MidiFile | None = None
        self.channels: Dict[int, MidiChannelState] = {}
        self.player = player

    # ---------------------------------------------------------
    # Laden und Analysieren der MIDI-Datei
    # ---------------------------------------------------------
    def load(self):
        if not os.path.exists(self.midi_path):
            raise FileNotFoundError(f"MIDI-Datei nicht gefunden: {self.midi_path}")

        logger.debug(f"🎚 MixerService: Lade MIDI → {self.midi_path}")
        self.mid = MidiFile(self.midi_path)

        self._analyze_channels()

    def _get_or_create_channel(self, ch: int) -> MidiChannelState:
        if ch not in self.channels:
            self.channels[ch] = MidiChannelState(channel=ch)
        return self.channels[ch]

    # ---------------------------------------------------------
    # MIDI-Analyse
    # ---------------------------------------------------------
    def _analyze_channels(self):
        assert self.mid is not None

        events = {ch: {"cc7": [], "cc11": [], "cc10": [], "note_on": []} for ch in range(16)}

        for track in self.mid.tracks:
            abs_time = 0
            for msg in track:
                abs_time += msg.time

                if not hasattr(msg, "channel"):
                    continue

                ch = msg.channel

                if msg.type == "note_on" and msg.velocity > 0:
                    events[ch]["note_on"].append(abs_time)

                elif msg.type == "control_change":
                    if msg.control == 7:
                        events[ch]["cc7"].append((abs_time, msg.value))
                    elif msg.control == 11:
                        events[ch]["cc11"].append((abs_time, msg.value))
                    elif msg.control == 10:
                        events[ch]["cc10"].append((abs_time, msg.value))

                elif msg.type == "program_change":
                    state = self._get_or_create_channel(ch)
                    state.program = msg.program
                    if ch == 9:
                        state.instrument = get_drumkit_name(msg.program)
                    else:
                        state.instrument = get_instrument_name(msg.program)

        for ch, data in events.items():
            state = self._get_or_create_channel(ch)

            state.note_count = len(data["note_on"])

            first_note = min(data["note_on"]) if data["note_on"] else None

            if first_note is not None:
                cc7_before = [v for t, v in data["cc7"] if t <= first_note]
                state.volume = cc7_before[-1] if cc7_before else 100
            else:
                state.volume = 100

            if first_note is not None:
                cc11_before = [v for t, v in data["cc11"] if t <= first_note]
                state.expression = cc11_before[-1] if cc11_before else 127
            else:
                state.expression = 127

            if first_note is not None:
                cc10_before = [v for t, v in data["cc10"] if t <= first_note]
                state.pan = (cc10_before[-1] - 64) if cc10_before else 0
            else:
                state.pan = 0

        # Nur Kanäle behalten, die überhaupt Note-On Events hatten
        self.channels = {
            ch: state for ch, state in self.channels.items()
            if getattr(state, "note_count", 0) > 0
        }

        logger.debug(f"🎚 MixerService: aktive Channels: {list(self.channels.keys())}")

    def get_channel_states(self) -> List[MidiChannelState]:
        return [self.channels[ch] for ch in sorted(self.channels.keys())]

    # ---------------------------------------------------------
    # Zustandsänderungen
    # ---------------------------------------------------------
    def set_volume(self, channel: int, value: int, live=False):
        # Original: ChannelStripWidget._on_volume_changed() setzt state.volume
        # (das ist, was export_mix() als CC7 rausschreibt) direkt am geteilten
        # State-Objekt, GETRENNT von diesem Service-Aufruf, der nur
        # state.expression für die Live-Vorschau setzt. Bei uns gibt es kein
        # separates Widget-Objekt, das diese Mutation übernimmt - deshalb hier
        # beides in einem Aufruf, sonst würde der Fader-Wert nie exportiert.
        state = self._get_or_create_channel(channel)
        state.volume = max(0, min(127, value))
        state.expression = state.volume

        if live and self.player:
            try:
                self.player.set_expression_live(channel, state.expression)
            except Exception as e:
                logger.debug(f"⚠️ Live-Expression konnte nicht gesendet werden: {e}")

    def set_pan(self, channel: int, pan: int, live=False):
        state = self._get_or_create_channel(channel)
        state.pan = max(-64, min(63, pan))

        if live and self.player:
            try:
                self.player.set_pan_live(channel, state.pan)
            except Exception as e:
                logger.debug(f"⚠️ Live-Pan konnte nicht gesendet werden: {e}")

    def set_mute(self, channel: int, muted: bool):
        """Mute per Expression. Volume bleibt unverändert (DAW-Standard)."""
        state = self._get_or_create_channel(channel)
        state.mute = muted

        if not self.player:
            return

        if muted:
            self.player.set_expression_live(channel, 0)
            self.player._send_cc(channel, 123, 0)
        else:
            self.player.set_expression_live(channel, state.expression)

    def set_solo(self, channel: int, solo: bool):
        state = self._get_or_create_channel(channel)
        state.solo = solo

        if not self.player:
            return

        any_solo = any(ch.solo for ch in self.channels.values())

        for ch, st in self.channels.items():
            if any_solo:
                if st.solo:
                    self.player.set_expression_live(ch, st.expression)
                else:
                    self.player.set_expression_live(ch, 0)
            else:
                if st.mute:
                    self.player.set_expression_live(ch, 0)
                else:
                    self.player.set_expression_live(ch, st.expression)

    # ---------------------------------------------------------
    # Solo-/Mute-Logik
    # ---------------------------------------------------------
    def _any_solo_active(self) -> bool:
        return any(ch.solo for ch in self.channels.values())

    def is_channel_audible(self, channel: int) -> bool:
        state = self.channels.get(channel)
        if state is None:
            return True

        if self._any_solo_active():
            return state.solo
        else:
            return not state.mute

    # ---------------------------------------------------------
    # Export der gemixten MIDI-Datei
    # ---------------------------------------------------------
    def _next_available_filename(self, base_dir: Path, base_name: str, suffix: str) -> Path:
        i = 1
        while True:
            candidate = base_dir / f"{base_name} ({suffix} {i}).mid"
            if not candidate.exists():
                return candidate
            i += 1

    def export_mix(self) -> Path:
        if self.mid is None:
            raise RuntimeError("MixerService: MIDI wurde noch nicht geladen.")

        out_dir = paths.MIXER_OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        original_name = Path(self.midi_path).stem
        out_path = self._next_available_filename(out_dir, original_name, "Mixer Edit")

        logger.debug(f"🎚 Exportiere Mixer-Edit → {out_path}")

        new_mid = MidiFile(type=self.mid.type, ticks_per_beat=self.mid.ticks_per_beat)

        for track in self.mid.tracks:
            new_track = MidiTrack()
            new_mid.tracks.append(new_track)

            inserted_cc_for_channel: set[int] = set()
            pending_time = 0

            for msg in track:
                pending_time += msg.time

                if msg.is_meta:
                    new_track.append(msg.copy(time=pending_time))
                    pending_time = 0
                    continue

                if not hasattr(msg, "channel"):
                    new_track.append(msg.copy(time=pending_time))
                    pending_time = 0
                    continue

                ch = msg.channel
                state = self.channels.get(ch)

                if state is None:
                    new_track.append(msg.copy(time=pending_time))
                    pending_time = 0
                    continue

                if not self.is_channel_audible(ch):
                    continue

                if ch not in inserted_cc_for_channel:
                    inserted_cc_for_channel.add(ch)

                    new_track.append(Message(
                        "control_change", channel=ch, control=7, value=state.volume, time=pending_time
                    ))
                    pending_time = 0

                    new_track.append(Message(
                        "control_change", channel=ch, control=10, value=state.pan_cc_value, time=0
                    ))

                new_track.append(msg.copy(time=pending_time))
                pending_time = 0

        new_mid.save(out_path)
        logger.info(f"✅ Mixer-Export gespeichert: {out_path}")
        return out_path
