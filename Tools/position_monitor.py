import rospy
from geometry_msgs.msg import PoseStamped, TransformStamped
from std_msgs.msg import Bool

target_xy = None
pub = None
alert_raised = False

def set_target(data):
    global target_xy
    target_xy = (data.pose.position.x, data.pose.position.y)
    global alert_raised
    alert_raised = False
    
    print("Got a destination")
    
def publish_is_here(data):
    global alert_raised
    threshold = 0.5
    if(target_xy == None):
        return
    current_x = data.transform.translation.x
    current_y = data.transform.translation.y
    is_here = is_within_threshold(current_x, current_y, target_xy[0], target_xy[1], threshold)
    if(is_here and not alert_raised):
        print("Arrived at destination")
        pub.publish(True)
        alert_raised = True
    
def is_within_threshold(x1, y1, x2, y2, threshold):
    delx = x1 - x2
    dely = y1 - y2
    return threshold*threshold > (delx*delx + dely*dely)

def listener():
    rospy.init_node('listener', anonymous=True)
    global pub 
    pub = rospy.Publisher("carter_ltl/inputs/nav_complete", Bool, queue_size=1)
    rospy.Subscriber("/carter_ltl/nav_target", PoseStamped, set_target)
    rospy.Subscriber("/amcl_pose_frequent", TransformStamped, publish_is_here)
    rospy.spin()


if __name__ == "__main__":
    listener()

