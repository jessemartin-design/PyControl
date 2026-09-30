"""Main Tk application — wires panels to MirClient services."""

from __future__ import annotations

import signal
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.dialogs import ask_keep_or_stop_charging
from gui.models import QueueAction, RunnerState
from gui.panels.catalog_panel import CatalogPanel
from gui.panels.map_panel import MapPanel
from gui.panels.queue_panel import QueuePanel
from gui.panels.status_panel import StatusPanel
from gui.services.draft_queue import DraftQueue
from gui.services.runner import QueueRunner
from gui.services.status_poller import StatusPoller
from mir.client import (
    MirClient,
    MirError,
    can_clear_error,
    charge_prompt_kind,
    load_dotenv,
)


def run_app() -> int:
    load_dotenv(str(ROOT / ".env"))
    try:
        client = MirClient.from_env()
        status = client.connect()
    except MirError as exc:
        _show_startup_error(str(exc))
        return 1

    app = MirGuiApp(client, status)
    app.run()
    return 0


def _show_startup_error(message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("MiR GUI", f"Could not connect:\n{message}")
    root.destroy()


class MirGuiApp:
    def __init__(self, client: MirClient, initial_status: dict[str, Any]) -> None:
        self.client = client
        self.draft = DraftQueue()
        self._closing = False

        self.root = tk.Tk()
        self.root.title(f"MiR Control — {initial_status.get('robot_name') or client.host}")
        self.root.minsize(720, 520)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._message_var = tk.StringVar(value="Connected.")
        self._build()

        self.runner = QueueRunner(
            client,
            get_actions=self.draft.items,
            pop_front=lambda: self.draft.remove_at(0),
            on_status=self._on_runner_status,
            on_message=self._on_runner_message,
            on_queue_changed=self._on_queue_changed,
            on_state=self._on_runner_state,
        )
        self.poller = StatusPoller(
            client,
            on_status=self._on_polled_status,
            on_error=lambda msg: self._set_message(f"Status error: {msg}"),
            interval=1.0,
        )

        self._refresh_catalogs()
        self.status_panel.update_from_status(initial_status)
        self.queue_panel.set_clear_error_enabled(can_clear_error(initial_status))
        self.poller.start()
        self._install_sigint_handler()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        self.status_panel = StatusPanel(outer)
        self.status_panel.pack(fill="x", pady=(0, 8))

        self.catalog_panel = CatalogPanel(outer, on_add=self._add_action)
        self.catalog_panel.pack(fill="x", pady=(0, 8))
        self.catalog_panel.set_refresh_handler(self._refresh_catalogs)

        self.queue_panel = QueuePanel(
            outer,
            self.draft,
            on_start=self._start,
            on_pause=self._pause,
            on_stop=self._stop,
            on_clear_paths=self._clear_paths,
            on_clear_error=self._clear_error,
        )
        self.queue_panel.pack(fill="both", expand=True, pady=(0, 8))

        # Optional / deferred map — easy to remove or replace later.
        self.map_panel = MapPanel(outer, host=self.client.host)
        self.map_panel.pack(fill="x", pady=(0, 8))

        ttk.Label(outer, textvariable=self._message_var).pack(fill="x")

    def run(self) -> None:
        self.root.mainloop()

    def _install_sigint_handler(self) -> None:
        # Ctrl-C in the terminal should use the same charging prompt as window close.
        def _handler(_signum: int, _frame: Any) -> None:
            self.root.after(0, self._on_close)

        try:
            signal.signal(signal.SIGINT, _handler)
        except (ValueError, OSError):
            return

        # Periodically wake the Tk loop so SIGINT is processed promptly on macOS/Unix.
        def _heartbeat() -> None:
            if not self._closing and self.root.winfo_exists():
                self.root.after(200, _heartbeat)

        self.root.after(200, _heartbeat)

    def _add_action(self, action: QueueAction) -> None:
        self.draft.add(action)
        self.queue_panel.refresh()
        self._set_message(f"Added {action.label()}")

    def _refresh_catalogs(self) -> None:
        try:
            positions = self.client.get_positions()
            missions = self.client.get_missions()
        except MirError as exc:
            self._set_message(f"Could not refresh catalogs: {exc}")
            return
        self.catalog_panel.set_catalogs(positions, missions)
        self._set_message(f"Loaded {len(positions)} positions, {len(missions)} missions.")

    def _start(self) -> None:
        self.runner.start()

    def _pause(self) -> None:
        self.runner.pause()

    def _stop(self) -> None:
        kind = self._charge_prompt_kind()
        if kind is not None:
            if ask_keep_or_stop_charging(self.root, kind):
                self.runner.stop()
                self._set_message("Stopped — charging/docking aborted.")
            else:
                self.runner.detach()
                self._set_message("Left robot charging (GUI runner detached).")
            return
        self.runner.stop()

    def _clear_paths(self) -> None:
        try:
            deleted = self.client.clear_paths()
        except MirError as exc:
            self._set_message(f"Clear paths failed: {exc}")
            return
        self._set_message(f"Cleared {deleted} stored path{'s' if deleted != 1 else ''} on the robot.")

    def _clear_error(self) -> None:
        try:
            status = self.client.clear_error()
        except MirError as exc:
            self._set_message(f"Clear errors failed: {exc}")
            self.queue_panel.set_clear_error_enabled(False)
            return
        self.status_panel.update_from_status(status, runner_label=self.runner.current_label)
        self.queue_panel.set_clear_error_enabled(can_clear_error(status))
        if can_clear_error(status):
            self._set_message("Clear errors requested, but the robot is still in Error.")
        else:
            self._set_message("Errors cleared.")

    def _charge_prompt_kind(self) -> str | None:
        queue_item = None
        try:
            status = self.client.get_status()
            qid = status.get("mission_queue_id")
            if qid is not None:
                try:
                    queue_item = self.client.get_mission_queue_item(qid)
                except MirError:
                    queue_item = None
        except MirError:
            status = {}
        label = self.runner.current_label
        # current_label may be "Moving to X" or a mission name; Charge uses the name.
        charge_label = label if label.casefold().strip() == "charge" else ""
        return charge_prompt_kind(
            status,
            queue_item=queue_item,
            preserving_charge=self.runner.preserving_charge,
            runner_label=charge_label,
        )

    def _on_queue_changed(self) -> None:
        self.root.after(0, self.queue_panel.refresh)

    def _on_runner_state(self, state: RunnerState) -> None:
        self.root.after(0, lambda: self.queue_panel.set_runner_state(state))

    def _on_runner_message(self, message: str) -> None:
        label = self.runner.current_label
        self.root.after(0, lambda: self._set_message(message))
        if label:
            self.root.after(0, lambda: self.status_panel.set_active_action(label))

    def _on_runner_status(self, status: dict[str, Any]) -> None:
        label = self.runner.current_label
        clearable = can_clear_error(status)

        def _apply() -> None:
            self.status_panel.update_from_status(status, runner_label=label)
            self.queue_panel.set_clear_error_enabled(clearable)

        self.root.after(0, _apply)

    def _on_polled_status(self, status: dict[str, Any]) -> None:
        label = self.runner.current_label
        clearable = can_clear_error(status)

        def _apply() -> None:
            self.status_panel.update_from_status(status, runner_label=label)
            self.queue_panel.set_clear_error_enabled(clearable)

        self.root.after(0, _apply)

    def _set_message(self, message: str) -> None:
        self._message_var.set(message)

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True

        kind = self._charge_prompt_kind()
        abort_charge = False
        if kind is not None:
            abort_charge = ask_keep_or_stop_charging(self.root, kind)

        self.poller.stop()
        if abort_charge:
            self.runner.stop()
            self._set_message("Closed — charging/docking aborted.")
        else:
            # Keep Charging, or not in a charge path: leave robot mission alone.
            self.runner.detach()
        self.root.destroy()


if __name__ == "__main__":
    raise SystemExit(run_app())
