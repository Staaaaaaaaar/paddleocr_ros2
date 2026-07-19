from glob import glob

from setuptools import find_packages, setup

package_name = "screen_ocr"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Staaaaaaaaar",
    maintainer_email="2300012435@stu.pku.edu.cn",
    description="ROS2 bridge for pipeline locator screen OCR via HTTP service.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "pipeline_locator_node = screen_ocr.pipeline_locator_node:main",
        ],
    },
)
