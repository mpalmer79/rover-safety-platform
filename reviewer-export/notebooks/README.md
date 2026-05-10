# Reviewer notebook

`reviewer_walkthrough.ipynb` loads the CSV files emitted alongside this directory (under `../csv/`) and shows simple counts + previews. The notebook uses only the Python standard library; pandas and matplotlib are imported behind optional guards.

## Run it

Open the notebook in Jupyter / VS Code / nbviewer. No additional configuration is required. The notebook does not need:

- ROS 2;
- Gazebo;
- Foxglove;
- live runtime evidence;
- a network connection.

## Honesty rules preserved

- Static-only evidence is rendered as static-only.
- Missing-bag evidence is rendered as missing-bag.
- ``causality_claimed`` stays ``false`` in subsystem-risk.
- Trend series labelled ``insufficient_history`` are not   forecast or interpolated.

_The platform is **not safety-certified**; this notebook is engineering review material._
