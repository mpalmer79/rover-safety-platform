"""ament_python setup for rover_mission_diagnostics."""

from __future__ import annotations

from glob import glob

from setuptools import find_packages, setup

PACKAGE_NAME = "rover_mission_diagnostics"

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         [f"resource/{PACKAGE_NAME}"]),
        (f"share/{PACKAGE_NAME}", ["package.xml"]),
        (f"share/{PACKAGE_NAME}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Rover Safety Platform",
    maintainer_email="rover-platform@example.com",
    description="Mission diagnostics for the rover platform.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            f"mission_diagnostics_node = {PACKAGE_NAME}.mission_diagnostics_node:main",
        ],
    },
)
