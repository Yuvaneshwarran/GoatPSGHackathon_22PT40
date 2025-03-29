import os
import time
import logging
import math

def setup_logging(log_file):
    """
    Set up logging to a file.
    
    Args:
        log_file (str): Path to the log file.
    """
    # Create the directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
def log_event(event_type, details):
    """
    Log an event.
    
    Args:
        event_type (str): Type of the event.
        details (dict): Details of the event.
    """
    logging.info(f"{event_type}: {details}")
    
def get_timestamp():
    """
    Get a formatted timestamp.
    
    Returns:
        str: Formatted timestamp.
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def format_path_for_logging(nav_graph, path):
    """
    Format a path for logging, using vertex names instead of indices.
    
    Args:
        nav_graph: The navigation graph.
        path (list): List of vertex indices.
        
    Returns:
        str: Formatted path string.
    """
    if not path:
        return "[]"
        
    path_names = [nav_graph.get_vertex_name(vertex) for vertex in path]
    return " → ".join(path_names)

def calculate_path_distance(nav_graph, path):
    """
    Calculate the total distance of a path.
    
    Args:
        nav_graph: The navigation graph.
        path (list): List of vertex indices.
        
    Returns:
        float: Total distance of the path.
    """
    if not path or len(path) < 2:
        return 0.0
        
    total_distance = 0.0
    for i in range(len(path) - 1):
        start_coords = nav_graph.get_vertex_coordinates(path[i])
        end_coords = nav_graph.get_vertex_coordinates(path[i+1])
        
        if start_coords and end_coords:
            dx = end_coords[0] - start_coords[0]
            dy = end_coords[1] - start_coords[1]
            distance = math.sqrt(dx*dx + dy*dy)
            total_distance += distance
            
    return total_distance

def generate_system_report(fleet_manager, nav_graph):
    """
    Generate a system report with statistics.
    
    Args:
        fleet_manager: The fleet manager.
        nav_graph: The navigation graph.
        
    Returns:
        dict: Report data.
    """
    # Count robots by status
    status_counts = {}
    for robot in fleet_manager.robots:
        status = robot.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Count waiting robots by vertex
    waiting_by_vertex = {}
    for vertex, robots in fleet_manager.waiting_robots.items():
        vertex_name = nav_graph.get_vertex_name(vertex)
        waiting_by_vertex[vertex_name] = len(robots)
    
    # Calculate average battery level
    total_battery = sum(robot.battery_level for robot in fleet_manager.robots)
    avg_battery = total_battery / len(fleet_manager.robots) if fleet_manager.robots else 0
    
    # Count robots at charging stations
    charging_stations = nav_graph.get_all_vertices_with_chargers()
    robots_at_chargers = sum(1 for robot in fleet_manager.robots if robot.position in charging_stations)
    
    return {
        "total_robots": len(fleet_manager.robots),
        "status_counts": status_counts,
        "waiting_by_vertex": waiting_by_vertex,
        "average_battery": avg_battery,
        "robots_at_chargers": robots_at_chargers,
        "total_chargers": len(charging_stations),
        "total_vertices": len(nav_graph.vertices),
        "total_lanes": len(nav_graph.lanes),
        "reserved_lanes": len(fleet_manager.reserved_lanes)
    } 