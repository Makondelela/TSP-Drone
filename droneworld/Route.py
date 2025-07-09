class Route:
    def __init__(self, hospitals):
        self.hospitals = hospitals.copy()
        self.distance = 0
        self.calculate_distance()

    def calculate_distance(self):
        self.distance = 0
        for i in range(len(self.hospitals)):
            current = self.hospitals[i]
            next_hospital = self.hospitals[(i + 1) % len(self.hospitals)]
            self.distance += current.distance_to(next_hospital)
        return self.distance

    def __repr__(self):
        return f"Route(hospitals={len(self.hospitals)}, distance={self.distance:.2f})"