cmake_minimum_required(VERSION 3.8)
project(screen_ocr)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)
find_package(screen_ocr_msgs REQUIRED)
find_package(CURL REQUIRED)
find_package(nlohmann_json REQUIRED)

add_library(${PROJECT_NAME}_lib
  src/ocr_client.cpp
  src/result_mapper.cpp
)
target_include_directories(${PROJECT_NAME}_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(${PROJECT_NAME}_lib
  geometry_msgs
  screen_ocr_msgs
  std_msgs
)
target_link_libraries(${PROJECT_NAME}_lib
  CURL::libcurl
  nlohmann_json::nlohmann_json
)

add_executable(pipeline_locator_node src/pipeline_locator_node.cpp)
target_link_libraries(pipeline_locator_node ${PROJECT_NAME}_lib)
ament_target_dependencies(pipeline_locator_node
  rclcpp
  sensor_msgs
  geometry_msgs
  std_msgs
  cv_bridge
  screen_ocr_msgs
)
target_link_libraries(pipeline_locator_node ${OpenCV_LIBS})

install(TARGETS
  ${PROJECT_NAME}_lib
  pipeline_locator_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
