import rospy
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import Bool

location_info = [\
['fah_start', 0.011, -0.041],\
['fah_intersection', -1.155, -2.302],\
['fah_supply_room', 1.485, -4.491],\
['fah_patient_room', 1.432, -8.736]]

locations = []

class Location:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.threshold = 0.2 #m
        self.publisher = rospy.Publisher("/position_monitor/" + name, Bool, queue_size=1)
    
    def publish_is_here(self, x, y):
        is_here = self.is_within_threshold(x, self.x, y, self.y, self.threshold)
        print("Is here!" + self.name + " " + str(is_here))
        self.publisher.publish(is_here)
    
    def is_within_threshold(self, x1, x2, y1, y2, threshold):
        delx = x1 - x2
        dely = y1 - y2
        return threshold*threshold > (delx*delx + dely*dely)

def publish_locations(data):
    x = data.pose.pose.position.x
    y = data.pose.pose.position.y
    print("Publishing locations.")
    for location in locations:
        location.publish_is_here(x, y)

def listener():
	rospy.init_node('listener', anonymous=True)
	for location in location_info:
	    locations.append(Location(location[0], location[1], location[2]))
	rospy.Subscriber("/amcl_pose", PoseWithCovarianceStamped, publish_locations)
	rospy.spin()


if __name__ == "__main__":
	listener()

