import json
import numpy as np
import math

class NavGraph:
    def __init__(self, graph_file):
        """
        Initialize the navigation graph from a JSON file.
        
        Args:
            graph_file (str): Path to the JSON file containing the navigation graph.
        """
        self.vertices = []  # List of vertices with coordinates and attributes
        self.lanes = []     # List of lanes connecting vertices
        self.building_name = ""
        self.level_name = ""
        self.load_graph(graph_file)
        
    def load_graph(self, graph_file):
        """
        Load the navigation graph from a JSON file.
        
        Args:
            graph_file (str): Path to the JSON file containing the navigation graph.
        """
        try:
            with open(graph_file, 'r') as f:
                data = json.load(f)
                
            # Extract building name
            self.building_name = data.get('building_name', "")
            
            # Extract the first level from the levels dictionary
            levels = data.get('levels', {})
            if not levels:
                print("No levels found in the navigation graph.")
                return
                
            # Get the first level name and data
            self.level_name = next(iter(levels))
            level_data = levels[self.level_name]
            
            # Extract vertices and lanes from the level data
            self.vertices = level_data.get('vertices', [])
            self.lanes = level_data.get('lanes', [])
            
            print(f"Loaded navigation graph for building '{self.building_name}', level '{self.level_name}'")
            print(f"Found {len(self.vertices)} vertices and {len(self.lanes)} lanes.")
        except Exception as e:
            print(f"Error loading navigation graph: {e}")
            # Initialize with empty data if loading fails
            self.vertices = []
            self.lanes = []
    
    def get_vertex_coordinates(self, vertex_index):
        """
        Get the coordinates of a vertex.
        
        Args:
            vertex_index (int): Index of the vertex.
            
        Returns:
            tuple: (x, y) coordinates of the vertex.
        """
        if 0 <= vertex_index < len(self.vertices):
            vertex = self.vertices[vertex_index]
            return (vertex[0], vertex[1])
        return None
    
    def get_vertex_name(self, vertex_index):
        """
        Get the name of a vertex.
        
        Args:
            vertex_index (int): Index of the vertex.
            
        Returns:
            str: Name of the vertex.
        """
        if 0 <= vertex_index < len(self.vertices):
            vertex = self.vertices[vertex_index]
            if len(vertex) > 2 and isinstance(vertex[2], dict) and 'name' in vertex[2]:
                name = vertex[2]['name']
                return name if name else f"V{vertex_index}"
        return f"V{vertex_index}"
    
    def is_charger(self, vertex_index):
        """
        Check if a vertex is a charging station.
        
        Args:
            vertex_index (int): Index of the vertex.
            
        Returns:
            bool: True if the vertex is a charging station, False otherwise.
        """
        if 0 <= vertex_index < len(self.vertices):
            vertex = self.vertices[vertex_index]
            if len(vertex) > 2 and isinstance(vertex[2], dict) and 'is_charger' in vertex[2]:
                return vertex[2]['is_charger']
        return False
    
    def get_connected_vertices(self, vertex_index):
        """
        Get all vertices connected to a given vertex.
        
        Args:
            vertex_index (int): Index of the vertex.
            
        Returns:
            list: List of indices of connected vertices.
        """
        connected = []
        for lane in self.lanes:
            if lane[0] == vertex_index:
                connected.append(lane[1])
        return connected
    
    def get_lane_between(self, vertex1, vertex2):
        """
        Check if there is a lane between two vertices and return its attributes.
        
        Args:
            vertex1 (int): Index of the first vertex.
            vertex2 (int): Index of the second vertex.
            
        Returns:
            dict or None: Lane attributes if there is a lane, None otherwise.
        """
        for lane in self.lanes:
            if lane[0] == vertex1 and lane[1] == vertex2:
                if len(lane) > 2:
                    return lane[2]
                return {}
        return None
    
    def get_all_vertices_with_chargers(self):
        """
        Get all vertices that are charging stations.
        
        Returns:
            list: List of indices of vertices that are charging stations.
        """
        chargers = []
        for i in range(len(self.vertices)):
            if self.is_charger(i):
                chargers.append(i)
        return chargers
    
    def get_all_vertices_with_names(self):
        """
        Get all vertices that have names.
        
        Returns:
            dict: Dictionary mapping vertex indices to their names.
        """
        named_vertices = {}
        for i in range(len(self.vertices)):
            name = self.get_vertex_name(i)
            if name != f"V{i}":  # If it's not the default name
                named_vertices[i] = name
        return named_vertices
    
    def get_lane_distance(self, from_vertex, to_vertex):
        """
        Get the distance between two connected vertices.
        
        Args:
            from_vertex (int): Index of the starting vertex.
            to_vertex (int): Index of the ending vertex.
            
        Returns:
            float: Distance between the vertices, or None if they are not connected.
        """
        # Check if there is a lane between the vertices
        lane_attrs = self.get_lane_between(from_vertex, to_vertex)
        if lane_attrs is None:
            return None
        
        # If the lane has a predefined distance, use it
        if isinstance(lane_attrs, dict) and 'distance' in lane_attrs:
            return lane_attrs['distance']
        
        # Otherwise, calculate the Euclidean distance
        from_coords = self.get_vertex_coordinates(from_vertex)
        to_coords = self.get_vertex_coordinates(to_vertex)
        
        if from_coords is None or to_coords is None:
            return None
        
        dx = to_coords[0] - from_coords[0]
        dy = to_coords[1] - from_coords[1]
        return math.sqrt(dx*dx + dy*dy)
    
    def get_lane_travel_time(self, from_vertex, to_vertex, speed=1.0):
        """
        Get the estimated travel time between two connected vertices.
        
        Args:
            from_vertex (int): Index of the starting vertex.
            to_vertex (int): Index of the ending vertex.
            speed (float): Speed factor.
            
        Returns:
            float: Estimated travel time, or None if the vertices are not connected.
        """
        distance = self.get_lane_distance(from_vertex, to_vertex)
        if distance is None:
            return None
        
        # Check if the lane has a speed modifier
        lane_attrs = self.get_lane_between(from_vertex, to_vertex)
        speed_modifier = 1.0
        
        if isinstance(lane_attrs, dict) and 'speed_modifier' in lane_attrs:
            speed_modifier = lane_attrs['speed_modifier']
        
        return distance / (speed * speed_modifier)
    
    def find_shortest_path(self, start, end, consider_traffic=True, fleet_manager=None, traffic_penalty_multiplier=5.0):
        """
        Find the shortest path from start to end using Dijkstra's algorithm.
        
        Args:
            start (int): Index of the starting vertex.
            end (int): Index of the ending vertex.
            consider_traffic (bool): Whether to consider traffic when planning.
            fleet_manager: The fleet manager, needed if consider_traffic is True.
            traffic_penalty_multiplier (float): Multiplier for the penalty applied to occupied lanes.
            
        Returns:
            list: List of vertex indices representing the path, or None if no path is found.
        """
        if start == end:
            return [start]
        
        # Initialize distances with infinity
        distances = {vertex: float('infinity') for vertex in range(len(self.vertices))}
        distances[start] = 0
        
        # Initialize previous vertices for path reconstruction
        previous = {vertex: None for vertex in range(len(self.vertices))}
        
        # Initialize unvisited set with all vertices
        unvisited = set(range(len(self.vertices)))
        
        while unvisited:
            # Find the unvisited vertex with the smallest distance
            current = min(unvisited, key=lambda vertex: distances[vertex])
            
            # If we've reached the destination or there's no path
            if current == end or distances[current] == float('infinity'):
                break
            
            unvisited.remove(current)
            
            # Check all neighbors of the current vertex
            for neighbor in self.get_connected_vertices(current):
                # Calculate the distance to the neighbor
                distance = self.get_lane_distance(current, neighbor)
                
                if distance is None:
                    continue
                
                # If considering traffic, add a penalty for lanes with traffic
                if consider_traffic and fleet_manager:
                    lane = (current, neighbor)
                    if not fleet_manager.is_lane_free(lane):
                        # Add a significant penalty for occupied lanes
                        distance *= traffic_penalty_multiplier
                
                # Calculate the new distance
                new_distance = distances[current] + distance
                
                # If this path is shorter, update the distance and previous vertex
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current
        
        # If there's no path to the destination
        if previous[end] is None:
            return None
        
        # Reconstruct the path
        path = []
        current = end
        
        while current is not None:
            path.append(current)
            current = previous[current]
        
        # Reverse the path to get it from start to end
        return path[::-1]

    def find_k_shortest_paths(self, start, end, k=3):
        """
        Find k shortest paths from start to end using Yen's algorithm.
        
        Args:
            start (int): Index of the starting vertex.
            end (int): Index of the ending vertex.
            k (int): Number of paths to find.
            
        Returns:
            list: List of paths, where each path is a list of vertex indices.
        """
        if start == end:
            return [[start]]
        
        # Find the shortest path first
        shortest_path = self.find_shortest_path(start, end)
        if not shortest_path:
            return []
        
        # Initialize the list of k shortest paths
        A = [shortest_path]
        # Initialize the list of potential k shortest paths
        B = []
        
        # Find k-1 more paths
        for i in range(1, k):
            # The previous k-shortest path
            prev_path = A[-1]
            
            # For each node in the previous path except the last one
            for j in range(len(prev_path) - 1):
                # The spur node is the j-th node in the previous path
                spur_node = prev_path[j]
                # The root path is the path from start to the spur node
                root_path = prev_path[:j+1]
                
                # Remove the links that are part of the previous shortest paths with the same root path
                removed_edges = []
                for path in A:
                    if len(path) > j and path[:j+1] == root_path:
                        if j+1 < len(path):
                            edge = (path[j], path[j+1])
                            if edge not in removed_edges:
                                removed_edges.append(edge)
                
                # Remove the root path nodes from the graph except the spur node
                for node in root_path:
                    if node != spur_node:
                        # Temporarily remove this node by removing all its edges
                        for edge in self.get_edges_with_node(node):
                            if edge not in removed_edges:
                                removed_edges.append(edge)
                
                # Calculate the spur path from the spur node to the end
                # We need to temporarily remove edges from the graph
                original_lanes = self.lanes.copy()
                self.lanes = [lane for lane in self.lanes if (lane[0], lane[1]) not in removed_edges]
                
                spur_path = self.find_shortest_path(spur_node, end)
                
                # Restore the graph
                self.lanes = original_lanes
                
                # If a spur path was found, concatenate with root path to form a complete path
                if spur_path:
                    total_path = root_path[:-1] + spur_path  # Avoid duplicating the spur node
                    if total_path not in B and total_path not in A:
                        # Calculate the path cost for sorting
                        path_cost = self.calculate_path_cost(total_path)
                        B.append((total_path, path_cost))
            
            if not B:
                # No more paths can be found
                break
            
            # Sort the potential k-shortest paths by cost
            B.sort(key=lambda x: x[1])
            
            # Add the lowest cost path to the k-shortest paths
            A.append(B[0][0])
            B.pop(0)
        
        return A

    def get_edges_with_node(self, node):
        """
        Get all edges that include the given node.
        
        Args:
            node (int): The node index.
            
        Returns:
            list: List of edges as (from_node, to_node) tuples.
        """
        edges = []
        for lane in self.lanes:
            if lane[0] == node or lane[1] == node:
                edges.append((lane[0], lane[1]))
        return edges

    def calculate_path_cost(self, path):
        """
        Calculate the total cost of a path.
        
        Args:
            path (list): List of vertex indices representing the path.
            
        Returns:
            float: Total cost of the path.
        """
        if not path or len(path) < 2:
            return 0
        
        total_cost = 0
        for i in range(len(path) - 1):
            distance = self.get_lane_distance(path[i], path[i+1])
            if distance is None:
                return float('inf')  # Invalid path
            total_cost += distance
        
        return total_cost