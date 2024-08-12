import cv2
import pandas as pd

class Annotator:

    def __init__(self,path_pgm, path_yaml):
        self.resize_factor = 1
        self.top_left_crop = [1620,1600] # height, width to subtract from top left
        self.original_shape = []
        self.img = self.load_img(path_pgm, self.resize_factor, self.top_left_crop)
        self.res = 0.05
        self.origin = [-100,-100] # x, y coordinate of lower left corner
        self.last_left_click = ()
        self.waypoints = []
        self.walls = []
        self.draw_circle(*self.ros2img_coord(0,0))

    def load_img(self, path, resize_factor, top_left_crop):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED);
        h, w = img.shape
        self.original_shape = [h,w]
        cropped_img = img[top_left_crop[0]:h,top_left_crop[1]:w]
        #img_small = cv2.resize(cropped_img, (int(w*resize_factor), int((h*resize_factor))))   
        return cropped_img
        
    def load_walls(self, path):
        wall_df = pd.read_table(path, header=None, sep=' ')
        for index, row in wall_df.iterrows():
            if(not len(row) == 4):
                print("Bad wall row! " + str(row))
                break
            start_point_ros = (row[0], row[1])
            end_point_ros = (row[2], row[3])
            start_point_img = self.ros2img_coord(*start_point_ros)
            end_point_img = self.ros2img_coord(*end_point_ros)
            self.draw_line(start_point_img, end_point_img)
            self.walls.append([start_point_ros,end_point_ros])
    
    def load_waypoints(self, path):
        waypoint_df = pd.read_table(path, header=None, sep=' ')
        for index, row in waypoint_df.iterrows():
            if(not len(row) == 2):
                print("Bad waypoint row! " + str(row))
                break
            waypoint_ros = (row[0], row[1])
            waypoint_img = self.ros2img_coord(*waypoint_ros)
            self.draw_circle(*waypoint_img)
            self.waypoints.append(waypoint_ros)
    
    def on_click(self, event,x,y,flags,param): 
        if event == cv2.EVENT_LBUTTONDOWN:
            #print("Left X: " + str(x) + " Y: " + str(y))
            if(len(self.last_left_click) == 2):
                self.draw_line((x,y), self.last_left_click)
                self.walls.append([self.img2ros_coord(x,y), self.img2ros_coord(*self.last_left_click)])
                cv2.imshow("Map", self.img)
            self.last_left_click = (x,y)
        if event == cv2.EVENT_RBUTTONDOWN:
            #print("Right X: " + str(x) + " Y: " + str(y))
            self.draw_circle(x, y)
            self.waypoints.append(self.img2ros_coord(x,y))
            cv2.imshow("Map", self.img)
            
    def ros2img_coord (self, x_ros, y_ros):
        x_img_orig = int((x_ros - self.origin[0])/self.res)
        y_img_orig = self.original_shape[0] - int((y_ros - self.origin[1])/self.res)
        x_img = x_img_orig - self.top_left_crop[1]
        y_img = y_img_orig - self.top_left_crop[0]
        return (x_img, y_img)
        
    def img2ros_coord (self, x, y):
        x_original = x + self.top_left_crop[1]
        y_original = y + self.top_left_crop[0]
        x_ros = x_original*self.res + self.origin[0]
        y_ros = (self.original_shape[0]-y_original)*self.res + self.origin[1]
        return (x_ros, y_ros)
    
    def print_walls(self):
        for wall in self.walls:
            print(str(wall[0][0]) + " " + str(wall[0][1]) + " " + str(wall[1][0]) + " " + str(wall[1][1]))
    
    def print_waypoints(self):
        for waypoint in self.waypoints:
            print(str(waypoint[0]) + " " + str(waypoint[1]))
            
    def draw_circle(self, x, y):
        cv2.circle(self.img, (x,y), 2, (0,255,0), -1)
    
    def draw_line(self, x1y1, x2y2):
        cv2.line(self.img, x1y1, x2y2, (0,255,0), 1)
        
    def show(self):
        cv2.namedWindow('Map')
        cv2.setMouseCallback('Map',self.on_click)
        cv2.imshow("Map", self.img)
        
        
def annotator_unit_test():
    path = "/home/david/ed_ws/src/Event-based-STL/ED_Data/072924_fah_labspace.pgm"
    annotator = Annotator(path, "")
    x_img_orig, y_img_orig = annotator.ros2img_coord(0,0)
    print("Ros origin (img) is roughly X: " + str(x_img_orig) + " Y: " + str(y_img_orig))
    x_orig, y_orig = annotator.img2ros_coord(x_img_orig,y_img_orig)
    print("Ros origin is roughly X: " + str(x_orig) + " Y: " + str(y_orig))


pgm_path = "/home/rhclab/catkin_ws/src/Event-based-STL/ED_Data/072924_fah_labspace.pgm"
wall_path = "/home/rhclab/catkin_ws/src/Event-based-STL/FinalPackage/Maps/072924_fah_labspace_walls.txt"
waypoint_path = "/home/rhclab/catkin_ws/src/Event-based-STL/FinalPackage/Maps/072924_fah_labspace_waypoints.txt"
annotator = Annotator(pgm_path, "")
annotator.load_walls(wall_path)
annotator.load_waypoints(waypoint_path)
annotator.show()
cv2.waitKey()
annotator.print_waypoints()
print()
annotator.print_walls()




