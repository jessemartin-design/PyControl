"""Small REST client for a single MiR robot."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests
import urllib3
from requests.auth import HTTPBasicAuth

HELPER_MISSION_NAME = "CLI_GoToPosition"
DEFAULT_HOST = "10.14.19.160"
DEFAULT_API_VERSION = "v2.0.0"
# Connect can fail fast; reads need headroom while the robot is navigating / docking.
DEFAULT_CONNECT_TIMEOUT = 15.0
DEFAULT_READ_TIMEOUT = 60.0
# Extra attempts after the first failure (0 = no retry). Shared by CLI and GUI.
DEFAULT_HTTP_RETRIES = 3
DEFAULT_HTTP_RETRY_BACKOFF = 1.0
# Methods safe to retry even after a partial/ambiguous response (e.g. read timeout).
_IDEMPOTENT_HTTP_METHODS = frozenset({"GET", "HEAD"})
READY_STATE_ID = 3
PAUSE_STATE_ID = 4
EXECUTING_STATE_ID = 5
COMPLETED_STATE_ID = 7
DOCKED_STATE_ID = 8
DOCKING_STATE_ID = 9
EMERGENCY_STATE_ID = 10
ERROR_STATE_ID = 12
PAGE_SIZE = 100

# Software 2.13 on this robot answers on HTTP/80. HTTPS and :8080 are fallbacks.
DISCOVERY_TEMPLATES = (
    "http://{host}/api/{version}",
    "https://{host}/api/{version}",
    "http://{host}:8080/api/{version}",
)


class MirError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass
class NamedItem:
    name: str
    guid: str
    extra: dict[str, Any]

    def __str__(self) -> str:
        return self.name


class MirClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        *,
        base_url: str | None = None,
        verify_tls: bool = False,
        timeout: float | tuple[float, float] = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT),
        http_retries: int | None = None,
        http_retry_backoff: float | None = None,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.base_url = (base_url or "").rstrip("/")
        self.verify_tls = verify_tls
        self.timeout = _normalize_timeout(timeout)
        self.http_retries = (
            DEFAULT_HTTP_RETRIES if http_retries is None else max(0, int(http_retries))
        )
        self.http_retry_backoff = (
            DEFAULT_HTTP_RETRY_BACKOFF
            if http_retry_backoff is None
            else max(0.0, float(http_retry_backoff))
        )
        self.session = requests.Session()
        # GUI status polling + queue runner share this client; lock all HTTP.
        self._request_lock = threading.RLock()
        # MiR Basic auth is username:sha256(password), not the plain UI password.
        self._set_auth(password)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Language": "en_US",
            }
        )
        if not verify_tls:
            self.session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.robot_version = ""
        self.api_version = ""
        self.product = ""
        self._auth_verified = False

    def _set_auth(self, password: str) -> None:
        self.session.auth = HTTPBasicAuth(self.username, _mir_password_hash(password))

    @classmethod
    def from_env(cls, host_override: str | None = None, base_url_override: str | None = None) -> MirClient:
        host = host_override or os.environ.get("MIR_HOST", DEFAULT_HOST).strip()
        username = os.environ.get("MIR_USERNAME", "").strip()
        password = os.environ.get("MIR_PASSWORD", "")
        base_url = base_url_override or os.environ.get("MIR_API_BASE", "").strip() or None
        verify = os.environ.get("MIR_VERIFY_TLS", "false").strip().lower() in {"1", "true", "yes"}
        if not username or not password:
            raise MirError(
                "Missing MIR_USERNAME or MIR_PASSWORD. Copy .env.example to .env "
                "and add the same login you use for the MiR web UI."
            )
        return cls(
            host,
            username,
            password,
            base_url=base_url,
            verify_tls=verify,
            timeout=_timeouts_from_env(),
            http_retries=_http_retries_from_env(),
            http_retry_backoff=_http_retry_backoff_from_env(),
        )

    def connect(self) -> dict[str, Any]:
        if not self.base_url:
            self.base_url = self._discover_base_url()
        self._authenticate()
        status = self.get_status()
        return status

    def _authenticate(self) -> None:
        """Prove Basic auth works. MiR hashes passwords case-sensitively; the web UI often does not."""
        if self._auth_verified:
            return
        if not self.base_url:
            self.base_url = self._discover_base_url()

        candidates: list[str] = []
        for candidate in (self.password, self.password.lower(), self.password.upper()):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        last_error: MirError | None = None
        for candidate in candidates:
            self._set_auth(candidate)
            try:
                self.request("GET", "/missions", params={"start": 0, "limit": 1})
            except MirError as exc:
                last_error = exc
                if exc.status_code != 401:
                    raise
                continue
            self.password = candidate
            self._auth_verified = True
            return

        raise MirError(
            "Login failed due to incorrect username or password. "
            "Confirm MIR_USERNAME / MIR_PASSWORD in .env match the MiR web UI. "
            "API auth hashes the password and is case-sensitive even when the UI is not."
        ) from last_error

    def get_status(self) -> dict[str, Any]:
        return self.request("GET", "/status")

    def get_positions(self) -> list[NamedItem]:
        items = []
        for raw in self._get_collection("/positions"):
            name = (raw.get("name") or "").strip()
            guid = raw.get("guid") or raw.get("id")
            if name and guid:
                items.append(NamedItem(name=name, guid=str(guid), extra=raw))
        return items

    def get_missions(self, *, include_hidden: bool = False) -> list[NamedItem]:
        items = []
        for raw in self._get_collection("/missions"):
            name = (raw.get("name") or "").strip()
            guid = raw.get("guid") or raw.get("id")
            if not name or not guid:
                continue
            hidden = bool(raw.get("hidden"))
            if name == HELPER_MISSION_NAME and not include_hidden:
                continue
            if hidden and not include_hidden:
                continue
            items.append(NamedItem(name=name, guid=str(guid), extra=raw))
        return items

    def ensure_ready(self, *, raise_on_estop: bool = True) -> dict[str, Any]:
        status = self.get_status()
        state_id = status.get("state_id")
        if state_id == EMERGENCY_STATE_ID:
            if raise_on_estop:
                raise MirError(
                    "Robot is in Emergency stop. Clear the e-stop on the robot before sending commands."
                )
            return status
        # Software Error (12) blocks new missions until clear_error — common after a failed GoTo.
        if state_id == ERROR_STATE_ID:
            self.request("PUT", "/status", json={"clear_error": True})
            status = self.get_status()
            state_id = status.get("state_id")
            if state_id == ERROR_STATE_ID:
                raise MirError(
                    "Robot is in Error state and did not clear. "
                    "Use Clear errors in the GUI (or the MiR UI), then retry."
                )
        if state_id == READY_STATE_ID or state_id == EXECUTING_STATE_ID:
            return status
        if state_id == PAUSE_STATE_ID:
            self.request("PUT", "/status", json={"state_id": READY_STATE_ID})
            return self.get_status()
        # Other idle-like states (Completed, Aborted, …): ask the robot to go Ready.
        self.request("PUT", "/status", json={"state_id": READY_STATE_ID})
        return self.get_status()

    def prepare_for_command(self, *, raise_on_estop: bool = True) -> dict[str, Any]:
        """Clear software errors if needed and put the robot in Ready/Executing for queueing."""
        return self.ensure_ready(raise_on_estop=raise_on_estop)

    def set_state(self, state_id: int) -> dict[str, Any]:
        """Request a robot state (Ready=3, Pause=4, etc.)."""
        self.request("PUT", "/status", json={"state_id": state_id})
        return self.get_status()

    def pause_robot(self) -> dict[str, Any]:
        return self.set_state(PAUSE_STATE_ID)

    def resume_robot(self) -> dict[str, Any]:
        return self.set_state(READY_STATE_ID)

    def clear_error(self) -> dict[str, Any]:
        """
        Clear a software Error state via PUT /status {"clear_error": true}.

        Only effective for clearable Error (state_id 12), not physical e-stop.
        """
        status = self.get_status()
        if not can_clear_error(status):
            raise MirError(
                "No clearable error on the robot "
                f"(state={status.get('state_text') or status.get('state_id')})."
            )
        self.request("PUT", "/status", json={"clear_error": True})
        status = self.get_status()
        # After clearing, request Ready so the robot can accept new missions.
        if status.get("state_id") == ERROR_STATE_ID:
            try:
                self.request("PUT", "/status", json={"state_id": READY_STATE_ID, "clear_error": True})
                status = self.get_status()
            except MirError:
                pass
        return status

    def get_mission_queue(self) -> list[dict[str, Any]]:
        return self._get_collection("/mission_queue")

    def get_mission_queue_item(self, queue_id: int | str) -> dict[str, Any]:
        data = self.request("GET", f"/mission_queue/{queue_id}")
        if not isinstance(data, dict):
            raise MirError(f"Unexpected mission_queue/{queue_id} payload: {type(data).__name__}")
        return data

    def delete_mission_queue_item(self, queue_id: int | str) -> None:
        self.request("DELETE", f"/mission_queue/{queue_id}")

    def abort_active_mission(self) -> dict[str, Any]:
        """DELETE the current mission_queue entry (if any) and pause the robot."""
        status = self.get_status()
        queue_id = status.get("mission_queue_id")
        if queue_id is not None:
            try:
                self.delete_mission_queue_item(queue_id)
            except MirError:
                pass
        try:
            return self.pause_robot()
        except MirError:
            return self.get_status()

    def get_paths(self) -> list[dict[str, Any]]:
        return self._get_collection("/paths")

    def clear_paths(self) -> int:
        """
        Delete all stored paths on the robot (GET /paths → DELETE /paths/{guid}).

        Clearing cached paths forces the planner to replan on the next move.
        """
        paths = self.get_paths()
        deleted = 0
        errors: list[str] = []
        for item in paths:
            guid = item.get("guid") or item.get("id")
            if not guid:
                continue
            try:
                self.request("DELETE", f"/paths/{guid}")
                deleted += 1
            except MirError as exc:
                errors.append(f"{guid}: {exc}")
        if errors and deleted == 0:
            raise MirError("Could not clear paths:\n  " + "\n  ".join(errors))
        return deleted

    def queue_mission(self, mission_guid: str, message: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"mission_id": mission_guid, "priority": 0}
        if message:
            payload["message"] = message
        return self.request("POST", "/mission_queue", json=payload)

    def run_mission_by_name(
        self,
        name: str,
        missions: list[NamedItem] | None = None,
        *,
        raise_on_estop: bool = True,
    ) -> dict[str, Any]:
        missions = missions if missions is not None else self.get_missions()
        mission = _pick_named(name, missions, label="mission")
        self.ensure_ready(raise_on_estop=raise_on_estop)
        return self.queue_mission(mission.guid, message=f"RunMission {mission.name}")

    def go_to_position_by_name(
        self,
        name: str,
        *,
        positions: list[NamedItem] | None = None,
        map_id: str | None = None,
        raise_on_estop: bool = True,
    ) -> dict[str, Any]:
        positions = positions if positions is not None else self.get_positions()
        position = _pick_named(name, positions, label="position", map_id=map_id)
        mission_guid = self._ensure_goto_helper(position.guid)
        self.ensure_ready(raise_on_estop=raise_on_estop)
        return self.queue_mission(mission_guid, message=f"GoToPosition {position.name}")

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self.base_url:
            raise MirError("Client is not connected. Call connect() first.")
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        method_upper = method.upper()
        attempts = 1 + self.http_retries
        last_error: MirError | None = None

        with self._request_lock:
            for attempt in range(attempts):
                try:
                    response = self.session.request(
                        method_upper, url, timeout=self.timeout, **kwargs
                    )
                except requests.RequestException as exc:
                    last_error = MirError(f"{method_upper} {path} failed: {exc}")
                    if attempt + 1 < attempts and should_retry_mir_request(
                        method_upper, last_error, transport_error=True
                    ):
                        time.sleep(self.http_retry_backoff * (attempt + 1))
                        continue
                    raise last_error from exc

                self._capture_headers(response)
                if response.status_code >= 400:
                    detail = _error_text(response)
                    last_error = MirError(
                        f"{method_upper} {path} returned {response.status_code}: {detail}",
                        status_code=response.status_code,
                        body=_safe_json(response),
                    )
                    if attempt + 1 < attempts and should_retry_mir_request(
                        method_upper, last_error, transport_error=False
                    ):
                        time.sleep(self.http_retry_backoff * (attempt + 1))
                        continue
                    raise last_error
                if response.status_code == 204 or not response.content:
                    return {}
                return _safe_json(response)

        if last_error is not None:
            raise last_error
        raise MirError(f"{method_upper} {path} failed with no response")

    def _discover_base_url(self) -> str:
        errors: list[str] = []
        # Discovery only needs connect + a short status body; use connect timeout for both.
        discover_timeout = self.timeout[0]
        for template in DISCOVERY_TEMPLATES:
            candidate = template.format(host=self.host, version=DEFAULT_API_VERSION)
            try:
                response = self.session.get(f"{candidate}/status", timeout=discover_timeout)
            except requests.RequestException as exc:
                errors.append(f"{candidate}: {exc}")
                continue
            self._capture_headers(response)
            if response.status_code < 500:
                return candidate
            errors.append(f"{candidate}: HTTP {response.status_code}")
        raise MirError(
            "Could not reach the MiR API. Tried:\n  " + "\n  ".join(errors)
        )

    def _get_collection(self, path: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        start = 0
        while True:
            data = self.request("GET", path, params={"start": start, "limit": PAGE_SIZE})
            if isinstance(data, list):
                batch = data
            elif isinstance(data, dict) and isinstance(data.get("data"), list):
                batch = data["data"]
            else:
                raise MirError(f"Unexpected {path} payload: {type(data).__name__}")
            items.extend(item for item in batch if isinstance(item, dict))
            if len(batch) < PAGE_SIZE:
                break
            start += PAGE_SIZE
        return items

    def _ensure_goto_helper(self, position_guid: str) -> str:
        helper = self._find_helper_mission()
        if helper is None:
            helper = self._create_helper_mission()
            self._add_move_action(helper["guid"], position_guid)
            return helper["guid"]

        actions = self.request("GET", f"/missions/{helper['guid']}/actions")
        if not isinstance(actions, list):
            actions = []
        move = next((action for action in actions if action.get("action_type") == "move"), None)
        if move is None:
            self._add_move_action(helper["guid"], position_guid)
        else:
            self._update_move_action(helper["guid"], move, position_guid)
        return helper["guid"]

    def _find_helper_mission(self) -> dict[str, Any] | None:
        for raw in self._get_collection("/missions"):
            if (raw.get("name") or "").strip() == HELPER_MISSION_NAME:
                return raw
        return None

    def _create_helper_mission(self) -> dict[str, Any]:
        groups = self._get_collection("/mission_groups")
        if not groups:
            raise MirError(
                "Cannot create the GoToPosition helper mission: no mission groups on the robot. "
                "Create a mission group in the MiR UI, or create a mission named "
                f"{HELPER_MISSION_NAME} with a single Move action."
            )
        group_id = groups[0].get("guid")
        try:
            created = self.request(
                "POST",
                "/missions",
                json={
                    "name": HELPER_MISSION_NAME,
                    "group_id": group_id,
                    "hidden": False,
                    "description": "Created by mir_command.py to send GoToPosition commands.",
                },
            )
        except MirError as exc:
            existing = self._find_helper_mission()
            if existing:
                return existing
            raise MirError(
                f"Could not create helper mission {HELPER_MISSION_NAME}: {exc}. "
                "Your user may need permission to create missions, or you can create "
                f"a mission named {HELPER_MISSION_NAME} with one Move action in the UI."
            ) from exc
        if not isinstance(created, dict) or not created.get("guid"):
            raise MirError("Robot created a helper mission but did not return a guid.")
        return created

    def _move_parameters(self, position_guid: str) -> list[dict[str, Any]]:
        try:
            definition = self.request("GET", "/actions/move")
        except MirError:
            definition = {}
        raw_params = definition.get("parameters") if isinstance(definition, dict) else None
        if not raw_params:
            return [
                {"id": "position", "value": position_guid},
                {"id": "retries", "value": 10},
                {"id": "distance_threshold", "value": 0.1},
            ]

        params = []
        for item in raw_params:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            entry = {"id": item["id"], "value": item.get("value")}
            if item.get("guid"):
                entry["guid"] = item["guid"]
            if item["id"] == "position":
                entry["value"] = position_guid
            elif entry["value"] in (None, "", "null"):
                if item["id"] == "retries":
                    entry["value"] = 10
                elif item["id"] == "distance_threshold":
                    entry["value"] = 0.1
            params.append(entry)
        if not any(item["id"] == "position" for item in params):
            params.insert(0, {"id": "position", "value": position_guid})
        return params

    def _add_move_action(self, mission_guid: str, position_guid: str) -> None:
        payload = {
            "action_type": "move",
            "mission_id": mission_guid,
            "priority": 1,
            "parameters": self._move_parameters(position_guid),
        }
        self.request("POST", f"/missions/{mission_guid}/actions", json=payload)

    def _update_move_action(self, mission_guid: str, action: dict[str, Any], position_guid: str) -> None:
        parameters = action.get("parameters") or self._move_parameters(position_guid)
        updated = []
        found_position = False
        for item in parameters:
            if not isinstance(item, dict):
                continue
            entry = dict(item)
            if entry.get("id") == "position":
                entry["value"] = position_guid
                found_position = True
            updated.append(entry)
        if not found_position:
            updated = self._move_parameters(position_guid)
        self.request(
            "PUT",
            f"/missions/{mission_guid}/actions/{action['guid']}",
            json={
                "priority": action.get("priority", 1),
                "parameters": updated,
            },
        )

    def _capture_headers(self, response: requests.Response) -> None:
        self.robot_version = response.headers.get("Robot-Version", self.robot_version)
        self.api_version = response.headers.get("API-Version", self.api_version)
        self.product = response.headers.get("MiR-Product", self.product)


def load_dotenv(path: str = ".env") -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            # Prefer values from .env over any leftover shell variables.
            os.environ[key] = value


def _normalize_timeout(timeout: float | tuple[float, float]) -> tuple[float, float]:
    if isinstance(timeout, (int, float)):
        value = float(timeout)
        return (value, value)
    connect, read = timeout
    return (float(connect), float(read))


def _timeouts_from_env() -> tuple[float, float]:
    """
    Optional .env overrides:
      MIR_HTTP_TIMEOUT=30          → connect and read both 30s
      MIR_CONNECT_TIMEOUT=15
      MIR_READ_TIMEOUT=60
    """
    connect = DEFAULT_CONNECT_TIMEOUT
    read = DEFAULT_READ_TIMEOUT
    both = os.environ.get("MIR_HTTP_TIMEOUT", "").strip()
    if both:
        try:
            value = float(both)
            connect = value
            read = value
        except ValueError:
            pass
    connect_raw = os.environ.get("MIR_CONNECT_TIMEOUT", "").strip()
    if connect_raw:
        try:
            connect = float(connect_raw)
        except ValueError:
            pass
    read_raw = os.environ.get("MIR_READ_TIMEOUT", "").strip()
    if read_raw:
        try:
            read = float(read_raw)
        except ValueError:
            pass
    return (connect, read)


def _http_retries_from_env() -> int:
    """MIR_HTTP_RETRIES = extra attempts after the first failure (default 3). Set 0 to disable."""
    raw = os.environ.get("MIR_HTTP_RETRIES", "").strip()
    if not raw:
        return DEFAULT_HTTP_RETRIES
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_HTTP_RETRIES


def _http_retry_backoff_from_env() -> float:
    """MIR_HTTP_RETRY_BACKOFF = seconds base delay; sleep is backoff * attempt_number."""
    raw = os.environ.get("MIR_HTTP_RETRY_BACKOFF", "").strip()
    if not raw:
        return DEFAULT_HTTP_RETRY_BACKOFF
    try:
        return max(0.0, float(raw))
    except ValueError:
        return DEFAULT_HTTP_RETRY_BACKOFF


def _mir_password_hash(password: str) -> str:
    """Return the hex SHA-256 digest MiR expects in Basic auth."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def format_status(status: dict[str, Any]) -> str:
    name = status.get("robot_name") or "MiR"
    battery = status.get("battery_percentage")
    battery_text = f"{battery:.1f}%" if isinstance(battery, (int, float)) else "unknown"
    state = status.get("state_text") or f"state_id={status.get('state_id')}"
    mission = status.get("mission_text") or ""
    parts = [f"{name}", f"battery {battery_text}", str(state)]
    if mission:
        parts.append(mission)
    return "  |  ".join(parts)


