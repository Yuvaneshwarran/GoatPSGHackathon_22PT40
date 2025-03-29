import time
import uuid
import random
import math

class Robot:
    # Robot status constants
    STATUS_IDLE = "idle"
    STATUS_MOVING = "moving"
    STATUS_WAITING = "waiting"
    STATUS_CHARGING = "charging"
    STATUS_TASK_COMPLETE = "task_complete"
    
    # Status colors
    STATUS_COLORS = {
        STATUS_IDLE: (100, 100, 100),        # Gray
        STATUS_MOVING: (0, 200, 0),          # Green
        STATUS_WAITING: (255, 165, 0),       # Orange
        STATUS_CHARGING: (0, 0, 255),        # Blue
        STATUS_TASK_COMPLETE: (128, 0, 128)  # Purple
    }
    
    def __init__(self, position, color=None):
        """
        Initialize a robot.
        
        Args:
            position (int): Index of the vertex where the robot is located.
            color (tuple): RGB color tuple for the robot.
        """
        self.id = str(uuid.uuid4())[:6]  # Generate a unique ID
        self.position = position  # Current vertex index
        
        # Generate a random color if none is provided
        if color is None:
            color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )
        self.color = color
        
        self.status = self.STATUS_IDLE
        self.path = []  # List of vertex indices representing the planned path
        self.destination = None  # Target vertex index
        self.progress = 0.0  # Progress along the current lane (0.0 to 1.0)
        self.current_lane = None  # Current lane being traversed [from_vertex, to_vertex]
        self.creation_time = time.time()
        self.animation_offset = random.random() * math.pi * 2  # For bobbing animation
        self.waiting_time = 0  # Time spent waiting in seconds
        self.battery_level = 100.0  # Battery level in percentage
        self.battery_drain_rate = 0.5  # Battery drain per second while moving
        self.battery_idle_drain_rate = 0.1  # Battery drain per second while idle
        
    def assign_task(self, destination, path):
        """
        Assign a navigation task to the robot.
        
        Args:
            destination (int): Index of the destination vertex.
            path (list): List of vertex indices representing the planned path.
        """
        self.destination = destination
        self.path = path
        self.status = self.STATUS_MOVING
        self.progress = 0.0
        self.waiting_time = 0
        
        # Set up the current lane if the path has at least 2 vertices
        if path and len(path) > 1:
            self.current_lane = [path[0], path[1]]
            print(f"Robot {self.id}: Setting current_lane to {self.current_lane}")
        else:
            self.current_lane = None
            print(f"Robot {self.id}: Path too short, current_lane set to None")
        
    def update(self, delta_time, speed=0.3):
        """
        Update the robot's position and status.
        
        Args:
            delta_time (float): Time elapsed since the last update in seconds.
            speed (float): Speed of the robot in units per second.
        
        Returns:
            bool: True if the robot's state changed, False otherwise.
        """
        # Update animation offset for bobbing effect
        self.animation_offset += delta_time * 2
        
        # Update battery level
        if self.status == self.STATUS_MOVING:
            self.battery_level = max(0, self.battery_level - self.battery_drain_rate * delta_time)
        else:
            self.battery_level = max(0, self.battery_level - self.battery_idle_drain_rate * delta_time)
        
        # If battery is depleted, robot can't move
        if self.battery_level <= 0 and self.status == self.STATUS_MOVING:
            self.status = self.STATUS_WAITING
            return True
        
        # Handle waiting status - don't do anything else while waiting
        # The fleet manager will change the status when the path is clear
        if self.status == self.STATUS_WAITING:
            self.waiting_time += delta_time
            return False
        
        # Handle charging status
        if self.status == self.STATUS_CHARGING:
            self.battery_level = min(100, self.battery_level + 5 * delta_time)  # Charge at 5% per second
            if self.battery_level >= 100:
                self.status = self.STATUS_IDLE
                return True
            return False
        
        # Don't proceed if not moving
        if self.status != self.STATUS_MOVING:
            return False
            
        # Check if current_lane is None before proceeding
        if self.current_lane is None:
            # Something went wrong, reset to idle state
            # But only if we're not waiting - waiting robots should stay waiting
            if self.status != self.STATUS_WAITING:
                self.status = self.STATUS_IDLE
                return True
            return False
            
        # Update progress along the current lane
        self.progress += speed * delta_time
        
        # If we've reached the end of the current lane
        if self.progress >= 1.0:
            # Move to the next vertex in the path
            self.position = self.current_lane[1]
            self.progress = 0.0
            
            # Remove the first vertex from the path as we've reached it
            if self.path and len(self.path) > 0:
                self.path.pop(0)
            
            # If there are more vertices in the path, continue moving
            if self.path and len(self.path) > 1:
                self.current_lane = [self.path[0], self.path[1]]
            # If we've reached the destination
            else:
                self.status = self.STATUS_TASK_COMPLETE
                self.current_lane = None
                self.waiting_time = 0
                
            return True
            
        return False
        
    def get_current_position(self, nav_graph):
        """
        Get the current coordinates of the robot.
        
        Args:
            nav_graph (NavGraph): The navigation graph.
            
        Returns:
            tuple: (x, y) coordinates of the robot.
        """
        if self.status != self.STATUS_MOVING or self.current_lane is None:
            return nav_graph.get_vertex_coordinates(self.position)
            
        # Interpolate between the two vertices of the current lane
        start_pos = nav_graph.get_vertex_coordinates(self.current_lane[0])
        end_pos = nav_graph.get_vertex_coordinates(self.current_lane[1])
        
        if start_pos is None or end_pos is None:
            return nav_graph.get_vertex_coordinates(self.position)
            
        # Use a slight easing function for smoother movement
        progress = self.progress
        if progress < 0.5:
            # Accelerate
            eased_progress = 2 * progress * progress
        else:
            # Decelerate
            eased_progress = -1 + (4 - 2 * progress) * progress
            
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * eased_progress
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * eased_progress
        
        return (x, y)
        
    def get_status_color(self):
        """
        Get the color representing the robot's current status.
        
        Returns:
            tuple: RGB color tuple.
        """
        return self.STATUS_COLORS.get(self.status, (255, 255, 255))
        
    def get_animation_offset(self):
        """
        Get the current animation offset for visual effects.
        
        Returns:
            float: Current animation offset value.
        """
        return math.sin(self.animation_offset) * 2  # Small bobbing effect 

    def start_charging(self):
        """
        Start charging the robot.
        
        Returns:
            bool: True if charging started, False otherwise.
        """
        if self.status != self.STATUS_CHARGING:
            self.status = self.STATUS_CHARGING
            return True
        return False 