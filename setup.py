import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'color_pct_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # CRITICAL: This line tells ROS 2 to install your launch files
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cchung',
    maintainer_email='cchung@ltu.edu',
    description='color_pct_pkg: ROS 2 package to calculate the percentage of color pixels in a webcam feed.',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'color_pct_node_exe = color_pct_pkg.color_pct_node:main', # trailling , needed???
        ],
    },
)