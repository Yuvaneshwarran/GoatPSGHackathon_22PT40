import os
import sys
import time
import pygame
import argparse

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.nav_graph import NavGraph
from src.controllers.fleet_manager import FleetManager
from src.gui.fleet_gui import FleetGUI
from src.utils.helpers import setup_logging, log_event

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Fleet Management System')
    parser.add_argument('--graph', type=str, default='nav_graph_1.json',
                        help='Navigation graph file (default: nav_graph_1.json)')
    args = parser.parse_args()
    
    # Set up paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data')
    log_dir = os.path.join(project_root, 'logs')
    
    # Set up logging
    log_file = os.path.join(log_dir, 'fleet_logs.txt')
    setup_logging(log_file)
    
    # Initialize the navigation graph
    nav_graph_path = os.path.join(data_dir, args.graph)
    nav_graph = NavGraph(nav_graph_path)
    
    # Initialize the fleet manager
    fleet_manager = FleetManager(nav_graph)
    
    # Initialize the GUI
    gui = FleetGUI(width=1024, height=768, title=f"Fleet Management System - {nav_graph.building_name}")
    gui.set_nav_graph(nav_graph)
    gui.set_robots(fleet_manager.robots)
    
    # Show welcome notification
    gui.show_notification(f"Welcome to Fleet Management System - {nav_graph.building_name}", 5000)
    
    # Log startup
    log_event("SYSTEM_START", {
        "graph_file": args.graph,
        "building": nav_graph.building_name,
        "level": nav_graph.level_name,
        "vertices": len(nav_graph.vertices),
        "lanes": len(nav_graph.lanes)
    })
    
    # Main loop
    last_time = time.time()
    while True:
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time
        
        # Handle events
        event_info = gui.handle_events()
        if event_info:
            if event_info['type'] == 'spawn_robot':
                robot = fleet_manager.spawn_robot(event_info['position'])
                log_event("ROBOT_SPAWNED", {
                    "robot_id": robot.id,
                    "position": event_info['position'],
                    "vertex_name": nav_graph.get_vertex_name(event_info['position'])
                })
            elif event_info['type'] == 'select_robot':
                log_event("ROBOT_SELECTED", {
                    "robot_id": event_info['robot'].id,
                    "position": event_info['robot'].position,
                    "status": event_info['robot'].status
                })
            elif event_info['type'] == 'assign_task':
                success = fleet_manager.assign_task(event_info['robot'], event_info['destination'])
                if success:
                    log_event("TASK_ASSIGNED", {
                        "robot_id": event_info['robot'].id,
                        "from": event_info['robot'].position,
                        "to": event_info['destination'],
                        "destination_name": nav_graph.get_vertex_name(event_info['destination'])
                    })
                else:
                    gui.show_notification("Could not assign task - No valid path found", 3000)
                    log_event("TASK_ASSIGNMENT_FAILED", {
                        "robot_id": event_info['robot'].id,
                        "from": event_info['robot'].position,
                        "to": event_info['destination']
                    })
        
        # Update robots
        fleet_manager.update_robots(delta_time)
        
        # Update the GUI
        gui.set_robots(fleet_manager.robots)
        gui.draw()
        
        # Cap the frame rate
        pygame.time.Clock().tick(60)

if __name__ == "__main__":
    main() 