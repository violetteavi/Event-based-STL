import rospy
from geometry_msgs.msg import PoseStamped, TransformStamped
from std_msgs.msg import Bool, String

target_xy = None
target_name = "supply_room"
pub = None
alert_raised = False

def set_target(data):
    global target_xy
    target_xy = (data.pose.position.x, data.pose.position.y)
    global alert_raised
    alert_raised = False
    
    print("Got a destination")

def set_target_name(data):
    global target_name
    target_name = data.data
    print("Destination name: " + data.data)
    
def publish_is_here(data):
    global alert_raised
    threshold = 0.5
    if(target_xy == None):
        return
    current_x = data.transform.translation.x
    current_y = data.transform.translation.y
    is_here = is_within_threshold(current_x, current_y, target_xy[0], target_xy[1], threshold)
    if(is_here and not alert_raised and not target_name == "supply_room"):
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
    pub = rospy.Publisher("carter_stl/nav_complete", Bool, queue_size=1)
    rospy.Subscriber("/carter_ltl/nav_dest", String, set_target_name)
    rospy.Subscriber("/carter_ltl/nav_target", PoseStamped, set_target)
    rospy.Subscriber("/amcl_pose_frequent", TransformStamped, publish_is_here)
    rospy.spin()


if __name__ == "__main__":
    listener()

