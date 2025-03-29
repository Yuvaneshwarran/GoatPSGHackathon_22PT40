import random
from collections import deque

class FleetManager:
    def __init__(self, nav_graph):
        """
        Initialize the fleet manager.
        
        Args:
            nav_graph: The navigation graph.
        """
        self.nav_graph = nav_graph
        self.robots = []
        
    def add_robot(self, robot):
        """
        Add a robot to the fleet.
        
        Args:
            robot: The robot to add.
        """
        self.robots.append(robot)
        
    def remove_robot(self, robot):
        """
        Remove a robot from the fleet.
        
        Args:
            robot: The robot to remove.
        """
        if robot in self.robots:
            self.robots.remove(robot)
            
    def update_robots(self, delta_time):
        """
        Update all robots in the fleet.
        
        Args:
            delta_time (float): Time elapsed since the last update in seconds.
        """
        for robot in self.robots:
            robot.update(delta_time)
            
    def find_path(self, start, end):
        """
        Find a path from start to end using breadth-first search.
        
        Args:
            start (int): Index of the starting vertex.
            end (int): Index of the ending vertex.
            
        Returns:
            list: List of vertex indices representing the path, or None if no path is found.
        """
        if start == end:
            return [start]
            
        # Use breadth-first search to find the shortest path
        queue = deque([(start, [start])])
        visited = set([start])
        
        while queue:
            vertex, path = queue.popleft()
            
            # Get all connected vertices
            connected = self.nav_graph.get_connected_vertices(vertex)
            
            for next_vertex in connected:
                if next_vertex == end:
                    # Found the destination
                    return path + [next_vertex]
                    
                if next_vertex not in visited:
                    visited.add(next_vertex)
                    queue.append((next_vertex, path + [next_vertex]))
                    
        # No path found
        return None
        
    def assign_task(self, robot, destination):
        """
        Assign a navigation task to a robot.
        
        Args:
            robot: The robot to assign the task to.
            destination (int): Index of the destination vertex.
            
        Returns:
            bool: True if the task was assigned successfully, False otherwise.
        """
        # If robot is already at the destination
        if robot.position == destination:
            print(f"Robot {robot.id} is already at the destination")
            return False
            
        # Find a path from the robot's current position to the destination
        path = self.find_path(robot.position, destination)
        
        if path is None:
            print(f"No path found from {robot.position} to {destination}")
            return False
            
        # Assign the task to the robot
                # Assign the task to the robot
        robot.assign_task(destination, path)
        print(f"Robot {robot.id} assigned path: {path}")
        
        # Get the names of the start and end vertices for better logging
        start_name = self.nav_graph.get_vertex_name(robot.position)
        end_name = self.nav_graph.get_vertex_name(destination)
        print(f"Task: {start_name} → {end_name}")
        
        return True
        
    def spawn_robot(self, position, color=None):
        """
        Spawn a new robot at the given position.
        
        Args:
            position (int): Index of the vertex where the robot should be spawned.
            color (tuple): RGB color tuple for the robot, or None for a random color.
            
        Returns:
            Robot: The newly spawned robot.
        """
        from src.models.robot import Robot
        
        # Generate a random color if none is provided
        if color is None:
            # Generate more vibrant colors for better visibility
            color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )
            
        # Create a new robot
        robot = Robot(position, color)
        vertex_name = self.nav_graph.get_vertex_name(position)
        print(f"Spawned robot {robot.id} at position {position} ({vertex_name})")
        
        # Add the robot to the fleet
        self.add_robot(robot)
        
        return robot