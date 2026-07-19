#include "screen_ocr/result_mapper.hpp"

#include <cmath>
#include <limits>
#include <regex>
#include <string>

namespace screen_ocr
{
namespace
{

constexpr double kUnknownCovariance = -1.0;

std::optional<double> parse_number(const std::string & text)
{
  if (text.empty() || text == "none") {
    return std::nullopt;
  }

  static const std::regex number_re(R"(([-+]?\d*\.?\d+))");
  std::smatch match;
  if (!std::regex_search(text, match, number_re)) {
    return std::nullopt;
  }

  try {
    return std::stod(match[1].str());
  } catch (const std::exception &) {
    return std::nullopt;
  }
}

geometry_msgs::msg::Vector3 heading_to_magnetic_field(std::optional<double> heading_deg)
{
  geometry_msgs::msg::Vector3 vector;
  if (!heading_deg.has_value()) {
    return vector;
  }

  const double radians = heading_deg.value() * M_PI / 180.0;
  vector.x = std::sin(radians);
  vector.y = std::cos(radians);
  vector.z = 0.0;
  return vector;
}

std::pair<bool, bool> arrow_flags(const std::string & arrow_direction)
{
  std::string direction = arrow_direction;
  for (char & ch : direction) {
    ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
  }

  const bool left = direction == "left" || direction == "both";
  const bool right = direction == "right" || direction == "both";
  return {left, right};
}

float to_nan_if_missing(const std::optional<double> & value)
{
  if (!value.has_value()) {
    return std::numeric_limits<float>::quiet_NaN();
  }
  return static_cast<float>(value.value());
}

}  // namespace

screen_ocr_msgs::msg::SensorMsg recognition_to_sensor_msg(
  const RecognitionResult & recognition,
  const std_msgs::msg::Header & header)
{
  const auto percent = parse_number(recognition.signal_strength);
  const auto current = parse_number(recognition.pipeline_current);
  const auto depth = parse_number(recognition.burial_depth);

  std::optional<double> heading = recognition.compass_angle_deg;
  if (!heading.has_value()) {
    heading = parse_number(recognition.compass_angle);
  }

  const auto [left_arrow, right_arrow] = arrow_flags(recognition.arrow_direction);

  screen_ocr_msgs::msg::SensorMsg msg;
  msg.header = header;
  msg.magnetic_field = heading_to_magnetic_field(heading);
  msg.magnetic_field_covariance = {
    kUnknownCovariance, 0.0, 0.0,
    0.0, kUnknownCovariance, 0.0,
    0.0, 0.0, kUnknownCovariance,
  };

  msg.signal_strength_percent = to_nan_if_missing(percent);
  msg.signal_strength = percent.has_value()
    ? static_cast<float>(percent.value() / 100.0)
    : std::numeric_limits<float>::quiet_NaN();
  msg.depth_meters = to_nan_if_missing(depth);
  msg.current_milliamps = to_nan_if_missing(current);
  msg.pipeline_heading_degrees = to_nan_if_missing(heading);
  msg.left_arrow = left_arrow;
  msg.right_arrow = right_arrow;
  return msg;
}

}  // namespace screen_ocr
