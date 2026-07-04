# Display % of target color in an image

### Video images from a webcam are published to a ROS2 topic by the usb_cam package. This node subscribes to that topic, converts the images to OpenCV format, and calculates the percentage of pixels in the image that match a target color. The target color is defined by HSV low and high values, which can be adjusted using rqt's Dynamic Reconfigure plugin.
```bash
$ ros2 launch color_pct_pkg color_pct_pkg.launch.py
```

On a separate terminal, run rqt
```bash
$ rqt
```

Plugings => Configution => Dynamic Reconfigure

Adjust sliders to adjust HSV low high values to get the target color. The percentage of the target color will be displayed in the terminal.

### Images from a rosbag. A new topic name can be specified for the image topic in the launch file. 
```bash
$ ros2 launch color_pct_pkg color_pct_pkg.bag.launch.py
```