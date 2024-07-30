import rospy
import tf
from geometry_msgs.msg import PoseWithCovarianceStamped
from geometry_msgs.msg import Transform, TransformStamped


def talker():
    pub = rospy.Publisher("/amcl_pose_frequent", Transform, queue_size=1)
    rospy.init_node('talker', anonymous=True)
    listener = tf.TransformListener()
    rate = rospy.Rate(100)
    while not rospy.is_shutdown():
        try:
	        (trans,rot,time) = listener.lookupTransform('map', 'base_link', rospy.Time(0))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            continue
        t = TransformStamped()
        t.header.stamp = time
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = trans.x
        t.transform.translation.y = trans.y
        t.transform.translation.z = trans.z
        t.transform.rotation.x = rot.x
        t.transform.rotation.y = rot.y
        t.transform.rotation.z = rot.z
        t.transform.rotation.w = rot.w
        pub.publish(t)
        rate.sleep()

if __name__ == "__main__":
	talker()


