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
    
    # Robot status constants
    STATUS_IDLE = "idle"
    STATUS_MOVING = "moving"
    STATUS_WAITING = "waiting"
    STATUS_CHARGING = "charging"
    STATUS_TASK_COMPLETE = "task_complete"
    
    def __init__(self, width=1024, height=768, title="Fleet Management System", fullscreen=True):
        """
        Initialize the GUI.
        
        Args:
            width (int): Width of the window.
            height (int): Height of the window.
            title (str): Title of the window.
            fullscreen (bool): Whether to run in fullscreen mode.
        """
        pygame.init()
        self.width = width
        self.height = height
        
        # Set up display mode
        if fullscreen:
            # Get the current screen info
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
        # Use better fonts with larger sizes
        try:
            # Try to use Arial or a similar sans-serif font
            self.font = pygame.font.SysFont("Arial", 28)
            self.small_font = pygame.font.SysFont("Arial", 22)
            self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
            self.bold_font = pygame.font.SysFont("Arial", 28, bold=True)
        except:
            # Fall back to default font if Arial is not available
            self.font = pygame.font.SysFont(None, 28)
            self.small_font = pygame.font.SysFont(None, 22)
            self.title_font = pygame.font.SysFont(None, 36, bold=True)
            self.bold_font = pygame.font.SysFont(None, 28, bold=True)
        
        # Visualization parameters - doubled thickness
        self.vertex_radius = 30  # Increased from 20 to 30
        self.robot_radius = 20   # Increased from 15 to 20
        self.scale_factor = 20   # Scale factor for converting coordinates
        self.offset_x = self.width // 2
        self.offset_y = self.height // 2
        self.edge_thickness = 8  # Increased from 4 to 8
        self.reserved_edge_thickness = 10  # Increased from 5 to 10
        
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
        self.show_robot_panel = True  # New flag to toggle robot info panel
        self.panel_width = 400  # Increased from 300 to 400 for more space
        
        # Load background image
        try:
            self.background = pygame.Surface((self.width, self.height))
            self.background.fill((240, 248, 255))  # Light blue background
            
            # Create a grid pattern
            for x in range(0, self.width, 20):
                pygame.draw.line(self.background, (220, 220, 220), (x, 0), (x, self.height))
            for y in range(0, self.height, 20):
                pygame.draw.line(self.background, (220, 220, 220), (0, y), (self.width, y))
                
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
                # Leave some margin (reduced for bigger graph)
                margin = 0.1  # Reduced from 0.2 to 0.1
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
        
    def draw_vertex(self, vertex_index):
        """
        Draw a vertex on the screen.
        
        Args:
            vertex_index (int): Index of the vertex to draw.
        """
        if self.nav_graph is None:
            return
            
        vertex = self.nav_graph.vertices[vertex_index]
        coords = self.nav_graph.get_vertex_coordinates(vertex_index)
        if coords is None:
            return
            
        screen_pos = self.world_to_screen(coords[0], coords[1])
        
        # Determine vertex type
        vertex_type = self.VERTEX_NORMAL
        if len(vertex) > 2 and isinstance(vertex[2], dict):
            if vertex[2].get('charger', False):
                vertex_type = self.VERTEX_CHARGER
            elif 'name' in vertex[2] and vertex[2]['name']:
                vertex_type = self.VERTEX_NAMED
        
        # Determine if this vertex is being hovered over
        is_hover = (self.hover_vertex == vertex_index)
        
        # Draw different vertex types with more distinctive colors
        if vertex_type == self.VERTEX_CHARGER:
            # Charging station - Blue with lightning bolt
            pygame.draw.circle(self.screen, self.BLUE, screen_pos, self.vertex_radius)
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.vertex_radius - 6)  # Thicker border
            
            # Draw a lightning bolt icon
            points = [
                (screen_pos[0], screen_pos[1] - self.vertex_radius//2),
                (screen_pos[0] - self.vertex_radius//3, screen_pos[1]),
                (screen_pos[0], screen_pos[1] - self.vertex_radius//4),
                (screen_pos[0], screen_pos[1] + self.vertex_radius//2),
                (screen_pos[0] + self.vertex_radius//3, screen_pos[1]),
                (screen_pos[0], screen_pos[1] + self.vertex_radius//4)
            ]
            pygame.draw.polygon(self.screen, self.BLUE, points)
            
        elif vertex_type == self.VERTEX_NAMED:
            # Named location - Bright green
            pygame.draw.circle(self.screen, self.GREEN, screen_pos, self.vertex_radius)
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.vertex_radius - 6)  # Thicker border
        else:
            # Normal vertex - Gray
            pygame.draw.circle(self.screen, self.GRAY, screen_pos, self.vertex_radius)
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.vertex_radius - 6)  # Thicker border
        
        # Draw hover effect
        if is_hover:
            pygame.draw.circle(self.screen, self.YELLOW, screen_pos, self.vertex_radius + 4, 3)  # Thicker hover ring
        
        # Draw vertex name if it has one
        if vertex_type in [self.VERTEX_NAMED, self.VERTEX_CHARGER]:
            name = self.nav_graph.get_vertex_name(vertex_index)
            text = self.bold_font.render(name, True, self.BLACK)  # Use bold font for names
            text_rect = text.get_rect(center=(screen_pos[0], screen_pos[1] - self.vertex_radius - 20))  # Moved further from vertex
            self.screen.blit(text, text_rect)
        
        # Draw vertex index for all vertices
        index_text = self.font.render(str(vertex_index), True, self.BLACK)
        index_rect = index_text.get_rect(center=screen_pos)
        self.screen.blit(index_text, index_rect)
        
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
            
            # Check if this lane is reserved by a robot
            lane_reserved = False
            for robot in self.robots:
                if robot.status == "moving" and robot.current_lane and \
                   robot.current_lane[0] == from_vertex and robot.current_lane[1] == to_vertex:
                    lane_reserved = True
                    lane_color = self.YELLOW
                    break
            
            # Draw the lane with appropriate color
            if lane_reserved:
                # Draw a thicker line with yellow color
                pygame.draw.line(self.screen, lane_color, (start_x, start_y), (end_x, end_y), self.reserved_edge_thickness)
            else:
                pygame.draw.line(self.screen, self.BLACK, (start_x, start_y), (end_x, end_y), self.edge_thickness)
            
            # Draw an arrow to indicate direction
            arrow_length = 16  # Increased from 12 to 16
            arrow_width = 12   # Increased from 8 to 12
            
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
        
        # Draw battery level indicator if below 30%
        if robot.battery_level < 30:
            # Draw battery outline
            battery_width = 20
            battery_height = 10
            battery_x = screen_pos[0] - battery_width // 2
            battery_y = screen_pos[1] + self.robot_radius + 5
            
            pygame.draw.rect(self.screen, self.BLACK, 
                            (battery_x, battery_y, battery_width, battery_height), 1)
            
            # Draw battery fill based on level
            fill_width = int((battery_width - 2) * (robot.battery_level / 100))
            if robot.battery_level < 15:
                fill_color = self.RED
            else:
                fill_color = self.YELLOW
            
            pygame.draw.rect(self.screen, fill_color, 
                            (battery_x + 1, battery_y + 1, fill_width, battery_height - 2))
        
        # If the robot is waiting, show a waiting indicator
        if robot.status == "waiting":
            # Draw a clock-like waiting indicator
            wait_radius = 8
            wait_x = screen_pos[0] - self.robot_radius - 10
            wait_y = screen_pos[1]
            
            # Draw clock face
            pygame.draw.circle(self.screen, self.WHITE, (wait_x, wait_y), wait_radius)
            pygame.draw.circle(self.screen, self.BLACK, (wait_x, wait_y), wait_radius, 1)
            
            # Draw clock hands based on waiting time
            angle = (robot.waiting_time % 4) * math.pi / 2
            hand_x = wait_x + math.sin(angle) * (wait_radius - 2)
            hand_y = wait_y - math.cos(angle) * (wait_radius - 2)
            pygame.draw.line(self.screen, self.BLACK, (wait_x, wait_y), (hand_x, hand_y), 2)
        
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
        info_surface = pygame.Surface((300, 220))
        info_surface.set_alpha(220)
        info_surface.fill(self.LIGHT_BLUE)
        self.screen.blit(info_surface, (10, 10))
        
        # Draw border
        pygame.draw.rect(self.screen, self.BLACK, (10, 10, 300, 220), 2)
        
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
            "• Orange vertices: Named locations",
            "• Yellow indicator: Robot waiting",
            "• Blue indicator: Robot charging"
        ]
        
        y_pos = 100
        for instruction in instructions:
            text = self.small_font.render(instruction, True, self.BLACK)
            self.screen.blit(text, (20, y_pos))
            y_pos += 20
            
        # Draw robot count
        robots_text = self.font.render(f"Robots: {len(self.robots)}", True, self.BLACK)
        self.screen.blit(robots_text, (20, 200))
        
        # Draw selected robot info
        if self.selected_robot:
            # Draw a semi-transparent background for robot info
            robot_info_surface = pygame.Surface((300, 120))
            robot_info_surface.set_alpha(220)
            robot_info_surface.fill(self.LIGHT_BLUE)
            self.screen.blit(robot_info_surface, (10, 240))
            
            # Draw border
            pygame.draw.rect(self.screen, self.BLACK, (10, 240, 300, 120), 2)
            
            # Draw robot info
            robot_title = self.bold_font.render(f"Selected Robot: {self.selected_robot.id}", True, self.BLACK)
            self.screen.blit(robot_title, (20, 245))
            
            status_text = self.font.render(f"Status: {self.selected_robot.status}", True, self.BLACK)
            self.screen.blit(status_text, (20, 270))
            
            position_name = self.nav_graph.get_vertex_name(self.selected_robot.position)
            position_text = self.font.render(f"Position: {position_name}", True, self.BLACK)
            self.screen.blit(position_text, (20, 295))
            
            battery_text = self.font.render(f"Battery: {self.selected_robot.battery_level:.1f}%", True, self.BLACK)
            self.screen.blit(battery_text, (20, 320))
            
            if self.selected_robot.destination is not None:
                dest_name = self.nav_graph.get_vertex_name(self.selected_robot.destination)
                dest_text = self.font.render(f"Destination: {dest_name}", True, self.BLACK)
                self.screen.blit(dest_text, (20, 345))
    
    def draw_notification(self):
        """
        Draw the current notification message.
        """
        if self.notification and pygame.time.get_ticks() < self.notification_time:
            # Create a semi-transparent background
            notification_surface = pygame.Surface((self.width // 3, 40))
            notification_surface.set_alpha(200)
            notification_surface.fill((50, 50, 50))
            
            # Position on the right side of the screen
            x = self.width - notification_surface.get_width() - 20
            y = 20
            
            self.screen.blit(notification_surface, (x, y))
            
            # Render the text
            text = self.font.render(self.notification, True, self.WHITE)
            text_rect = text.get_rect(center=(x + notification_surface.get_width() // 2, y + notification_surface.get_height() // 2))
            self.screen.blit(text, text_rect)
    
    def draw(self):
        """
        Draw the GUI.
        """
        # Clear the screen
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(self.WHITE)
        
        # Draw the navigation graph
        if self.nav_graph:
            # Draw lanes first (so they appear behind vertices)
            for lane in self.nav_graph.lanes:
                # Extract just the first two elements (from_vertex, to_vertex)
                from_vertex, to_vertex = lane[0], lane[1]
                self.draw_lane(from_vertex, to_vertex)
            
            # Draw vertices
            for i in range(len(self.nav_graph.vertices)):
                self.draw_vertex(i)
        
        # Draw robots
        for robot in self.robots:
            self.draw_robot(robot)
        
        # Draw help panel
        if self.show_help:
            self.draw_info_panel()
        
        # Draw robot info panel
        if self.show_robot_panel:
            self.draw_robot_panel()
        
        # Draw notification
        self.draw_notification()
        
        # Update the display
        pygame.display.flip()

    def draw_robot_panel(self):
        """
        Draw a panel showing detailed information about all robots.
        """
        # Create panel background
        panel_rect = pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height)
        panel_surface = pygame.Surface((self.panel_width, self.height))
        panel_surface.fill((240, 240, 240))  # Light gray background
        panel_surface.set_alpha(230)  # Slightly transparent
        
        # Draw panel border
        pygame.draw.rect(panel_surface, (180, 180, 180), (0, 0, self.panel_width, self.height), 2)
        
        # Draw panel title
        title = self.title_font.render("Robot Status", True, self.BLACK)
        title_rect = title.get_rect(center=(self.panel_width // 2, 30))
        panel_surface.blit(title, title_rect)
        
        # Draw horizontal line below title
        pygame.draw.line(panel_surface, (180, 180, 180), (20, 60), (self.panel_width - 20, 60), 2)
        
        # Count robots by status
        status_counts = {}
        for robot in self.robots:
            status = robot.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Draw status summary
        y_pos = 80
        summary_title = self.bold_font.render("Summary:", True, self.BLACK)
        panel_surface.blit(summary_title, (20, y_pos))
        y_pos += 40
        
        for status, count in status_counts.items():
            status_text = self.font.render(f"{status.capitalize()}: {count}", True, self.BLACK)
            panel_surface.blit(status_text, (40, y_pos))
            y_pos += 30
        
        # Draw horizontal line below summary
        y_pos += 10
        pygame.draw.line(panel_surface, (180, 180, 180), (20, y_pos), (self.panel_width - 20, y_pos), 2)
        y_pos += 20
        
        # Draw detailed robot information
        details_title = self.bold_font.render("Robot Details:", True, self.BLACK)
        panel_surface.blit(details_title, (20, y_pos))
        y_pos += 40
        
        # Sort robots by status for better organization
        sorted_robots = sorted(self.robots, key=lambda r: (r.status, r.id))
        
        for robot in sorted_robots:
            # Draw robot color indicator
            pygame.draw.circle(panel_surface, robot.color, (30, y_pos + 12), 10)
            
            # Highlight selected robot
            if robot == self.selected_robot:
                pygame.draw.rect(panel_surface, self.YELLOW, (45, y_pos, self.panel_width - 65, 60), 2)
            
            # Draw robot ID and status
            id_text = self.bold_font.render(f"Robot {robot.id}", True, self.BLACK)
            panel_surface.blit(id_text, (50, y_pos))
            
            # Get status with first letter capitalized
            status_display = robot.status.capitalize()
            status_color = self.BLACK
            
            # Use different colors for different statuses
            if robot.status == self.STATUS_IDLE:
                status_color = self.GRAY
            elif robot.status == self.STATUS_MOVING:
                status_color = self.GREEN
            elif robot.status == self.STATUS_WAITING:
                status_color = self.ORANGE
            elif robot.status == self.STATUS_CHARGING:
                status_color = self.BLUE
            
            # Draw position information if available
            if robot.position is not None:
                position_name = self.nav_graph.get_vertex_name(robot.position) or f"Node {robot.position}"
                pos_text = self.font.render(f"At: {position_name}", True, self.BLACK)
                panel_surface.blit(pos_text, (50, y_pos + 25))
            
            # Draw status on the right side
            status_text = self.font.render(f"Status: {status_display}", True, status_color)
            panel_surface.blit(status_text, (50, y_pos + 50))
            
            # Draw battery level on the right side
            battery_color = self.BLACK
            if robot.battery_level < 20:
                battery_color = self.RED
            elif robot.battery_level < 50:
                battery_color = self.ORANGE
            
            battery_text = self.font.render(f"Battery: {robot.battery_level:.1f}%", True, battery_color)
            panel_surface.blit(battery_text, (self.panel_width - 200, y_pos + 25))
            
            # Add more space between robot entries
            y_pos += 80
            
            # If we're running out of space, stop drawing robots
            if y_pos > self.height - 60:
                more_text = self.font.render(f"+ {len(self.robots) - self.robots.index(robot) - 1} more robots", True, self.BLACK)
                panel_surface.blit(more_text, (50, y_pos))
                break
        
        # Blit the panel to the screen
        self.screen.blit(panel_surface, panel_rect)

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
                # Toggle robot panel with R key
                elif event.key == pygame.K_r:
                    self.show_robot_panel = not self.show_robot_panel
                    self.show_notification("Robot panel toggled")
                # Start charging with C key if robot is selected and at a charging station
                elif event.key == pygame.K_c and self.selected_robot:
                    if self.nav_graph.is_charger(self.selected_robot.position):
                        if self.selected_robot.start_charging():
                            self.show_notification(f"Robot {self.selected_robot.id} is now charging")
                            return {
                                'type': 'start_charging',
                                'robot': self.selected_robot
                            }
                        else:
                            self.show_notification("Robot is already charging")
                    else:
                        self.show_notification("Robot must be at a charging station to charge")
                # Toggle fullscreen with F11 key
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    self.show_notification("Toggled fullscreen mode")
                # Exit fullscreen with Escape key
                elif event.key == pygame.K_ESCAPE:
                    if pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
                        pygame.display.set_mode((1024, 768))
                        self.width = 1024
                        self.height = 768
                        self.offset_x = self.width // 2
                        self.offset_y = self.height // 2
                        self.show_notification("Exited fullscreen mode")
                    else:
                        pygame.quit()
                        sys.exit()
            
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