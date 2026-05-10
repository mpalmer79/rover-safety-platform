"""Reviewer notebook scaffold.

Builds an ``.ipynb`` document that loads the CSV files from a
neighbour ``../csv/`` directory using only the Python standard
library plus optional pandas / matplotlib via guarded imports. The
notebook is reviewer-safe: no network calls, no ROS / Gazebo /
Foxglove dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_notebook(*, csv_dir_relative: str = "../csv") -> dict:
    """Return the notebook dict ready to serialise as ``.ipynb``."""

    cells: list[dict] = []
    cells.append(_markdown(_intro_markdown(csv_dir_relative)))
    cells.append(_code(_setup_code(csv_dir_relative)))
    cells.append(_markdown("## Programme health"))
    cells.append(_code(_load_table_code("programme_health")))
    cells.append(_markdown("## Replay quality"))
    cells.append(_code(_load_table_code("replay_quality")))
    cells.append(_markdown("## Incident index"))
    cells.append(_code(_load_table_code("incident_index")))
    cells.append(_markdown("## Drift findings"))
    cells.append(_code(_load_table_code("drift_findings")))
    cells.append(_markdown("## Subsystem risk"))
    cells.append(_code(_load_table_code("subsystem_risk")))
    cells.append(_markdown("## Requirement coverage"))
    cells.append(_code(_load_table_code("requirement_coverage")))
    cells.append(_markdown("## Trend series"))
    cells.append(_code(_load_table_code("trend_series")))
    cells.append(_markdown("## Gate history"))
    cells.append(_code(_load_table_code("gate_history")))
    cells.append(_markdown(_closing_markdown()))

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.x",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(*, path: Path, csv_dir_relative: str = "../csv") -> Path:
    payload = build_notebook(csv_dir_relative=csv_dir_relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_readme(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_readme_markdown(), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Cell builders.
# ---------------------------------------------------------------------------


def _markdown(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": _split_lines(text),
    }


def _code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _split_lines(text),
    }


def _split_lines(text: str) -> list[str]:
    """nbformat expects a list of strings; preserve trailing newlines."""

    lines = text.splitlines(keepends=True)
    return lines or [text]


# ---------------------------------------------------------------------------
# Cell content.
# ---------------------------------------------------------------------------


def _intro_markdown(csv_dir_relative: str) -> str:
    return (
        "# Reviewer walkthrough\n"
        "\n"
        "This notebook loads the CSV files emitted by the reviewer-export "
        "pipeline (Phase 11) and shows simple counts + previews. It is "
        "reviewer-safe:\n"
        "\n"
        "- it uses only the Python standard library;\n"
        "- pandas and matplotlib are imported behind guards (the notebook "
        "still works without them);\n"
        "- it never reaches the network;\n"
        "- it does not require ROS, Gazebo, or Foxglove.\n"
        "\n"
        "_The platform is **not safety-certified**; this notebook is "
        "engineering review material._\n"
        "\n"
        f"CSV files are expected at ``{csv_dir_relative}/<table>.csv``.\n"
    )


def _setup_code(csv_dir_relative: str) -> str:
    return (
        "import csv\n"
        "import json\n"
        "from pathlib import Path\n"
        "\n"
        f"CSV_DIR = Path({csv_dir_relative!r}).resolve()\n"
        "print('CSV directory:', CSV_DIR)\n"
        "print('Files:', sorted(p.name for p in CSV_DIR.glob('*.csv')))\n"
        "\n"
        "try:\n"
        "    import pandas as _pd  # type: ignore\n"
        "    _HAS_PANDAS = True\n"
        "except Exception:\n"
        "    _HAS_PANDAS = False\n"
        "\n"
        "def load_table(name):\n"
        "    path = CSV_DIR / f'{name}.csv'\n"
        "    if not path.is_file():\n"
        "        return []\n"
        "    if _HAS_PANDAS:\n"
        "        return _pd.read_csv(path)\n"
        "    with path.open('r', encoding='utf-8') as fh:\n"
        "        return list(csv.DictReader(fh))\n"
        "\n"
        "def preview(rows, limit=5):\n"
        "    if _HAS_PANDAS and hasattr(rows, 'head'):\n"
        "        return rows.head(limit)\n"
        "    return rows[:limit]\n"
    )


def _load_table_code(table: str) -> str:
    return (
        f"rows = load_table({table!r})\n"
        f"print('row count:', len(rows) if not _HAS_PANDAS or not hasattr(rows, 'shape') else rows.shape[0])\n"
        "preview(rows)\n"
    )


def _closing_markdown() -> str:
    return (
        "## How to interpret this export\n"
        "\n"
        "- Static-only evidence stays static-only across the export. "
        "  The replay-quality table records the original ``static_only`` "
        "  flag verbatim; never read it as live evidence.\n"
        "- Missing-bag evidence stays missing-bag. The reviewer "
        "  cannot assume bag-backed coverage exists.\n"
        "- ``causality_claimed`` is always ``false`` in subsystem-risk; "
        "  the export never claims source-level causation.\n"
        "- Trend series with ``insufficient_history`` mean the "
        "  underlying programme review had fewer than two samples.\n"
        "\n"
        "See ``../reviewer-export-summary.md`` and ``manifest.json`` for "
        "the full disclaimer set.\n"
    )


def _readme_markdown() -> str:
    return (
        "# Reviewer notebook\n"
        "\n"
        "`reviewer_walkthrough.ipynb` loads the CSV files emitted alongside "
        "this directory (under `../csv/`) and shows simple counts + "
        "previews. The notebook uses only the Python standard library; "
        "pandas and matplotlib are imported behind optional guards.\n"
        "\n"
        "## Run it\n"
        "\n"
        "Open the notebook in Jupyter / VS Code / nbviewer. No additional "
        "configuration is required. The notebook does not need:\n"
        "\n"
        "- ROS 2;\n"
        "- Gazebo;\n"
        "- Foxglove;\n"
        "- live runtime evidence;\n"
        "- a network connection.\n"
        "\n"
        "## Honesty rules preserved\n"
        "\n"
        "- Static-only evidence is rendered as static-only.\n"
        "- Missing-bag evidence is rendered as missing-bag.\n"
        "- ``causality_claimed`` stays ``false`` in subsystem-risk.\n"
        "- Trend series labelled ``insufficient_history`` are not "
        "  forecast or interpolated.\n"
        "\n"
        "_The platform is **not safety-certified**; this notebook is "
        "engineering review material._\n"
    )
