import time
import threading
import datetime
import random
from droneworld.Drone import Drone
from droneworld.WeatherHazard import WeatherHazard
from droneworld.Reroute import Reroute


class PerformDelivery:
    """
    Class to perform a drone delivery simulation based on a calculated route.
    """

    def __init__(self, update_interval=0.05):
        """
        Initialize the delivery simulation.

        Args:
            update_interval (float): Time between position updates in seconds
        """
        self.drone = Drone()
        self.update_interval = update_interval
        self.simulation_thread = None
        self.is_running = False
        self.is_paused = False
        self.on_update_callback = None
        self.on_complete_callback = None
        self.start_time = None
        self.delivery_history = []
        self.current_route = []
        self.hazards = []
        self.previous_location = None  # Store the previous location for continuing after pause
        self.router = Reroute()  # Initialize the reroute system
        self.rerouting_in_progress = False

    def _generate_weather_hazard_on_route(self, route_details):
        """
        Generate a weather hazard on the route for visualization purposes.

        Args:
            route_details (list): List of stops with coordinates

        Returns:
            dict: Weather hazard information with position and type
        """
        if len(route_details) <= 2:
            return None

        start_idx = random.randint(1, len(route_details) - 2)
        end_idx = start_idx + 1

        start_point = route_details[start_idx]
        end_point = route_details[end_idx]

        weather_hazard = WeatherHazard.generate_on_route(start_point, end_point)
        return weather_hazard.to_dict()

    def start_delivery(self, route_details):
        """
        Start the delivery process with the provided route.

        Args:
            route_details (list): List of stops with coordinates
        """
        # Reset the drone position to origin
        origin = route_details[0]
        self.drone = Drone(current_x=origin['x'], current_y=origin['y'])
        
        # Initialize the router with origin coordinates
        self.router = Reroute(origin_x=origin['x'], origin_y=origin['y'])

        # Generate weather hazard for visualization
        hazard = self._generate_weather_hazard_on_route(route_details)
        self.hazards = [hazard] if hazard else []

        # Create enhanced route for frontend
        enhanced_route = route_details.copy()
        if hazard:
            enhanced_route.append(hazard)

        self.current_route = enhanced_route
        self.drone.set_route(route_details)

        # Stop any existing simulation
        self.stop_delivery()

        # Reset simulation state
        self.start_time = datetime.datetime.now()
        self.delivery_history = []
        self.is_paused = False
        self.previous_location = None
        self.rerouting_in_progress = False

        # Start new simulation thread
        self.is_running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

        return self.get_current_status()

    def stop_delivery(self):
        """
        Stop the current delivery simulation.
        """
        self.is_running = False
        self.is_paused = False
        self.rerouting_in_progress = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            current_thread = threading.current_thread()
            if current_thread != self.simulation_thread:
                self.simulation_thread.join(timeout=1.0)

    def pause_delivery(self):
        """
        Pause the current delivery simulation when a hazard is detected.
        Stores the current location to continue from later.
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            # Get the previous position from the drone's tracking
            self.previous_location = self.drone.get_previous_position()
            print(f"Delivery paused at: {self.drone.get_position()}")
            print(f"Previous safe location: {self.previous_location}")
            
            # Stop the drone movement
            self.drone.is_moving = False
            
            # Notify frontend of pause
            status = self.get_current_status()
            status['status'] = 'paused'
            if self.on_update_callback:
                self.on_update_callback(status)
                
            return True
        return False

    def continue_delivery(self, location=None):
        """
        Continue the delivery after pause.
        Moves the drone to the previous location, then recalculates the route for the
        remaining hospitals using the Reroute class.

        Args:
            location (tuple, optional): (x, y) coordinates to continue from
        """
        if self.is_paused:
            # If no location provided, use previous location
            target_location = location if location else self.previous_location
            
            if target_location:
                print(f"Continuing delivery from previous safe location: {target_location}")
                self.drone.current_x, self.drone.current_y = target_location
                
                # Recalculate route for remaining hospitals
                if not self.rerouting_in_progress:
                    self.rerouting_in_progress = True
                    self._recalculate_route()
                
            # Clear hazard status and resume movement
            self.drone.hazard_detected = False
            self.drone.is_moving = True
            self.is_paused = False
            
            # Notify frontend of continuation
            status = self.get_current_status()
            status['status'] = 'in_progress'
            if self.on_update_callback:
                self.on_update_callback(status)
                
            return True
        return False

    def _recalculate_route(self):
        """
        Recalculate the route for the remaining unvisited hospitals.
        Uses the Reroute class to find a path around any known hazards.
        """
        print("Recalculating route for remaining unvisited hospitals...")
        
        # Get current position
        current_x, current_y = self.drone.get_position()
        
        # Identify unvisited hospitals
        unvisited_hospitals = []
        for i in range(self.drone.current_stop_index + 1, len(self.drone.route)):
            if i < len(self.drone.route):
                unvisited_hospitals.append(self.drone.route[i])
        
        print(f"Found {len(unvisited_hospitals)} unvisited hospitals")
        
        # If we still have hospitals to visit, reroute
        if unvisited_hospitals:
            # Find new route using the Reroute class
            new_route = self.router.find_best_route(
                unvisited_hospitals, 
                self.hazards, 
                current_x, 
                current_y
            )
            
            # Update the drone's route with the new calculated route
            self.drone.set_route(new_route)
            
            # Update the current route for the frontend display
            self.current_route = new_route.copy()
            if self.hazards:
                for hazard in self.hazards:
                    self.current_route.append(hazard)
            
            print(f"Route recalculated with {len(new_route)} stops")
        else:
            print("No remaining hospitals to visit, continuing to origin")
        
        self.rerouting_in_progress = False

    def _simulation_loop(self):
        """
        Main simulation loop that updates the drone's position.
        """
        last_stop_index = -1
        last_position = None
        hazard_timer = None
        
        print("=== SIMULATION STARTED ===")
        print(f"Initial position: {self.drone.get_position()}")

        while self.is_running and not self.drone.delivery_complete:
            # Get current position
            current_pos = self.drone.get_position()

            # Log position changes
            if last_position != current_pos:
                print(f"Drone moved to: ({current_pos[0]:.2f}, {current_pos[1]:.2f}), " +
                      f"Target stop: {self.drone.current_stop_index + 1}/{len(self.drone.route)}")
                last_position = current_pos

            # Check for hazards and handle pausing/continuing
            if not self.is_paused and self.drone.detect_hazards(self.hazards):
                print(f"Weather hazard detected at {current_pos}!")
                
                # Pause delivery when hazard is detected
                self.pause_delivery()
                
                # Set a timer to continue after 3 seconds
                hazard_timer = datetime.datetime.now()
                
            # If we're paused due to hazard and 3 seconds have passed, continue
            if self.is_paused and hazard_timer and (datetime.datetime.now() - hazard_timer).total_seconds() >= 3:
                print("3 seconds elapsed since hazard detection, continuing delivery from previous safe location")
                self.continue_delivery()
                hazard_timer = None

            # Only move the drone if not paused and not currently rerouting
            if not self.is_paused and not self.rerouting_in_progress:
                # Move the drone
                self.drone.move_to_next_stop(self.hazards)
                
                # Ensure drone is always moving unless paused
                if not self.drone.is_moving:
                    self.drone.is_moving = True

            # Record arrival at new stops
            if last_stop_index != self.drone.current_stop_index:
                last_stop_index = self.drone.current_stop_index
                if last_stop_index > 0 and last_stop_index < len(self.current_route):
                    stop_info = self.drone.route[last_stop_index]
                    stop_name = stop_info.get('name', f"Stop {last_stop_index}")
                    print(f"ARRIVED at stop {last_stop_index}: {stop_name}")
                    self.delivery_history.append({
                        'stop': last_stop_index,
                        'name': stop_name,
                        'time': datetime.datetime.now().strftime('%H:%M:%S'),
                        'elapsed': str(datetime.datetime.now() - self.start_time).split('.')[0]
                    })

            # Get current status and call update callback
            status = self.get_current_status()
            if self.on_update_callback:
                self.on_update_callback(status)

            # Sleep for the update interval
            time.sleep(self.update_interval)
        
        # Call completion callback when done
        if self.on_complete_callback and self.drone.delivery_complete:
            print("=== DELIVERY COMPLETE ===")
            self.on_complete_callback(self.get_current_status())

    def get_current_status(self):
        """
        Get the current status of the delivery with details needed by frontend.

        Returns:
            dict: Status information about the delivery
        """
        base_status = self.drone.get_progress()

        # Override status if paused or rerouting
        if self.is_paused:
            base_status['status'] = 'paused'
        elif self.rerouting_in_progress:
            base_status['status'] = 'rerouting'

        enhanced_status = {
            **base_status,
            'elapsed_time': str(datetime.datetime.now() - self.start_time).split('.')[0] if self.start_time else "00:00:00",
            'history': self.delivery_history,
            'estimated_completion': self._estimate_completion_time(),
            'route': self.current_route,
            'hazards': self.hazards,
            'stops_completed': self.drone.current_stop_index,
            'is_paused': self.is_paused,
            'is_rerouting': self.rerouting_in_progress
        }

        return enhanced_status

    def _estimate_completion_time(self):
        """
        Estimate the time remaining for the delivery to complete.

        Returns:
            str: Estimated time remaining
        """
        if not self.start_time or not self.is_running:
            return "N/A"

        progress = self.drone.get_progress()['progress']
        if progress <= 0:
            return "Calculating..."

        elapsed_seconds = (datetime.datetime.now() - self.start_time).total_seconds()
        total_estimated_seconds = elapsed_seconds / (progress / 100)
        remaining_seconds = total_estimated_seconds - elapsed_seconds

        if remaining_seconds <= 0:
            return "Completing..."

        minutes, seconds = divmod(int(remaining_seconds), 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def register_update_callback(self, callback):
        """
        Register a callback function to be called on each position update.

        Args:
            callback (function): Function to call with drone progress
        """
        self.on_update_callback = callback

    def register_complete_callback(self, callback):
        """
        Register a callback function to be called when delivery completes.

        Args:
            callback (function): Function to call when delivery is complete
        """
        self.on_complete_callback = callback