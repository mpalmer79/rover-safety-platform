"""Fault injection subsystem.

The injector observes scenario time and active fault profiles, and
applies effects to sensor frames and gateway heartbeats *before* the
supervisor sees them. The supervisor then reacts to those altered
inputs through normal mechanisms; the injector never sets safety state
or writes authorized motion.
"""

from app.faults.injector import FaultInjector, InjectionContext, InjectionOutput
from app.faults.models import FaultEffect
from app.faults.profiles import (
    bridge_disconnect,
    command_timeout,
    encoder_drift,
    imu_bias,
    packet_delay,
    sensor_disagreement,
    stale_lidar,
    watchdog_expiration,
    wheel_slip,
)

__all__ = [
    "FaultEffect",
    "FaultInjector",
    "InjectionContext",
    "InjectionOutput",
    "bridge_disconnect",
    "command_timeout",
    "encoder_drift",
    "imu_bias",
    "packet_delay",
    "sensor_disagreement",
    "stale_lidar",
    "watchdog_expiration",
    "wheel_slip",
]
