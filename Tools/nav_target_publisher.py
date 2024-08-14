#! /usr/bin/env python

"""
Filename: nav_target_publisher.py
Package: ???
Description: Publish nav data to STL from spec controller.
"""


import rospy 
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped
import logging

node_logger = logging.getLogger("node_logger")
fah_pose_dictionary = {
    'RM 1': [1.5, -8.5],
    'RM 2': [1.75, 1.5],
    'RM 3': [-0.35, -3.14],
    'RM 4': [0, 0],
    'supply_room': [-0.8, 2.5],
    'nurse_station': [0.0, 0.0]
}

ged_pose_dictionary = {
    'RM 1': [0.5, 0.85],
    'RM 2': [-4.65, 11.9],
    'RM 3': [0, 0],
    'RM 4': [0, 0],
    'supply_room': [2.4, 8.55],
    'nurse_station': [2.4, 8.55]
}

pub_pose_topic = rospy.Publisher("/carter_ltl/nav_target", PoseStamped, queue_size=1)

def destCallback(data):
    #dictionary = fah_pose_dictionary
    dictionary = ged_pose_dictionary
    dest = data.data
    dest_pose = dictionary.get(dest)
    pose = PoseStamped()
    pose.pose.position.x = dest_pose[0]
    pose.pose.position.y = dest_pose[1]
    pose.pose.orientation.w = 1.0
    pose.header.frame_id = "map"
    pose.header.stamp = rospy.Time.now()
    # tell the robot where to go
    pub_pose_topic.publish(pose)
    print("Navigating to: " + str(data.data))

def isDeliveryCallback(data):
    is_delivery = data.data
    # if the task is a delivery, the robot needs to go to the supply room
    #if is_delivery:
    #    pub_supply_room_topic.publish(pose_dictionary.get('supply_room'))

if __name__ == '__main__':
    # Initialize node
    rospy.init_node('nav_target_publisher')
    rate = rospy.Rate(10)

    # Create subscriber to /carter_ltl/nav_dest
    dest_topic = '/carter_ltl/nav_dest'
    rospy.Subscriber(dest_topic, String, destCallback)
    
    rospy.spin()
