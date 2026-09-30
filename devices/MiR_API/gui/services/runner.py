"""Sequential draft-queue runner: Start / Pause / Stop."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from gui.models import ActionKind, QueueAction, RunnerState
from mir.client import (
    COMPLETED_STATE_ID,
    MirClient,
    MirError,
    PAUSE_STATE_ID,
    READY_STATE_ID,
    can_clear_error,
    is_charge_action_name,
    is_charging_started,
    is_terminal_queue_state,
    is_transient_mir_error,
)


StatusCallback = Callable[[dict[str, Any]], None]
MessageCallback = Callable[[str], None]
QueueChangedCallback = Callable[[], None]
StateCallback = Callable[[RunnerState], None]

_ACTIVE_QUEUE_STATES = frozenset({"pending", "executing"})
_FAILED_QUEUE_STATES = frozenset({"aborted", "abort", "error", "failed"})


class QueueRunner:
    """
    Executes draft-queue items one after another without stopping between them.

    Normal actions: wait until that mission_queue entry reaches a terminal state
    (Done / Aborted / …), then send the next draft item.

    Charge is indefinite on the robot (stays Executing until something else is
    queued). Semantics:
      - Always wait until charging has *initiated* (mission_text / dock state).
      - If more draft items follow → then send the next action (interrupts Charge).
      - If Charge is last → end the GUI sequence and leave the robot charging.

    Draft items are only removed after that item has been successfully handled, so
    a failed send does not skip / drop an action.
    """

    def __init__(
        self,
        client: MirClient,
        *,
        get_actions: Callable[[], list[QueueAction]],
        pop_front: Callable[[], QueueAction | None],
        on_status: StatusCallback | None = None,
        on_message: MessageCallback | None = None,
        on_queue_changed: QueueChangedCallback | None = None,
        on_state: StateCallback | None = None,
        poll_seconds: float = 0.6,
    ) -> None:
        self.client = client
        self._get_actions = get_actions
        self._pop_front = pop_front
        self._on_status = on_status
        self._on_message = on_message
        self._on_queue_changed = on_queue_changed
        self._on_state = on_state
        self.poll_seconds = poll_seconds

        self._lock = threading.Lock()
        self._state = RunnerState.IDLE
        self._thread: threading.Thread | None = None
        self._pause = threading.Event()
        self._pause.set()  # not paused
        self._stop = threading.Event()
        self._current_label = ""
        self._last_error = ""
        # Set when Charge was the last draft item and charging initiated successfully.
        # Completing the queue must not abort/pause that Charge mission.
        self._preserve_charging = False

    @property
    def state(self) -> RunnerState:
        return self._state

    @property
    def preserving_charge(self) -> bool:
        return self._preserve_charging

    @property
    def current_label(self) -> str:
        return self._current_label

    @property
    def last_error(self) -> str:
        return self._last_error

    def start(self) -> None:
        with self._lock:
            if self._state == RunnerState.PAUSED:
                self._pause.set()
                try:
                    self._recover_robot()
                except MirError as exc:
                    self._emit_message(f"Resume warning: {exc}")
                self._set_state(RunnerState.RUNNING)
                self._emit_message("Resumed.")
                return
            if self._state in (RunnerState.RUNNING, RunnerState.STOPPING):
                return
            if not self._get_actions():
                self._emit_message("Draft queue is empty.")
                return
            # A new Start may intentionally interrupt a prior Charge-last run.
            self._preserve_charging = False
            self._stop.clear()
            self._pause.set()
            self._last_error = ""
            self._set_state(RunnerState.RUNNING)
            total = len(self._get_actions())
            self._emit_message(f"Starting queue ({total} action{'s' if total != 1 else ''})…")
            self._thread = threading.Thread(target=self._run_loop, name="mir-queue-runner", daemon=True)
            self._thread.start()

    def pause(self) -> None:
        with self._lock:
            if self._state != RunnerState.RUNNING:
                return
            # Do not pause the robot if we already finished on Charge — Pause mid-run only.
            self._pause.clear()
            self._set_state(RunnerState.PAUSED)
        try:
            self.client.pause_robot()
            self._emit_message("Paused — press Start to resume the remaining queue.")
        except MirError as exc:
            self._emit_message(f"Pause failed: {exc}")

    def stop(self) -> None:
        with self._lock:
            if self._state in (RunnerState.IDLE, RunnerState.STOPPING):
                # Idle after Charge-last: leave the robot charging (battery safety).
                if self._preserve_charging:
                    self._emit_message("Leaving Charge running (queue ended on charger).")
                    return
                try:
                    self.client.abort_active_mission()
                except MirError:
                    pass
                return
            self._preserve_charging = False
            self._set_state(RunnerState.STOPPING)
            self._stop.set()
            self._pause.set()
        try:
            self.client.abort_active_mission()
            self._emit_message("Stopped.")
        except MirError as exc:
            self._emit_message(f"Stop warning: {exc}")

    def detach(self) -> None:
        """
        Stop local runner threads without aborting the robot mission.

        Used when closing the GUI so an in-progress or Charge-last mission
        (especially charging) keeps running overnight.
        """
        with self._lock:
            if self._state in (RunnerState.RUNNING, RunnerState.PAUSED, RunnerState.STOPPING):
                self._set_state(RunnerState.STOPPING)
                self._stop.set()
                self._pause.set()
        # Do not call abort_active_mission / pause_robot here.
    def _run_loop(self) -> None:
        """Drain the draft queue until empty, stopped, or a hard error."""
        ended_on_charge = False
        try:
            while not self._stop.is_set():
                self._pause.wait()
                if self._stop.is_set():
                    break

                remaining = self._get_actions()
                if not remaining:
                    if ended_on_charge or self._preserve_charging:
                        self._emit_message(
                            "Queue finished — robot left charging until a new action is started."
                        )
                    else:
                        self._emit_message("Queue finished.")
                    break

                # Peek only — remove after success so failures do not skip an action.
                action = remaining[0]
                has_more = len(remaining) > 1

                try:
                    outcome = self._run_action(action, has_more=has_more)
                except MirError as exc:
                    self._last_error = str(exc)
                    left = len(self._get_actions())
                    self._emit_message(
                        f"Stopped on {action.label()}: {exc}"
                        + (
                            f" ({left} still in draft — fix robot, then Start)."
                            if left
                            else ""
                        )
                    )
                    break
                except Exception as exc:  # noqa: BLE001 — surface unexpected runner failures in UI
                    self._last_error = str(exc)
                    self._emit_message(f"Unexpected error on {action.label()}: {exc}")
                    break

                if self._stop.is_set():
                    break

                # Successfully handled → remove from draft.
                head = self._pop_front()
                self._emit_queue_changed()
                if head is None or head.uid != action.uid:
                    self._emit_message("Draft queue changed during run — stopping.")
                    break

                left_after = len(self._get_actions())

                if outcome == "charging" and not has_more:
                    # Charge was last: keep mission Executing — do not recover/abort/pause.
                    ended_on_charge = True
                    self._preserve_charging = True
                    self._emit_message(
                        "Queue complete on Charge — MiR stays charging until you Start a new action."
                    )
                    break

                if outcome in _FAILED_QUEUE_STATES:
                    self._emit_message(
                        f"{action.label()} ended with {outcome}. "
                        "Clearing robot error (if any) and continuing…"
                    )
                    try:
                        self._recover_robot()
                    except MirError as exc:
                        self._emit_message(f"Could not clear robot after failure: {exc}")

                if left_after:
                    self._emit_message(
                        f"Finished {action.label()}. Continuing — {left_after} remaining…"
                    )
        finally:
            self._current_label = ""
            self._set_state(RunnerState.IDLE)
            self._emit_queue_changed()
            # Intentionally no abort/pause/ensure_ready here — especially when
            # _preserve_charging is set after a Charge-last completion.

    def _recover_robot(self) -> None:
        status = self.client.get_status()
        if can_clear_error(status):
            self.client.clear_error()
        self.client.ensure_ready(raise_on_estop=False)

    def _run_action(self, action: QueueAction, *, has_more: bool) -> str:
        """
        Queue once, then wait. On wait failure, recover and retry wait only —
        never POST the same action twice (that caused double Charge / re-dock).
        """
        queue_id: int | str | None = None
        try:
            queue_id = self._queue_action(action)
            return self._wait_for_action(action, queue_id, has_more=has_more)
        except MirError as exc:
            if queue_id is None:
                # Never made it onto the robot — safe to recover and try a full re-queue.
                self._emit_message(f"Retrying {action.label()} after: {exc}")
                self._recover_robot()
                queue_id = self._queue_action(action)
                return self._wait_for_action(action, queue_id, has_more=has_more)

            # Already queued — do not POST again (re-queueing Charge caused undock+re-dock).
            # Keep waiting on the same mission_queue id without ensure_ready/abort.
            self._emit_message(
                f"Wait error on {action.label()} (queue id {queue_id}): {exc}. "
                "Continuing to wait without re-queueing…"
            )
            return self._wait_for_action(action, queue_id, has_more=has_more)

    def _queue_action(self, action: QueueAction) -> int | str:
        self.client.ensure_ready(raise_on_estop=False)

        if action.kind is ActionKind.POSITION:
            self._current_label = f"Moving to {action.name}"
            self._emit_message(self._current_label)
            result = self.client.go_to_position_by_name(
                action.name,
                map_id=self.client.get_status().get("map_id"),
                raise_on_estop=False,
            )
        else:
            self._current_label = action.name
            self._emit_message(f"Running mission {action.name}")
            result = self.client.run_mission_by_name(
                action.name,
                raise_on_estop=False,
            )

        queue_id = result.get("id")
        if queue_id is None:
            raise MirError("Robot queued the mission but did not return a queue id.")
        return queue_id

    def _wait_for_action(self, action: QueueAction, queue_id: int | str, *, has_more: bool) -> str:
        if action.kind is ActionKind.MISSION and is_charge_action_name(action.name):
            self._emit_message("Waiting until charging has started…")
            outcome = self._wait_until_charging_started(queue_id)
            if outcome in _FAILED_QUEUE_STATES:
                return outcome
            if has_more:
                self._emit_message(
                    "Charging started — next draft action will interrupt Charge."
                )
            else:
                self._emit_message(
                    "Charging started — leaving Charge mission running (last queue item)."
                )
            return "charging" if outcome == "charging" else outcome

        return self._wait_for_queue_item(queue_id)

    def _wait_until_charging_started(self, queue_id: int | str) -> str:
        """
        Block until Charge has initiated, or the queue entry fails/aborts.

        Does not wait for Charge to finish (it normally never reaches Done while
        docked). Transient API timeouts are retried — they must not abort the draft.
        """
        seen_active = False
        missing_streak = 0
        last_state = ""
        while not self._stop.is_set():
            self._pause.wait()
            if self._stop.is_set():
                return last_state or "stopped"
            try:
                item = self.client.get_mission_queue_item(queue_id)
            except MirError as exc:
                handled = self._handle_wait_poll_error(
                    exc,
                    queue_id=queue_id,
                    seen_active=seen_active,
                    missing_streak=missing_streak,
                )
                if handled[0] == "retry":
                    missing_streak = handled[1]
                    continue
                if handled[0] == "done":
                    return handled[1]
                raise

            missing_streak = 0
            state = str(item.get("state") or "").strip()
            last_state = state
            state_key = state.casefold()
            if state_key in _ACTIVE_QUEUE_STATES:
                seen_active = True

            if is_terminal_queue_state(state):
                return state_key

            try:
                status = self.client.get_status()
                self._emit_status(status)
                if seen_active and is_charging_started(status):
                    return "charging"
            except MirError as exc:
                if not is_transient_mir_error(exc):
                    raise
            time.sleep(self.poll_seconds)

        return last_state or "stopped"

    def _wait_for_queue_item(self, queue_id: int | str) -> str:
        """Block until this mission_queue entry reaches a terminal state."""
        seen_active = False
        missing_streak = 0
        last_state = ""
        while not self._stop.is_set():
            self._pause.wait()
            if self._stop.is_set():
                return last_state or "stopped"
            try:
                item = self.client.get_mission_queue_item(queue_id)
            except MirError as exc:
                handled = self._handle_wait_poll_error(
                    exc,
                    queue_id=queue_id,
                    seen_active=seen_active,
                    missing_streak=missing_streak,
                )
                if handled[0] == "retry":
                    missing_streak = handled[1]
                    continue
                if handled[0] == "done":
                    return handled[1]
                raise

            missing_streak = 0
            state = str(item.get("state") or "").strip()
            last_state = state
            state_key = state.casefold()
            if state_key in _ACTIVE_QUEUE_STATES:
                seen_active = True

            if is_terminal_queue_state(state):
                return state_key

            finished = item.get("finished")
            if seen_active and finished not in (None, "", False):
                return state_key or "done"

            try:
                self._emit_status(self.client.get_status())
            except MirError as exc:
                if not is_transient_mir_error(exc):
                    raise
            time.sleep(self.poll_seconds)

        return last_state or "stopped"

    def _handle_wait_poll_error(
        self,
        exc: MirError,
        *,
        queue_id: int | str,
        seen_active: bool,
        missing_streak: int,
    ) -> tuple[str, Any]:
        """
        Decide how to treat a poll failure while waiting on mission_queue/{id}.

        Returns ("retry", new_missing_streak), ("done", state_token), or ("raise", None).
        """
        if exc.status_code == 404:
            missing_streak += 1
            if seen_active:
                return ("done", "gone")
            if missing_streak >= 10:
                return ("raise", None)
            time.sleep(self.poll_seconds)
            return ("retry", missing_streak)

        if is_transient_mir_error(exc):
            # Robot often finishes the mission while a single GET times out — check status.
            inferred = self._infer_queue_finished_from_status(queue_id, seen_active=seen_active)
            if inferred is not None:
                self._emit_message(
                    f"Poll timed out for queue id {queue_id}; robot status says it finished ({inferred})."
                )
                return ("done", inferred)
            self._emit_message(f"Transient API timeout — retrying wait for queue id {queue_id}…")
            time.sleep(max(self.poll_seconds, 1.0))
            return ("retry", missing_streak)

        return ("raise", None)

    def _infer_queue_finished_from_status(
        self, queue_id: int | str, *, seen_active: bool
    ) -> str | None:
        """If the robot has clearly moved on from our queue id, treat the wait as done."""
        if not seen_active:
            return None
        try:
            status = self.client.get_status()
        except MirError:
            return None
        self._emit_status(status)
        active = status.get("mission_queue_id")
        state_id = status.get("state_id")
        if active is not None and str(active) != str(queue_id):
            return "done"
        if active is None and state_id in {
            READY_STATE_ID,
            PAUSE_STATE_ID,
            COMPLETED_STATE_ID,
        }:
            return "done"
        return None

    def _set_state(self, state: RunnerState) -> None:
        self._state = state
        if self._on_state:
            self._on_state(state)

    def _emit_status(self, status: dict[str, Any]) -> None:
        if self._on_status:
            self._on_status(status)

    def _emit_message(self, message: str) -> None:
        if self._on_message:
            self._on_message(message)

    def _emit_queue_changed(self) -> None:
        if self._on_queue_changed:
            self._on_queue_changed()
