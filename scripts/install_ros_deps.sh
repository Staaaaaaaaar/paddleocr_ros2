#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script supports Debian/Ubuntu (apt) only." >&2
  exit 1
fi

echo "Installing ROS2 Humble workspace dependencies for screen_ocr_ros2..."

sudo apt update
sudo apt install -y \
  ros-humble-ros-base \
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  libcurl4-openssl-dev \
  nlohmann-json3-dev \
  python3-colcon-common-extensions

echo
echo "Done. Next steps:"
echo "  source /opt/ros/humble/setup.bash"
echo "  cd ~/screen_ocr_ros2 && colcon build && source install/setup.bash"
