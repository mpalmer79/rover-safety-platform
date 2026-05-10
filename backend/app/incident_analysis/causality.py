"""Rule-based causality reconstruction.

Each rule walks the ordered timeline looking for a documented chain
pattern (e.g. ``stale_lidar -> freshness_violation -> degraded ->
safe_stop -> zero_authorized_motion``). If every link is present,
the chain reports ``direct`` confidence. If one link is missing but
the others held, the chain downgrades to ``moderate``. If the
expected outcome contradicts the evidence (e.g. SAFE_STOP reached
without authorized motion zeroing), that is recorded as a
contradiction; the chain never silently passes.

The engine is read-only: it never writes to the timeline.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.incident_analysis.models import (
    CausalityChain,
    CausalityConfidence,
    CausalLink,
    IncidentTimeline,
    TimelineEntry,
)


def build_causality_chains(
    timeline: IncidentTimeline,
) -> list[CausalityChain]:
    """Return every applicable causality chain for ``timeline``."""

    chains: list[CausalityChain] = []
    for builder in (
        _stale_lidar_chain,
        _command_timeout_chain,
        _operator_estop_chain,
        _wheel_slip_chain,
        _keepout_violation_chain,
        _bridge_disconnect_chain,
    ):
        chain = builder(timeline)
        if chain is not None:
            chains.append(chain)
    return chains


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _find_first(
    timeline: IncidentTimeline,
    predicate,
) -> Optional[TimelineEntry]:
    for entry in timeline.entries:
        if predicate(entry):
            return entry
    return None


def _find_first_after(
    timeline: IncidentTimeline,
    after_index: int,
    predicate,
) -> Optional[TimelineEntry]:
    for entry in timeline.entries:
        if entry.sequence_index <= after_index:
            continue
        if predicate(entry):
            return entry
    return None


def _safety_with_state(state: str):
    def _p(e: TimelineEntry) -> bool:
        return (
            e.category == "safety_transition"
            and (e.safety_state == state or e.attributes.get("to_state") == state)
        )

    return _p


def _fault_of_type(fault_type: str):
    def _p(e: TimelineEntry) -> bool:
        if e.category != "fault_injection":
            return False
        if e.event_type != "fault_injection.fired":
            return False
        return e.attributes.get("fault_type") == fault_type

    return _p


def _fault_armed_of_type(fault_type: str):
    def _p(e: TimelineEntry) -> bool:
        if e.category != "fault_injection":
            return False
        if e.event_type != "fault_injection.armed":
            return False
        return e.attributes.get("fault_type") == fault_type

    return _p


def _watchdog_named(name: str):
    def _p(e: TimelineEntry) -> bool:
        if e.category != "watchdog":
            return False
        return e.attributes.get("watchdog") == name or name in (e.message or "")

    return _p


def _command_audit_summary() -> Optional[TimelineEntry]:
    """Picks the synthetic command-audit summary entry (if present)."""

    return None  # filled by callers via the timeline


def _link(
    *,
    source: TimelineEntry,
    target: TimelineEntry,
    relation: str,
    confidence: CausalityConfidence,
    rationale: str,
    inferred: bool = False,
) -> CausalLink:
    return CausalLink(
        from_entry_index=source.sequence_index,
        to_entry_index=target.sequence_index,
        relation=relation,
        confidence=confidence,
        rationale=rationale,
        inferred=inferred,
    )


def _summarise_overall(chain: CausalityChain) -> CausalityConfidence:
    """The chain's overall confidence is the *minimum* link confidence,
    downgraded when any link is missing or contradictory.
    """

    if chain.contradictions:
        return CausalityConfidence.INCONCLUSIVE
    if not chain.links:
        return CausalityConfidence.INCONCLUSIVE
    order = {
        CausalityConfidence.DIRECT: 4,
        CausalityConfidence.STRONG: 3,
        CausalityConfidence.MODERATE: 2,
        CausalityConfidence.WEAK: 1,
        CausalityConfidence.INCONCLUSIVE: 0,
    }
    min_conf = min(chain.links, key=lambda l: order[l.confidence]).confidence
    if chain.missing_links:
        # A missing link cannot exceed MODERATE.
        if order[min_conf] > order[CausalityConfidence.MODERATE]:
            min_conf = CausalityConfidence.MODERATE
    return min_conf


def _command_audit(timeline: IncidentTimeline) -> Optional[TimelineEntry]:
    for entry in timeline.entries:
        if (
            entry.category == "motion_arbitration"
            and entry.event_type == "motion_arbitration.summary"
        ):
            return entry
    return None


# ---------------------------------------------------------------------------
# Chain: stale_lidar.
# ---------------------------------------------------------------------------


def _stale_lidar_chain(timeline: IncidentTimeline) -> Optional[CausalityChain]:
    fault = _find_first(timeline, _fault_of_type("stale_lidar"))
    if fault is None:
        # Try fault_armed if no fault_fired (some scenarios only arm).
        fault = _find_first(timeline, _fault_armed_of_type("stale_lidar"))
    if fault is None:
        return None

    chain = CausalityChain(
        chain_id="stale_lidar_chain",
        description=(
            "stale_lidar -> freshness_violation -> degraded/restricted -> "
            "safe_stop -> zero_authorized_motion"
        ),
    )

    watchdog = _find_first_after(timeline, fault.sequence_index, _watchdog_named("lidar_freshness"))
    degraded = _find_first_after(
        timeline, fault.sequence_index, _safety_with_state("ACTIVE_DEGRADED")
    )
    safe_stop = _find_first_after(
        timeline, fault.sequence_index, _safety_with_state("SAFE_STOP")
    )
    cmd_audit = _command_audit(timeline)

    if watchdog is not None:
        chain.links.append(
            _link(
                source=fault,
                target=watchdog,
                relation="triggered",
                confidence=CausalityConfidence.DIRECT,
                rationale="lidar_freshness watchdog expired after fault fired",
            )
        )
    else:
        chain.missing_links.append("lidar_freshness watchdog event")

    if degraded is not None:
        chain.links.append(
            _link(
                source=fault,
                target=degraded,
                relation="escalated_to",
                confidence=CausalityConfidence.DIRECT if watchdog else CausalityConfidence.MODERATE,
                rationale="ACTIVE_DEGRADED follows the stale_lidar fault",
                inferred=watchdog is None,
            )
        )
    else:
        chain.missing_links.append("ACTIVE_DEGRADED transition")

    if safe_stop is not None:
        anchor = degraded or watchdog or fault
        chain.links.append(
            _link(
                source=anchor,
                target=safe_stop,
                relation="escalated_to",
                confidence=CausalityConfidence.DIRECT if degraded else CausalityConfidence.MODERATE,
                rationale="SAFE_STOP reached; supervisor consumed stale_lidar",
                inferred=degraded is None,
            )
        )
    else:
        chain.missing_links.append("SAFE_STOP transition")

    if cmd_audit is not None and safe_stop is not None:
        zeroed = int(cmd_audit.attributes.get("zeroed_count", 0) or 0)
        if zeroed > 0:
            chain.links.append(
                _link(
                    source=safe_stop,
                    target=cmd_audit,
                    relation="zeroed_motion_in",
                    confidence=CausalityConfidence.DIRECT,
                    rationale=f"command audit reports {zeroed} zeroed authorisations after SAFE_STOP",
                )
            )
        else:
            chain.contradictions.append(
                "SAFE_STOP reached but command-audit reports zero "
                "zeroed authorisations"
            )

    chain.overall_confidence = _summarise_overall(chain)
    return chain


# ---------------------------------------------------------------------------
# Chain: command_timeout.
# ---------------------------------------------------------------------------


def _command_timeout_chain(
    timeline: IncidentTimeline,
) -> Optional[CausalityChain]:
    timeout = _find_first(timeline, _fault_of_type("command_timeout"))
    if timeout is None:
        # Some scenarios surface this via watchdog rather than fault.
        timeout = _find_first(
            timeline,
            lambda e: e.category == "watchdog"
            and "command" in (e.message or "").lower(),
        )
    if timeout is None:
        return None
    chain = CausalityChain(
        chain_id="command_timeout_chain",
        description="command_timeout -> stale_command -> safe_stop -> zero_authorized_motion",
    )
    safe_stop = _find_first_after(
        timeline, timeout.sequence_index, _safety_with_state("SAFE_STOP")
    )
    cmd_audit = _command_audit(timeline)
    if safe_stop is not None:
        chain.links.append(
            _link(
                source=timeout,
                target=safe_stop,
                relation="escalated_to",
                confidence=CausalityConfidence.DIRECT,
                rationale="SAFE_STOP reached after command timeout",
            )
        )
    else:
        chain.missing_links.append("SAFE_STOP transition")
    if cmd_audit is not None and safe_stop is not None:
        zeroed = int(cmd_audit.attributes.get("zeroed_count", 0) or 0)
        if zeroed > 0:
            chain.links.append(
                _link(
                    source=safe_stop,
                    target=cmd_audit,
                    relation="zeroed_motion_in",
                    confidence=CausalityConfidence.DIRECT,
                    rationale=f"command audit reports {zeroed} zeroed authorisations after SAFE_STOP",
                )
            )
        else:
            chain.contradictions.append(
                "SAFE_STOP reached but command-audit reports zero "
                "zeroed authorisations"
            )
    chain.overall_confidence = _summarise_overall(chain)
    return chain


# ---------------------------------------------------------------------------
# Chain: operator E-stop.
# ---------------------------------------------------------------------------


def _operator_estop_chain(
    timeline: IncidentTimeline,
) -> Optional[CausalityChain]:
    estop = _find_first(
        timeline,
        lambda e: e.category == "operator_action"
        and "estop" in (e.event_type or "").lower(),
    )
    latched = _find_first(timeline, _safety_with_state("E_STOP_LATCHED"))
    if estop is None and latched is None:
        return None

    chain = CausalityChain(
        chain_id="operator_estop_chain",
        description="operator_estop -> estop_latched -> motion_inhibited",
    )
    if estop is not None and latched is not None:
        chain.links.append(
            _link(
                source=estop,
                target=latched,
                relation="latched_into",
                confidence=CausalityConfidence.DIRECT,
                rationale="operator E-stop event preceded E_STOP_LATCHED transition",
            )
        )
    elif latched is not None:
        chain.missing_links.append("operator E-stop event")
        chain.links.append(
            _link(
                source=latched,
                target=latched,
                relation="self_latched",
                confidence=CausalityConfidence.MODERATE,
                rationale="E_STOP_LATCHED reached without an explicit operator event in the timeline",
                inferred=True,
            )
        )
    else:
        chain.missing_links.append("E_STOP_LATCHED transition")

    cmd_audit = _command_audit(timeline)
    if cmd_audit is not None and latched is not None:
        zeroed = int(cmd_audit.attributes.get("zeroed_count", 0) or 0)
        rejected = int(cmd_audit.attributes.get("rejected_count", 0) or 0)
        if (zeroed + rejected) > 0:
            chain.links.append(
                _link(
                    source=latched,
                    target=cmd_audit,
                    relation="motion_inhibited_in",
                    confidence=CausalityConfidence.DIRECT,
                    rationale=(
                        f"command audit reports {zeroed} zeroed and {rejected} "
                        "rejected authorisations under E_STOP_LATCHED"
                    ),
                )
            )
        else:
            chain.contradictions.append(
                "E_STOP_LATCHED reached but command-audit reports no "
                "zeroed or rejected authorisations"
            )
    chain.overall_confidence = _summarise_overall(chain)
    return chain


# ---------------------------------------------------------------------------
# Chain: wheel_slip / odometry divergence.
# ---------------------------------------------------------------------------


def _wheel_slip_chain(timeline: IncidentTimeline) -> Optional[CausalityChain]:
    fault = _find_first(timeline, _fault_of_type("wheel_slip"))
    odom = _find_first(
        timeline,
        lambda e: e.category == "fault_injection"
        and e.attributes.get("fault_type") == "odometry_divergence",
    )
    if fault is None and odom is None:
        return None
    chain = CausalityChain(
        chain_id="wheel_slip_chain",
        description="wheel_slip / odometry_divergence -> degraded -> safe_stop (when severe)",
    )
    seed = fault or odom
    degraded = _find_first_after(
        timeline, seed.sequence_index, _safety_with_state("ACTIVE_DEGRADED")
    )
    safe_stop = _find_first_after(
        timeline, seed.sequence_index, _safety_with_state("SAFE_STOP")
    )
    if degraded is not None:
        chain.links.append(
            _link(
                source=seed,
                target=degraded,
                relation="escalated_to",
                confidence=CausalityConfidence.DIRECT,
                rationale="ACTIVE_DEGRADED follows the slip / odometry fault",
            )
        )
    else:
        chain.missing_links.append("ACTIVE_DEGRADED transition")
    if safe_stop is not None:
        chain.links.append(
            _link(
                source=degraded or seed,
                target=safe_stop,
                relation="escalated_to",
                confidence=CausalityConfidence.STRONG,
                rationale="SAFE_STOP reached; severe drift escalated past degraded mode",
            )
        )
    chain.overall_confidence = _summarise_overall(chain)
    return chain


# ---------------------------------------------------------------------------
# Chain: keepout violation.
# ---------------------------------------------------------------------------


def _keepout_violation_chain(
    timeline: IncidentTimeline,
) -> Optional[CausalityChain]:
    keepout = _find_first(
        timeline,
        lambda e: e.category == "world_model"
        and "keepout" in (e.event_type or "").lower(),
    )
    if keepout is None:
        return None
    chain = CausalityChain(
        chain_id="keepout_violation_chain",
        description="keepout_violation -> world_model_event -> mission_degraded_or_abort",
    )
    abort = _find_first_after(
        timeline,
        keepout.sequence_index,
        lambda e: e.category == "mission_transition"
        and ("abort" in (e.event_type or "").lower()
             or "mission_aborted" in (e.message or "").lower()),
    )
    if abort is not None:
        chain.links.append(
            _link(
                source=keepout,
                target=abort,
                relation="escalated_to",
                confidence=CausalityConfidence.DIRECT,
                rationale="mission abort recorded after keepout violation",
            )
        )
    else:
        chain.missing_links.append("mission abort event")
    chain.overall_confidence = _summarise_overall(chain)
    return chain


# ---------------------------------------------------------------------------
# Chain: bridge disconnect.
# ---------------------------------------------------------------------------


def _bridge_disconnect_chain(
    timeline: IncidentTimeline,
) -> Optional[CausalityChain]:
    fault = _find_first(timeline, _fault_of_type("bridge_disconnect"))
    if fault is None:
        return None
    chain = CausalityChain(
        chain_id="bridge_disconnect_chain",
        description="bridge_disconnect -> stale_inputs -> safe_stop",
    )
    safe_stop = _find_first_after(
        timeline, fault.sequence_index, _safety_with_state("SAFE_STOP")
    )
    if safe_stop is not None:
        chain.links.append(
            _link(
                source=fault,
                target=safe_stop,
                relation="escalated_to",
                confidence=CausalityConfidence.DIRECT,
                rationale="SAFE_STOP reached after bridge disconnect fault",
            )
        )
    else:
        chain.missing_links.append("SAFE_STOP transition")
    chain.overall_confidence = _summarise_overall(chain)
    return chain
