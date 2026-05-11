"""Thin filesystem reporter for proposal audits.

Distinguishes "build the audit object" (audit.py) from "write it to
disk" (this module) so CLIs and tests can call either side without
the other.
"""

from __future__ import annotations

from pathlib import Path

from .audit import build_audit, write_audit_bundle
from .adapter import AdapterResult
from .models import ProposalAudit


def write_audit_files(
    adapter_result: AdapterResult,
    bundle_dir: Path,
    *,
    generated_at_utc: str,
) -> tuple[ProposalAudit, dict]:
    """Build and write the audit bundle.

    Returns the (audit, paths_written) pair so the caller can log
    the artefacts produced without re-reading from disk.
    """

    audit = build_audit(adapter_result, generated_at_utc=generated_at_utc)
    paths = write_audit_bundle(audit, bundle_dir)
    return audit, paths
