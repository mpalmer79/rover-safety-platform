"""Tests for the ``/simulation/run`` route's response shape.

The trust-boundary invariant: the response must not contain absolute
filesystem paths. The caller addresses runs by ``run_id``; server-side
paths are an implementation detail of the runner.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from starlette.testclient import TestClient

from app.api.main import create_app


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(runs_root=tmp_path))


def _payload() -> dict:
    return {
        "scenario_id": "scenario-route-test",
        "duration_seconds": 0.5,
        "time_step_ms": 100,
    }


def test_response_omits_run_dir(tmp_path: Path) -> None:
    resp = _client(tmp_path).post("/simulation/run", json=_payload())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "run_dir" not in body
    for value in body.values():
        if isinstance(value, str):
            assert not value.startswith("/"), f"absolute path leaked: {value!r}"
            assert str(tmp_path) not in value


def test_invalid_payload_returns_generic_400(tmp_path: Path) -> None:
    resp = _client(tmp_path).post(
        "/simulation/run",
        json={"scenario_id": "s", "duration_seconds": -1},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "invalid scenario payload"


def test_oversized_duration_returns_generic_400(tmp_path: Path) -> None:
    resp = _client(tmp_path).post(
        "/simulation/run",
        json={"scenario_id": "s", "duration_seconds": 999999},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "invalid scenario payload"


def test_missing_scenario_id_returns_generic_400(tmp_path: Path) -> None:
    resp = _client(tmp_path).post(
        "/simulation/run",
        json={"duration_seconds": 1.0},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "invalid scenario payload"
