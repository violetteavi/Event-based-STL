import rospy
from geometry_msgs.msg import PoseStamped


def talker():
	pub = rospy.Publisher("/carter_ltl/nav_target", PoseStamped, queue_size=1)
	rospy.init_node('talker', anonymous=True)
	rate = rospy.Rate(10)
	while not rospy.is_shutdown():
		p = PoseStamped()
		p.pose.position.x = 0 #18
		p.pose.position.y = 0 #-19
		p.pose.orientation.w = 0
		p.header.stamp = rospy.Time.now()
		p.header.frame_id = "map"
		pub.publish(p)
		rate.sleep()


if __name__ == "__main__":
	talker()
