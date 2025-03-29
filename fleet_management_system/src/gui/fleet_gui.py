import pygame
import sys
import math

class FleetGUI:
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (200, 200, 200)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    LIGHT_BLUE = (173, 216, 230)
    
    # Vertex types
    VERTEX_NORMAL = 0
    VERTEX_CHARGER = 1
    VERTEX_NAMED = 2
    
    def __init__(self, width=1024, height=768, title="Fleet Management System"):
        """
        Initialize the GUI.
        
        Args:
            width (int): Width of the window.
            height (int): Height of the window.
            title (str): Title of the window.
        """
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        self.title_font = pygame.font.SysFont(None, 32)
        self.bold_font = pygame.font.SysFont(None, 24, bold=True)
        
        # Visualization parameters
        self.vertex_radius = 15
        self.robot_radius = 12
        self.scale_factor = 20  # Scale factor for converting coordinates
        self.offset_x = width // 2
        self.offset_y = height // 2
        
        # Store references to the navigation graph and robots
        self.nav_graph = None
        self.robots = []
        
        # Interaction state
        self.selected_robot = None
        self.hover_vertex = None
        self.hover_robot = None
        
        # Calculate bounds for auto-scaling
        self.min_x = float('inf')
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')
        
        # UI elements
        self.show_help = True
        self.notification = None
        self.notification_time = 0
        
        # Load background image
        try:
            self.background = pygame.Surface((width, height))
            self.background.fill((240, 248, 255))  # Light blue background
            
            # Create a grid pattern
            for x in range(0, width, 20):
                pygame.draw.line(self.background, (220, 220, 220), (x, 0), (x, height))
            for y in range(0, height, 20):
                pygame.draw.line(self.background, (220, 220, 220), (0, y), (width, y))
                
        except Exception as e:
            print(f"Could not load background: {e}")
            self.background = None
        
    def set_nav_graph(self, nav_graph):
        """
        Set the navigation graph to be visualized.
        
        Args:
            nav_graph: The navigation graph object.
        """
        self.nav_graph = nav_graph
        
        # Calculate bounds for auto-scaling
        if nav_graph and nav_graph.vertices:
            for vertex in nav_graph.vertices:
                x, y = vertex[0], vertex[1]
                self.min_x = min(self.min_x, x)
                self.max_x = max(self.max_x, x)
                self.min_y = min(self.min_y, y)
                self.max_y = max(self.max_y, y)
            
            # Calculate scale factor and offset
            width_range = self.max_x - self.min_x
            height_range = self.max_y - self.min_y
            
            if width_range > 0 and height_range > 0:
                # Leave some margin
                margin = 0.2
                width_scale = (1 - 2 * margin) * self.width / width_range
                height_scale = (1 - 2 * margin) * self.height / height_range
                
                # Use the smaller scale to ensure everything fits
                self.scale_factor = min(width_scale, height_scale)
                
                # Calculate center of the graph
                center_x = (self.min_x + self.max_x) / 2
                center_y = (self.min_y + self.max_y) / 2
                
                # Set offset to center the graph
                self.offset_x = self.width / 2 - center_x * self.scale_factor
                self.offset_y = self.height / 2 + center_y * self.scale_factor  # Y is inverted
        
    def set_robots(self, robots):
        """
        Set the robots to be visualized.
        
        Args:
            robots (list): List of robot objects.
        """
        self.robots = robots
        
    def world_to_screen(self, x, y):
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            x (float): X coordinate in world space.
            y (float): Y coordinate in world space.
            
        Returns:
            tuple: (x, y) coordinates in screen space.
        """
        screen_x = int(x * self.scale_factor + self.offset_x)
        screen_y = int(-y * self.scale_factor + self.offset_y)  # Y is inverted in screen space
        return (screen_x, screen_y)
        
    def screen_to_world(self, screen_x, screen_y):
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x (int): X coordinate in screen space.
            screen_y (int): Y coordinate in screen space.
            
        Returns:
            tuple: (x, y) coordinates in world space.
        """
        x = (screen_x - self.offset_x) / self.scale_factor
        y = -(screen_y - self.offset_y) / self.scale_factor  # Y is inverted in screen space
        return (x, y)
        
    def draw_vertex(self, vertex_index, highlight=False):
        """
        Draw a vertex on the screen.
        
        Args:
            vertex_index (int): Index of the vertex to draw.
            highlight (bool): Whether to highlight the vertex.
        """
        if self.nav_graph is None:
            return
            
        coords = self.nav_graph.get_vertex_coordinates(vertex_index)
        if coords is None:
            return
            
        screen_coords = self.world_to_screen(coords[0], coords[1])
        
        # Determine vertex type and color
        vertex_type = self.VERTEX_NORMAL
        if self.nav_graph.is_charger(vertex_index):
            vertex_type = self.VERTEX_CHARGER
        elif self.nav_graph.get_vertex_name(vertex_index) != f"V{vertex_index}":
            vertex_type = self.VERTEX_NAMED
            
        color = self.GREEN if vertex_type == self.VERTEX_CHARGER else (
                self.ORANGE if vertex_type == self.VERTEX_NAMED else self.BLUE)
        
        # Highlight if needed
        if highlight:
            # Pulsating highlight effect
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5  # 0 to 1
            highlight_radius = self.vertex_radius + 3 + int(pulse * 2)
            pygame.draw.circle(self.screen, self.YELLOW, screen_coords, highlight_radius)
            
            # If a robot is selected, show a line to indicate potential path
            if self.selected_robot:
                robot_pos = self.selected_robot.get_current_position(self.nav_graph)
                if robot_pos:
                    robot_screen_pos = self.world_to_screen(robot_pos[0], robot_pos[1])
                    # Draw dashed line
                    dash_length = 5
                    dash_gap = 3
                    dx = screen_coords[0] - robot_screen_pos[0]
                    dy = screen_coords[1] - robot_screen_pos[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance > 0:
                        dx, dy = dx/distance, dy/distance
                        pos = robot_screen_pos
                        dash_pos = 0
                        while dash_pos < distance:
                            start_pos = (int(robot_screen_pos[0] + dx * dash_pos), 
                                        int(robot_screen_pos[1] + dy * dash_pos))
                            end_pos = (int(robot_screen_pos[0] + dx * min(dash_pos + dash_length, distance)), 
                                      int(robot_screen_pos[1] + dy * min(dash_pos + dash_length, distance)))
                            pygame.draw.line(self.screen, self.YELLOW, start_pos, end_pos, 2)
                            dash_pos += dash_length + dash_gap
        
        # Draw the vertex
        pygame.draw.circle(self.screen, color, screen_coords, self.vertex_radius)
        pygame.draw.circle(self.screen, self.BLACK, screen_coords, self.vertex_radius, 2)
        
        # Draw the vertex name
        name = self.nav_graph.get_vertex_name(vertex_index)
        text = self.small_font.render(name, True, self.BLACK)
        text_rect = text.get_rect(center=screen_coords)
        self.screen.blit(text, text_rect)
        
    def draw_lane(self, from_vertex, to_vertex):
        """
        Draw a lane between two vertices.
        
        Args:
            from_vertex (int): Index of the starting vertex.
            to_vertex (int): Index of the ending vertex.
        """
        if self.nav_graph is None:
            return
            
        from_coords = self.nav_graph.get_vertex_coordinates(from_vertex)
        to_coords = self.nav_graph.get_vertex_coordinates(to_vertex)
        
        if from_coords is None or to_coords is None:
            return
            
        from_screen = self.world_to_screen(from_coords[0], from_coords[1])
        to_screen = self.world_to_screen(to_coords[0], to_coords[1])
        
        # Calculate the direction vector
        dx = to_screen[0] - from_screen[0]
        dy = to_screen[1] - from_screen[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # Normalize
            dx, dy = dx/length, dy/length
            
            # Adjust start and end points to be outside the vertices
            start_x = from_screen[0] + dx * self.vertex_radius
            start_y = from_screen[1] + dy * self.vertex_radius
            end_x = to_screen[0] - dx * self.vertex_radius
            end_y = to_screen[1] - dy * self.vertex_radius
            
            # Draw the lane
            pygame.draw.line(self.screen, self.BLACK, (start_x, start_y), (end_x, end_y), 2)
            
            # Draw an arrow to indicate direction
            arrow_length = 10
            arrow_width = 6
            
            # Calculate arrow position (3/4 of the way)
            arrow_pos_x = start_x + (end_x - start_x) * 0.75
            arrow_pos_y = start_y + (end_y - start_y) * 0.75
            
            # Calculate arrow points
            angle = math.atan2(dy, dx)
            arrow_p1 = (
                arrow_pos_x - arrow_length * math.cos(angle - math.pi/6),
                arrow_pos_y - arrow_length * math.sin(angle - math.pi/6)
            )
            arrow_p2 = (arrow_pos_x, arrow_pos_y)
            arrow_p3 = (
                arrow_pos_x - arrow_length * math.cos(angle + math.pi/6),
                arrow_pos_y - arrow_length * math.sin(angle + math.pi/6)
            )
            
            # Draw the arrow
            pygame.draw.polygon(self.screen, self.BLACK, [arrow_p1, arrow_p2, arrow_p3])
        
    def draw_robot(self, robot):
        """
        Draw a robot on the screen.
        
        Args:
            robot: The robot object to draw.
        """
        if self.nav_graph is None:
            return
            
        # Get the current position of the robot
        pos = robot.get_current_position(self.nav_graph)
        if pos is None:
            return
            
        screen_pos = self.world_to_screen(pos[0], pos[1])
        
        # Determine if this robot is being hovered over
        is_hover = (self.hover_robot == robot)
        
        # Determine if this robot is selected
        is_selected = (self.selected_robot == robot)
        
        # Draw selection/hover indicators
        if is_selected:
            # Pulsating selection ring
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5  # 0 to 1
            select_radius = self.robot_radius + 5 + int(pulse * 2)
            pygame.draw.circle(self.screen, self.YELLOW, screen_pos, select_radius, 2)
        elif is_hover:
            # Hover indicator
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.robot_radius + 4, 2)
        
        # Draw the robot with a gradient effect
        for i in range(self.robot_radius, 0, -2):
            # Lighten the color as we get to the center
            factor = 0.7 + 0.3 * (1 - i / self.robot_radius)
            color = (
                min(255, int(robot.color[0] * factor)),
                min(255, int(robot.color[1] * factor)),
                min(255, int(robot.color[2] * factor))
            )
            pygame.draw.circle(self.screen, color, screen_pos, i)
        
        # Draw the robot outline
        pygame.draw.circle(self.screen, self.BLACK, screen_pos, self.robot_radius, 2)
        
        # Draw the robot ID
        text = self.small_font.render(robot.id, True, self.BLACK)
        text_rect = text.get_rect(center=(screen_pos[0], screen_pos[1] - self.robot_radius - 10))
        self.screen.blit(text, text_rect)
        
        # Draw the robot status
        status_colors = {
            "idle": self.GRAY,
            "moving": self.GREEN,
            "waiting": self.YELLOW,
            "charging": self.BLUE,
            "task_complete": self.GREEN
        }
        status_color = status_colors.get(robot.status, self.WHITE)
        
        # Draw a small status indicator
        pygame.draw.circle(self.screen, status_color, 
                          (screen_pos[0] + self.robot_radius + 5, screen_pos[1] - self.robot_radius - 5), 5)
        
        # If the robot is moving, draw its path
        if robot.status == "moving" and robot.path and len(robot.path) > 1:
            # Draw the remaining path
            path_points = []
            for i in range(robot.path.index(robot.position), len(robot.path)):
                vertex_pos = self.nav_graph.get_vertex_coordinates(robot.path[i])
                if vertex_pos:
                    path_points.append(self.world_to_screen(vertex_pos[0], vertex_pos[1]))
            
            if len(path_points) > 1:
                # Draw dashed line for the path
                pygame.draw.lines(self.screen, robot.color, False, path_points, 2)
                
                # Draw destination marker
                dest_pos = path_points[-1]
                pygame.draw.circle(self.screen, robot.color, dest_pos, 5, 2)
        
    def find_vertex_at_position(self, screen_x, screen_y):
        """
        Find the vertex at the given screen position.
        
        Args:
            screen_x (int): X coordinate in screen space.
            screen_y (int): Y coordinate in screen space.
            
        Returns:
            int: Index of the vertex at the position, or None if no vertex is found.
        """
        if self.nav_graph is None:
            return None
            
        for i in range(len(self.nav_graph.vertices)):
            coords = self.nav_graph.get_vertex_coordinates(i)
            if coords is None:
                continue
                
            screen_coords = self.world_to_screen(coords[0], coords[1])
            distance = math.sqrt((screen_coords[0] - screen_x) ** 2 + (screen_coords[1] - screen_y) ** 2)
            
            if distance <= self.vertex_radius:
                return i
                
        return None
        
    def find_robot_at_position(self, screen_x, screen_y):
        """
        Find the robot at the given screen position.
        
        Args:
            screen_x (int): X coordinate in screen space.
            screen_y (int): Y coordinate in screen space.
            
        Returns:
            Robot: The robot at the position, or None if no robot is found.
        """
        if self.nav_graph is None:
            return None
            
        for robot in self.robots:
            pos = robot.get_current_position(self.nav_graph)
            if pos is None:
                continue
                
            screen_pos = self.world_to_screen(pos[0], pos[1])
            distance = math.sqrt((screen_pos[0] - screen_x) ** 2 + (screen_pos[1] - screen_y) ** 2)
            
            if distance <= self.robot_radius:
                return robot
                
        return None
    
    def show_notification(self, message, duration=3000):
        """
        Show a notification message.
        
        Args:
            message (str): The message to display.
            duration (int): Duration in milliseconds to show the message.
        """
        self.notification = message
        self.notification_time = pygame.time.get_ticks() + duration
    
    def draw_info_panel(self):
        """
        Draw an information panel with instructions and status.
        """
        # Draw a semi-transparent background
        info_surface = pygame.Surface((300, 200))
        info_surface.set_alpha(220)
        info_surface.fill(self.LIGHT_BLUE)
        self.screen.blit(info_surface, (10, 10))
        
        # Draw border
        pygame.draw.rect(self.screen, self.BLACK, (10, 10, 300, 200), 2)
        
        # Draw title
        title_text = self.title_font.render("Fleet Management System", True, self.BLACK)
        self.screen.blit(title_text, (20, 15))
        
        # Draw building and level info
        if self.nav_graph:
            building_text = self.font.render(f"Building: {self.nav_graph.building_name}", True, self.BLACK)
            level_text = self.font.render(f"Level: {self.nav_graph.level_name}", True, self.BLACK)
            self.screen.blit(building_text, (20, 50))
            self.screen.blit(level_text, (20, 75))
        
        # Draw instructions
        instructions = [
            "• Click on vertex: Spawn robot",
            "• Click on robot: Select robot (yellow outline)",
            "• Click on vertex after selecting: Assign task",
            "• Green vertices: Charging stations",
            "• Orange vertices: Named locations"
        ]
        
        y_pos = 100
        for instruction in instructions:
            text = self.small_font.render(instruction, True, self.BLACK)
            self.screen.blit(text, (20, y_pos))
            y_pos += 20
            
        # Draw robot count
        robots_text = self.font.render(f"Robots: {len(self.robots)}", True, self.BLACK)
        self.screen.blit(robots_text, (20, 180))
        
        # Draw selected robot info
        if self.selected_robot:
            # Draw a semi-transparent background for robot info
            robot_info_surface = pygame.Surface((300, 100))
            robot_info_surface.set_alpha(220)
            robot_info_surface.fill(self.LIGHT_BLUE)
            self.screen.blit(robot_info_surface, (10, 220))
            
            # Draw border
            pygame.draw.rect(self.screen, self.BLACK, (10, 220, 300, 100), 2)
            
            # Draw robot info
            robot_title = self.bold_font.render(f"Selected Robot: {self.selected_robot.id}", True, self.BLACK)
            self.screen.blit(robot_title, (20, 225))
            
            status_text = self.font.render(f"Status: {self.selected_robot.status}", True, self.BLACK)
            self.screen.blit(status_text, (20, 250))
            
            position_name = self.nav_graph.get_vertex_name(self.selected_robot.position)
            position_text = self.font.render(f"Position: {position_name}", True, self.BLACK)
            self.screen.blit(position_text, (20, 275))
            
            if self.selected_robot.destination is not None:
                dest_name = self.nav_graph.get_vertex_name(self.selected_robot.destination)
                dest_text = self.font.render(f"Destination: {dest_name}", True, self.BLACK)
                self.screen.blit(dest_text, (20, 300))
    
    def draw_notification(self):
        """
        Draw any active notification messages.
        """
        if self.notification and pygame.time.get_ticks() < self.notification_time:
            # Draw a semi-transparent background
            text = self.bold_font.render(self.notification, True, self.BLACK)
            text_width = text.get_rect().width
            text_height = text.get_rect().height
            
            padding = 10
            notification_surface = pygame.Surface((text_width + padding*2, text_height + padding*2))
            notification_surface.set_alpha(220)
            notification_surface.fill(self.YELLOW)
            
            # Position at the bottom center of the screen
            x = (self.width - text_width - padding*2) // 2
            y = self.height - text_height - padding*2 - 20
            
            self.screen.blit(notification_surface, (x, y))
            pygame.draw.rect(self.screen, self.BLACK, (x, y, text_width + padding*2, text_height + padding*2), 2)
            self.screen.blit(text, (x + padding, y + padding))
        
    def draw(self):
        """
        Draw the entire scene.
        """
        # Fill the background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(self.WHITE)
        
        if self.nav_graph is not None:
            # Draw all lanes
            for lane in self.nav_graph.lanes:
                self.draw_lane(lane[0], lane[1])
                
            # Draw all vertices
            for i in range(len(self.nav_graph.vertices)):
                self.draw_vertex(i, highlight=(i == self.hover_vertex))
                
        # Draw all robots
        for robot in self.robots:
            self.draw_robot(robot)
            
        # Draw information panel
        if self.show_help:
            self.draw_info_panel()
            
        # Draw any active notifications
        self.draw_notification()
            
        # Update the display
        pygame.display.flip()
        
    def handle_events(self):
        """
        Handle pygame events.
        
        Returns:
            dict: Event information if an event occurred, None otherwise.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                # Toggle help panel with H key
                if event.key == pygame.K_h:
                    self.show_help = not self.show_help
                
            elif event.type == pygame.MOUSEMOTION:
                # Update hover states
                self.hover_vertex = self.find_vertex_at_position(event.pos[0], event.pos[1])
                self.hover_robot = self.find_robot_at_position(event.pos[0], event.pos[1])
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if clicked on a robot
                    robot = self.find_robot_at_position(event.pos[0], event.pos[1])
                    if robot is not None:
                        # If clicking on the already selected robot, deselect it
                        if self.selected_robot == robot:
                            self.selected_robot = None
                            self.show_notification("Robot deselected")
                        else:
                            self.selected_robot = robot
                            self.show_notification(f"Robot {robot.id} selected - Click a destination")
                        return {
                            'type': 'select_robot',
                            'robot': robot
                        }
                    
                    # Check if clicked on a vertex
                    vertex = self.find_vertex_at_position(event.pos[0], event.pos[1])
                    if vertex is not None:
                        # If a robot is selected, assign a task to it
                        if self.selected_robot is not None:
                            result = {
                                'type': 'assign_task',
                                'robot': self.selected_robot,
                                'destination': vertex
                            }
                            self.show_notification(f"Task assigned to {self.selected_robot.id}")
                            self.selected_robot = None
                            return result
                        # Otherwise, spawn a new robot
                        else:
                            self.show_notification(f"New robot spawned at {self.nav_graph.get_vertex_name(vertex)}")
                            return {
                                'type': 'spawn_robot',
                                'position': vertex
                            }
                            
                    # If clicked on empty space, deselect robot
                    if self.selected_robot is not None:
                        self.selected_robot = None
                        self.show_notification("Robot deselected")
                    
        return None
        
    def run(self, fps=60):
        """
        Run the main loop of the GUI.
        
        Args:
            fps (int): Frames per second.
        """
        while True:
            event_info = self.handle_events()
            if event_info:
                print(f"Event: {event_info}")
                
            self.draw()
            self.clock.tick(fps) 