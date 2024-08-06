import rospy
import tf
from geometry_msgs.msg import PoseWithCovarianceStamped
from geometry_msgs.msg import Transform, TransformStamped


def talker():
    pub = rospy.Publisher("/amcl_pose_frequent", TransformStamped, queue_size=1)
    rospy.init_node('talker', anonymous=True)
    listener = tf.TransformListener()
    rate = rospy.Rate(100)
    while not rospy.is_shutdown():
        try:
	        (trans,rot) = listener.lookupTransform('map', 'base_link', rospy.Time(0))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            continue
        t = TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        print("Translation" + str(trans))
        print("Rotation " + str(rot))
        t.transform.translation.x = trans[0]
        t.transform.translation.y = trans[1]
        t.transform.translation.z = trans[2]
        t.transform.rotation.x = rot[0]
        t.transform.rotation.y = rot[1]
        t.transform.rotation.z = rot[2]
        t.transform.rotation.w = rot[3]
        pub.publish(t)
        rate.sleep()

if __name__ == "__main__":
	talker()


