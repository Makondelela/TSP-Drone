class Drone:
    """
    Represents a delivery drone that can move around the map.
    """

    def __init__(self, name="Delivery Drone", speed=1, current_x=0, current_y=0):
        """
        Initialize a drone with its position and properties.

        Args:
            name (str): The name of the drone
            speed (float): The speed of the drone in units per second
            current_x (float): Starting x coordinate
            current_y (float): Starting y coordinate
        """
        self.name = name
        self.speed = speed
        self.current_x = current_x
        self.current_y = current_y
        self.route = []
        self.current_stop_index = 0
        self.is_moving = False
        self.delivery_complete = False
        self.hazard_detected = False
        self.hazard_detection_range = 1.0  # Minimum distance to detect hazards
        self.previous_positions = []  # Track previous positions for backtracking
        self.min_position_change = 0.5  # Minimum movement before recording a new position

    def set_route(self, route_details):
        """
        Set the route for the drone to follow.

        Args:
            route_details (list): List of stops with coordinates
        """
        self.route = route_details
        self.current_stop_index = 0
        self.is_moving = False
        self.delivery_complete = False
        # Initialize the previous_positions with the current position
        self.previous_positions = [(self.current_x, self.current_y)]
        # Hazard_detected is not reset to allow for explicit control during rerouting

    def detect_hazards(self, hazards):
        """
        Detect if any hazards are within the drone's detection range.

        Args:
            hazards (list): List of hazard dictionaries with x, y coordinates

        Returns:
            bool: True if a hazard is detected, False otherwise
        """
        if not hazards:
            return False

        for hazard in hazards:
            # Calculate distance to hazard center
            dx = hazard['x'] - self.current_x
            dy = hazard['y'] - self.current_y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            # Account for the hazard's dimensions (approximately)
            adjusted_distance = distance - (hazard.get('width', 0) + hazard.get('height', 0)) / 4

            # If hazard is within detection range, stop the drone
            if adjusted_distance <= self.hazard_detection_range:
                # Only update hazard status if newly detected
                if not self.hazard_detected:
                    self.hazard_detected = True
                    print(f"Hazard detected at ({self.current_x:.2f}, {self.current_y:.2f})")
                    print(f"Previous safe position was: {self.get_previous_position()}")
                return True

        # No hazards within range
        self.hazard_detected = False
        return False

    def move_to_next_stop(self, hazards=None):
        """
        Move the drone to the next stop in the route.
        Will pause movement if a hazard is detected within range.
        
        Args:
            hazards (list): Optional list of hazard dictionaries

        Returns:
            bool: True if movement is complete, False if still in progress
        """
        # Debug route information
        if len(self.route) <= self.current_stop_index + 1:
            print(f"WARNING: No next stop available. Current index: {self.current_stop_index}, Route length: {len(self.route)}")
            self.delivery_complete = True
            self.is_moving = False
            return True

        # Check for hazard detection but don't modify movement here
        # Let the PerformDelivery class handle the pause/continue logic
        if hazards:
            self.detect_hazards(hazards)

        # If we're not moving (paused), don't proceed
        if not self.is_moving:
            return False

        # Get current and next positions
        next_stop = self.route[self.current_stop_index + 1]
        target_x = next_stop['x']
        target_y = next_stop['y']

        # Calculate direction
        dx = target_x - self.current_x
        dy = target_y - self.current_y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        # If we've reached the destination (or very close)
        if distance < 0.1:
            # Store position before updating to next stop
            self._record_position()
            
            self.current_x = target_x
            self.current_y = target_y
            self.current_stop_index += 1
            
            # Record the position at each stop
            self._record_position(force=True)
            
            print(f"Reached stop #{self.current_stop_index}: {next_stop.get('name', 'Unknown')}")

            # Check if we've completed the route
            if self.current_stop_index >= len(self.route) - 1:
                print("Reached final destination!")
                self.delivery_complete = True
                self.is_moving = False
                return True

            return False

        # Move towards the next point
        old_x, old_y = self.current_x, self.current_y
        move_distance = min(self.speed, distance)
        if distance > 0:
            self.current_x += (dx / distance) * move_distance
            self.current_y += (dy / distance) * move_distance
            
            # Record position if we've moved enough
            total_moved = ((self.current_x - old_x)**2 + (self.current_y - old_y)**2)**0.5
            if total_moved >= self.min_position_change:
                self._record_position()

        return False

    def _record_position(self, force=False):
        """
        Record the current position in the history if it's different enough
        from the last recorded position or if forced.
        
        Args:
            force (bool): Force recording even if position hasn't changed much
        """
        current_pos = (self.current_x, self.current_y)
        
        # If we have no positions or the position has changed significantly, or force is True
        if force or not self.previous_positions:
            self.previous_positions.append(current_pos)
            return True
            
        last_pos = self.previous_positions[-1]
        distance = ((current_pos[0] - last_pos[0])**2 + (current_pos[1] - last_pos[1])**2)**0.5
        
        if distance >= self.min_position_change:
            self.previous_positions.append(current_pos)
            # Keep only the last 10 positions to limit memory usage
            if len(self.previous_positions) > 10:
                self.previous_positions.pop(0)
            return True
            
        return False

    def get_previous_position(self):
        """
        Get the previously visited position for backtracking.
        
        Returns:
            tuple: (x, y) coordinates of previous position, or current position if history is empty
        """
        # Get the second-to-last position if available (last is current)
        if len(self.previous_positions) > 1:
            return self.previous_positions[-2]
        # Otherwise return the last recorded position
        elif self.previous_positions:
            return self.previous_positions[-1]
        # Fallback to current position if no history
        return (self.current_x, self.current_y)

    def get_position(self):
        """
        Get the current position of the drone.

        Returns:
            tuple: (x, y) coordinates
        """
        return (self.current_x, self.current_y)

    def get_progress(self):
        """
        Get the progress of the delivery.

        Returns:
            dict: Status information about the delivery
        """
        if len(self.route) == 0:
            return {
                "status": "idle",
                "progress": 0,
                "current_location": (self.current_x, self.current_y),
                "next_stop": None,
                "stops_completed": 0,
                "total_stops": 0,
                "hazard_detected": self.hazard_detected
            }

        total_stops = len(self.route)
        progress = (self.current_stop_index / (total_stops - 1)) * 100 if total_stops > 1 else 0

        next_stop = None
        if self.current_stop_index < total_stops - 1:
            next_stop = self.route[self.current_stop_index + 1]["name"]

        status = "completed" if self.delivery_complete else "in_progress"
        if self.hazard_detected:
            status = "hazard_detected"

        return {
            "status": status,
            "progress": progress,
            "current_location": (self.current_x, self.current_y),
            "next_stop": next_stop,
            "stops_completed": self.current_stop_index,
            "total_stops": total_stops - 1,  # Subtract 1 because the last stop is returning to origin
            "hazard_detected": self.hazard_detected
        }