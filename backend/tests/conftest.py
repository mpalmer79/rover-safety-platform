"""Shared test fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure ``app`` is importable when tests are invoked from the
# repository root (e.g. ``pytest backend/tests``) without a prior
# ``pip install``.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


import pytest

from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.time import ManualClock


@pytest.fixture
def manual_clock() -> ManualClock:
    return ManualClock()


@pytest.fixture
def id_generator() -> SequentialIdGenerator:
    return SequentialIdGenerator()


@pytest.fixture
def run_id() -> RunId:
    return RunId("run-test-0001")


@pytest.fixture
def scenario_id() -> ScenarioId:
    return ScenarioId("scenario-test-0001")