def format_battery_time(seconds: Any) -> str:
    """Format Mir status battery_time_remaining (seconds) as H:MM."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "unknown"
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    return f"{hours}:{minutes:02d}"


def format_error_item(item: Any) -> str:
    """Turn one status.errors[] entry into a readable line."""
    if not isinstance(item, dict):
        return str(item)
    raw = item.get("description") or item.get("error_human") or item.get("message")
    text = _expand_mir_error_description(raw)
    if not text:
        code = item.get("code")
        module = item.get("module")
        bits = [str(x) for x in (code, module) if x not in (None, "")]
        text = " ".join(bits) if bits else str(item)
    module = item.get("module")
    code = item.get("code")
    suffix_parts = []
    if code not in (None, ""):
        suffix_parts.append(f"code {code}")
    if module not in (None, ""):
        suffix_parts.append(str(module))
    if suffix_parts and not any(s in text for s in suffix_parts):
        return f"{text} ({', '.join(suffix_parts)})"
    return text


def _expand_mir_error_description(raw: Any) -> str:
    if raw is None:
        return ""
    if not isinstance(raw, str):
        return str(raw)
    stripped = raw.strip()
    if not stripped:
        return ""
    if stripped.startswith("{"):
        try:
            import json

            payload = json.loads(stripped)
        except (ValueError, TypeError):
            return stripped
        if isinstance(payload, dict):
            message = str(payload.get("message") or "")
            args = payload.get("args")
            if message and isinstance(args, dict):
                try:
                    return message % args
                except (TypeError, ValueError, KeyError):
                    return message or stripped
            return message or stripped
    return stripped


def format_robot_errors(status: dict[str, Any]) -> str | None:
    """
    Human-readable robot error text when status reports problems.

    Shows for Emergency stop (10), Error (12), or any non-empty status['errors'].
    """
    state_id = status.get("state_id")
    errors = status.get("errors") or []
    parts: list[str] = []
    if isinstance(errors, list):
        for item in errors:
            text = format_error_item(item).strip()
            if text:
                parts.append(text)

    mission_text = (status.get("mission_text") or "").strip()
    if mission_text and mission_text not in parts:
        # Often duplicates the expanded error; keep if we have nothing else.
        if not parts:
            parts.append(mission_text)

    if not parts:
        if state_id == EMERGENCY_STATE_ID:
            return status.get("state_text") or "Emergency stop"
        if state_id == ERROR_STATE_ID:
            return status.get("state_text") or "Error"
        return None

    detail = "; ".join(parts)
    if state_id == EMERGENCY_STATE_ID:
        return f"E-STOP: {detail}"
    if state_id == ERROR_STATE_ID:
        return f"Error: {detail}"
    return f"Fault: {detail}"


def can_clear_error(status: dict[str, Any]) -> bool:
    """
    True when the robot is in software Error state (12), which PUT clear_error can clear.

    Physical e-stop (10) is not clearable from the API alone.
    """
    return status.get("state_id") == ERROR_STATE_ID


def format_estop_details(status: dict[str, Any]) -> str | None:
    """Deprecated alias — prefer format_robot_errors (includes Error state 12)."""
    if status.get("state_id") != EMERGENCY_STATE_ID:
        return None
    text = format_robot_errors(status)
    if text and text.startswith("E-STOP: "):
        return text[len("E-STOP: ") :]
    return text


TERMINAL_QUEUE_STATES = frozenset({"done", "aborted", "abort", "error", "failed", "cancelled", "canceled"})


def is_terminal_queue_state(state: Any) -> bool:
    return str(state or "").strip().casefold() in TERMINAL_QUEUE_STATES


def is_transient_mir_error(exc: MirError) -> bool:
    """True for timeouts / brief connectivity blips that wait loops should retry."""
    if exc.status_code in {408, 425, 429, 500, 502, 503, 504}:
        return True
    text = str(exc).casefold()
    markers = (
        "timed out",
        "timeout",
        "temporarily unavailable",
        "connection aborted",
        "connection reset",
        "connection refused",
        "connecttimeout",
        "max retries exceeded",
        "failed to establish a new connection",
        "network is unreachable",
        "broken pipe",
        "remote end closed",
        "name or service not known",
        "nodename nor servname",
    )
    return any(marker in text for marker in markers)


def should_retry_mir_request(
    method: str,
    exc: MirError,
    *,
    transport_error: bool,
) -> bool:
    """
    Whether MirClient.request should retry this failure.

    - Transport errors with no HTTP response (connect timeout, connection reset):
      retry any method — the request likely never reached the robot.
    - Read timeout / 5xx / 429 after a possible server-side effect:
      retry only GET/HEAD so we never double-POST /mission_queue.
    """
    if not is_transient_mir_error(exc):
        return False
    method_upper = method.upper()
    if method_upper in _IDEMPOTENT_HTTP_METHODS:
        return True
    if not transport_error:
        return False
    # Ambiguous: read timeout on POST might mean the mission was accepted.
    text = str(exc).casefold()
    if "read timed out" in text or "read timeout" in text:
        return False
    return True


def is_charge_action_name(name: str) -> bool:
    """True for the dock/charge mission (name matches 'charge', case-insensitive)."""
    return name.casefold().strip() == "charge"


def is_charging_started(status: dict[str, Any]) -> bool:
    """
    True when the robot is actually on the charger / charging — not still
    approaching or mid-dock-maneuver.

    Important: do NOT treat Docking (9) or \"Moving to 'Charger'\" as started;
    sending the next draft item then aborts Charge and causes an undock.
    """
    state_id = status.get("state_id")
    # Docked on charger. (Docking=9 is still in progress — keep waiting.)
    if state_id == DOCKED_STATE_ID:
        return True

    text = (status.get("mission_text") or "").strip().casefold()
    if not text:
        return False

    # e.g. "Charging... Waiting for new mission..."
    if text.startswith("charging"):
        return True
    if "charging..." in text or "charging …" in text:
        return True

    return False


def is_about_to_charge(status: dict[str, Any], queue_item: dict[str, Any] | None = None) -> bool:
    """
    True when a Charge mission is in progress but charging has not fully started
    (travel to Charger, docking, etc.).
    """
    if is_charging_started(status):
        return False

    state_id = status.get("state_id")
    if state_id == DOCKING_STATE_ID:
        return True

    text = (status.get("mission_text") or "").casefold()
    if "dock" in text:
        return True
    if "charg" in text and ("moving" in text or "go to" in text or "goto" in text):
        return True

    if queue_item and _queue_item_looks_like_charge(queue_item):
        state = str(queue_item.get("state") or "").casefold()
        if state in {"pending", "executing"}:
            return True

    return False


def _queue_item_looks_like_charge(queue_item: dict[str, Any]) -> bool:
    message = str(queue_item.get("message") or "").casefold()
    if is_charge_action_name(message.replace("runmission", "").strip()) or message.strip() in {
        "charge",
        "runmission charge",
    }:
        return True
    if "runmission charge" in message.replace(" ", ""):
        return True
    # message is often "RunMission Charge"
    parts = message.replace(":", " ").split()
    return any(is_charge_action_name(part) for part in parts)


def charge_prompt_kind(
    status: dict[str, Any],
    *,
    queue_item: dict[str, Any] | None = None,
    preserving_charge: bool = False,
    runner_label: str = "",
) -> str | None:
    """
    Return \"charging\", \"about_to_charge\", or None for interrupt prompts.
    """
    if is_charging_started(status) or preserving_charge:
        return "charging"
    if runner_label and is_charge_action_name(runner_label):
        return "about_to_charge"
    if is_about_to_charge(status, queue_item):
        return "about_to_charge"
    return None


def _pick_named(
    name: str,
    items: list[NamedItem],
    *,
    label: str,
    map_id: str | None = None,
) -> NamedItem:
    wanted = name.casefold().strip()
    matches = [item for item in items if item.name.casefold() == wanted]
    if map_id:
        on_map = [item for item in matches if item.extra.get("map_id") == map_id]
        if len(on_map) == 1:
            return on_map[0]
        if on_map:
            matches = on_map
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        listed = ", ".join(f"{item.name} ({item.guid[:8]}…)" for item in matches)
        raise MirError(f"Multiple {label}s named '{name}': {listed}")
    available = ", ".join(item.name for item in items[:12]) or "(none)"
    raise MirError(f"No {label} named '{name}'. Available: {available}")


def _error_text(response: requests.Response) -> str:
    payload = _safe_json(response)
    if isinstance(payload, dict):
        for key in ("error_human", "error_code", "error", "message"):
            if payload.get(key):
                return str(payload[key])
    text = (response.text or "").strip()
    return text[:400] if text else response.reason


def _safe_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text
