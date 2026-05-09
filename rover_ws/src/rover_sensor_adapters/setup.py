"""ament_python setup for rover_sensor_adapters."""

from __future__ import annotations

from glob import glob
from pathlib import Path

from setuptools import find_packages, setup

PACKAGE_NAME = "rover_sensor_adapters"

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
    description="ROS adapters that normalise raw sensor streams for the deterministic safety supervisor.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            f"lidar_adapter = {PACKAGE_NAME}.lidar_adapter:main",
            f"imu_adapter = {PACKAGE_NAME}.imu_adapter:main",
            f"odometry_adapter = {PACKAGE_NAME}.odometry_adapter:main",
            f"contact_adapter = {PACKAGE_NAME}.contact_adapter:main",
        ],
    },
)
