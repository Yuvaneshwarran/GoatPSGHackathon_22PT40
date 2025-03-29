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
    gui = FleetGUI(width=1024, height=768, title=f"Fleet Management System - {nav_graph.building_name}", fullscreen=True)
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
                if robot:
                    log_event("ROBOT_SPAWNED", {
                        "robot_id": robot.id,
                        "position": event_info['position'],
                        "vertex_name": nav_graph.get_vertex_name(event_info['position'])
                    })
                else:
                    gui.show_notification(f"Cannot spawn robot: Position already occupied", 3000)
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
        
        # Check for low battery robots and notify
        for robot in fleet_manager.robots:
            if robot.battery_level < 10 and robot.status != robot.STATUS_CHARGING:
                # Find nearest charging station
                chargers = nav_graph.get_all_vertices_with_chargers()
                if chargers and robot.status != robot.STATUS_WAITING:
                    nearest_charger = None
                    min_distance = float('inf')
                    
                    for charger in chargers:
                        path = fleet_manager.find_path(robot.position, charger)
                        if path and len(path) < min_distance:
                            min_distance = len(path)
                            nearest_charger = charger
                    
                    if nearest_charger is not None and robot.status != robot.STATUS_MOVING:
                        success = fleet_manager.assign_task(robot, nearest_charger)
                        if success:
                            gui.show_notification(f"Robot {robot.id} low battery - heading to charger", 3000)
                            log_event("LOW_BATTERY_CHARGING", {
                                "robot_id": robot.id,
                                "battery_level": robot.battery_level,
                                "charger": nav_graph.get_vertex_name(nearest_charger)
                            })
        
        # Check for robots at charging stations
        for robot in fleet_manager.robots:
            if nav_graph.is_charger(robot.position) and robot.status == robot.STATUS_TASK_COMPLETE:
                robot.start_charging()
                gui.show_notification(f"Robot {robot.id} arrived at charger and started charging", 3000)
                log_event("ROBOT_CHARGING", {
                    "robot_id": robot.id,
                    "position": robot.position,
                    "battery_level": robot.battery_level
                })
        
        # Check for traffic conflicts and log them
        for vertex, waiting_list in fleet_manager.waiting_robots.items():
            if len(waiting_list) > 1:
                robot_ids = [robot.id for robot in waiting_list]
                log_event("TRAFFIC_CONFLICT", {
                    "vertex": vertex,
                    "vertex_name": nav_graph.get_vertex_name(vertex),
                    "waiting_robots": robot_ids,
                    "queue_length": len(waiting_list)
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