import json
import numpy as np

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