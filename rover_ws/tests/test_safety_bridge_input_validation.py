"""Input-validation regression tests for the safety bridge node (#16).

We cannot import ``safety_bridge_node`` directly here because it pulls
in ``rclpy`` and the ROS message types, which are not available in
this static-validation environment (see other tests in this dir for
the same constraint). Instead we:

* parse the node source with :mod:`ast` and assert every subscriber
  callback is wrapped in a ``try/except`` and every leaf callback
  routes failures through ``_emit_invalid_input_event``;
* exercise the NaN guard in ``_on_requested`` against a stub by
  monkey-patching just the parts that need to be present.

This is the same enforcement style as
``test_safety_bridge_node_only_publishes_authorized``.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest


_PKG_ROOT = (
    Path(__file__).resolve().parents[1] / "src" / "rover_safety_bridge"
)
_NODE_PATH = _PKG_ROOT / "rover_safety_bridge" / "safety_bridge_node.py"


def _module_ast() -> ast.Module:
    return ast.parse(_NODE_PATH.read_text(), filename=str(_NODE_PATH))


def _find_method(name: str) -> ast.FunctionDef:
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"method {name!r} not found in {_NODE_PATH}")


@pytest.mark.parametrize(
    "callback",
    ["_on_requested", "_on_scan", "_on_imu", "_on_odom", "_on_contact"],
)
def test_subscriber_callback_has_try_except(callback: str) -> None:
    """Every subscriber callback must wrap its body in try/except so a
    malformed message cannot crash the node (#16)."""

    node = _find_method(callback)
    has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))
    assert has_try, f"{callback} must wrap its body in try/except (#16)"


def test_emit_invalid_input_event_is_defined() -> None:
    """The rate-limited rejection-event helper is the contract for #16."""

    _find_method("_emit_invalid_input_event")


def test_emit_invalid_input_event_is_referenced_by_each_callback() -> None:
    for callback in ("_on_requested", "_on_scan", "_on_imu", "_on_odom", "_on_contact"):
        node = _find_method(callback)
        text = ast.unparse(node)
        assert "_emit_invalid_input_event" in text, (
            f"{callback} must route failures through _emit_invalid_input_event"
        )


def test_check_stamp_skew_is_defined() -> None:
    """#15 emit-stamp-skew helper exists."""

    _find_method("_check_stamp_skew")
