#!/usr/bin/env python3
"""ROS2 node: subscribe image topic, call HTTP recognition service, publish SensorMsg."""

from __future__ import annotations

import threading

import cv2
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from screen_ocr.ocr_client import recognize_image
from screen_ocr.result_mapper import recognition_to_sensor_msg
from screen_ocr_msgs.msg import SensorMsg
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import Header


class PipelineLocatorNode(Node):
    def __init__(self) -> None:
        super().__init__("pipeline_locator_node")

        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("image_type", "raw")
        self.declare_parameter("output_topic", "/pipeline_locator/sensor")
        self.declare_parameter("inference_rate_hz", 2.0)
        self.declare_parameter("output_frame_id", "pipeline_locator")
        self.declare_parameter("api_base_url", "http://127.0.0.1:8000")
        self.declare_parameter("api_timeout_sec", 5.0)
        self.declare_parameter("debug", False)
        self.declare_parameter("qos_reliability", "best_effort")
        self.declare_parameter("qos_history_depth", 1)

        self._image_topic = self.get_parameter("image_topic").get_parameter_value().string_value
        self._image_type = self.get_parameter("image_type").get_parameter_value().string_value
        self._output_topic = self.get_parameter("output_topic").get_parameter_value().string_value
        self._inference_rate_hz = self.get_parameter("inference_rate_hz").get_parameter_value().double_value
        self._output_frame_id = self.get_parameter("output_frame_id").get_parameter_value().string_value
        self._api_base_url = self.get_parameter("api_base_url").get_parameter_value().string_value
        self._api_timeout_sec = self.get_parameter("api_timeout_sec").get_parameter_value().double_value
        self._debug = self.get_parameter("debug").get_parameter_value().bool_value
        self._qos_reliability = self.get_parameter("qos_reliability").get_parameter_value().string_value
        self._qos_history_depth = self.get_parameter("qos_history_depth").get_parameter_value().integer_value

        self._bridge = CvBridge()
        self._image_lock = threading.Lock()
        self._latest_header: Header | None = None
        self._latest_cv_image = None
        self._latest_jpeg_bytes: bytes | None = None

        qos = self._build_qos_profile()
        if self._image_type == "compressed":
            self._image_subscription = self.create_subscription(
                CompressedImage,
                self._image_topic,
                self._compressed_image_callback,
                qos,
            )
        else:
            self._image_subscription = self.create_subscription(
                Image,
                self._image_topic,
                self._image_callback,
                qos,
            )

        self._publisher = self.create_publisher(SensorMsg, self._output_topic, 10)

        period_sec = 1.0 / max(self._inference_rate_hz, 0.1)
        self._timer = self.create_timer(period_sec, self._on_timer)

        self.get_logger().info(
            "Pipeline locator node started: "
            f"image={self._image_topic} ({self._image_type}), "
            f"api={self._api_base_url}, output={self._output_topic}, "
            f"rate={self._inference_rate_hz:.2f} Hz"
        )

    def _build_qos_profile(self) -> QoSProfile:
        reliability = (
            ReliabilityPolicy.RELIABLE
            if self._qos_reliability.lower() == "reliable"
            else ReliabilityPolicy.BEST_EFFORT
        )
        return QoSProfile(
            reliability=reliability,
            history=HistoryPolicy.KEEP_LAST,
            depth=max(self._qos_history_depth, 1),
            durability=DurabilityPolicy.VOLATILE,
        )

    def _image_callback(self, msg: Image) -> None:
        try:
            cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except CvBridgeError as exc:
            self.get_logger().warning(f"Failed to convert Image message: {exc}")
            return

        with self._image_lock:
            self._latest_header = msg.header
            self._latest_cv_image = cv_image
            self._latest_jpeg_bytes = None

    def _compressed_image_callback(self, msg: CompressedImage) -> None:
        if msg.data:
            with self._image_lock:
                self._latest_header = msg.header
                self._latest_jpeg_bytes = bytes(msg.data)
                self._latest_cv_image = None
            return

        try:
            cv_image = self._bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except CvBridgeError as exc:
            self.get_logger().warning(f"Failed to convert CompressedImage message: {exc}")
            return

        with self._image_lock:
            self._latest_header = msg.header
            self._latest_cv_image = cv_image
            self._latest_jpeg_bytes = None

    def _encode_image(self, cv_image) -> bytes | None:
        ok, encoded = cv2.imencode(".jpg", cv_image)
        if not ok:
            return None
        return encoded.tobytes()

    def _on_timer(self) -> None:
        with self._image_lock:
            header = self._latest_header
            cv_image = None if self._latest_cv_image is None else self._latest_cv_image.copy()
            jpeg_bytes = self._latest_jpeg_bytes

        if header is None:
            self.get_logger().debug(f"Waiting for image on {self._image_topic}")
            return

        if jpeg_bytes is None:
            if cv_image is None:
                self.get_logger().debug(f"Waiting for image on {self._image_topic}")
                return
            jpeg_bytes = self._encode_image(cv_image)
            if jpeg_bytes is None:
                self.get_logger().warning(f"Failed to encode image for frame {header.frame_id}")
                return

        recognition = recognize_image(
            jpeg_bytes,
            api_base_url=self._api_base_url,
            frame_id=header.frame_id or "ros",
            debug=self._debug,
            timeout_sec=self._api_timeout_sec,
        )
        if recognition is None:
            self.get_logger().warning(
                f"Recognition failed for frame {header.frame_id} (api={self._api_base_url})"
            )
            return

        output_header = Header()
        output_header.stamp = self.get_clock().now().to_msg()
        output_header.frame_id = self._output_frame_id or header.frame_id

        sensor_msg = recognition_to_sensor_msg(recognition, output_header)
        self._publisher.publish(sensor_msg)

        self.get_logger().debug(
            "Published "
            f"heading={sensor_msg.pipeline_heading_degrees:.1f} deg, "
            f"current={sensor_msg.current_milliamps:.0f} mA, "
            f"depth={sensor_msg.depth_meters:.0f} m, "
            f"signal={sensor_msg.signal_strength_percent:.1f}%"
        )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = PipelineLocatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
