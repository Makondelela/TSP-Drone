# droneworld/WeatherHazard.py

import random


class WeatherHazard:
    """
    Represents a weather hazard that acts as an obstacle in the drone's path.
    Weather hazards can include rain, wind, fog, or storms that impede drone navigation.
    """

    HAZARD_TYPES = ['rain', 'storm', 'fog', 'wind', 'turbulence']

    def __init__(self, x=0, y=0, width=2, height=2, hazard_type=None, intensity=None):
        """
        Initialize a weather hazard at a specific location.
        
        Args:
            x (float): X coordinate of the hazard
            y (float): Y coordinate of the hazard
            width (float): Width of the hazard area
            height (float): Height of the hazard area
            hazard_type (str): Type of weather hazard ('rain', 'storm', 'fog', 'wind', 'turbulence')
            intensity (str): Intensity level ('low', 'medium', 'high')
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hazard_type = hazard_type or random.choice(self.HAZARD_TYPES)
        self.intensity = intensity or random.choice(['low', 'medium', 'high'])

    def to_dict(self):
        """
        Convert the hazard to a dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation of the weather hazard
        """
        return {
            'type': 'weatherHazard',
            'hazard_type': self.hazard_type,
            'intensity': self.intensity,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'name': f'{self.intensity.capitalize()} {self.hazard_type}',
            'description': f'A {self.intensity} intensity {self.hazard_type} zone that may affect drone flight'
        }

    @classmethod
    def generate_on_route(cls, start_point, end_point, size_range=(1, 2)):
        """
        Generate a weather hazard on a route segment between two points.
        
        Args:
            start_point (dict): Starting point with x, y coordinates
            end_point (dict): Ending point with x, y coordinates
            size_range (tuple): Range for hazard size (min, max)
            
        Returns:
            WeatherHazard: A new weather hazard instance positioned on the path
        """
        # Position the hazard somewhere along the path
        ratio = random.uniform(0.3, 0.7)
        x = start_point['x'] + ratio * (end_point['x'] - start_point['x'])
        y = start_point['y'] + ratio * (end_point['y'] - start_point['y'])

        # Random size within the specified range
        width = random.uniform(size_range[0], size_range[1])
        height = random.uniform(size_range[0], size_range[1])

        return cls(x=x, y=y, width=width, height=height)
