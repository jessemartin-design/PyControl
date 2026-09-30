"""Mission Status + Robot Status readouts."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from mir.client import EXECUTING_STATE_ID, format_battery_time, format_robot_errors


class StatusPanel(ttk.LabelFrame):
    """
    Top status strip.

    Future: progress % / distance_to_next_target can be added here without
    touching other panels — see docs/PROJECT_KNOWLEDGE.md.
    """

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        super().__init__(master, text="Status", padding=8, **kwargs)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Mission Status:").grid(row=0, column=0, sticky="nw", padx=(0, 8))
        self.mission_var = tk.StringVar(value="Idle")
        ttk.Label(self, textvariable=self.mission_var, wraplength=520, justify="left").grid(
            row=0, column=1, sticky="ew"
        )

        ttk.Label(self, text="Robot Status:").grid(row=1, column=0, sticky="nw", padx=(0, 8), pady=(6, 0))
        self.robot_var = tk.StringVar(value="—")
        ttk.Label(self, textvariable=self.robot_var, wraplength=520, justify="left").grid(
            row=1, column=1, sticky="ew", pady=(6, 0)
        )

        self._active_label = ""

    def set_active_action(self, label: str) -> None:
        self._active_label = label.strip()
        if self._active_label:
            self.mission_var.set(self._active_label)

    def update_from_status(self, status: dict[str, Any], *, runner_label: str = "") -> None:
        mission_text = (status.get("mission_text") or "").strip()
        state = (status.get("state_text") or "").strip()

        if runner_label:
            self._active_label = runner_label
            # Show GUI action plus live robot text when they differ (e.g. Stage2Rally
            # internally moves to position Rally — that is not a separate draft item).
            if mission_text and mission_text.casefold() not in runner_label.casefold():
                self.mission_var.set(f"{runner_label}  —  {mission_text}")
            else:
                self.mission_var.set(runner_label)
        elif self._active_label and status.get("state_id") == EXECUTING_STATE_ID:
            if mission_text and mission_text.casefold() not in self._active_label.casefold():
                self.mission_var.set(f"{self._active_label}  —  {mission_text}")
            else:
                self.mission_var.set(self._active_label)
        elif mission_text:
            self.mission_var.set(mission_text)
        elif state:
            self.mission_var.set(state)
        else:
            self.mission_var.set("Idle")

        battery = status.get("battery_percentage")
        if isinstance(battery, (int, float)):
            battery_text = f"{battery:.0f}%"
        else:
            battery_text = "unknown"
        time_text = format_battery_time(status.get("battery_time_remaining"))
        state_text = status.get("state_text") or f"state {status.get('state_id')}"
        parts = [f"Battery {battery_text}", f"Remaining {time_text}", str(state_text)]

        fault = format_robot_errors(status)
        if fault:
            parts.append(fault)

        self.robot_var.set("  |  ".join(parts))
