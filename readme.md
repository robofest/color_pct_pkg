# Display % of target color in an image
```bash
$ ros2 launch color_pct_pgurationkg color_pct_pkg.launch.py
```

On a separate terminal, run rqt
```bash
$ rqt
```

Plugings => Configution => Dynamic Reconfigure

Adjust sliders to adjust HSV low high values to get the target color. The percentage of the target color will be displayed in the terminal.