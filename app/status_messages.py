# Port von dev-modus/alt/src/utils/status_messages.py

STATUS_MESSAGES = {
    100: ("Bereit.", "info"),
    101: ("Song markiert", "success"),
    102: ("Song abgewählt / Auswahl zurückgesetzt", "info"),
    103: ("🔄 Übersicht aktualisiert", "info"),

    200: ("▶️ Wiedergabe gestartet", "info"),
    201: ("⏹️ Wiedergabe gestoppt", "info"),
    202: ("⚠️ Fehler beim Abspielen", "error"),

    300: ("⭐ Zu Favoriten hinzugefügt", "success"),
    301: ("⭐ Aus Favoriten entfernt", "info"),

    400: ("📁 Neue Quelle angelegt", "success"),
    401: ("🗑️ Quelle gelöscht", "info"),
    402: ("✏️ Quelle umbenannt", "info"),
    403: ("📂 Quellenverwaltung geöffnet", "info"),

    500: ("🎶 Neue Playlist erstellt", "success"),
    501: ("💾 Playlist gespeichert", "info"),
    502: ("🗑️ Playlist gelöscht", "info"),
    503: ("➕ Songs zur Playlist hinzugefügt", "success"),
    504: ("➖ Songs aus Playlist entfernt", "info"),
    505: ("🧹 Playlist geleert", "info"),
    506: ("✏️ Playlist umbenannt", "info"),
    510: ("🎵 Playlist-Manager geöffnet", "info"),
    511: ("📂 Playlist geöffnet", "info"),
    520: ("⚠️ Keine Songs ausgewählt", "warning"),

    600: ("📝 Song bearbeitet", "info"),
    601: ("⚙️ Bearbeitungsstatus geändert", "info"),
    602: ("✏️ Songdetails geöffnet", "info"),

    650: ("🗑️ Song gelöscht", "success"),
    651: ("❌ Löschen nicht erlaubt (Originaldatei)", "warning"),
    652: ("⚠️ Datei konnte nicht gelöscht werden", "error"),

    700: ("📥 Song importiert", "success"),
    701: ("📦 Export gestartet", "info"),
    702: ("✅ Export abgeschlossen", "success"),
    703: ("⚠️ Keine Songs zum Export gefunden", "error"),
    704: ("🧠 Metadatenanalyse gestartet", "info"),
    705: ("💾 Metadaten aktualisiert", "success"),
    706: ("⚠️ Fehler bei der Analyse", "error"),
    710: ("💾 Backup gestartet", "info"),
    711: ("✅ Backup abgeschlossen", "success"),
    712: ("❌ Backup fehlgeschlagen", "error"),

    720: ("⚙️ Einstellungen übernommen", "success"),

    740: ("🎚️ Mixer geöffnet", "info"),
    741: ("⚠️ Kein Song für Mixer ausgewählt", "warning"),
    742: ("❌ Mixer konnte nicht geöffnet werden", "error"),
    743: ("💾 Mixer-Export gespeichert", "success"),
    744: ("❌ Mixer-Export fehlgeschlagen", "error"),

    800: ("📂 Dashboard geöffnet", "info"),
    801: ("🎵 Alle Songs geöffnet", "info"),
    802: ("⭐ Favoriten geöffnet", "info"),
    803: ("🔍 Suchansicht geöffnet", "info"),
    804: ("📄 Suchergebnisse angezeigt", "info"),

    810: ("🔍 Suche gestartet", "info"),
    811: ("🔍 Treffer gefunden", "info"),
    812: ("🔍 Keine Treffer gefunden", "warning"),

    850: ("📖 Hilfe geöffnet", "info"),
    851: ("⌨️ Tastenkürzel geöffnet", "info"),
    852: ("📜 Log-Viewer geöffnet", "info"),
    853: ("ℹ️ Info-Fenster geöffnet", "info"),
    854: ("📝 Changelog geöffnet", "info"),

    900: ("🚀 MidiRanger gestartet", "info"),
    901: ("💾 Datenbank initialisiert", "info"),
    902: ("🧩 Migration erfolgreich abgeschlossen", "success"),
    903: ("🔍 Scan der MIDI-Dateien gestartet", "info"),
    904: ("✅ Scan abgeschlossen", "success"),
    905: ("⚠️ Keine MIDI-Dateien gefunden", "error"),
    906: ("📂 Quellenverzeichnis aktualisiert", "info"),
    907: ("🧠 Statussystem initialisiert", "info"),
    908: ("⚙️ Konfiguration geladen", "info"),
    909: ("❌ Schwerer Fehler im System", "error"),

    930: ("🔍 Datenbankprüfung gestartet", "info"),
    931: ("✅ Datenbankprüfung abgeschlossen", "success"),
    932: ("❌ Fehler in der Datenbank entdeckt", "error"),

    9001: ("⚠️ Kein Eintrag ausgewählt", "warning"),
    9002: ("⚠️ Ungültiger oder leerer Name", "warning"),
}


def status_text(msg_id: int) -> str:
    text, _level = STATUS_MESSAGES.get(msg_id, ("Unbekannte Meldung", "info"))
    return text


def status_level(msg_id: int) -> str:
    _text, level = STATUS_MESSAGES.get(msg_id, ("Unbekannte Meldung", "info"))
    return level


def log_status(logger, msg_id: int):
    """Port von StatusManager._log(): loggt "[id] text" auf dem passenden Level."""
    text, level = STATUS_MESSAGES.get(msg_id, ("Unbekannte Meldung", "info"))
    message = f"[{msg_id}] {text}"
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)

    _set_status(text, level)


def log_status_text(logger, text: str, level: str = "info"):
    """Port von StatusManager.show_text(): Freitext-Meldung statt Code."""
    message = f"[?] {text}"
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)

    _set_status(text, level)


# ---------------------------------------------------------------------
# Entspricht dem linken Statusleisten-Feld (StatusManager.show/show_text):
# zeigt die Meldung ~3s an, dann leert sie sich von selbst. Bei uns global
# statt pro-Fenster - passt zur Single-User/Haushalt-Natur der App (wie der
# Player-Singleton), und wird per WebSocket an alle offenen Tabs verteilt,
# damit auch rein per AJAX ausgelöste Aktionen (Modals) sie live zeigen.
# ---------------------------------------------------------------------
import time as _time

_last_status = {'text': None, 'level': 'info', 'ts': 0.0}
STATUS_DISPLAY_SECONDS = 3.0


def _set_status(text, level):
    _last_status['text'] = text
    _last_status['level'] = level
    _last_status['ts'] = _time.time()

    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is not None:
            async_to_sync(layer.group_send)('player_status', {
                'type': 'player_event',
                'data': {'event': 'status', 'text': text, 'level': level},
            })
    except Exception:
        pass


def get_current_status_message():
    if _last_status['text'] and (_time.time() - _last_status['ts']) < STATUS_DISPLAY_SECONDS:
        return _last_status['text']
    return None
