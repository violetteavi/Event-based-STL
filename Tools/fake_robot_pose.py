import rospy
from nav_msgs.msg import Odometry


def talker():
	pub = rospy.Publisher("/odom", Odometry, queue_size=1)
	rospy.init_node('talker', anonymous=True)
	rate = rospy.Rate(10)
	while not rospy.is_shutdown():
		o = Odometry()
		o.pose.pose.position.x = 0 #18
		o.pose.pose.position.x= 0 #-19
		o.pose.pose.orientation.w = 0
		o.header.stamp = rospy.Time.now()
		o.header.frame_id = "start"
		o.child_frame_id = "base_link"
		pub.publish(o)
		rate.sleep()


if __name__ == "__main__":
	talker()


