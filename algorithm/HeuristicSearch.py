import heapq
import math
from droneworld.Route import Route


class HeuristicSearch:
    """
    A* search algorithm implementation for finding optimal paths
    through a set of points while avoiding hazards.
    """

    def __init__(self, hospitals, origin=None, hazards=None):
        """
        Initialize the A* search algorithm.

        Args:
            hospitals (list): List of hospital objects to visit
            origin (object): Starting position (coordinates 0,0 typically)
            hazards (list): List of hazard objects to avoid
        """
        self.hospitals = hospitals
        self.origin = origin
        self.hazards = hazards or []
        self.best_path = None
        self.best_distance = float('inf')
        self.nodes_explored = 0
        self.iterations = 0
        self.start_point = None  # Add a custom starting point property
        self.exclude_first_hospital = True  # Flag to exclude the first hospital in the list

        # Hazard avoidance parameters
        self.hazard_buffer = 1.5  # Buffer distance to keep from hazards

    def _distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

    def _is_safe_path(self, point1, point2):
        """Check if path between two points avoids all hazards."""
        if not self.hazards:
            return True

        for hazard in self.hazards:
            # For each hazard, check if the path between point1 and point2 comes too close

            # Calculate distance from line segment to hazard center
            # Using the formula for distance from point to line segment
            x1, y1 = point1.x, point1.y
            x2, y2 = point2.x, point2.y
            hx, hy = hazard['x'], hazard['y']

            # Vector from point1 to point2
            line_length = self._distance(point1, point2)
            if line_length == 0:  # If points are the same
                dist = math.sqrt((x1 - hx) ** 2 + (y1 - hy) ** 2)
            else:
                # Calculate projection
                t = ((hx - x1) * (x2 - x1) + (hy - y1) * (y2 - y1)) / (line_length ** 2)
                t = max(0, min(1, t))  # Clamp t to [0,1]

                # Calculate closest point on line segment
                px = x1 + t * (x2 - x1)
                py = y1 + t * (y2 - y1)

                # Distance from hazard to line segment
                dist = math.sqrt((px - hx) ** 2 + (py - hy) ** 2)

            # Adjust hazard size (width/height) for safety buffer
            hazard_size = (hazard.get('width', 1) + hazard.get('height', 1)) / 2
            safe_distance = hazard_size + self.hazard_buffer

            if dist < safe_distance:
                # Format the hazard avoidance message with hazard name
                hazard_name = hazard.get('name', 'hazard')
                print(f"Path unsafe: too close to {hazard_name} ({dist:.2f} < {safe_distance:.2f})")
                
                # Special warning for storm hazards
                if "storm" in hazard_name.lower():
                    print(f"Path would pass directly through the storm!")
                
                return False

        return True

    def _heuristic(self, node, goal):
        """A* heuristic function - simple Euclidean distance."""
        return self._distance(node, goal)

    def find_path(self, time_limit=None, iterations_limit=100):
        """
        Find an optimal path through all hospitals while avoiding hazards.

        Args:
            time_limit (float): Maximum time to run in seconds
            iterations_limit (int): Maximum number of iterations

        Returns:
            Route: Best route found
        """
        # Make sure we have a start point
        if not self.start_point:
            if self.origin:
                self.start_point = self.origin
            elif self.hospitals:
                self.start_point = self.hospitals[0]
            else:
                print("Error: No start point or hospitals provided")
                return Route([])

        # Prepare the set of unvisited hospitals
        unvisited = set(self.hospitals)
        
        # Make sure the start point is not in the unvisited set if it's one of the hospitals
        if self.start_point in unvisited:
            unvisited.remove(self.start_point)

        # Identify the first hospital in the original list for exclusion if needed
        first_hospital = None
        if self.exclude_first_hospital and self.hospitals:
            first_hospital = self.hospitals[0]

        # Begin with the current position
        current = self.start_point
        path = [current]
        total_distance = 0

        # For tracking the best path across all iterations
        best_ever_path = None
        best_ever_distance = float('inf')

        # While there are still hospitals to visit
        while unvisited and self.iterations < iterations_limit:
            self.iterations += 1
            
            # Find the best next hospital using a combination of distance and safety
            best_next = None
            best_cost = float('inf')

            # Display current iteration status
            print(f"\nIteration {self.iterations}: Current at {current.name}, {len(unvisited)} hospitals remaining")

            # Evaluate each unvisited hospital
            for hospital in unvisited:
                self.nodes_explored += 1

                # Skip the first hospital in the list as the first move
                if self.iterations == 1 and hospital == first_hospital and self.exclude_first_hospital:
                    print(f"  SKIPPING {hospital.name} as it's the first hospital in the list")
                    continue

                # Check if path to this hospital is safe
                print(f"  Evaluating path to {hospital.name}...")
                path_safe = self._is_safe_path(current, hospital)

                # Calculate cost (distance with safety penalty if needed)
                cost = self._distance(current, hospital)
                
                # Print path evaluation results
                if path_safe:
                    print(f"  Path to {hospital.name}: distance={cost:.2f}, safe=YES")
                else:
                    # Apply penalty to unsafe paths
                    penalized_cost = cost * 10
                    print(f"  Path to {hospital.name}: distance={cost:.2f}, penalized={penalized_cost:.2f}, safe=NO")
                    cost = penalized_cost

                # Update best next hospital if this one is better
                if cost < best_cost:
                    best_cost = cost
                    best_next = hospital

            # Move to the best next hospital
            if best_next:
                print(f"  Selected next stop: {best_next.name} (cost: {best_cost:.2f})")
                current = best_next
                path.append(current)
                unvisited.remove(current)
                total_distance += best_cost
            else:
                # Special case: If we couldn't find any valid next stop and we skipped the first hospital,
                # now consider it as we might have no choice
                if self.iterations == 1 and first_hospital in unvisited and self.exclude_first_hospital:
                    print("  No valid next stop found! Reconsidering the first hospital...")
                    
                    hospital = first_hospital
                    print(f"  Evaluating path to {hospital.name}...")
                    path_safe = self._is_safe_path(current, hospital)
                    cost = self._distance(current, hospital)
                    
                    if not path_safe:
                        penalized_cost = cost * 10
                        print(f"  Path to {hospital.name}: distance={cost:.2f}, penalized={penalized_cost:.2f}, safe=NO")
                        cost = penalized_cost
                    else:
                        print(f"  Path to {hospital.name}: distance={cost:.2f}, safe=YES")
                    
                    current = hospital
                    path.append(current)
                    unvisited.remove(current)
                    total_distance += cost
                    print(f"  Selected next stop: {hospital.name} (cost: {cost:.2f})")
                else:
                    print("  No valid next stop found!")
                    break

        # Complete the route by returning to origin if specified
        if self.origin and current != self.origin:
            # Check if path back to origin is safe
            print(f"\nEvaluating return path to Origin...")
            path_safe = self._is_safe_path(current, self.origin)
            return_cost = self._distance(current, self.origin)
            
            if not path_safe:
                penalized_cost = return_cost * 10
                print(f"Return path to Origin: distance={return_cost:.2f}, penalized={penalized_cost:.2f}, safe=NO")
                return_cost = penalized_cost
            else:
                print(f"Return path to Origin: distance={return_cost:.2f}, safe=YES")
            
            total_distance += return_cost
            path.append(self.origin)

        # Create the route object
        route = Route(path)
        
        # Update the best path if this one is better
        if total_distance < self.best_distance:
            self.best_distance = total_distance
            self.best_path = route

        # Update the best ever path if this iteration's path is better
        if total_distance < best_ever_distance:
            best_ever_distance = total_distance
            best_ever_path = route

        # Print the route summary in the requested format
        route_string = " -> ".join(h.name for h in path)
        print(f"\Route {self.iterations}: Best distance: {total_distance:.2f} km Best ever distance: {best_ever_distance:.2f} km")
        print(f"Route: {route_string}")
        print("-" * 60)

        return route

    def get_final_route(self):
        """
        Get the best route found.

        Returns:
            Route: Best route found
        """
        return self.best_path