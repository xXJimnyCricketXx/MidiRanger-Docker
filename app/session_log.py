# Port von dev-modus/alt/src/utils/session_log.py (reines Python/JSON,
# keine Qt-Abhängigkeit). Original lag unter config/, bei uns unter data/,
# da das im Docker-Betrieb das persistente Volume ist.
import json
from collections import deque
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from django.conf import settings

DEFAULT_MAX = 50
LOG_PATH = settings.BASE_DIR / 'data' / 'home_session_log.json'


@dataclass
class LogItem:
    ts: str
    title: str
    extra: Optional[Dict[str, Any]] = field(default=None)


class SessionLog:
    def __init__(self, max_items: int = DEFAULT_MAX):
        self.max_items = max_items
        self._data: Dict[str, deque] = {
            "recent_play": deque(maxlen=max_items),
            "recent_import": deque(maxlen=max_items),
        }
        self._load()

    def add_recent_play(self, title: str, **extra):
        self._append("recent_play", title, extra)

    def add_recent_import(self, title: str, **extra):
        self._append("recent_import", title, extra)

    def get_recent(self, key: str, limit: int = 10) -> List[Dict[str, Any]]:
        self._load()
        q = self._data.get(key, deque())
        return list(list(q)[-limit:])[::-1]

    def _append(self, key: str, title: str, extra: Dict[str, Any]):
        if key not in self._data:
            self._data[key] = deque(maxlen=self.max_items)
        item = LogItem(ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title=title, extra=extra or None)
        self._data[key].append(asdict(item))
        self._save()

    def _load(self):
        try:
            if LOG_PATH.exists():
                raw = json.loads(LOG_PATH.read_text(encoding='utf-8'))
                for k, arr in (raw or {}).items():
                    self._data[k] = deque(arr or [], maxlen=self.max_items)
        except (OSError, json.JSONDecodeError):
            pass

    def _save(self):
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            out = {k: list(dq) for k, dq in self._data.items()}
            LOG_PATH.write_text(json.dumps(out, indent=2), encoding='utf-8')
        except OSError:
            pass
