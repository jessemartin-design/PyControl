"""Tests for MirClient HTTP retry / timeout helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import requests

from mir.client import MirClient, MirError, should_retry_mir_request


class RetryPolicyTests(unittest.TestCase):
    def test_connect_timeout_retries_post(self) -> None:
        exc = MirError(
            "POST /mission_queue failed: ConnectTimeoutError(connect timeout=15)"
        )
        self.assertTrue(should_retry_mir_request("POST", exc, transport_error=True))

    def test_read_timeout_does_not_retry_post(self) -> None:
        exc = MirError("POST /mission_queue failed: Read timed out. (read timeout=60.0)")
        self.assertFalse(should_retry_mir_request("POST", exc, transport_error=True))

    def test_read_timeout_retries_get(self) -> None:
        exc = MirError("GET /status failed: Read timed out. (read timeout=60.0)")
        self.assertTrue(should_retry_mir_request("GET", exc, transport_error=True))

    def test_http_503_retries_get_not_post(self) -> None:
        exc = MirError("GET /status returned 503: unavailable", status_code=503)
        self.assertTrue(should_retry_mir_request("GET", exc, transport_error=False))
        self.assertFalse(
            should_retry_mir_request(
                "POST",
                MirError("POST /mission_queue returned 503: unavailable", status_code=503),
                transport_error=False,
            )
        )


class RequestRetryTests(unittest.TestCase):
    def test_retries_then_succeeds_on_connect_timeout(self) -> None:
        client = MirClient(
            "10.14.19.160",
            "u",
            "p",
            base_url="http://10.14.19.160/api/v2.0.0",
            http_retries=2,
            http_retry_backoff=0.0,
        )
        ok = MagicMock()
        ok.status_code = 200
        ok.content = b'{"state_id": 3}'
        ok.headers = {}
        ok.json = MagicMock(return_value={"state_id": 3})

        with patch.object(
            client.session,
            "request",
            side_effect=[
                requests.exceptions.ConnectTimeout("connect timed out"),
                ok,
            ],
        ) as mocked:
            data = client.request("GET", "/status")
        self.assertEqual(data, {"state_id": 3})
        self.assertEqual(mocked.call_count, 2)

    def test_retries_disabled(self) -> None:
        client = MirClient(
            "10.14.19.160",
            "u",
            "p",
            base_url="http://10.14.19.160/api/v2.0.0",
            http_retries=0,
            http_retry_backoff=0.0,
        )
        with patch.object(
            client.session,
            "request",
            side_effect=requests.exceptions.ConnectTimeout("connect timed out"),
        ) as mocked:
            with self.assertRaises(MirError):
                client.request("GET", "/status")
        self.assertEqual(mocked.call_count, 1)


if __name__ == "__main__":
    unittest.main()
