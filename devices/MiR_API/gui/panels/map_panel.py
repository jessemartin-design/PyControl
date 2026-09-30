"""
Optional map panel placeholder.

v1 intentionally skips the onboard map. Later options:
- Embed map image from Mir map API if a stable endpoint is confirmed
- Open http://<MIR_HOST>/ in a browser
- Swap this module for a WebView-based panel without changing app layout much
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import webbrowser


class MapPanel(ttk.LabelFrame):
    """Stub so the main layout can host a map later."""

    def __init__(self, master: tk.Misc, *, host: str, **kwargs) -> None:
        super().__init__(master, text="Map (optional)", padding=8, **kwargs)
        self.host = host
        ttk.Label(
            self,
            text="Map embedding is deferred. Open the onboard UI in a browser if needed.",
            wraplength=480,
        ).pack(anchor="w")
        ttk.Button(self, text="Open robot UI in browser", command=self._open).pack(anchor="w", pady=(8, 0))

    def _open(self) -> None:
        webbrowser.open(f"http://{self.host}/")
