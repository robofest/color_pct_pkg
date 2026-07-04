from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            output='screen',
            parameters=[
                # --- Essential Hardware/WSL Connection Settings ---
                {'video_device': '/dev/video0'},
                {'image_width': 320},
                {'image_height': 240},
                {'framerate': 20.0}, # was 30.0
                
                # --- The WSL Bandwidth Fix (MJPEG Compression) ---
                {'pixel_format': 'mjpeg2rgb'},  # Hardware compression over usbipd
                {'io_method': 'mmap'},

                # --- Image/Brightness Controls ---
                # Note: Parameter names depend on the driver version. 
                # If these specific parameters aren't parsed by your version, 
                # keep using 'v4l2-ctl' in a separate terminal.
                {'brightness': 180},           # Boost low-light performance, was 200
                {'gain': 150},                 # Increases sensitivity if supported
                {'autoexposure': False},       # Set to False to manually override exposure
                {'exposure': 150},             # Adjust exposure absolute value
                
                # --- Topic Configuration ---
                {'camera_name': 'default_cam'},
                {'frame_id': 'camera_link'},
            ]
        ),
        Node(
            package='color_pct_pkg',
            executable='color_pct_node_exe',
            name='color_pct_node', # nick_name for this node
            output='screen'
        )
    ])