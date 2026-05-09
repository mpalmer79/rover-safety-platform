"""ament_python setup for rover_observability."""

from __future__ import annotations

from glob import glob

from setuptools import find_packages, setup

PACKAGE_NAME = "rover_observability"

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         [f"resource/{PACKAGE_NAME}"]),
        (f"share/{PACKAGE_NAME}", ["package.xml"]),
        (f"share/{PACKAGE_NAME}/launch", glob("launch/*.launch.py")),
        (f"share/{PACKAGE_NAME}/config", glob("config/*.yaml")),
    ],
    install_requires=[
        "setuptools",
        "rover-safety-platform-backend>=0.1.0",
    ],
    zip_safe=True,
    maintainer="Rover Safety Platform",
    maintainer_email="rover-platform@example.com",
    description="Run lifecycle and replay observability for the rover platform.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            f"run_manager = {PACKAGE_NAME}.run_manager:main",
            f"event_recorder = {PACKAGE_NAME}.event_recorder:main",
        ],
    },
)
