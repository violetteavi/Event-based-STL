import rospy
from geometry_msgs.msg import TransformStamped


def talker():
	pub = rospy.Publisher("/amcl_pose_frequent", TransformStamped, queue_size=1)
	rospy.init_node('talker', anonymous=True)
	rate = rospy.Rate(10)
	while not rospy.is_shutdown():
		p = TransformStamped()
		p.transform.translation.x = 0.5 #18
		p.transform.translation.y = 0.5 #-19
		p.transform.rotation.w = 1
		p.header.stamp = rospy.Time.now()
		p.header.frame_id = "map"
		pub.publish(p)
		rate.sleep()


if __name__ == "__main__":
	talker()


