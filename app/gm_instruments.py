# ---------------------------------------------------------------------
# General MIDI (GM1) Instrument Definitions for MidiRanger
# 
# Dieses Modul enthält die vollständigen GM-Program-Liste (0–127)
# und GM-Drumkit-Mapping. Es stellt Lookup-Funktionen bereit,
# um GM-Programmnummern in aussagekräftige Namen umzuwandeln.
# 
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# GM PROGRAM CHANGES (0–127)
# ---------------------------------------------------------------------

GM_PROGRAMS = {
    0:  ("Acoustic Grand Piano", "Konzertflügel"),
    1:  ("Bright Acoustic Piano", "Heller Flügel"),
    2:  ("Electric Grand Piano", "Elektrischer Flügel"),
    3:  ("Honky-tonk Piano", "Honky-Tonk Klavier"),
    4:  ("Electric Piano 1", "E-Piano 1"),
    5:  ("Electric Piano 2", "E-Piano 2"),
    6:  ("Harpsichord", "Cembalo"),
    7:  ("Clavinet", "Clavinet"),

    8:  ("Celesta", "Celesta"),
    9:  ("Glockenspiel", "Glockenspiel"),
    10: ("Music Box", "Spieldose"),
    11: ("Vibraphone", "Vibraphon"),
    12: ("Marimba", "Marimba"),
    13: ("Xylophone", "Xylophon"),
    14: ("Tubular Bells", "Röhrenglocken"),
    15: ("Dulcimer", "Hackbrett"),

    16: ("Drawbar Organ", "Zugriegelorgel"),
    17: ("Percussive Organ", "Percussion-Orgel"),
    18: ("Rock Organ", "Rockorgel (Hammond)"),
    19: ("Church Organ", "Kirchenorgel"),
    20: ("Reed Organ", "Harmonium"),
    21: ("Accordion", "Akkordeon"),
    22: ("Harmonica", "Mundharmonika"),
    23: ("Bandoneon", "Bandoneon"),

    24: ("Acoustic Guitar (Nylon)", "Akustikgitarre (Nylon)"),
    25: ("Acoustic Guitar (Steel)", "Akustikgitarre (Stahl)"),
    26: ("Electric Guitar (Jazz)", "E-Gitarre Jazz"),
    27: ("Electric Guitar (Clean)", "E-Gitarre Clean"),
    28: ("Electric Guitar (Muted)", "E-Gitarre Gedämpft"),
    29: ("Overdriven Guitar", "Overdrive Gitarre"),
    30: ("Distortion Guitar", "Distortion Gitarre"),
    31: ("Guitar Harmonics", "Gitarrenflageolett"),

    32: ("Acoustic Bass", "Kontrabass"),
    33: ("Electric Bass (Finger)", "E-Bass (Finger)"),
    34: ("Electric Bass (Pick)", "E-Bass (Plektrum)"),
    35: ("Fretless Bass", "Fretless Bass"),
    36: ("Slap Bass 1", "Slap Bass 1"),
    37: ("Slap Bass 2", "Slap Bass 2"),
    38: ("Synth Bass 1", "Synth Bass 1"),
    39: ("Synth Bass 2", "Synth Bass 2"),

    40: ("Violin", "Violine"),
    41: ("Viola", "Bratsche"),
    42: ("Cello", "Cello"),
    43: ("Contrabass", "Kontrabass"),
    44: ("Tremolo Strings", "Tremolo-Streicher"),
    45: ("Pizzicato Strings", "Pizzicato-Streicher"),
    46: ("Harp", "Harfe"),
    47: ("Timpani", "Pauke"),

    48: ("String Ensemble 1", "Streicher-Ensemble 1"),
    49: ("String Ensemble 2", "Streicher-Ensemble 2"),
    50: ("Synth Strings 1", "Synth-Streicher 1"),
    51: ("Synth Strings 2", "Synth-Streicher 2"),
    52: ("Choir Aahs", "Choir Aahs"),
    53: ("Voice Oohs", "Voice Oohs"),
    54: ("Synth Voice", "Synth Voice"),
    55: ("Orchestra Hit", "Orchestra Hit"),

    56: ("Trumpet", "Trompete"),
    57: ("Trombone", "Posaune"),
    58: ("Tuba", "Tuba"),
    59: ("Muted Trumpet", "Gedämpfte Trompete"),
    60: ("French Horn", "Horn"),
    61: ("Brass Section", "Blechbläser"),
    62: ("Synth Brass 1", "Synth Brass 1"),
    63: ("Synth Brass 2", "Synth Brass 2"),

    64: ("Soprano Sax", "Sopransax"),
    65: ("Alto Sax", "Altsax"),
    66: ("Tenor Sax", "Tenorsax"),
    67: ("Baritone Sax", "Baritonsax"),
    68: ("Oboe", "Oboe"),
    69: ("English Horn", "Englischhorn"),
    70: ("Bassoon", "Fagott"),
    71: ("Clarinet", "Klarinette"),

    72: ("Piccolo", "Piccoloflöte"),
    73: ("Flute", "Flöte"),
    74: ("Recorder", "Blockflöte"),
    75: ("Pan Flute", "Panflöte"),
    76: ("Blown Bottle", "Flaschenpfeife"),
    77: ("Shakuhachi", "Shakuhachi"),
    78: ("Whistle", "Pfeife"),
    79: ("Ocarina", "Okarina"),

    80: ("Lead 1 (square)", "Lead 1 (square)"),
    81: ("Lead 2 (sawtooth)", "Lead 2 (saw)"),
    82: ("Lead 3 (calliope)", "Lead 3 (calliope)"),
    83: ("Lead 4 (chiff)", "Lead 4 (chiff)"),
    84: ("Lead 5 (charang)", "Lead 5 (charang)"),
    85: ("Lead 6 (voice)", "Lead 6 (voice)"),
    86: ("Lead 7 (fifths)", "Lead 7 (fifths)"),
    87: ("Lead 8 (bass + lead)", "Lead 8 (bass+lead)"),

    88: ("Pad 1 (Fantasia)", "Pad 1 Fantasia"),
    89: ("Pad 2 (Warm)", "Pad 2 Warm"),
    90: ("Pad 3 (Polysynth)", "Pad 3 Polysynth"),
    91: ("Pad 4 (Choir)", "Pad 4 Choir"),
    92: ("Pad 5 (Bowed)", "Pad 5 Bowed"),
    93: ("Pad 6 (Metallic)", "Pad 6 Metallic"),
    94: ("Pad 7 (Halo)", "Pad 7 Halo"),
    95: ("Pad 8 (Sweep)", "Pad 8 Sweep"),

    96: ("FX 1 (Rain)", "FX 1 Rain"),
    97: ("FX 2 (Soundtrack)", "FX 2 Soundtrack"),
    98: ("FX 3 (Crystal)", "FX 3 Crystal"),
    99: ("FX 4 (Atmosphere)", "FX 4 Atmosphere"),
    100: ("FX 5 (Brightness)", "FX 5 Brightness"),
    101: ("FX 6 (Goblins)", "FX 6 Goblins"),
    102: ("FX 7 (Echoes)", "FX 7 Echoes"),
    103: ("FX 8 (Sci-fi)", "FX 8 Sci-fi"),

    104: ("Sitar", "Sitar"),
    105: ("Banjo", "Banjo"),
    106: ("Shamisen", "Shamisen"),
    107: ("Koto", "Koto"),
    108: ("Kalimba", "Kalimba"),
    109: ("Bagpipe", "Dudelsack"),
    110: ("Fiddle", "Fiddle"),
    111: ("Shanai", "Shanai"),

    112: ("Tinkle Bell", "Windspiel"),
    113: ("Agogo", "Agogo"),
    114: ("Steel Drums", "Steel Drums"),
    115: ("Woodblock", "Holzblock"),
    116: ("Taiko Drum", "Taiko"),
    117: ("Melodic Tom", "Melodic Tom"),
    118: ("Synth Drum", "Synth Drum"),
    119: ("Reverse Cymbal", "Reverse Cymbal"),

    120: ("Guitar Fret Noise", "Saitengeräusch"),
    121: ("Breath Noise", "Atemgeräusch"),
    122: ("Seashore", "Brandung"),
    123: ("Bird Tweet", "Vogelzwitschern"),
    124: ("Telephone Ring", "Telefonklingeln"),
    125: ("Helicopter", "Helikopter"),
    126: ("Applause", "Applaus"),
    127: ("Gunshot", "Pistolenschuss"),
}

# ---------------------------------------------------------------------
# GM DRUMKITS (Program Change auf Kanal 10)
# ---------------------------------------------------------------------

GM_DRUMKITS = {
    0:  "Standard Kit",
    8:  "Room Kit",
    16: "Power Kit",
    24: "Electronic Kit",
    25: "TR-808 Kit",
    32: "Jazz Kit",
    40: "Brush Kit",
    48: "Orchestra Kit",
    56: "Sound FX Kit",
}

# ---------------------------------------------------------------------
# HELPER
# ---------------------------------------------------------------------

def get_instrument_name(program: int, german: bool = False) -> str:
    if program not in GM_PROGRAMS:
        return f"Program {program}"

    eng, ger = GM_PROGRAMS[program]
    return ger if german else eng


def get_drumkit_name(program: int) -> str:
    return GM_DRUMKITS.get(program, f"Drumkit {program}")
