"""URDF / TF tree validator.

Parses ``rover.urdf.xacro`` and validates the resulting frame graph
without invoking xacro. Catches the classes of regression that turn
into runtime "TF_OLD_DATA" / "look up failed" failures:

* every joint references parent and child links that are declared,
* the link graph is a single connected tree,
* the documented frames are present (``base_link``, ``base_footprint``,
  ``lidar_link``, ``imu_link``, ``contact_link``, ``left_wheel_link``,
  ``right_wheel_link``, ``caster_link``).

The validator does not evaluate xacro macros, so wheel joints declared
inside a ``xacro:macro`` are recognised heuristically by scanning for
``${prefix}_wheel_link`` / ``${prefix}_wheel_joint`` patterns plus the
two macro invocations.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TfValidationResult:
    source: Path
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    joints: list[tuple[str, str, str, str]] = field(default_factory=list)
    """Each tuple is (joint_name, joint_type, parent_link, child_link)."""

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict:
        return {
            "source": str(self.source),
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "links": list(self.links),
            "joints": [list(j) for j in self.joints],
        }


_REQUIRED_LINKS: frozenset[str] = frozenset(
    {
        "base_footprint",
        "base_link",
        "lidar_link",
        "imu_link",
        "contact_link",
        "left_wheel_link",
        "right_wheel_link",
        "caster_link",
    }
)


def validate_urdf_tf_tree(path: Path | str) -> TfValidationResult:
    path = Path(path)
    result = TfValidationResult(source=path)
    if not path.exists():
        result.add_error(f"URDF / xacro file does not exist: {path}")
        return result

    try:
        tree = ET.parse(str(path))
    except ET.ParseError as exc:
        result.add_error(f"URDF did not parse: {exc}")
        return result
    root = tree.getroot()
    if root.tag != "robot":
        result.add_error(f"unexpected root element: {root.tag!r}")
        return result

    declared_links: set[str] = set()
    for link_el in root.findall("link"):
        name = link_el.get("name")
        if not name:
            result.add_error("link element with no name attribute")
            continue
        declared_links.add(name)
        result.links.append(name)

    declared_joints: list[tuple[str, str, str, str]] = []
    for joint_el in root.findall("joint"):
        name = joint_el.get("name") or "<unnamed>"
        jtype = joint_el.get("type") or "<missing>"
        parent_el = joint_el.find("parent")
        child_el = joint_el.find("child")
        parent = parent_el.get("link") if parent_el is not None else None
        child = child_el.get("link") if child_el is not None else None
        if not parent or not child:
            result.add_error(f"joint {name!r}: parent or child link missing")
            continue
        declared_joints.append((name, jtype, parent, child))
    result.joints = declared_joints

    # Macro-derived wheels: rover.urdf.xacro uses xacro:macro drive_wheel.
    text = path.read_text(encoding="utf-8")
    macro_invocations = re.findall(
        r'xacro:drive_wheel\s+prefix\s*=\s*"([^"]+)"',
        text,
    )
    declared_links_via_macro: set[str] = set()
    declared_joints_via_macro: list[tuple[str, str, str, str]] = []
    for prefix in macro_invocations:
        declared_links_via_macro.add(f"{prefix}_wheel_link")
        declared_joints_via_macro.append(
            (f"{prefix}_wheel_joint", "continuous", "base_link", f"{prefix}_wheel_link")
        )
    declared_links |= declared_links_via_macro
    declared_joints += declared_joints_via_macro
    result.links = sorted(declared_links)
    result.joints = list(declared_joints)

    # Required link presence.
    missing_required = sorted(_REQUIRED_LINKS - declared_links)
    for link in missing_required:
        result.add_error(f"required link missing: {link}")

    # Joint references must resolve.
    for joint_name, _, parent, child in declared_joints:
        if parent not in declared_links:
            result.add_error(
                f"joint {joint_name!r}: parent link {parent!r} not declared"
            )
        if child not in declared_links:
            result.add_error(
                f"joint {joint_name!r}: child link {child!r} not declared"
            )

    # Tree connectivity: every link except the root must appear as a
    # child exactly once. The root is base_footprint by convention.
    children = [c for _, _, _, c in declared_joints]
    repeated_children = [c for c in children if children.count(c) > 1]
    for child in sorted(set(repeated_children)):
        result.add_error(
            f"link {child!r} declared as child of more than one joint"
        )

    children_set = set(children)
    candidate_roots = sorted(declared_links - children_set)
    if not candidate_roots:
        result.add_error("URDF has no root link (every link is a child)")
    elif len(candidate_roots) > 1:
        result.add_warning(
            "URDF has multiple root candidates (forest, not a tree): "
            + ", ".join(candidate_roots)
        )
    else:
        if candidate_roots[0] != "base_footprint":
            result.add_warning(
                f"unexpected root link {candidate_roots[0]!r} (expected 'base_footprint')"
            )

    # All non-root links must be reachable from the root.
    if candidate_roots:
        root_link = candidate_roots[0]
        adjacency: dict[str, list[str]] = {l: [] for l in declared_links}
        for _, _, p, c in declared_joints:
            if p in adjacency:
                adjacency[p].append(c)
        reachable: set[str] = set()
        stack = [root_link]
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            stack.extend(adjacency.get(current, []))
        unreachable = sorted(declared_links - reachable)
        for link in unreachable:
            result.add_error(f"link {link!r} not reachable from root {root_link!r}")

    return result
