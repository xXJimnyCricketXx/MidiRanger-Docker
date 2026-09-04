# Ersetzt PySide6.QtCore.Signal/QObject in den Engine-Backends. Original nutzt
# Qt-Signals rein als Publish/Subscribe (.connect()/.emit()), ohne Event-Loop-
# Abhängigkeit - dieselbe API als reine Callback-Liste reicht deshalb aus und
# lässt den Rest des portierten Codes (Backend-Klassen, PlayerController)
# nahezu unverändert.
import logging

logger = logging.getLogger('midiranger')


class Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, fn):
        self._callbacks.append(fn)

    def disconnect(self, fn):
        if fn in self._callbacks:
            self._callbacks.remove(fn)

    def emit(self, *args):
        for fn in list(self._callbacks):
            try:
                fn(*args)
            except Exception:
                logger.exception('💥 Fehler in Signal-Callback')
