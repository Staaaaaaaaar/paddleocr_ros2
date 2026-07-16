from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description() -> LaunchDescription:
    default_config = os.path.join(
        get_package_share_directory("paddle_ocr"),
        "config",
        "pipeline_locator.yaml",
    )

    config_arg = DeclareLaunchArgument(
        "config_file",
        default_value=default_config,
        description="Pipeline locator node parameter file",
    )

    node = Node(
        package="paddle_ocr",
        executable="pipeline_locator_node",
        name="pipeline_locator_node",
        output="screen",
        parameters=[LaunchConfiguration("config_file")],
    )

    return LaunchDescription([config_arg, node])
