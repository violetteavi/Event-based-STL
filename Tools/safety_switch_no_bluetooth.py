#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from sensor_msgs.msg import LaserScan
import math

enable = True
pub = rospy.Publisher('/cmd_vel_mux/input/teleop', Twist, queue_size=10)
can_go_forward = False
can_go_backward = False
# last_time = 0  #last time recieving bluetooth joystick message 

def callback_listener(data):
    # rospy.loginfo(rospy.get_caller_id() + "I heard %s", data)
    
    # diff_time = rospy.get_time() - last_time 
    # print("current time is:  %f" % rospy.get_time())
    # print(diff_time)

    # print('heard inverted command vel')
    if (data.linear.x > 0) :
        if not enable or not can_go_forward : 
    	    empty_twist = Twist()
    	    pub.publish(empty_twist)
        else: 
    	    pub.publish(data)
    else:
        if not enable or not can_go_backward:
            empty_twist = Twist()
            pub.publish(empty_twist)
        else:
            pub.publish(data)

def callback_joy(data):
   # rospy.loginfo(rospy.get_caller_id() + "I heard %s", data)
   #  print("current joystick time is: %f" % rospy.get_time())
    global enable
    # global last_time
    # last_time = rospy.get_time()
    if (data.axes[5] < 0.95 and not (data.axes[2]>-0.001 and data.axes[2]<0.001)):
    	enable = True
    else: 
    	enable = False

def callback_lidar(data):
    # min_dist = min(data.ranges)
    # print("minimum distance is: %f" % min_dist)
    global can_go_forward
    global can_go_backward
    ignore_threshold = 0.2 # ignore anything closer than this
    x_ThreshFront_forward = 0.5
    x_ThreshBack_forward = 0
    x_ThreshFront_backward = 0
    x_ThreshBack_backward = -0.5
    y_ThreshLeft  = 0.40
    y_ThreshRight = -0.40
    can_go_forward_temp = True
    can_go_backward_temp = True
    for i in range(len(data.ranges)):
        if data.ranges[i] < ignore_threshold:
            continue
        theta = data.angle_min + (i*data.angle_increment)
        x = math.cos(theta) * data.ranges[i]
        y = math.sin(theta) * data.ranges[i]
       # print("x coordinate is: %f" % x)
       # print("y coordinate is: %f" % y)
        isInDangerZoneX_forward = (x<x_ThreshFront_forward and x>x_ThreshBack_forward)
        isInDangerZoneX_backward = (x<x_ThreshFront_backward and x>x_ThreshBack_backward)
        isInDangerZoneY = (y<y_ThreshLeft and y>y_ThreshRight)
        if isInDangerZoneX_forward and isInDangerZoneY:
            can_go_forward_temp = False
        if isInDangerZoneX_backward and isInDangerZoneY:
            can_go_backward_temp = False
    can_go_forward = can_go_forward_temp
    can_go_backward = can_go_backward_temp

def safety_switch():

    # In ROS, nodes are uniquely named. If two nodes with the same
    # name are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    rospy.init_node('safety_switch', anonymous=True)
    rospy.Subscriber("/controller/cmd_vel", Twist, callback_listener)
    # rospy.Subscriber("/controller/cmd_vel_inverted", Twist, callback_listener)
    rospy.Subscriber("/controller/cmd_vel_smooth", Twist, callback_listener)

    #rospy.Subscriber("/bluetooth_teleop/joy", Joy, callback_joy)
    rospy.Subscriber("/scan", LaserScan, callback_lidar)
    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()

if __name__ == '__main__':
    safety_switch()
