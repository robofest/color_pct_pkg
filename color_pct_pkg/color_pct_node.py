import threading  # Added for thread safety

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rcl_interfaces.msg import IntegerRange, ParameterDescriptor, SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Image


class ColorPct(Node):

    def __init__(self):
        super().__init__("color_pct_node")

        # Initialize dynamic reconfigure values (Base values)
        self.h_low = 0
        self.h_high = 179
        self.s_low = 0
        self.s_high = 255
        self.v_low = 0
        self.v_high = 255

        # Thread lock to prevent resource contention between ROS and OpenCV GUI
        self.lock = threading.Lock()

        # Tracks cursor grid alignment coordinates
        self.mouse_x = None
        self.mouse_y = None
        self.mouse_data = None

        # Current frame references for mouse callback sampling
        self.current_bgr_frame = None
        self.current_hsv_frame = None

        # Initialize the CLAHE processor
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

        # Thread-safe image storage and play state
        self.latest_msg = None
        self.is_playing = True

        # Declare the parameter with a default topic name
        self.declare_parameter("cam_topic", "/image_raw")
        cam_topic = self.get_parameter("cam_topic").value

        # Define HSV parameters
        int_range = IntegerRange(from_value=0, to_value=179, step=1)
        self.declare_parameter(
            "hsv_h_low",
            0,
            ParameterDescriptor(
                description="HSV - H low value", integer_range=[int_range]
            ),
        )
        self.declare_parameter(
            "hsv_h_high",
            179,
            ParameterDescriptor(
                description="HSV - H high value", integer_range=[int_range]
            ),
        )

        int_range = IntegerRange(from_value=0, to_value=255, step=1)
        self.declare_parameter(
            "hsv_s_low",
            0,
            ParameterDescriptor(
                description="HSV - S low value", integer_range=[int_range]
            ),
        )
        self.declare_parameter(
            "hsv_s_high",
            255,
            ParameterDescriptor(
                description="HSV - S high value", integer_range=[int_range]
            ),
        )
        self.declare_parameter(
            "hsv_v_low",
            0,
            ParameterDescriptor(
                description="HSV - V low value", integer_range=[int_range]
            ),
        )
        self.declare_parameter(
            "hsv_v_high",
            255,
            ParameterDescriptor(
                description="HSV - V high value", integer_range=[int_range]
            ),
        )

        self.add_on_set_parameters_callback(self.param_callback)
        self.bridge = CvBridge()

        # Create windows explicitly so we can bind mouse callbacks to them
        cv2.namedWindow("ROS2 Webcam Feed")

        # Bind the mouse callback function to the raw image window
        cv2.setMouseCallback("ROS2 Webcam Feed", self.on_mouse_move)

        # Subscribe to camera topic
        self.subscription = self.create_subscription(
            Image, cam_topic, self.listener_callback, 1
        )

        # Processing loop timer
        self.timer = self.create_timer(1.0 / 30.0, self.process_image_loop)

        self.get_logger().info(
            f"Color Percent node started. Listening on: {cam_topic}"
        )

    def on_mouse_move(self, event, x, y, flags, param):
        """Callback function that triggers on mouse movement inside the raw feed window."""
        with self.lock:
            self.mouse_x = x
            self.mouse_y = y

            if (
                self.current_bgr_frame is not None
                and self.current_hsv_frame is not None
            ):
                h, w, _ = self.current_bgr_frame.shape
                if 0 <= x < w and 0 <= y < h:
                    hsv = self.current_hsv_frame[y, x]

                    # Save string dictionary of hover data
                    self.mouse_data = {
                        "text": f"H:{hsv[0]:3d} S:{hsv[1]:3d} V:{hsv[2]:3d}"
                    }

    def _calculate_and_draw_centroid(self, mask_img):
        """Calculates the center of mass of the white mask pixels and draws a red dot."""
        color_mask = cv2.cvtColor(mask_img, cv2.COLOR_GRAY2BGR)
        M = cv2.moments(mask_img)

        if M["m00"] > 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            # Draw a solid red circle at the centroid
            cv2.circle(color_mask, (cX, cY), 7, (0, 0, 255), -1)
            cv2.putText(
                color_mask,
                f"({cX}, {cY})",
                (cX + 15, cY - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

        return color_mask

    def param_callback(self, parameters):
        for param in parameters:
            if param.name == "hsv_h_low":
                self.h_low = param.value
            elif param.name == "hsv_h_high":
                self.h_high = param.value
            elif param.name == "hsv_s_low":
                self.s_low = param.value
            elif param.name == "hsv_s_high":
                self.s_high = param.value
            elif param.name == "hsv_v_low":
                self.v_low = param.value
            elif param.name == "hsv_v_high":
                self.v_high = param.value
        return SetParametersResult(successful=True)

    def listener_callback(self, msg):
        self.latest_msg = msg

    def process_image_loop(self):
        # Always call waitKey to register dynamic play/pause keys and window events
        key = cv2.waitKey(1) & 0xFF
        if key == ord("p"):
            self.is_playing = False
            self.get_logger().info("Stream paused ('p' pressed).")
        elif key == ord(" "):
            self.is_playing = True
            self.get_logger().info("Stream resumed (Spacebar pressed).")

        # Skip execution loop entirely if no image data has entered the pipeline yet
        if self.latest_msg is None and self.current_bgr_frame is None:
            return

        try:
            # 1. Ingest fresh data if stream is currently playing
            if self.is_playing and self.latest_msg is not None:
                msg = self.latest_msg
                self.latest_msg = None

                cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
                rows, cols, _ = cv_img.shape

                new_width = int(cols * 2 / 3)
                new_height = int(rows * 2 / 3)
                resized_img = cv2.resize(
                    cv_img, (new_width, new_height), interpolation=cv2.INTER_AREA
                )

                # Heavy image processing calculations done locally without lock
                hsv_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv_img)
                v_equalized = self.clahe.apply(v)
                hsv_equalized = cv2.merge([h, s, v_equalized])
                img_hsv = cv2.medianBlur(hsv_equalized, 7)

                # Assign computed values quickly inside a brief lock window
                with self.lock:
                    self.current_bgr_frame = resized_img
                    self.current_hsv_frame = img_hsv

                    # Force-sample current pixel if cursor is active inside window
                    if self.mouse_x is not None and self.mouse_y is not None:
                        # Call internal pixel extraction manually safely under lock
                        h, w, _ = self.current_bgr_frame.shape
                        if 0 <= self.mouse_x < w and 0 <= self.mouse_y < h:
                            hsv_pixel = self.current_hsv_frame[self.mouse_y, self.mouse_x]
                            self.mouse_data = {
                                "text": f"H:{hsv_pixel[0]:3d} S:{hsv_pixel[1]:3d} V:{hsv_pixel[2]:3d}"
                            }

            # 2. Render Windows (Runs persistently whether playing OR paused)
            # Create snapshot variables under brief lock to minimize UI blocking time
            with self.lock:
                bgr_snapshot = self.current_bgr_frame.copy() if self.current_bgr_frame is not None else None
                hsv_snapshot = self.current_hsv_frame # Shared array read pointer
                hud_text = self.mouse_data["text"] if self.mouse_data else None

            if bgr_snapshot is not None:
                new_height, new_width, _ = bgr_snapshot.shape

                # --- HUD DESIGN: Top-Left Static Box ---
                if hud_text:
                    cv2.rectangle(
                        bgr_snapshot, (5, 5), (180, 30), (0, 0, 0), cv2.FILLED
                    )
                    cv2.putText(
                        bgr_snapshot,
                        hud_text,
                        (15, 22),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 0),
                        1,
                        cv2.LINE_AA,
                    )

                cv2.imshow("ROS2 Webcam Feed", bgr_snapshot)

                # Draw mask view metrics
                if hsv_snapshot is not None:
                    mask = cv2.inRange(
                        hsv_snapshot,
                        (self.h_low, self.s_low, self.v_low),
                        (self.h_high, self.s_high, self.v_high),
                    )

                    num_white_pix = cv2.countNonZero(mask)
                    color_pct = (100 * num_white_pix) / (new_height * new_width)

                    visual_mask = self._calculate_and_draw_centroid(mask)
                    cv2.putText(
                        visual_mask,
                        f"Area: {color_pct:.1f}%",
                        (10, new_height - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (128, 128, 128),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.imshow("Target Color Mask", visual_mask)

        except Exception as e:
            self.get_logger().error(f"Processing error: {str(e)}")

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    color_pct = ColorPct()
    try:
        rclpy.spin(color_pct)
    except KeyboardInterrupt:
        pass
    finally:
        color_pct.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()