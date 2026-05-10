"""Programme-review dashboard payload.

Produces a compact JSON document suitable for a static reviewer
page. The dashboard is metadata only; the layer never invents
trend continuity or causal narrative.
"""

from __future__ import annotations

from app.programme_review.models import (
    PROGRAMME_CERTIFICATION_DISCLAIMER,
    ProgrammeReview,
)


def build_dashboard(review: ProgrammeReview) -> dict:
    """Compose the dashboard payload."""

    return {
        "generated_at_utc": review.generated_at_utc,
        "fixture_mode": review.fixture_mode,
        "history_counts": dict(review.history_counts),
        "overall_health": review.governance_health.overall.value,
        "disciplines": [
            {
                "category": d.category.value,
                "rating": d.rating.value,
                "reasons": list(d.reasons),
            }
            for d in review.governance_health.disciplines
        ],
        "drift": {
            "severity": review.drift_report.severity.value,
            "summary_counts": review.drift_report.summary_counts(),
            "findings": [
                {
                    "label": f.label,
                    "severity": f.severity.value,
                    "detail": f.detail,
                }
                for f in review.drift_report.findings
            ],
        },
        "trends": [
            {
                "label": s.label,
                "category": s.category.value,
                "rolling_3": s.rolling_3.value,
                "rolling_5": s.rolling_5.value,
                "window_size": s.window_size,
            }
            for s in review.trend_report.series
        ],
        "subsystem_risk": [
            {
                "subsystem": r.subsystem,
                "frequency": r.frequency,
                "repeat_regressions": r.repeat_regression_count,
                "gate_failures": r.gate_failure_count,
                "warnings": r.unresolved_warning_count,
                "severity_distribution": dict(r.severity_distribution),
            }
            for r in review.subsystem_risk_report.rows
        ],
        "coverage_evolution": {
            "origin_mix": review.coverage_evolution.origin_mix_label,
            "origin_distribution": review.coverage_evolution.origin_distribution(),
            "bag_status_distribution": review.coverage_evolution.bag_status_distribution(),
        },
        "gate": {
            "volatility": review.gate_history.volatility.value,
            "pass_count": review.gate_history.pass_count,
            "warning_count": review.gate_history.warning_count,
            "failure_count": review.gate_history.failure_count,
            "not_executed_count": review.gate_history.not_executed_count,
            "last_status": review.gate_history.last_status,
        },
        "freshness": {
            "reference_time_utc": review.freshness_report.reference_time_utc,
            "counts": review.freshness_report.status_counts(),
        },
        "warnings": list(review.warnings),
        "known_limitations": list(review.known_limitations),
        "disclaimer": PROGRAMME_CERTIFICATION_DISCLAIMER,
    }
