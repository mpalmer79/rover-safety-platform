"""ament_python setup for rover_runtime_diagnostics."""

from __future__ import annotations

from glob import glob

from setuptools import find_packages, setup

PACKAGE_NAME = "rover_runtime_diagnostics"

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
    install_requires=[
        "setuptools",
        "rover-safety-platform-backend>=0.1.0",
    ],
    zip_safe=True,
    maintainer="Rover Safety Platform",
    maintainer_email="rover-platform@example.com",
    description="Runtime diagnostics for the rover platform.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            f"topic_freshness_node = {PACKAGE_NAME}.topic_freshness_node:main",
            f"bridge_health_node = {PACKAGE_NAME}.bridge_health_node:main",
            f"tf_validator_node = {PACKAGE_NAME}.tf_validator_node:main",
            f"runtime_summary_node = {PACKAGE_NAME}.runtime_summary_node:main",
        ],
    },
)
