"""Draft action queue list with reorder, remove, Start/Pause/Stop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from gui.models import QueueAction, RunnerState
from gui.services.draft_queue import DraftQueue


class QueuePanel(ttk.LabelFrame):
    def __init__(
        self,
        master: tk.Misc,
        draft: DraftQueue,
        *,
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_clear_paths: Callable[[], None] | None = None,
        on_clear_error: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, text="Action queue (draft)", padding=8, **kwargs)
        self.draft = draft
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.on_clear_paths = on_clear_paths
        self.on_clear_error = on_clear_error

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        list_frame = ttk.Frame(body)
        list_frame.pack(side="left", fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, height=12, exportselection=False, activestyle="dotbox")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.listbox.bind("<Button-1>", self._on_click, add="+")
        self.listbox.bind("<B1-Motion>", self._on_drag, add="+")
        self.listbox.bind("<ButtonRelease-1>", self._on_drop, add="+")
        self._drag_from: int | None = None

        side = ttk.Frame(body)
        side.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(side, text="▲ Up", command=self._move_up).pack(fill="x", pady=2)
        ttk.Button(side, text="▼ Down", command=self._move_down).pack(fill="x", pady=2)
        ttk.Button(side, text="Remove", command=self._remove).pack(fill="x", pady=(12, 2))
        ttk.Button(side, text="Clear", command=self._clear).pack(fill="x", pady=2)

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(10, 0))
        self.start_btn = ttk.Button(controls, text="Start", command=self.on_start)
        self.start_btn.pack(side="left", padx=(0, 6))
        self.pause_btn = ttk.Button(controls, text="Pause", command=self.on_pause)
        self.pause_btn.pack(side="left", padx=(0, 6))
        self.stop_btn = ttk.Button(controls, text="Stop", command=self.on_stop)
        self.stop_btn.pack(side="left", padx=(0, 6))
        if self.on_clear_paths is not None:
            ttk.Button(controls, text="Clear paths", command=self.on_clear_paths).pack(
                side="left", padx=(0, 6)
            )
        self.clear_error_btn: ttk.Button | None = None
        if self.on_clear_error is not None:
            self.clear_error_btn = ttk.Button(
                controls, text="Clear errors", command=self.on_clear_error, state="disabled"
            )
            self.clear_error_btn.pack(side="left", padx=(0, 6))

        self.state_var = tk.StringVar(value="Runner: idle")
        ttk.Label(controls, textvariable=self.state_var).pack(side="right")

        self.refresh()

    def refresh(self) -> None:
        selected = self.listbox.curselection()
        selected_index = selected[0] if selected else None
        self.listbox.delete(0, tk.END)
        for action in self.draft.items():
            self.listbox.insert(tk.END, action.label())
        if selected_index is not None and selected_index < self.listbox.size():
            self.listbox.selection_set(selected_index)
            self.listbox.activate(selected_index)

    def set_runner_state(self, state: RunnerState) -> None:
        self.state_var.set(f"Runner: {state.value}")
        running = state in (RunnerState.RUNNING, RunnerState.PAUSED, RunnerState.STOPPING)
        # Start doubles as Resume when paused.
        if state == RunnerState.PAUSED:
            self.start_btn.configure(text="Resume")
        else:
            self.start_btn.configure(text="Start")
        self.pause_btn.configure(state=("disabled" if state != RunnerState.RUNNING else "normal"))
        self.stop_btn.configure(state=("normal" if running or state == RunnerState.IDLE else "normal"))

    def set_clear_error_enabled(self, enabled: bool) -> None:
        if self.clear_error_btn is None:
            return
        self.clear_error_btn.configure(state=("normal" if enabled else "disabled"))

    def selected_index(self) -> int | None:
        sel = self.listbox.curselection()
        return int(sel[0]) if sel else None

    def _move_up(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        if self.draft.move_up(index):
            self.refresh()
            self.listbox.selection_set(index - 1)

    def _move_down(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        if self.draft.move_down(index):
            self.refresh()
            self.listbox.selection_set(index + 1)

    def _remove(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        self.draft.remove_at(index)
        self.refresh()

    def _clear(self) -> None:
        self.draft.clear()
        self.refresh()

    def _on_click(self, event: tk.Event) -> None:
        index = self.listbox.nearest(event.y)
        self._drag_from = index

    def _on_drag(self, event: tk.Event) -> None:
        if self._drag_from is None:
            return
        index = self.listbox.nearest(event.y)
        if index != self._drag_from and 0 <= index < self.listbox.size():
            if self.draft.move(self._drag_from, index):
                self._drag_from = index
                self.refresh()
                self.listbox.selection_set(index)

    def _on_drop(self, _event: tk.Event) -> None:
        self._drag_from = None
