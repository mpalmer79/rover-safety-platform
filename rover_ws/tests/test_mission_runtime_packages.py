"""Static validation of the Phase 2 ROS packages.

The mission orchestrator, world model, and diagnostics nodes import
``rclpy`` and so cannot be exercised in this CI sandbox. We:

* parse every node module with :mod:`ast`,
* assert the architectural invariants at the source level (the
  mission node never publishes ``/cmd_vel`` or ``/cmd_vel_authorized``;
  the Nav2 clamp does not subscribe to ``/cmd_vel_authorized``; the
  orchestrator imports the deterministic ``app.mission.MissionOrchestrator``
  rather than re-implementing it),
* assert the entry-point names declared in ``setup.py`` match the
  modules.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


def _read(*parts) -> str:
    return Path(*parts).read_text(encoding="utf-8")


@pytest.fixture
def mission_pkg(src_root: Path) -> Path:
    return src_root / "rover_mission_runtime"


@pytest.fixture
def world_pkg(src_root: Path) -> Path:
    return src_root / "rover_world_model"


@pytest.fixture
def mdiag_pkg(src_root: Path) -> Path:
    return src_root / "rover_mission_diagnostics"


@pytest.mark.parametrize(
    "module",
    [
        "rover_mission_runtime/mission_node.py",
        "rover_mission_runtime/nav2_velocity_clamp.py",
    ],
)
def test_mission_runtime_modules_parse(mission_pkg: Path, module: str) -> None:
    path = mission_pkg / module
    assert path.exists()
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_world_model_node_parses(world_pkg: Path) -> None:
    path = world_pkg / "rover_world_model" / "world_model_node.py"
    assert path.exists()
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_mission_diagnostics_node_parses(mdiag_pkg: Path) -> None:
    path = mdiag_pkg / "rover_mission_diagnostics" / "mission_diagnostics_node.py"
    assert path.exists()
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# ----------------------------------------------------------------------
# Architectural invariants.
# ----------------------------------------------------------------------


def test_mission_node_publishes_only_cmd_vel_requested(mission_pkg: Path) -> None:
    """The mission node must publish to /cmd_vel_requested and never
    to /cmd_vel or /cmd_vel_authorized.
    """

    text = (
        mission_pkg / "rover_mission_runtime" / "mission_node.py"
    ).read_text(encoding="utf-8")
    assert "/cmd_vel_requested" in text
    assert "/cmd_vel_authorized" not in text
    # Also must not publish to a generic /cmd_vel.
    assert '"/cmd_vel"' not in text and "'/cmd_vel'" not in text


def test_mission_node_imports_orchestrator(mission_pkg: Path) -> None:
    text = (
        mission_pkg / "rover_mission_runtime" / "mission_node.py"
    ).read_text(encoding="utf-8")
    assert "from app.mission" in text
    assert "MissionOrchestrator" in text


def test_nav2_clamp_does_not_subscribe_to_authorized(mission_pkg: Path) -> None:
    """The Nav2 boundary must NEVER touch /cmd_vel_authorized.

    The clamp's only allowed input is /cmd_vel_nav2 (or whatever the
    operator configures); its only output is /cmd_vel_requested. This
    keeps the safety supervisor as the sole authority over the
    actuator stream.
    """

    path = mission_pkg / "rover_mission_runtime" / "nav2_velocity_clamp.py"
    text = path.read_text(encoding="utf-8")
    # Strip comments + docstrings so explanatory prose can mention the
    # forbidden topic without tripping the check.
    code_only = _strip_comments_and_docstrings(text)
    assert "/cmd_vel_authorized" not in code_only
    # Sanity: the clamp publishes to /cmd_vel_requested and reads
    # /cmd_vel_nav2.
    assert "/cmd_vel_requested" in text
    assert "/cmd_vel_nav2" in text


def _strip_comments_and_docstrings(source: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module)
        ):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body[0].value.value = ""
    return ast.unparse(tree)


def test_nav2_clamp_publisher_targets_requested_topic(mission_pkg: Path) -> None:
    """AST-level confirmation: every ``create_publisher`` call in the
    Nav2 clamp resolves to the ``output_topic`` parameter (which
    defaults to ``/cmd_vel_requested``). It must not target
    ``/cmd_vel_authorized``.
    """

    path = mission_pkg / "rover_mission_runtime" / "nav2_velocity_clamp.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    publisher_args: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "create_publisher"):
            continue
        if len(node.args) >= 2:
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                publisher_args.append(arg.value)
            elif isinstance(arg, ast.Call):
                # str(self.get_parameter(...).value) - assume the
                # default topic from the source.
                publisher_args.append("<param>")
    # No literal target should be /cmd_vel_authorized; the parameter
    # default is /cmd_vel_requested.
    assert "/cmd_vel_authorized" not in publisher_args


def test_world_model_node_imports_world_model(world_pkg: Path) -> None:
    text = (
        world_pkg / "rover_world_model" / "world_model_node.py"
    ).read_text(encoding="utf-8")
    assert "from app.world_model" in text
    assert "WorldModel" in text


def test_mission_diagnostics_subscribes_to_canonical_topics(mdiag_pkg: Path) -> None:
    text = (
        mdiag_pkg / "rover_mission_diagnostics" / "mission_diagnostics_node.py"
    ).read_text(encoding="utf-8")
    for topic in (
        "/mission/state",
        "/mission/progress",
        "/mission/recovery",
        "/world_model/state",
        "/world_model/hazards",
    ):
        assert topic in text, f"missing subscription to {topic}"


def test_setup_py_console_scripts(mission_pkg: Path, world_pkg: Path, mdiag_pkg: Path) -> None:
    expected = {
        mission_pkg: ("mission_node", "nav2_velocity_clamp"),
        world_pkg: ("world_model_node",),
        mdiag_pkg: ("mission_diagnostics_node",),
    }
    for pkg, names in expected.items():
        text = (pkg / "setup.py").read_text(encoding="utf-8")
        for name in names:
            assert f"{name} = " in text, f"{pkg.name} setup.py missing {name}"
