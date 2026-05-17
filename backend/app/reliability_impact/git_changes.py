"""Git change inventory for impact analysis.

Supports three modes:

1. ``--changed-files`` — an explicit newline / comma-separated list
   of paths provided by the caller (CI typically wires this from
   ``GITHUB_BASE_REF`` + ``git diff``).
2. ``--base-ref / --head-ref`` — run ``git diff --name-status``
   between two refs.
3. fallback: ``git status --porcelain`` against the working tree.

Network access is never required. If git is unavailable, the
inventory falls back to whatever input was supplied and records a
warning. The caller decides how to surface that.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable, Optional

from app.reliability_impact.models import (
    ChangedFile,
    ChangeType,
    SourceChange,
    Subsystem,
)
from app.reliability_impact.subsystem_classifier import classify_path


_GIT_STATUS_MAP: dict[str, ChangeType] = {
    "A": ChangeType.ADDED,
    "M": ChangeType.MODIFIED,
    "D": ChangeType.DELETED,
    "R": ChangeType.RENAMED,
    "C": ChangeType.RENAMED,
    "T": ChangeType.MODIFIED,
    "?": ChangeType.UNKNOWN,
    " ": ChangeType.MODIFIED,
}


def collect_source_change(
    *,
    base_ref: Optional[str] = None,
    head_ref: Optional[str] = None,
    changed_files: Optional[Iterable[str]] = None,
    repo_root: Optional[Path] = None,
    fixture_mode: bool = False,
) -> SourceChange:
    """Return a :class:`SourceChange` for the requested mode.

    Resolution order:

    * explicit ``changed_files`` always wins;
    * else ``base_ref + head_ref`` triggers ``git diff``;
    * else fall back to ``git status --porcelain`` (working tree).
    """

    repo_root = repo_root or Path.cwd()
    warnings: list[str] = []

    if changed_files is not None:
        files = _parse_explicit_list(changed_files)
        return SourceChange(
            base_ref=base_ref or "",
            head_ref=head_ref or "",
            source="fixture" if fixture_mode else "explicit_list",
            changed_files=tuple(files),
            warnings=tuple(warnings),
        )

    if base_ref and head_ref:
        files, w = _git_diff(base_ref, head_ref, repo_root=repo_root)
        warnings.extend(w)
        return SourceChange(
            base_ref=base_ref,
            head_ref=head_ref,
            source="git_diff",
            changed_files=tuple(files),
            warnings=tuple(warnings),
        )

    # Working-tree fallback.
    files, w = _git_status(repo_root=repo_root)
    warnings.extend(w)
    return SourceChange(
        base_ref=base_ref or "",
        head_ref=head_ref or "",
        source="working_tree",
        changed_files=tuple(files),
        warnings=tuple(warnings),
    )


def _parse_explicit_list(value: Iterable[str]) -> list[ChangedFile]:
    """Accept iterable of strings, comma-separated, or newline-separated."""

    out: list[ChangedFile] = []
    seen: set[str] = set()
    flattened: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        for piece in item.replace(",", "\n").splitlines():
            piece = piece.strip()
            if not piece:
                continue
            flattened.append(piece)
    for path in flattened:
        # Accept either ``A path`` or just ``path`` rows.
        change_type = ChangeType.MODIFIED
        if len(path) > 2 and path[1] in {" ", "\t"} and path[0].upper() in _GIT_STATUS_MAP:
            change_type = _GIT_STATUS_MAP.get(path[0].upper(), ChangeType.MODIFIED)
            path = path[2:].strip()
        if path in seen:
            continue
        seen.add(path)
        subsystem = classify_path(path)
        out.append(
            ChangedFile(path=path, change_type=change_type, subsystem=subsystem)
        )
    return out


def _git_diff(
    base_ref: str, head_ref: str, *, repo_root: Path
) -> tuple[list[ChangedFile], list[str]]:
    cmd = [
        "git",
        "-C",
        str(repo_root),
        "diff",
        "--name-status",
        f"{base_ref}...{head_ref}",
    ]
    rc, out = _run(cmd)
    if rc != 0:
        return [], [f"git diff failed (rc={rc}): {out.strip().splitlines()[:1]}"]
    files: list[ChangedFile] = []
    for line in out.splitlines():
        parsed = _parse_git_status_line(line)
        if parsed is not None:
            files.append(parsed)
    return files, []


def _git_status(*, repo_root: Path) -> tuple[list[ChangedFile], list[str]]:
    cmd = ["git", "-C", str(repo_root), "status", "--porcelain"]
    rc, out = _run(cmd)
    if rc != 0:
        return [], [f"git status failed (rc={rc})"]
    files: list[ChangedFile] = []
    for line in out.splitlines():
        if len(line) < 3:
            continue
        flag = line[0]
        path = line[3:].strip()
        # Handle renames: "R  old -> new"
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        change_type = _GIT_STATUS_MAP.get(flag.upper(), ChangeType.MODIFIED)
        files.append(
            ChangedFile(
                path=path,
                change_type=change_type,
                subsystem=classify_path(path),
            )
        )
    return files, []


def _parse_git_status_line(line: str) -> Optional[ChangedFile]:
    line = line.strip()
    if not line:
        return None
    parts = line.split(None, 1)
    if len(parts) != 2:
        return None
    flag, rest = parts
    code = flag[0].upper()
    change_type = _GIT_STATUS_MAP.get(code, ChangeType.MODIFIED)
    # Renames look like ``R100\told_path\tnew_path``; we prefer the new path.
    if "\t" in rest:
        pieces = rest.split("\t")
        path = pieces[-1]
    else:
        path = rest
    path = path.strip()
    if not path:
        return None
    return ChangedFile(
        path=path, change_type=change_type, subsystem=classify_path(path)
    )


def _run(cmd: list[str], *, timeout: float = 20.0) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (
            completed.returncode,
            (completed.stdout or "") + (completed.stderr or ""),
        )
    except FileNotFoundError:
        return (127, "git binary not found")
    except (subprocess.TimeoutExpired, OSError) as exc:  # pragma: no cover
        return (255, f"subprocess error: {exc}")


def collect_from_ci_env(*, repo_root: Optional[Path] = None) -> SourceChange:
    """Convenience: pick up base / head refs from GitHub env vars."""

    base = os.environ.get("GITHUB_BASE_REF", "")
    head = os.environ.get("GITHUB_HEAD_REF", "") or os.environ.get(
        "GITHUB_SHA", ""
    )
    if base and head:
        change = collect_source_change(
            base_ref=base, head_ref=f"origin/{head}" if not head.startswith("origin/") else head,
            repo_root=repo_root,
        )
        # Re-tag the source so the reporter can show it was CI-driven.
        return SourceChange(
            base_ref=change.base_ref,
            head_ref=change.head_ref,
            source="ci_env",
            changed_files=change.changed_files,
            warnings=change.warnings,
        )
    return collect_source_change(repo_root=repo_root)
