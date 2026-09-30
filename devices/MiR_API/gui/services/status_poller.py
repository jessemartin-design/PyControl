"""Background status polling for the GUI."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from mir.client import MirClient, MirError


class StatusPoller:
    def __init__(
        self,
        client: MirClient,
        on_status: Callable[[dict[str, Any]], None],
        on_error: Callable[[str], None] | None = None,
        *,
        interval: float = 1.0,
    ) -> None:
        self.client = client
        self.on_status = on_status
        self.on_error = on_error
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="mir-status-poller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                status = self.client.get_status()
                self.on_status(status)
            except MirError as exc:
                if self.on_error:
                    self.on_error(str(exc))
            self._stop.wait(self.interval)
