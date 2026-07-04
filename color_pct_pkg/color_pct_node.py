# With a param for Image topic name. 
#
import cv2
import rclpy
from cv_bridge import CvBridge
from rcl_interfaces.msg import IntegerRange, ParameterDescriptor, SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Image


class WhitePct(Node):
    def __init__(self):
        super().__init__('color_pct_node')

        # Initialize dynamic reconfigure values
        self.h_low = 0
        self.h_high = 179
        self.s_low = 0
        self.s_high = 255
        self.v_low = 0
        self.v_high = 255
        
        # Declare the parameter with a default topic name
        self.declare_parameter('cam_topic', '/image_raw')
        
        # Read the parameter value
        cam_topic = self.get_parameter('cam_topic').value

        # Define HSV parameters
        int_range = IntegerRange(from_value=0, to_value=179, step=1)
        param_hl_descriptor = ParameterDescriptor(description='HSV - H low value', integer_range=[int_range])
        self.declare_parameter('hsv_h_low', 0, param_hl_descriptor)

        int_range = IntegerRange(from_value=0, to_value=179, step=1)
        param_hh_descriptor = ParameterDescriptor(description='HSV - H high value', integer_range=[int_range])
        self.declare_parameter('hsv_h_high', 179, param_hh_descriptor)

        int_range = IntegerRange(from_value=0, to_value=255, step=1)
        param_sl_descriptor = ParameterDescriptor(description='HSV - S low value', integer_range=[int_range])
        self.declare_parameter('hsv_s_low', 0, param_sl_descriptor)

        int_range = IntegerRange(from_value=0, to_value=255, step=1)
        param_sh_descriptor = ParameterDescriptor(description='HSV - S high value', integer_range=[int_range])
        self.declare_parameter('hsv_s_high', 255, param_sh_descriptor)
        
        int_range = IntegerRange(from_value=0, to_value=255, step=1)
        param_vl_descriptor = ParameterDescriptor(description='HSV - V low value', integer_range=[int_range])
        self.declare_parameter('hsv_v_low', 0, param_vl_descriptor)

        int_range = IntegerRange(from_value=0, to_value=255, step=1)
        param_vh_descriptor = ParameterDescriptor(description='HSV - V high value', integer_range=[int_range])
        self.declare_parameter('hsv_v_high', 255, param_vh_descriptor)

        self.add_on_set_parameters_callback(self.param_callback)
        
        # Initialize the CvBridge utility
        self.bridge = CvBridge()
        
        # Subscribe to the webcam stream topic published 
        self.subscription = self.create_subscription(
            Image,
            cam_topic, # type: ignore or improve later
            self.listener_callback,
            10)
            
        self.get_logger().info('Color Percent node started. Waiting for frames...')

    def param_callback(self, parameters):
        for param in parameters:
            if param.name == 'hsv_h_low':
                self.h_low = param.value
            if param.name == 'hsv_h_high':
                self.h_high = param.value
            if param.name == 'hsv_s_low':
                self.s_low = param.value
            if param.name == 'hsv_s_high':
                self.s_high = param.value
            if param.name == 'hsv_v_low':
                self.v_low = param.value
            if param.name == 'hsv_v_high':
                self.v_high = param.value
        return SetParametersResult(successful=True)
    
    def listener_callback(self, msg):
        try:
            # Convert the ROS 2 Image message into a standard OpenCV image array
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            (rows, cols, channels) = cv_img.shape
            # Display the frame in a window
            cv2.imshow("ROS2 Webcam Feed", cv_img)

            hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
            img_hsv = cv2.medianBlur(hsv_img, 7)

            # Threshold HSV image to binary based on range
            mask = cv2.inRange(img_hsv,
                                (self.h_low, self.s_low, self.v_low),
                                (self.h_high,self.s_high,self.v_high))
            num_white_pix = cv2.countNonZero(mask)
            color_pct = (100 * num_white_pix) / (rows * cols)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(mask,f"{color_pct:.1f}%",(10,rows-10), font, 1, 128, 2, cv2.LINE_AA)
            
            # Display the frame in a window
            cv2.imshow("Target Color Mask", mask)
            
            # Must call waitKey to refresh the GUI frame window
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {str(e)}')

    def destroy_node(self):
        # Clean up OpenCV windows on shutdown
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    color_pct = WhitePct()
    
    try:
        rclpy.spin(color_pct)
    except KeyboardInterrupt:
        pass
    finally:
        color_pct.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()