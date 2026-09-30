"""Lightweight tests for GUI draft queue, runner loop, and status helpers."""

from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock

from gui.models import ActionKind, QueueAction, RunnerState
from gui.services.draft_queue import DraftQueue
from gui.services.runner import QueueRunner
from mir.client import (
    MirError,
    can_clear_error,
    format_battery_time,
    format_estop_details,
    format_robot_errors,
    is_charge_action_name,
    is_charging_started,
    is_terminal_queue_state,
    is_transient_mir_error,
)


class DraftQueueTests(unittest.TestCase):
    def test_reorder(self) -> None:
        q = DraftQueue()
        a = QueueAction(ActionKind.POSITION, "A", "g1")
        b = QueueAction(ActionKind.MISSION, "B", "g2")
        c = QueueAction(ActionKind.POSITION, "C", "g3")
        q.add(a)
        q.add(b)
        q.add(c)
        self.assertTrue(q.move_up(1))
        self.assertEqual([i.name for i in q.items()], ["B", "A", "C"])
        self.assertTrue(q.move(0, 2))
        self.assertEqual([i.name for i in q.items()], ["A", "C", "B"])


class StatusHelperTests(unittest.TestCase):
    def test_battery_time(self) -> None:
        self.assertEqual(format_battery_time(47999), "13:19")
        self.assertEqual(format_battery_time(90), "0:01")
        self.assertEqual(format_battery_time(None), "unknown")

    def test_estop_only_when_triggered(self) -> None:
        self.assertIsNone(format_estop_details({"state_id": 3, "errors": [{"message": "x"}]}))
        text = format_estop_details({"state_id": 10, "errors": [{"description": "Bumper"}]})
        self.assertEqual(text, "Bumper")

    def test_error_state_expands_json_description(self) -> None:
        status = {
            "state_id": 12,
            "state_text": "Error",
            "mission_text": "Failed to reach goal position 'Station 2'",
            "errors": [
                {
                    "code": 10120,
                    "module": "MissionController",
                    "description": (
                        '{"message": "Failed to reach goal position \'%(position_name)s\'", '
                        '"args": {"position_name":"Station 2"}}'
                    ),
                }
            ],
        }
        text = format_robot_errors(status)
        assert text is not None
        self.assertIn("Failed to reach goal position 'Station 2'", text)
        self.assertTrue(text.startswith("Error:"))

    def test_terminal_states(self) -> None:
        self.assertTrue(is_terminal_queue_state("Done"))
        self.assertTrue(is_terminal_queue_state("Aborted"))
        self.assertFalse(is_terminal_queue_state("Executing"))

    def test_charge_name(self) -> None:
        self.assertTrue(is_charge_action_name("Charge"))
        self.assertTrue(is_charge_action_name("charge"))
        self.assertFalse(is_charge_action_name("ChargeStation"))

    def test_charging_started(self) -> None:
        self.assertTrue(
            is_charging_started({"mission_text": "Charging... Waiting for new mission..."})
        )
        self.assertTrue(is_charging_started({"state_id": 8}))  # Docked
        # Still docking / driving to Charger — NOT started yet.
        self.assertFalse(is_charging_started({"state_id": 9}))
        self.assertFalse(
            is_charging_started({"mission_text": "Moving to 'Charger' (1.8 meters to goal)", "state_id": 5})
        )
        self.assertFalse(is_charging_started({"mission_text": "Moving", "state_id": 5}))

    def test_charge_prompt_kind(self) -> None:
        from mir.client import charge_prompt_kind

        self.assertEqual(
            charge_prompt_kind({"mission_text": "Charging... Waiting for new mission..."}),
            "charging",
        )
        self.assertEqual(
            charge_prompt_kind({"state_id": 9, "mission_text": "Docking"}),
            "about_to_charge",
        )
        self.assertEqual(
            charge_prompt_kind(
                {"state_id": 5, "mission_text": "Moving to 'Charger'"},
                queue_item={"message": "RunMission Charge", "state": "Executing"},
            ),
            "about_to_charge",
        )
        self.assertIsNone(charge_prompt_kind({"state_id": 3, "mission_text": "Waiting"}))
        self.assertEqual(
            charge_prompt_kind({"state_id": 3}, preserving_charge=True),
            "charging",
        )
        self.assertTrue(
            is_transient_mir_error(
                MirError(
                    "GET /mission_queue/886 failed: HTTPConnectionPool(host='10.14.19.160', port=80): "
                    "Read timed out. (read timeout=12.0)"
                )
            )
        )
        self.assertFalse(is_transient_mir_error(MirError("bad name", status_code=400)))

    def test_can_clear_error_only_in_error_state(self) -> None:
        self.assertTrue(can_clear_error({"state_id": 12}))
        self.assertFalse(can_clear_error({"state_id": 10}))  # e-stop
        self.assertFalse(can_clear_error({"state_id": 3}))
        self.assertFalse(can_clear_error({"state_id": 5, "errors": [{"code": 1}]}))


