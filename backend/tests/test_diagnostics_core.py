"""Unit tests for the pure-logic diagnostics core."""

from __future__ import annotations

import pytest

from app.diagnostics import (
    BridgeHealthMonitor,
    DEFAULT_TOPIC_SPECS,
    HealthSeverity,
    TopicFreshnessMonitor,
    TopicSpec,
    aggregate_health,
)
from app.diagnostics.runtime_summary import HealthReport


def test_default_specs_include_canonical_topics() -> None:
    names = {s.name for s in DEFAULT_TOPIC_SPECS}
    for required in (
        "/clock",
        "/scan",
        "/imu",
        "/odom",
        "/cmd_vel_authorized",
        "/safety/state",
    ):
        assert required in names


def test_topic_spec_validates_thresholds() -> None:
    with pytest.raises(ValueError):
        TopicSpec(name="/x", expected_period_ms=0, warn_age_ms=10, error_age_ms=20)
    with pytest.raises(ValueError):
        TopicSpec(name="/x", expected_period_ms=10, warn_age_ms=5, error_age_ms=20)
    with pytest.raises(ValueError):
        TopicSpec(name="/x", expected_period_ms=10, warn_age_ms=20, error_age_ms=15)


def test_warmup_window_suppresses_initial_missing_topic() -> None:
    monitor = TopicFreshnessMonitor(
        specs=(TopicSpec(name="/scan", expected_period_ms=100, warn_age_ms=250, error_age_ms=750),)
    )
    monitor.declare(now_ms=1000)
    # Within the warmup window (warn_age_ms=250), missing topic is OK.
    report = monitor.report(now_ms=1100)
    assert report.severity == HealthSeverity.OK
    assert "warmup" in (report.per_topic[0].attributes or {})


def test_missing_topic_after_warmup_is_error() -> None:
    monitor = TopicFreshnessMonitor(
        specs=(TopicSpec(name="/scan", expected_period_ms=100, warn_age_ms=250, error_age_ms=750),)
    )
    monitor.declare(now_ms=0)
    report = monitor.report(now_ms=10_000)
    assert report.severity == HealthSeverity.ERROR


def test_observed_topic_starts_fresh_then_goes_warn_then_error() -> None:
    monitor = TopicFreshnessMonitor(
        specs=(TopicSpec(name="/scan", expected_period_ms=100, warn_age_ms=250, error_age_ms=750),)
    )
    monitor.declare(now_ms=0)
    monitor.observe(topic="/scan", now_ms=100)
    fresh = monitor.report(now_ms=200)
    assert fresh.severity == HealthSeverity.OK
    warn = monitor.report(now_ms=400)  # 300ms since last observation
    assert warn.severity == HealthSeverity.WARN
    err = monitor.report(now_ms=1100)  # 1000ms since last observation
    assert err.severity == HealthSeverity.ERROR


def test_optional_topic_missing_is_warning() -> None:
    monitor = TopicFreshnessMonitor(
        specs=(
            TopicSpec(
                name="/safety/events",
                expected_period_ms=1000,
                warn_age_ms=5000,
                error_age_ms=15000,
                required=False,
            ),
        )
    )
    monitor.declare(now_ms=0)
    report = monitor.report(now_ms=20_000)
    assert report.severity == HealthSeverity.WARN


def test_aggregate_picks_worst_severity() -> None:
    reports = [
        HealthReport(component="a", severity=HealthSeverity.OK, summary=""),
        HealthReport(component="b", severity=HealthSeverity.WARN, summary=""),
        HealthReport(component="c", severity=HealthSeverity.ERROR, summary=""),
    ]
    summary = aggregate_health(reports)
    assert summary.severity == HealthSeverity.ERROR
    assert len(summary.reports) == 3


def test_aggregate_empty_is_ok() -> None:
    summary = aggregate_health([])
    assert summary.severity == HealthSeverity.OK
    assert summary.reports == ()


def test_bridge_monitor_advertised_topic_inherits_freshness() -> None:
    fresh = TopicFreshnessMonitor(specs=DEFAULT_TOPIC_SPECS)
    fresh.declare(now_ms=0)
    fresh.observe(topic="/scan", now_ms=100)
    fresh.observe(topic="/imu", now_ms=100)
    fresh.observe(topic="/odom", now_ms=100)
    fresh.observe(topic="/contact", now_ms=100)
    fresh.observe(topic="/cmd_vel_authorized", now_ms=100)
    fresh.observe(topic="/clock", now_ms=100)
    monitor = BridgeHealthMonitor(fresh)
    for t in monitor.required_topics:
        monitor.set_advertised(topic=t, advertised=True)
    report = monitor.report(now_ms=200)
    assert report.severity == HealthSeverity.OK


def test_bridge_monitor_unadvertised_topic_is_error() -> None:
    fresh = TopicFreshnessMonitor(specs=DEFAULT_TOPIC_SPECS)
    fresh.declare(now_ms=0)
    monitor = BridgeHealthMonitor(fresh)
    # No advertised topics.
    report = monitor.report(now_ms=10_000)
    assert report.severity == HealthSeverity.ERROR
    assert "ros_gz_bridge unhealthy" in report.summary
