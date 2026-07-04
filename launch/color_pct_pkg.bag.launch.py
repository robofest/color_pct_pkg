from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node

from launch import LaunchDescription


def generate_launch_description():
    
    # Mute the noisy Qt warning messages
    quiet_qt = SetEnvironmentVariable('QT_LOGGING_RULES', '*.warning=false')
    
    # 1. Path to your bag file directory (Replace with your actual path)
    # Example: '/home/user/bag_files/my_camera_data'
    bag_file_path = '/home/developer/rosbags/L_sun1_bag'

    # 2. Process to play the rosbag file
    rosbag_play = ExecuteProcess(
        cmd=['ros2', 'bag', 'play', bag_file_path, '--loop'],  
        output='screen'
    )

    # 3. Your image viewer node listening to the bag file's topic
    image_view_node = Node(
        package='color_pct_pkg',
        executable='color_pct_node_exe',
        name='color_pct_node',
        output='screen',
        # Updated to match the /cam_pub/image_raw topic stored inside the bag
        parameters=[
            {'cam_topic': '/cam_pub/image_raw'}
        ]
    )

    return LaunchDescription([
        quiet_qt,
        rosbag_play,
        image_view_node
    ])