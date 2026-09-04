# Port der Filter-/Einfärbe-Logik aus dev-modus/alt/src/views/log_view.py
# + utils/logger.py (Session-Offset: der Viewer zeigt nur, was seit
# Prozessstart neu dazukam, nicht die komplette Historie).
from django.conf import settings

LOG_PATH = settings.LOG_PATH


def _get_session_offset() -> int:
    try:
        return LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    except OSError:
        return 0


SESSION_OFFSET = _get_session_offset()


def read_lines():
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(SESSION_OFFSET)
        return f.readlines()


def matches_filter(line: str, filter_name: str) -> bool:
    if filter_name == 'NORMAL':
        return '[DEBUG]' not in line
    if filter_name == 'INFO':
        return '[INFO]' in line
    if filter_name == 'WARNUNG':
        return '[WARNING]' in line or '[WARN]' in line
    if filter_name == 'FEHLER':
        return '[ERROR]' in line
    if filter_name == 'DEBUG':
        return True
    return True


def filter_lines(lines, filter_name: str):
    return [line for line in lines if matches_filter(line, filter_name)]


def line_level(line: str) -> str:
    if '[ERROR]' in line:
        return 'error'
    if '[WARNING]' in line or '[WARN]' in line:
        return 'warn'
    if '[INFO]' in line:
        return 'info'
    if '[DEBUG]' in line:
        return 'debug'
    return 'default'
