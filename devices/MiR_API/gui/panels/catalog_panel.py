"""Position / Mission dropdowns and Add buttons."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from gui.models import ActionKind, QueueAction
from mir.client import NamedItem


class CatalogPanel(ttk.LabelFrame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        on_add: Callable[[QueueAction], None],
        **kwargs,
    ) -> None:
        super().__init__(master, text="Add actions", padding=8, **kwargs)
        self.on_add = on_add
        self._positions: list[NamedItem] = []
        self._missions: list[NamedItem] = []

        self.position_var = tk.StringVar()
        self.mission_var = tk.StringVar()

        row = ttk.Frame(self)
        row.pack(fill="x")

        ttk.Label(row, text="Position").grid(row=0, column=0, sticky="w")
        self.position_combo = ttk.Combobox(
            row, textvariable=self.position_var, state="readonly", width=36
        )
        self.position_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(row, text="Add position", command=self._add_position).grid(row=1, column=1, padx=(0, 16))

        ttk.Label(row, text="Mission").grid(row=0, column=2, sticky="w")
        self.mission_combo = ttk.Combobox(
            row, textvariable=self.mission_var, state="readonly", width=36
        )
        self.mission_combo.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        ttk.Button(row, text="Add mission", command=self._add_mission).grid(row=1, column=3)

        row.columnconfigure(0, weight=1)
        row.columnconfigure(2, weight=1)

        tools = ttk.Frame(self)
        tools.pack(fill="x", pady=(8, 0))
        ttk.Button(tools, text="Refresh lists", command=self._on_refresh_click).pack(side="left")
        self._refresh_handler: Callable[[], None] | None = None

    def set_refresh_handler(self, handler: Callable[[], None]) -> None:
        self._refresh_handler = handler

    def _on_refresh_click(self) -> None:
        if self._refresh_handler:
            self._refresh_handler()

    def set_catalogs(self, positions: list[NamedItem], missions: list[NamedItem]) -> None:
        self._positions = sorted(positions, key=lambda item: item.name.casefold())
        self._missions = sorted(missions, key=lambda item: item.name.casefold())
        pos_names = [item.name for item in self._positions]
        mis_names = [item.name for item in self._missions]
        self.position_combo["values"] = pos_names
        self.mission_combo["values"] = mis_names
        if pos_names and self.position_var.get() not in pos_names:
            self.position_var.set(pos_names[0])
        if mis_names and self.mission_var.get() not in mis_names:
            self.mission_var.set(mis_names[0])
        if not pos_names:
            self.position_var.set("")
        if not mis_names:
            self.mission_var.set("")

    def _add_position(self) -> None:
        name = self.position_var.get().strip()
        item = next((p for p in self._positions if p.name == name), None)
        if not item:
            return
        self.on_add(QueueAction(kind=ActionKind.POSITION, name=item.name, guid=item.guid))

    def _add_mission(self) -> None:
        name = self.mission_var.get().strip()
        item = next((m for m in self._missions if m.name == name), None)
        if not item:
            return
        self.on_add(QueueAction(kind=ActionKind.MISSION, name=item.name, guid=item.guid))
