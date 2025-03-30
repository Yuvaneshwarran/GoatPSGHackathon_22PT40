import pygame
import sys
import math

class FleetGUI:
    # Dark mode color palette
    WHITE = (255, 255, 255)
    BLACK = (18, 18, 18)  # Dark background
    GRAY = (45, 45, 45)  # Darker gray for elements
    RED = (244, 67, 54)  # Material Design Red
    GREEN = (76, 175, 80)  # Material Design Green
    BLUE = (33, 150, 243)  # Material Design Blue
    YELLOW = (255, 235, 59)  # Material Design Yellow
    ORANGE = (255, 152, 0)  # Material Design Orange
    PURPLE = (156, 39, 176)  # Material Design Purple
    LIGHT_BLUE = (33, 150, 243)  # Light blue for accents
    DARK_BLUE = (25, 118, 210)  # Darker blue for accents
    TEXT_COLOR = (200, 200, 200)  # Light gray for text
    CARD_BG = (30, 30, 30)  # Slightly lighter than background for cards
    PANEL_BG = (35, 35, 35)  # Panel background
    BORDER_COLOR = (60, 60, 60)  # Border color
    SHADOW_COLOR = (10, 10, 10)  # Shadow color
    
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
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
        # Use modern fonts
        try:
            self.font = pygame.font.SysFont("Segoe UI", 24)
            self.small_font = pygame.font.SysFont("Segoe UI", 20)
            self.title_font = pygame.font.SysFont("Segoe UI", 32, bold=True)
            self.bold_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        except:
            self.font = pygame.font.SysFont(None, 24)
            self.small_font = pygame.font.SysFont(None, 20)
            self.title_font = pygame.font.SysFont(None, 32, bold=True)
            self.bold_font = pygame.font.SysFont(None, 24, bold=True)
        
        # Visualization parameters
        self.vertex_radius = 25  # Reduced from 35
        self.robot_radius = 35   # Reduced from 25
        self.scale_factor = 20
        self.offset_x = self.width // 2
        self.offset_y = self.height // 2
        self.edge_thickness = 4  # Reduced from 6
        self.reserved_edge_thickness = 6  # Reduced from 8
        
        # Store references
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
        self.show_robot_panel = True
        self.panel_width = 450  # Increased for better readability
        
        # Animation state
        self.animation_time = 0
        self.pulse_scale = 1.0
        
        # Create dark mode background
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(self.BLACK)  # Dark background
        
        # Create subtle grid pattern
        for x in range(0, self.width, 30):
            pygame.draw.line(self.background, (25, 25, 25), (x, 0), (x, self.height))
        for y in range(0, self.height, 30):
            pygame.draw.line(self.background, (25, 25, 25), (0, y), (self.width, y))
        
        # Load robot image
        self.robot_image = pygame.image.load("/home/yuvanesh/Desktop/Github/GoatPSGHackathon_22PT40/fleet_management_system/src/gui/robot.png")  # Update with the correct path to your image
        self.robot_image = pygame.transform.scale(self.robot_image, (self.robot_radius * 2, self.robot_radius * 2))  # Scale the image to fit the robot size
        
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
        Draw a vertex with modern styling.
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
        
        # Draw vertex with modern styling
        if vertex_type == self.VERTEX_CHARGER:
            # Charging station with modern design
            pygame.draw.circle(self.screen, self.BLUE, screen_pos, self.vertex_radius)
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.vertex_radius - 8)
            
            # Draw lightning bolt with gradient
            points = [
                (screen_pos[0], screen_pos[1] - self.vertex_radius//2),
                (screen_pos[0] - self.vertex_radius//3, screen_pos[1]),
                (screen_pos[0], screen_pos[1] - self.vertex_radius//4),
                (screen_pos[0], screen_pos[1] + self.vertex_radius//2),
                (screen_pos[0] + self.vertex_radius//3, screen_pos[1]),
                (screen_pos[0], screen_pos[1] + self.vertex_radius//4)
            ]
            pygame.draw.polygon(self.screen, self.DARK_BLUE, points)
            
        elif vertex_type == self.VERTEX_NAMED:
            # Named location with modern design
            pygame.draw.circle(self.screen, self.GREEN, screen_pos, self.vertex_radius)
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.vertex_radius - 8)
            
            # Add subtle pattern
            for i in range(3):
                radius = self.vertex_radius - 12 - i * 4
                pygame.draw.circle(self.screen, (200, 255, 200), screen_pos, radius, 2)
        else:
            # Normal vertex with modern design
            pygame.draw.circle(self.screen, self.GRAY, screen_pos, self.vertex_radius)
            pygame.draw.circle(self.screen, self.WHITE, screen_pos, self.vertex_radius - 8)
        
        # Draw hover effect with animation
        if is_hover:
            pulse = (math.sin(self.animation_time * 0.01) + 1) * 0.5
            hover_radius = self.vertex_radius + 4 + int(pulse * 2)
            pygame.draw.circle(self.screen, self.YELLOW, screen_pos, hover_radius, 3)
        
        # Draw vertex name with modern typography and dark mode
        if vertex_type in [self.VERTEX_NAMED, self.VERTEX_CHARGER]:
            name = self.nav_graph.get_vertex_name(vertex_index)
            text = self.bold_font.render(name, True, self.TEXT_COLOR)
            text_rect = text.get_rect(center=(screen_pos[0], screen_pos[1] - self.vertex_radius - 25))
            
            # Draw text background with dark mode colors
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, self.CARD_BG, bg_rect)
            pygame.draw.rect(self.screen, self.BORDER_COLOR, bg_rect, 1)
            
            self.screen.blit(text, text_rect)
        
        # Draw vertex index with dark mode
        index_text = self.font.render(str(vertex_index), True, self.TEXT_COLOR)
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
                pygame.draw.line(self.screen, self.WHITE, (start_x, start_y), (end_x, end_y), self.edge_thickness)
            
            # Draw an arrow to indicate direction
            arrow_length = 12  # Reduced from 16
            arrow_width = 8    # Reduced from 12
            
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
            pygame.draw.polygon(self.screen, self.WHITE, [arrow_p1, arrow_p2, arrow_p3])
        
    def draw_robot(self, robot):
        """
        Draw a robot on the screen.
        
        Args:
            robot: The robot object to draw.
        """
        if self.nav_graph is None:
            return
        
        pos = robot.get_current_position(self.nav_graph)
        if pos is None:
            return
        
        screen_pos = self.world_to_screen(pos[0], pos[1])
        
        # Draw the robot image instead of a circle
        self.screen.blit(self.robot_image, (screen_pos[0] - self.robot_radius, screen_pos[1] - self.robot_radius))
        
        # Optionally, you can add a border or highlight if the robot is selected
        if robot == self.selected_robot:
            pygame.draw.rect(self.screen, self.YELLOW, (screen_pos[0] - self.robot_radius, screen_pos[1] - self.robot_radius, self.robot_radius * 2, self.robot_radius * 2), 2)
        
        # Draw the robot ID with dark mode
        text = self.bold_font.render(robot.id, True, self.TEXT_COLOR)
        text_rect = text.get_rect(center=(screen_pos[0], screen_pos[1] - self.robot_radius - 15))
        
        # Draw text background with dark mode colors
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, self.CARD_BG, bg_rect)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, bg_rect, 1)
        
        self.screen.blit(text, text_rect)
        
        # Draw status indicator with modern design
        status_colors = {
            "idle": self.GRAY,
            "moving": self.GREEN,
            "waiting": self.YELLOW,
            "charging": self.BLUE,
            "task_complete": self.GREEN
        }
        status_color = status_colors.get(robot.status, self.WHITE)
        
        # Draw status indicator with animation
        if robot.status == "moving":
            pulse = (math.sin(self.animation_time * 0.02) + 1) * 0.5
            indicator_radius = 6 + int(pulse * 2)
        else:
            indicator_radius = 6
            
        pygame.draw.circle(self.screen, status_color, 
                          (screen_pos[0] + self.robot_radius + 8, screen_pos[1] - self.robot_radius - 8), 
                          indicator_radius)
        
        # Draw battery level with modern design
        if robot.battery_level < 30:
            # Draw battery outline
            battery_width = 25
            battery_height = 12
            battery_x = screen_pos[0] - battery_width // 2
            battery_y = screen_pos[1] + self.robot_radius + 8
            
            # Draw battery background
            pygame.draw.rect(self.screen, self.WHITE, 
                            (battery_x, battery_y, battery_width, battery_height))
            pygame.draw.rect(self.screen, self.BLACK, 
                            (battery_x, battery_y, battery_width, battery_height), 1)
            
            # Draw battery fill with gradient
            fill_width = int((battery_width - 2) * (robot.battery_level / 100))
            if robot.battery_level < 15:
                fill_color = self.RED
            else:
                fill_color = self.YELLOW
                
            pygame.draw.rect(self.screen, fill_color, 
                            (battery_x + 1, battery_y + 1, fill_width, battery_height - 2))
        
        # Draw waiting indicator with animation
        if robot.status == "waiting":
            wait_radius = 10
            wait_x = screen_pos[0] - self.robot_radius - 15
            wait_y = screen_pos[1]
            
            # Draw clock face with modern design
            pygame.draw.circle(self.screen, self.WHITE, (wait_x, wait_y), wait_radius)
            pygame.draw.circle(self.screen, self.BLACK, (wait_x, wait_y), wait_radius, 1)
            
            # Animate clock hands
            angle = (robot.waiting_time % 4) * math.pi / 2
            hand_x = wait_x + math.sin(angle) * (wait_radius - 3)
            hand_y = wait_y - math.cos(angle) * (wait_radius - 3)
            pygame.draw.line(self.screen, self.BLACK, (wait_x, wait_y), (hand_x, hand_y), 2)
        
        # Draw path with modern styling
        if robot.status == "moving" and robot.path and len(robot.path) > 1:
            path_points = []
            for i in range(robot.path.index(robot.position), len(robot.path)):
                vertex_pos = self.nav_graph.get_vertex_coordinates(robot.path[i])
                if vertex_pos:
                    path_points.append(self.world_to_screen(vertex_pos[0], vertex_pos[1]))
            
            if len(path_points) > 1:
                # Draw dashed line with animation
                dash_length = 10
                gap_length = 5
                total_length = dash_length + gap_length
                
                for i in range(len(path_points) - 1):
                    start = path_points[i]
                    end = path_points[i + 1]
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]
                    length = math.sqrt(dx*dx + dy*dy)
                    
                    if length > 0:
                        dx, dy = dx/length, dy/length
                        current_pos = 0
                        
                        while current_pos < length:
                            dash_start = (
                                start[0] + dx * current_pos,
                                start[1] + dy * current_pos
                            )
                            dash_end = (
                                start[0] + dx * min(current_pos + dash_length, length),
                                start[1] + dy * min(current_pos + dash_length, length)
                            )
                            pygame.draw.line(self.screen, robot.color, dash_start, dash_end, 2)
                            current_pos += total_length
                
                # Draw destination marker with animation
                dest_pos = path_points[-1]
                pulse = (math.sin(self.animation_time * 0.02) + 1) * 0.5
                marker_radius = 6 + int(pulse * 2)
                pygame.draw.circle(self.screen, robot.color, dest_pos, marker_radius, 2)

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
        Draw an information panel with dark mode styling.
        """
        # Create modern card background
        card_width = 350
        card_height = 300  # Increased height to accommodate better spacing
        card_x = 20
        card_y = 20
        
        # Draw card with shadow
        card_surface = pygame.Surface((card_width, card_height))
        card_surface.fill(self.CARD_BG)
        
        # Add subtle shadow
        shadow_surface = pygame.Surface((card_width + 4, card_height + 4))
        shadow_surface.fill(self.SHADOW_COLOR)
        self.screen.blit(shadow_surface, (card_x + 2, card_y + 2))
        self.screen.blit(card_surface, (card_x, card_y))
        
        # Draw card border
        pygame.draw.rect(self.screen, self.BORDER_COLOR, (card_x, card_y, card_width, card_height), 1)
        
        # Draw title with dark mode typography
        title_text = self.title_font.render("Fleet Management System", True, self.TEXT_COLOR)
        title_rect = title_text.get_rect()
        title_rect.centerx = card_x + card_width // 2
        title_rect.y = card_y + 20
        self.screen.blit(title_text, title_rect)
        
        # Draw horizontal line below title
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (card_x + 20, card_y + 55), 
                        (card_x + card_width - 20, card_y + 55), 2)
        
        # Draw building and level info
        if self.nav_graph:
            building_text = self.font.render(f"Building: {self.nav_graph.building_name}", True, self.TEXT_COLOR)
            level_text = self.font.render(f"Level: {self.nav_graph.level_name}", True, self.TEXT_COLOR)
            
            # Center align building and level info
            building_rect = building_text.get_rect()
            level_rect = level_text.get_rect()
            
            building_rect.centerx = card_x + card_width // 2
            level_rect.centerx = card_x + card_width // 2
            
            building_rect.y = card_y + 70
            level_rect.y = card_y + 95
            
            self.screen.blit(building_text, building_rect)
            self.screen.blit(level_text, level_rect)
        
        # Draw horizontal line below building/level info
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (card_x + 20, card_y + 120), 
                        (card_x + card_width - 20, card_y + 120), 2)
        
        # Draw instructions with dark mode styling and better spacing
        instructions = [
            "• Click on vertex: Spawn robot",
            "• Click on robot: Select robot",
            "• Click on vertex after selecting: Assign task",
            "• Green vertices: Charging stations",
            "• Orange vertices: Named locations",
            "• Yellow indicator: Robot waiting",
            "• Blue indicator: Robot charging"
        ]
        
        # Calculate total height of instructions
        instruction_height = len(instructions) * 28  # 28 pixels per line
        start_y = card_y + 135  # Start position after the line
        
        for i, instruction in enumerate(instructions):
            # Create a background rect for each instruction
            text = self.small_font.render(instruction, True, self.TEXT_COLOR)
            text_rect = text.get_rect()
            text_rect.x = card_x + 30  # Increased left margin
            text_rect.y = start_y + (i * 28)  # Increased line spacing
            
            # Draw subtle highlight for alternate lines
            if i % 2 == 0:
                highlight_rect = pygame.Rect(card_x + 20, text_rect.y - 2, 
                                          card_width - 40, text_rect.height + 4)
                pygame.draw.rect(self.screen, (35, 35, 35), highlight_rect)
            
            self.screen.blit(text, text_rect)
        
        # Draw horizontal line below instructions
        line_y = start_y + instruction_height + 10
        pygame.draw.line(self.screen, self.BORDER_COLOR, 
                        (card_x + 20, line_y), 
                        (card_x + card_width - 20, line_y), 2)
        
        # Draw robot count with dark mode styling
        robots_text = self.font.render(f"Active Robots: {len(self.robots)}", True, self.TEXT_COLOR)
        robots_rect = robots_text.get_rect()
        robots_rect.centerx = card_x + card_width // 2
        robots_rect.y = line_y + 15
        self.screen.blit(robots_text, robots_rect)

    def draw_robot_panel(self):
        """
        Draw a modern robot status panel with dark mode.
        """
        # Create panel background with gradient
        panel_rect = pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height)
        panel_surface = pygame.Surface((self.panel_width, self.height))
        panel_surface.fill(self.PANEL_BG)
        
        # Add subtle gradient
        for y in range(self.height):
            alpha = int(255 * (1 - y / self.height))
            pygame.draw.line(panel_surface, (30, 30, 30), (0, y), (self.panel_width, y))
        
        panel_surface.set_alpha(240)  # Slightly transparent
        
        # Draw panel border
        pygame.draw.rect(panel_surface, self.BORDER_COLOR, (0, 0, self.panel_width, self.height), 2)
        
        # Draw panel title with dark mode typography
        title = self.title_font.render("Robot Status", True, self.TEXT_COLOR)
        title_rect = title.get_rect(center=(self.panel_width // 2, 40))
        panel_surface.blit(title, title_rect)
        
        # Draw horizontal line with gradient
        pygame.draw.line(panel_surface, self.BORDER_COLOR, (20, 70), (self.panel_width - 20, 70), 2)
        
        # Count robots by status
        status_counts = {}
        for robot in self.robots:
            status = robot.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Draw status summary with modern cards
        y_pos = 90
        summary_title = self.bold_font.render("Summary", True, self.TEXT_COLOR)
        panel_surface.blit(summary_title, (20, y_pos))
        y_pos += 40
        
        for status, count in status_counts.items():
            # Draw status card
            card_width = self.panel_width - 40
            card_height = 40
            card_x = 20
            
            # Draw card background
            pygame.draw.rect(panel_surface, self.CARD_BG, 
                            (card_x, y_pos, card_width, card_height))
            pygame.draw.rect(panel_surface, self.BORDER_COLOR, 
                            (card_x, y_pos, card_width, card_height), 1)
            
            # Draw status text
            status_text = self.font.render(f"{status.capitalize()}: {count}", True, self.TEXT_COLOR)
            panel_surface.blit(status_text, (card_x + 20, y_pos + 10))
            
            y_pos += 50
        
        # Draw horizontal line with gradient
        y_pos += 10
        pygame.draw.line(panel_surface, self.BORDER_COLOR, (20, y_pos), (self.panel_width - 20, y_pos), 2)
        y_pos += 20
        
        # Draw detailed robot information
        details_title = self.bold_font.render("Robot Details", True, self.TEXT_COLOR)
        panel_surface.blit(details_title, (20, y_pos))
        y_pos += 40
        
        # Sort robots by status
        sorted_robots = sorted(self.robots, key=lambda r: (r.status, r.id))
        
        for robot in sorted_robots:
            # Draw robot card
            card_width = self.panel_width - 40
            card_height = 80
            card_x = 20
            
            # Draw card background
            pygame.draw.rect(panel_surface, self.CARD_BG, 
                            (card_x, y_pos, card_width, card_height))
            pygame.draw.rect(panel_surface, self.BORDER_COLOR, 
                            (card_x, y_pos, card_width, card_height), 1)
            
            # Highlight selected robot
            if robot == self.selected_robot:
                pygame.draw.rect(panel_surface, self.YELLOW, 
                                (card_x, y_pos, card_width, card_height), 2)
            
            # Draw robot color indicator
            pygame.draw.circle(panel_surface, robot.color, (card_x + 30, y_pos + 40), 15)
            
            # Draw robot ID and status
            id_text = self.bold_font.render(f"Robot {robot.id}", True, self.TEXT_COLOR)
            panel_surface.blit(id_text, (card_x + 60, y_pos + 15))
            
            # Get status with first letter capitalized
            status_display = robot.status.capitalize()
            status_color = self.TEXT_COLOR
            
            # Use different colors for different statuses
            if robot.status == self.STATUS_IDLE:
                status_color = self.GRAY
            elif robot.status == self.STATUS_MOVING:
                status_color = self.GREEN
            elif robot.status == self.STATUS_WAITING:
                status_color = self.ORANGE
            elif robot.status == self.STATUS_CHARGING:
                status_color = self.BLUE
            
            # Draw position information
            if robot.position is not None:
                position_name = self.nav_graph.get_vertex_name(robot.position) or f"Node {robot.position}"
                pos_text = self.font.render(f"At: {position_name}", True, self.TEXT_COLOR)
                panel_surface.blit(pos_text, (card_x + 60, y_pos + 40))
            
            # Draw status and battery
            status_text = self.font.render(f"Status: {status_display}", True, status_color)
            panel_surface.blit(status_text, (card_x + 60, y_pos + 65))
            
            # Draw battery level with modern design
            battery_color = self.TEXT_COLOR
            if robot.battery_level < 20:
                battery_color = self.RED
            elif robot.battery_level < 50:
                battery_color = self.ORANGE
            
            battery_text = self.font.render(f"Battery: {robot.battery_level:.1f}%", True, battery_color)
            panel_surface.blit(battery_text, (card_x + card_width - 150, y_pos + 40))
            
            y_pos += 100
            
            # If we're running out of space, stop drawing robots
            if y_pos > self.height - 60:
                more_text = self.font.render(f"+ {len(self.robots) - self.robots.index(robot) - 1} more robots", 
                                           True, self.TEXT_COLOR)
                panel_surface.blit(more_text, (card_x + 60, y_pos))
                break
        
        # Blit the panel to the screen
        self.screen.blit(panel_surface, panel_rect)

    def draw_notification(self):
        """
        Draw notification with dark mode styling.
        """
        if self.notification and pygame.time.get_ticks() < self.notification_time:
            # Create notification surface with modern design
            notification_width = self.width // 3
            notification_height = 50
            notification_surface = pygame.Surface((notification_width, notification_height))
            
            # Add gradient background
            for y in range(notification_height):
                alpha = int(255 * (1 - y / notification_height))
                pygame.draw.line(notification_surface, (40, 40, 40), (0, y), (notification_width, y))
            
            notification_surface.set_alpha(230)
            
            # Position on the right side of the screen
            x = self.width - notification_width - 20
            y = 20
            
            # Draw notification with shadow
            shadow_surface = pygame.Surface((notification_width + 4, notification_height + 4))
            shadow_surface.fill(self.SHADOW_COLOR)
            self.screen.blit(shadow_surface, (x + 2, y + 2))
            self.screen.blit(notification_surface, (x, y))
            
            # Draw border
            pygame.draw.rect(self.screen, self.BORDER_COLOR, 
                            (x, y, notification_width, notification_height), 1)
            
            # Render the text
            text = self.font.render(self.notification, True, self.TEXT_COLOR)
            text_rect = text.get_rect(center=(x + notification_width // 2, y + notification_height // 2))
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
        Run the main loop with animation updates.
        """
        while True:
            # Update animation time
            self.animation_time += 1
            
            event_info = self.handle_events()
            if event_info:
                print(f"Event: {event_info}")
                
            self.draw()
            self.clock.tick(fps)