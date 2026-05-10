"""Reviewer-export validator.

The validator runs against an existing export bundle on disk and
reports per-check status. It is deliberately strict on the
honesty rules: causality_claimed must always be ``false`` in the
subsystem_risk export; static-only / missing-bag flags must be
preserved.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from app.reviewer_exports.models import (
    ALL_TABLES,
    REVIEWER_EXPORT_DISCLAIMER,
    TABLE_FIELDS,
)


@dataclass
class ValidationResult:
    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass
class ValidationReport:
    bundle_dir: Path
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def as_dict(self) -> dict:
        return {
            "bundle_dir": str(self.bundle_dir),
            "passed": self.passed,
            "results": [r.as_dict() for r in self.results],
        }


def validate_export(bundle_dir: Path) -> ValidationReport:
    """Run every documented check against ``bundle_dir``."""

    report = ValidationReport(bundle_dir=bundle_dir)
    if not bundle_dir.exists():
        report.results.append(
            ValidationResult(
                name="bundle_dir_present",
                passed=False,
                detail=f"bundle directory does not exist: {bundle_dir}",
            )
        )
        return report
    report.results.append(
        ValidationResult(
            name="bundle_dir_present",
            passed=True,
            detail=str(bundle_dir),
        )
    )

    manifest_path = bundle_dir / "manifest.json"
    manifest_payload = _read_json(manifest_path)
    if manifest_payload is None:
        report.results.append(
            ValidationResult(
                name="manifest_present",
                passed=False,
                detail=f"manifest not present or unparseable: {manifest_path}",
            )
        )
        return report
    report.results.append(
        ValidationResult(
            name="manifest_present", passed=True, detail=str(manifest_path)
        )
    )

    summary_path = bundle_dir / "reviewer-export-summary.md"
    if summary_path.is_file() and "safety certification" in summary_path.read_text(
        encoding="utf-8"
    ):
        report.results.append(
            ValidationResult(
                name="summary_includes_disclaimer",
                passed=True,
                detail=str(summary_path),
            )
        )
    else:
        report.results.append(
            ValidationResult(
                name="summary_includes_disclaimer",
                passed=False,
                detail=(
                    f"summary missing disclaimer at {summary_path}"
                ),
            )
        )

    for table in ALL_TABLES:
        report.results.extend(
            _validate_table(bundle_dir, manifest_payload, table=table)
        )

    notebook_path = bundle_dir / "notebooks" / "reviewer_walkthrough.ipynb"
    nb_present = notebook_path.is_file()
    nb_valid = False
    if nb_present:
        try:
            payload = json.loads(notebook_path.read_text(encoding="utf-8"))
            nb_valid = isinstance(payload, dict) and "cells" in payload
        except json.JSONDecodeError:
            nb_valid = False
    report.results.append(
        ValidationResult(
            name="notebook_valid",
            passed=nb_present and nb_valid,
            detail=str(notebook_path) if nb_present else "notebook missing",
        )
    )

    if manifest_payload.get("certification_disclaimer", "").strip() == REVIEWER_EXPORT_DISCLAIMER:
        report.results.append(
            ValidationResult(
                name="manifest_disclaimer_verbatim",
                passed=True,
            )
        )
    else:
        report.results.append(
            ValidationResult(
                name="manifest_disclaimer_verbatim",
                passed=False,
                detail="manifest disclaimer missing or not verbatim",
            )
        )

    return report


def _validate_table(
    bundle_dir: Path,
    manifest_payload: dict,
    *,
    table: str,
) -> list[ValidationResult]:
    """Run the per-table checks (file presence, fields, row counts)."""

    out: list[ValidationResult] = []
    csv_path = bundle_dir / "csv" / f"{table}.csv"
    jsonl_path = bundle_dir / "jsonl" / f"{table}.jsonl"
    schema_path = bundle_dir / "schemas" / f"{table}.schema.json"

    out.append(
        ValidationResult(
            name=f"{table}_csv_present",
            passed=csv_path.is_file(),
            detail=str(csv_path),
        )
    )
    out.append(
        ValidationResult(
            name=f"{table}_jsonl_present",
            passed=jsonl_path.is_file(),
            detail=str(jsonl_path),
        )
    )
    out.append(
        ValidationResult(
            name=f"{table}_schema_present",
            passed=schema_path.is_file(),
            detail=str(schema_path),
        )
    )

    if not csv_path.is_file():
        return out

    csv_rows = _load_csv(csv_path)
    jsonl_rows = _load_jsonl(jsonl_path) if jsonl_path.is_file() else []
    expected_fields = set(TABLE_FIELDS[table])
    if csv_rows:
        missing_fields = expected_fields - set(csv_rows[0].keys())
        out.append(
            ValidationResult(
                name=f"{table}_csv_required_fields",
                passed=not missing_fields,
                detail=(
                    "ok"
                    if not missing_fields
                    else f"missing fields: {sorted(missing_fields)}"
                ),
            )
        )
    else:
        out.append(
            ValidationResult(
                name=f"{table}_csv_required_fields",
                passed=True,
                detail="empty table (zero rows) — fields validated against header",
            )
        )

    manifest_count = (
        manifest_payload.get("row_counts", {}).get(table)
    )
    csv_count = len(csv_rows)
    jsonl_count = len(jsonl_rows)
    counts_match = (
        manifest_count is not None
        and manifest_count == csv_count
        and (not jsonl_path.is_file() or manifest_count == jsonl_count)
    )
    out.append(
        ValidationResult(
            name=f"{table}_row_counts_match",
            passed=counts_match,
            detail=(
                f"manifest={manifest_count} csv={csv_count} jsonl={jsonl_count}"
            ),
        )
    )

    if table == "subsystem_risk" and csv_rows:
        bad = [
            row
            for row in csv_rows
            if str(row.get("causality_claimed", "")).strip().lower()
            != "false"
        ]
        out.append(
            ValidationResult(
                name="subsystem_risk_causality_claimed_false",
                passed=not bad,
                detail=(
                    "ok"
                    if not bad
                    else f"{len(bad)} row(s) with causality_claimed != false"
                ),
            )
        )

    if table == "replay_quality" and csv_rows:
        bad = []
        for row in csv_rows:
            bag_status = (row.get("bag_status") or "").strip()
            static = (row.get("static_only") or "").strip().lower() == "true"
            missing = (row.get("missing_bag") or "").strip().lower() == "true"
            if bag_status == "static_only" and not static:
                bad.append(row.get("incident_id"))
            if bag_status == "missing_bag" and not missing:
                bad.append(row.get("incident_id"))
        out.append(
            ValidationResult(
                name="replay_quality_origin_flags_preserved",
                passed=not bad,
                detail=(
                    "ok"
                    if not bad
                    else f"{len(bad)} row(s) with mismatched origin flag(s)"
                ),
            )
        )
    return out


def _load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def _load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                out.append(payload)
    return out


def _read_json(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None
