"""Event recorder node.

Subscribes to ``/safety/events`` (a ``std_msgs/String`` topic carrying
canonical-JSON event envelopes from :mod:`app.domain.events`) and
appends every line to ``runs/<run_id>/events.jsonl``.

Schema validation is performed against
:mod:`app.telemetry.schemas.validate_event_dict`. Invalid events are
logged and dropped — the recorder never silently passes a malformed
event into the replay artefacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import IO, Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from app.telemetry.schemas import EventSchemaError, validate_event_dict


class EventRecorderNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_event_recorder")
        self.declare_parameter("run_id", "unknown")
        self.declare_parameter("runs_root", str(Path.cwd() / "runs"))
        self.declare_parameter("events_topic", "/safety/events")

        run_id = str(self.get_parameter("run_id").value)
        runs_root = Path(str(self.get_parameter("runs_root").value))
        run_dir = runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self._events_path = run_dir / "events.jsonl"
        self._fh: Optional[IO[str]] = self._events_path.open("a", encoding="utf-8")

        self._sub = self.create_subscription(
            String,
            str(self.get_parameter("events_topic").value),
            self._on_event,
            50,
        )
        self.get_logger().info(
            "rover_event_recorder appending to %s", str(self._events_path)
        )

    def _on_event(self, msg: String) -> None:
        if self._fh is None:
            return
        try:
            payload = json.loads(msg.data)
            validate_event_dict(payload)
        except (json.JSONDecodeError, EventSchemaError) as exc:
            self.get_logger().warn("dropping malformed event: %s" % exc)
            return
        self._fh.write(msg.data)
        self._fh.write("\n")
        self._fh.flush()

    def destroy_node(self):  # pragma: no cover - rclpy lifecycle
        if self._fh is not None:
            self._fh.close()
            self._fh = None
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = EventRecorderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