class QueueRunnerTests(unittest.TestCase):
    def test_runs_all_items_without_waiting_for_restart(self) -> None:
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "One", "g1"))
        draft.add(QueueAction(ActionKind.MISSION, "Two", "g2"))
        draft.add(QueueAction(ActionKind.MISSION, "Three", "g3"))

        client = MagicMock()
        client.get_status.return_value = {"map_id": "m", "mission_queue_id": None}
        client.ensure_ready.return_value = {"state_id": 3}
        client.run_mission_by_name.side_effect = [
            {"id": 101},
            {"id": 102},
            {"id": 103},
        ]
        client.get_mission_queue_item.side_effect = [
            {"id": 101, "state": "Executing", "finished": None},
            {"id": 101, "state": "Done", "finished": "t"},
            {"id": 102, "state": "Executing", "finished": None},
            {"id": 102, "state": "Done", "finished": "t"},
            {"id": 103, "state": "Executing", "finished": None},
            {"id": 103, "state": "Done", "finished": "t"},
        ]

        messages: list[str] = []
        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            on_message=messages.append,
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        runner._thread.join(timeout=5)
        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual(len(draft), 0)
        self.assertEqual(client.run_mission_by_name.call_count, 3)
        self.assertTrue(any("Queue finished" in m for m in messages))
        self.assertTrue(any("Continuing" in m for m in messages))

    def test_charge_last_waits_until_charging_then_ends(self) -> None:
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "Charge", "gc"))

        client = MagicMock()
        client.ensure_ready.return_value = {"state_id": 3}
        client.run_mission_by_name.return_value = {"id": 200}
        client.get_mission_queue_item.side_effect = [
            {"id": 200, "state": "Pending", "finished": None},
            {"id": 200, "state": "Executing", "finished": None},
        ]
        client.get_status.side_effect = [
            {"mission_text": "Going to charge"},
            {"mission_text": "Charging... Waiting for new mission...", "state_id": 5},
        ]

        messages: list[str] = []
        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            on_message=messages.append,
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        runner._thread.join(timeout=5)
        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual(len(draft), 0)
        self.assertTrue(runner.preserving_charge)
        self.assertTrue(any("leaving Charge mission running" in m for m in messages))
        # Completing the queue must not abort/pause the Charge mission.
        client.abort_active_mission.assert_not_called()
        client.pause_robot.assert_not_called()
        # Stop while idle must also leave charging alone.
        runner.stop()
        client.abort_active_mission.assert_not_called()
        self.assertTrue(any("Leaving Charge running" in m for m in messages))

    def test_failed_action_stays_in_draft(self) -> None:
        from mir.client import MirError

        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "One", "g1"))
        draft.add(QueueAction(ActionKind.MISSION, "Two", "g2"))

        client = MagicMock()
        client.ensure_ready.side_effect = MirError("not ready")
        client.get_status.return_value = {"state_id": 12}
        client.clear_error.side_effect = MirError("still bad")

        messages: list[str] = []
        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            on_message=messages.append,
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        runner._thread.join(timeout=5)
        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual([a.name for a in draft.items()], ["One", "Two"])
        self.assertTrue(any("still in draft" in m for m in messages))

    def test_continues_after_aborted_mission(self) -> None:
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "One", "g1"))
        draft.add(QueueAction(ActionKind.MISSION, "Two", "g2"))

        client = MagicMock()
        client.get_status.return_value = {"map_id": "m", "state_id": 12}
        client.ensure_ready.return_value = {"state_id": 3}
        client.clear_error.return_value = {"state_id": 3}
        client.run_mission_by_name.side_effect = [{"id": 1}, {"id": 2}]
        client.get_mission_queue_item.side_effect = [
            {"id": 1, "state": "Executing", "finished": None},
            {"id": 1, "state": "Aborted", "finished": "t"},
            {"id": 2, "state": "Executing", "finished": None},
            {"id": 2, "state": "Done", "finished": "t"},
        ]

        messages: list[str] = []
        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            on_message=messages.append,
            poll_seconds=0.01,
        )
        from unittest.mock import patch

        with patch("gui.services.runner.can_clear_error", return_value=True):
            runner.start()
            assert runner._thread is not None
            runner._thread.join(timeout=5)

        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual(client.run_mission_by_name.call_count, 2)
        self.assertTrue(any("Continuing" in m for m in messages))
        self.assertTrue(any("ended with aborted" in m for m in messages))
        client.clear_error.assert_called()

    def test_charge_then_next_waits_for_charging_started_only(self) -> None:
        """GUI waits until charging initiated, then sends the next draft action."""
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "Charge", "gc"))
        draft.add(QueueAction(ActionKind.MISSION, "Next", "gn"))

        client = MagicMock()
        client.ensure_ready.return_value = {"state_id": 3}
        client.run_mission_by_name.side_effect = [{"id": 201}, {"id": 202}]
        # Charge never reaches Done — only Executing + charging status.
        client.get_mission_queue_item.side_effect = [
            {"id": 201, "state": "Executing", "finished": None},
            {"id": 202, "state": "Executing", "finished": None},
            {"id": 202, "state": "Done", "finished": "t"},
        ]
        client.get_status.side_effect = [
            {"mission_text": "Charging... Waiting for new mission...", "state_id": 5},
            {"mission_text": "Next", "state_id": 5},
            {"mission_text": "Next", "state_id": 5},
        ]

        messages: list[str] = []
        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            on_message=messages.append,
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        runner._thread.join(timeout=5)
        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual(len(draft), 0)
        self.assertEqual(client.run_mission_by_name.call_count, 2)
        self.assertTrue(any("Charging started" in m for m in messages))
        self.assertTrue(any("interrupt Charge" in m for m in messages))

    def test_timeout_during_wait_does_not_stop_queue(self) -> None:
        """Read timeouts while polling must not abort the draft (RallyToSt2 green-light case)."""
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "RallyToSt2", "g1"))
        draft.add(QueueAction(ActionKind.MISSION, "Charge", "gc"))

        client = MagicMock()
        client.ensure_ready.return_value = {"state_id": 3}
        client.run_mission_by_name.side_effect = [{"id": 886}, {"id": 887}]

        polls = {"n": 0}

        def queue_item(qid):
            polls["n"] += 1
            if str(qid) == "886":
                if polls["n"] == 1:
                    return {"id": 886, "state": "Executing", "finished": None}
                if polls["n"] == 2:
                    raise MirError(
                        "GET /mission_queue/886 failed: Read timed out. (read timeout=12.0)"
                    )
                return {"id": 886, "state": "Done", "finished": "t"}
            return {"id": 887, "state": "Executing", "finished": None}

        client.get_mission_queue_item.side_effect = queue_item
        client.get_status.return_value = {
            "state_id": 3,
            "mission_queue_id": None,
            "mission_text": "Charging... Waiting for new mission...",
        }

        messages: list[str] = []
        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            on_message=messages.append,
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        runner._thread.join(timeout=5)

        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual(len(draft), 0)
        self.assertTrue(runner.preserving_charge)
        self.assertEqual(client.run_mission_by_name.call_count, 2)
        self.assertFalse(any(m.startswith("Stopped on") for m in messages))

    def test_detach_does_not_abort_mission(self) -> None:
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "Charge", "gc"))

        client = MagicMock()
        client.ensure_ready.return_value = {"state_id": 3}
        client.run_mission_by_name.return_value = {"id": 200}
        client.get_mission_queue_item.return_value = {
            "id": 200,
            "state": "Executing",
            "finished": None,
        }
        client.get_status.return_value = {
            "mission_text": "Charging... Waiting for new mission...",
            "state_id": 5,
        }

        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        # Detach while Charge is active / just finished — must not abort.
        time.sleep(0.05)
        runner.detach()
        runner._thread.join(timeout=2)
        client.abort_active_mission.assert_not_called()
        client.pause_robot.assert_not_called()

        """A transient wait error must not POST Charge a second time (undock/re-dock bug)."""
        draft = DraftQueue()
        draft.add(QueueAction(ActionKind.MISSION, "Charge", "gc"))
        draft.add(QueueAction(ActionKind.MISSION, "Next", "gn"))

        client = MagicMock()
        client.ensure_ready.return_value = {"state_id": 3}
        client.run_mission_by_name.side_effect = [{"id": 201}, {"id": 202}]

        calls = {"n": 0}

        def queue_item(qid):
            calls["n"] += 1
            if calls["n"] == 1:
                raise MirError("transient", status_code=500)
            if str(qid) == "201":
                return {"id": 201, "state": "Executing", "finished": None}
            if calls["n"] == 2:
                return {"id": 202, "state": "Executing", "finished": None}
            return {"id": 202, "state": "Done", "finished": "t"}

        client.get_mission_queue_item.side_effect = queue_item
        client.get_status.return_value = {
            "mission_text": "Charging... Waiting for new mission...",
            "state_id": 5,
        }

        runner = QueueRunner(
            client,
            get_actions=draft.items,
            pop_front=lambda: draft.remove_at(0),
            poll_seconds=0.01,
        )
        runner.start()
        assert runner._thread is not None
        runner._thread.join(timeout=5)

        self.assertEqual(runner.state, RunnerState.IDLE)
        self.assertEqual(client.run_mission_by_name.call_count, 2)
        self.assertEqual(client.run_mission_by_name.call_args_list[0].args[0], "Charge")
        self.assertEqual(client.run_mission_by_name.call_args_list[1].args[0], "Next")


if __name__ == "__main__":
    unittest.main()
