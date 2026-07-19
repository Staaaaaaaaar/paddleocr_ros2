#pragma once

#include <optional>
#include <string>
#include <vector>

namespace screen_ocr
{

struct RecognitionResult
{
  std::string signal_strength;
  std::string pipeline_current;
  std::string burial_depth;
  std::string arrow_direction;
  std::string compass_angle;
  std::optional<double> compass_angle_deg;
};

std::optional<RecognitionResult> recognize_image(
  const std::vector<uint8_t> & image_bytes,
  const std::string & api_base_url,
  const std::string & frame_id,
  bool debug,
  double timeout_sec);

}  // namespace screen_ocr
