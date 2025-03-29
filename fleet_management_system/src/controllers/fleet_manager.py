import random
from collections import deque
import time

class FleetManager:
    def __init__(self, nav_graph):
        """
        Initialize the fleet manager.
        
        Args:
            nav_graph: The navigation graph.
        """
        self.nav_graph = nav_graph
        self.robots = []
        self.reserved_lanes = {}  # Maps lane (from_vertex, to_vertex) to robot and timestamp
        self.waiting_robots = {}  # Maps vertex to list of robots waiting at that vertex
        
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
        # Track if any robot changed state
        any_state_changed = False
        
        # Update all robots
        for robot in self.robots:
            state_changed = robot.update(delta_time)
            
            # If the robot's state changed, update reservations
            if state_changed:
                self.update_lane_reservations(robot)
                any_state_changed = True
        
        # Only process waiting robots if a robot's state changed
        if any_state_changed:
            self.process_waiting_robots()
        
        # Clean up expired reservations (do this less frequently)
        self.clean_expired_reservations()

    def process_waiting_robots(self):
        """
        Process robots that are waiting at intersections.
        """
        # Only print if there are waiting robots that we actually process
        processed_any = False
        
        for vertex, waiting_list in list(self.waiting_robots.items()):
            if not waiting_list:
                del self.waiting_robots[vertex]
                continue
            
            # Process each waiting robot
            i = 0
            while i < len(waiting_list):
                robot = waiting_list[i]
                processed_any = True
                
                # If the robot is no longer waiting or not at this vertex, remove it
                if robot.status != robot.STATUS_WAITING or robot.position != vertex:
                    waiting_list.pop(i)
                    continue  # Don't increment i since we removed an element
                
                # Check if the robot still has a valid path
                if not robot.path or len(robot.path) < 2:
                    print(f"[WAITING] Robot {robot.id} has an invalid path, resetting to idle")
                    robot.status = robot.STATUS_IDLE
                    waiting_list.pop(i)
                    continue
                
                # First check if the original path is now clear
                path_clear = self.is_path_clear(robot.path, robot)
                
                if path_clear:
                    # If the original path is clear, let the robot move
                    next_lane = (robot.path[0], robot.path[1])
                    # Reserve the lane and let the robot move
                    self.reserve_lane(next_lane, robot)
                    
                    # Set up the current_lane for the robot
                    robot.current_lane = [robot.path[0], robot.path[1]]
                    
                    robot.status = robot.STATUS_MOVING
                    print(f"[WAITING] Robot {robot.id} original path is now clear, resuming movement from {vertex} to {robot.destination}")
                    waiting_list.pop(i)
                    continue  # Don't increment i since we removed an element
                
                # If original path is still blocked, try to find an alternative path
                print(f"[WAITING] Robot {robot.id} original path still blocked, looking for alternatives...")
                alt_path = self.find_alternative_path(robot.position, robot.destination, robot)
                
                if alt_path and alt_path != robot.path:
                    # Found a clear alternative path
                    robot.path = alt_path
                    next_lane = (robot.path[0], robot.path[1])
                    # Reserve the lane and let the robot move
                    self.reserve_lane(next_lane, robot)
                    
                    # Set up the current_lane for the robot
                    robot.current_lane = [robot.path[0], robot.path[1]]
                    
                    robot.status = robot.STATUS_MOVING
                    print(f"[WAITING] Robot {robot.id} found alternative path, resuming movement from {vertex} to {robot.destination}")
                    waiting_list.pop(i)
                    continue  # Don't increment i since we removed an element
                
                # If we still couldn't find a clear path, robot continues waiting
                i += 1  # Only increment if we didn't remove an element
        
        # Only print if we actually processed any waiting robots
        if processed_any:
            waiting_count = sum(len(robots) for robots in self.waiting_robots.values())
            print(f"[WAITING] Processed {waiting_count} waiting robots")

    def update_lane_reservations(self, robot):
        """
        Update lane reservations when a robot's state changes.
        
        Args:
            robot: The robot whose state changed.
        """
        # If the robot just completed a lane, release the reservation
        if robot.status == robot.STATUS_TASK_COMPLETE or robot.status == robot.STATUS_IDLE:
            lanes_released = False
            for lane, (res_robot, _) in list(self.reserved_lanes.items()):
                if res_robot == robot:
                    print(f"[LANES] Robot {robot.id} releasing lane {lane}")
                    del self.reserved_lanes[lane]
                    lanes_released = True
            
            # After releasing lanes, check if any waiting robots can now proceed
            if lanes_released:
                print(f"[LANES] Robot {robot.id} released lanes, checking waiting robots")
                self.process_waiting_robots()
            
        # If the robot is waiting, add it to the waiting list
        if robot.status == robot.STATUS_WAITING:
            if robot.position not in self.waiting_robots:
                self.waiting_robots[robot.position] = []
            if robot not in self.waiting_robots[robot.position]:
                self.waiting_robots[robot.position].append(robot)
                print(f"[WAITING] Added robot {robot.id} to waiting list at {robot.position}")

    def clean_expired_reservations(self):
        """
        Clean up expired lane reservations.
        """
        current_time = time.time()
        for lane, (robot, timestamp) in list(self.reserved_lanes.items()):
            # If the reservation is older than 60 seconds, it's probably stale
            if current_time - timestamp > 60:
                del self.reserved_lanes[lane]

    def is_lane_free(self, lane, requesting_robot=None):
        """
        Check if a lane is free for a robot to use.
        
        Args:
            lane (tuple): The lane to check, as (from_vertex, to_vertex).
            requesting_robot: The robot requesting to use the lane.
            
        Returns:
            bool: True if the lane is free, False otherwise.
        """
        if lane in self.reserved_lanes:
            reserved_robot, _ = self.reserved_lanes[lane]
            return reserved_robot == requesting_robot
        return True

    def reserve_lane(self, lane, robot):
        """
        Reserve a lane for a robot.
        
        Args:
            lane (tuple): The lane to reserve, as (from_vertex, to_vertex).
            robot: The robot reserving the lane.
        """
        self.reserved_lanes[lane] = (robot, time.time())

    def find_path(self, start, end):
        """
        Find a path from start to end using advanced path planning.
        
        Args:
            start (int): Index of the starting vertex.
            end (int): Index of the ending vertex.
            
        Returns:
            list: List of vertex indices representing the path, or None if no path is found.
        """
        # First try the shortest path
        shortest_path = self.nav_graph.find_shortest_path(start, end, consider_traffic=False)
        
        # If no path exists at all, return None
        if not shortest_path:
            print(f"No path exists from {start} to {end}")
            return None
        
        # If the shortest path is clear, return it
        if self.is_path_clear(shortest_path):
            return shortest_path
        
        print(f"Shortest path from {start} to {end} is blocked, looking for alternatives...")
        
        # Try to find alternative paths with increasing penalties for occupied lanes
        for penalty_multiplier in [5, 10, 20, 50]:
            alt_path = self.nav_graph.find_shortest_path(
                start, end, 
                consider_traffic=True, 
                fleet_manager=self,
                traffic_penalty_multiplier=penalty_multiplier
            )
            
            if alt_path and self.is_path_clear(alt_path):
                print(f"Found clear alternative path with penalty multiplier {penalty_multiplier}")
                return alt_path
        
        # If we still couldn't find a clear path, try to find k-shortest paths
        # This is a more exhaustive search for alternatives
        k_paths = self.nav_graph.find_k_shortest_paths(start, end, k=5)
        
        for i, path in enumerate(k_paths):
            if path != shortest_path and self.is_path_clear(path):
                print(f"Found clear path among k-shortest paths (path #{i+1})")
                return path
        
        # If we still couldn't find a clear path, return the original shortest path
        # (the robot will wait until it's clear)
        print(f"No clear alternative path found, robot will wait for shortest path to clear")
        return shortest_path

    def is_vertex_occupied(self, vertex, requesting_robot=None):
        """
        Check if a vertex is occupied by any robot other than the requesting robot.
        
        Args:
            vertex (int): The vertex to check.
            requesting_robot: The robot requesting to use the vertex (will be excluded from check).
            
        Returns:
            bool: True if the vertex is occupied, False otherwise.
        """
        for robot in self.robots:
            if robot != requesting_robot and robot.position == vertex:
                return True
        return False

    def is_path_clear(self, path, requesting_robot=None):
        """
        Check if a path is clear of other robots.
        
        Args:
            path (list): List of vertex indices representing the path.
            requesting_robot: The robot requesting to use the path.
            
        Returns:
            bool: True if the path is clear, False otherwise.
        """
        if not path or len(path) < 2:
            return True
        
        # Check each lane in the path
        for i in range(len(path) - 1):
            lane = (path[i], path[i+1])
            if not self.is_lane_free(lane, requesting_robot):
                return False
            
        # Check if any other robot is currently at any vertex in the path
        # (except the starting vertex)
        for vertex in path[1:]:
            if self.is_vertex_occupied(vertex, requesting_robot):
                return False
                
        return True

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
        
        # Check if destination is already occupied by another robot
        if self.is_vertex_occupied(destination, robot):
            print(f"Destination {destination} is already occupied by another robot")
            return False
        
        # Find a path from the robot's current position to the destination
        path = self.find_path(robot.position, destination)
        
        if path is None:
            print(f"No path found from {robot.position} to {destination}")
            return False
        
        # Always set the destination and path, regardless of whether the robot will wait or move
        robot.destination = destination
        robot.path = path
        
        # Check if the entire path is clear of other robots
        path_clear = self.is_path_clear(path, robot)
        
        if not path_clear:
            # Set the robot to waiting status
            robot.status = robot.STATUS_WAITING
            robot.current_lane = None  # Clear current lane since we're waiting
            
            # Add to waiting list
            if robot.position not in self.waiting_robots:
                self.waiting_robots[robot.position] = []
            if robot not in self.waiting_robots[robot.position]:
                self.waiting_robots[robot.position].append(robot)
            
            print(f"Robot {robot.id} is waiting at {robot.position} - path is not clear")
            return True
        
        # Check if the first lane is free
        if len(path) > 1:
            first_lane = (path[0], path[1])
            lane_free = self.is_lane_free(first_lane, robot)
            
            if not lane_free:
                # Set the robot to waiting status
                robot.status = robot.STATUS_WAITING
                robot.current_lane = None  # Clear current lane since we're waiting
                
                # Add to waiting list
                if robot.position not in self.waiting_robots:
                    self.waiting_robots[robot.position] = []
                if robot not in self.waiting_robots[robot.position]:
                    self.waiting_robots[robot.position].append(robot)
                
                print(f"Robot {robot.id} is waiting at {robot.position} for lane {first_lane} to become free")
                return True
            
            # Reserve the first lane
            self.reserve_lane(first_lane, robot)
        
        # Assign the task to the robot
        robot.assign_task(destination, path)
        print(f"Robot {robot.id} assigned path: {path}")
        
        # Get the names of the start and end vertices for better logging
        start_name = self.nav_graph.get_vertex_name(robot.position)
        end_name = self.nav_graph.get_vertex_name(destination)
        print(f"Task: {start_name} → {end_name}")
        
        # Check if any waiting robots can now proceed
        # This is important if this task assignment changes traffic patterns
        self.process_waiting_robots()
        
        return True
        
    def spawn_robot(self, position, color=None):
        """
        Spawn a new robot at the given position.
        
        Args:
            position (int): Index of the vertex where the robot should be spawned.
            color (tuple): RGB color tuple for the robot, or None for a random color.
            
        Returns:
            Robot: The newly spawned robot, or None if the position is already occupied.
        """
        from src.models.robot import Robot
        
        # Check if the position is already occupied
        if self.is_vertex_occupied(position):
            print(f"Cannot spawn robot: Position {position} is already occupied")
            return None
        
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

    def find_alternative_path(self, start, end, robot):
        """
        Find an alternative path that's clear of obstacles.
        
        Args:
            start (int): Starting vertex
            end (int): Destination vertex
            robot: The robot requesting the path
            
        Returns:
            list: A clear path if found, None otherwise
        """
        # Try to find alternative paths with increasing penalties for occupied lanes
        for penalty_multiplier in [5, 10, 20, 50]:
            alt_path = self.nav_graph.find_shortest_path(
                start, end, 
                consider_traffic=True, 
                fleet_manager=self,
                traffic_penalty_multiplier=penalty_multiplier
            )
            
            if alt_path and self.is_path_clear(alt_path, robot):
                print(f"[WAITING] Found clear alternative path with penalty multiplier {penalty_multiplier}")
                return alt_path
        
        # If we still couldn't find a clear path, try to find k-shortest paths
        # This is a more exhaustive search for alternatives
        k_paths = self.nav_graph.find_k_shortest_paths(start, end, k=5)
        
        for i, path in enumerate(k_paths):
            if self.is_path_clear(path, robot):
                print(f"[WAITING] Found clear path among k-shortest paths (path #{i+1})")
                return path
        
        # If we still couldn't find a clear path, return None
        print(f"[WAITING] No clear alternative path found, robot will continue waiting")
        return None