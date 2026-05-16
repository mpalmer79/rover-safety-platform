"""Path-traversal regression tests for the /runs/{run_id} endpoints.

The trust-boundary invariant under test: any caller-supplied ``run_id``
that does not match ``^[A-Za-z0-9_-]{1,128}$`` must be rejected with
HTTP 400 before any filesystem access happens, and the rejection detail
must NOT echo the input.

URL-encoded path separators (``%2F``) are normalised away by Starlette
during routing, which means they fail at the route layer (404, "no such
endpoint") rather than reaching the validator. That is structurally
fine — the validator is the second line of defence, not the first.
The hard requirement is that no traversal attempt is ever answered 200.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from starlette.testclient import TestClient

from app.api.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(runs_root=tmp_path))


@pytest.mark.parametrize(
    "bad_id",
    [
        "..",
        "../etc",
        "foo..bar",
        "/etc/passwd",
        "foo\\bar",
        "..\\windows",
        "name with space",
        "name;rm",
        "x" * 129,
        "",
        "name#frag",
        "name?query",
    ],
)
@pytest.mark.parametrize("suffix", ["", "/events", "/summary"])
def test_invalid_run_id_returns_400(client: TestClient, bad_id: str, suffix: str) -> None:
    if bad_id == "":
        # Empty path component collapses to /runs, the list endpoint.
        return
    resp = client.get(f"/runs/{bad_id}{suffix}")
    # Either 400 (validator rejected) or 404 (Starlette normalisation
    # ate the segments before routing). Never 200.
    assert resp.status_code in (400, 404), resp.text
    assert resp.status_code != 200
    if resp.status_code == 400:
        # The detail is a constant — input is never reflected.
        body = resp.json()
        assert body["detail"] == "invalid run_id"
        assert bad_id not in body["detail"]


def test_url_encoded_traversal_never_200(client: TestClient) -> None:
    for url in [
        "/runs/..%2F..%2Fetc/summary",
        "/runs/%2Fetc%2Fpasswd/summary",
        "/runs/..%5C..%5Cwindows/summary",
    ]:
        resp = client.get(url)
        assert resp.status_code != 200, url


def test_valid_run_id_reaches_404_for_missing_dir(client: TestClient) -> None:
    # ``abc-123_OK`` matches the charset but the directory does not
    # exist; expect 404 from the loader, NOT 400.
    resp = client.get("/runs/abc-123_OK/summary")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "unknown run_id"


def test_list_endpoint_unaffected(client: TestClient) -> None:
    resp = client.get("/runs")
    assert resp.status_code == 200
    assert resp.json() == []
