# Port von dev-modus/alt/src/services/midi_channel_state.py - unverändert,
# reines dataclass ohne Qt-Abhängigkeit.

from dataclasses import dataclass
from typing import Optional


@dataclass
class MidiChannelState:
    # -------------------------------------------------------------------------
    # MIDI-Kanal-Zustand für den Mixer
    # Dient als gemeinsame Datenstruktur zwischen Service, Dialog und Widgets
    # -------------------------------------------------------------------------
    
    channel: int                             # 0–15 (MIDI-intern), Anzeige = channel + 1
    program: Optional[int] = None            # Program Change (0–127), falls vorhanden
    instrument: str = "Unbekannt"            # Anzeige-Name
    volume: int = 100                        # 0–127 (Mixer-Fader)
    pan: int = 0                             # -64 (links) ... 0 (Center) ... +63 (rechts)
    mute: bool = False
    solo: bool = False

    # ---------------------------------------------------------
    # Channel-Nummer für die UI
    # ---------------------------------------------------------
    @property
    def display_channel(self) -> int:
        return self.channel + 1

    # ---------------------------------------------------------
    # CC-Wert für Pan und Volume
    # ---------------------------------------------------------
    @property
    def pan_cc_value(self) -> int:
        v = 64 + self.pan
        return max(0, min(127, v))

    def volume_to_db(self) -> str:
        if self.volume <= 0:
            return "-inf dB"

        # einfache logarithmische Umrechnung
        import math
        ratio = self.volume / 127.0
        db = 20 * math.log10(ratio)
        return f"{db:.1f} dB"
