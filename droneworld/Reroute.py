from algorithm.HeuristicSearch import HeuristicSearch
from droneworld.Hospital import Hospital


class Reroute:
    """
    Reroute class for handling the recalculation of a drone's route when a hazard is detected.
    Uses HeuristicSearch algorithm to find the best path around hazards.
    """

    def __init__(self, origin_x=0, origin_y=0):
        """
        Initialize the rerouting system.

        Args:
            origin_x (float): X coordinate of the origin point
            origin_y (float): Y coordinate of the origin point
        """
        self.origin = Hospital("Origin", origin_x, origin_y)

    def find_best_route(self, unvisited_hospitals, hazards, current_x, current_y):
        """
        Find the best route from the current position through all unvisited hospitals
        and back to the origin, avoiding any hazards.

        Args:
            unvisited_hospitals (list): List of hospital dictionaries not yet visited
            hazards (list): List of hazard dictionaries to avoid
            current_x (float): Current X position of the drone
            current_y (float): Current Y position of the drone

        Returns:
            list: New route details as a list of coordinate dictionaries
        """
        print(f"\n=== REROUTING DRONE ===")
        print(f"Current position: ({current_x:.2f}, {current_y:.2f})")
        print(f"Hazards detected: {len(hazards)}")
        print(f"Unvisited hospitals: {len(unvisited_hospitals)}")

        # Convert current position to a Hospital object (for algorithm compatibility)
        current_position = Hospital("Current Position", current_x, current_y)

        # Convert unvisited hospital dictionaries to Hospital objects
        hospital_objects = []
        for h in unvisited_hospitals:
            hospital = Hospital(h['name'], h['x'], h['y'])
            hospital_objects.append(hospital)
            print(f"  Hospital to visit: {hospital.name} at ({hospital.x:.2f}, {hospital.y:.2f})")

        print(f"Hazard details:")
        for h in hazards:
            hname = h.get('name', 'Unknown Hazard')
            print(f"  {hname} at ({h['x']:.2f}, {h['y']:.2f}), " +
                  f"size: {h.get('width', 1):.1f}x{h.get('height', 1):.1f}")
            
            # Special handling for storm hazards
            if "storm" in hname.lower():
                print(f"  WARNING: Storm hazard detected - will ensure paths avoid it completely!")

        # Create and run the HeuristicSearch algorithm with the current position as the start
        heuristic_search = HeuristicSearch(
            hospitals=hospital_objects,  # Just the hospitals to visit
            origin=self.origin,  # The final destination (origin)
            hazards=hazards
        )

        # Important: Set the starting point to the current position
        heuristic_search.start_point = current_position
        
        # Enable the exclusion of the first hospital in the list for the initial move
        heuristic_search.exclude_first_hospital = True

        print("\nRunning HeuristicSearch algorithm to find safe path...")
        best_route = heuristic_search.find_path(iterations_limit=100)

        # Verify final route safety
        final_path = best_route.hospitals
        for i in range(len(final_path) - 1):
            point1 = final_path[i]
            point2 = final_path[i + 1]
            if not heuristic_search._is_safe_path(point1, point2):
                print(f"WARNING: Final path segment from {point1.name} to {point2.name} may not be safe!")

        # Convert the result back to the format expected by the drone system
        route_details = []

        # Add current position as first stop
        route_details.append({
            'name': 'Current Position',
            'x': current_x,
            'y': current_y
        })

        # Add each hospital in the calculated route
        for hospital in best_route.hospitals:
            # Skip if it's the current position (we already added it)
            if hospital.name == "Current Position":
                continue

            route_details.append({
                'name': hospital.name,
                'x': hospital.x,
                'y': hospital.y
            })

        print(f"\nRerouting complete!")
        print(f"New route has {len(route_details)} stops")
        print(f"Route: {' -> '.join(stop['name'] for stop in route_details)}")
        
        # Final check for unsafe path segments
        if any("may not be safe" in line for line in [l for l in globals().get('_', '').split('\n') if l]):
            print("NOTE: The route contains potentially unsafe segments - proceed with caution!")
        
        print("======================\n")

        return route_details