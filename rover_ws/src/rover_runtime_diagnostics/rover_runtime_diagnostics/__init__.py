"""rover_runtime_diagnostics: live diagnostics for the rover platform.

Each node in this package wraps a pure-logic monitor from
:mod:`app.diagnostics`. The nodes subscribe to live topics, feed the
monitors, and publish structured diagnostics on
``/diagnostics/<component>``. The aggregated summary lands on
``/diagnostics/runtime_summary`` for Foxglove and operator visibility.
"""

__version__ = "0.1.0"
