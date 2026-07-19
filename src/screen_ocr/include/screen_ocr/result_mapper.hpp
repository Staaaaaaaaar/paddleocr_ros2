#pragma once

#include <optional>
#include <string>

#include "screen_ocr/ocr_client.hpp"
#include "screen_ocr_msgs/msg/sensor_msg.hpp"
#include "std_msgs/msg/header.hpp"

namespace screen_ocr
{

screen_ocr_msgs::msg::SensorMsg recognition_to_sensor_msg(
  const RecognitionResult & recognition,
  const std_msgs::msg::Header & header);

}  // namespace screen_ocr
