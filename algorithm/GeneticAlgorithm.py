import random
from droneworld.Route import Route


class GeneticAlgorithm:
    def __init__(self, hospitals, population_size, mutation_rate, origin=None):
        self.hospitals = hospitals
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.origin = origin
        self.population = []
        self.elitism_rate = 0.1
        self.tournament_size = 5
        self.best_ever_route = None
        self.initialize_population()

    def initialize_population(self):
        self.population = []
        self.population.append(self.create_greedy_route())
        
        reversed_hospitals = self.hospitals.copy()
        reversed_hospitals.reverse()
        self.population.append(Route(reversed_hospitals))

        while len(self.population) < self.population_size:
            shuffled = self.hospitals.copy()
            random.shuffle(shuffled)
            self.population.append(Route(shuffled))

        # Sort by complete distance including origin
        self.population.sort(key=lambda r: self.calculate_complete_distance(r))
        self.best_ever_route = Route(self.population[0].hospitals.copy())

    def create_greedy_route(self):
        route = []
        unvisited = set(self.hospitals)
        current = random.choice(self.hospitals)
        route.append(current)
        unvisited.remove(current)

        while unvisited:
            closest = min(unvisited, key=lambda h: current.distance_to(h))
            current = closest
            route.append(current)
            unvisited.remove(current)

        return Route(route)

    def calculate_complete_distance(self, route):
        if not self.origin:
            return route.distance
            
        total = self.origin.distance_to(route.hospitals[0])
        total += route.distance
        total += route.hospitals[-1].distance_to(self.origin)
        return total

    def evolve(self, generations):
        no_improvement_count = 0
        previous_best_complete = float('inf')

        for generation in range(generations):
            # Sort population by complete distance
            self.population.sort(key=lambda r: self.calculate_complete_distance(r))
            elites_count = int(self.population_size * self.elitism_rate)
            new_population = self.population[:elites_count]

            # Generate offspring using complete distance for selection
            while len(new_population) < self.population_size:
                parent1 = self.select_parent()
                parent2 = self.select_parent()

                if random.random() < 0.9:
                    child = self.crossover(parent1, parent2)
                else:
                    child = Route(parent1.hospitals.copy())

                if random.random() < self.get_mutation_rate(generation, generations):
                    self.mutate(child)

                new_population.append(child)

            # Update and sort population
            self.population = new_population
            self.population.sort(key=lambda r: self.calculate_complete_distance(r))

            # Update best ever route using complete distance
            current_best = self.population[0]
            current_complete = self.calculate_complete_distance(current_best)
            best_ever_complete = self.calculate_complete_distance(self.best_ever_route)
            
            if current_complete < best_ever_complete:
                self.best_ever_route = Route(current_best.hospitals.copy())

            # Check stagnation using complete distance
            if current_complete < previous_best_complete:
                previous_best_complete = current_complete
                no_improvement_count = 0
            else:
                no_improvement_count += 1

            # Inject diversity if needed
            if no_improvement_count >= 15:
                self.inject_diversity()
                no_improvement_count = 0

            # Logging
            route_str = self.get_complete_route_string(current_best) if self.origin else self.get_route_string(current_best)
            
            print(f"Generation {generation + 1}: Best distance: {current_complete:.2f} km")
            print(f"Best ever distance: {self.calculate_complete_distance(self.best_ever_route):.2f} km")
            print(f"Route: {route_str}")
            print("------------------------------------------------------------")

    def get_mutation_rate(self, current_gen, total_gens):
        return self.mutation_rate * (1.0 - (current_gen / total_gens))

    def inject_diversity(self):
        diversity_count = int(self.population_size * 0.3)
        start_index = self.population_size - diversity_count

        for i in range(start_index, self.population_size):
            shuffled = self.hospitals.copy()
            random.shuffle(shuffled)
            self.population[i] = Route(shuffled)

        for i in range(start_index, start_index + diversity_count // 2):
            if i < self.population_size:
                improved = self.two_opt_improvement(random.choice(self.population))
                self.population[i] = improved

    def two_opt_improvement(self, route):
        best = route.hospitals.copy()
        best_distance = self.calculate_complete_distance(Route(best))
        improved = True

        while improved:
            improved = False
            for i in range(len(best) - 1):
                for j in range(i + 1, len(best)):
                    new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                    new_distance = self.calculate_complete_distance(Route(new_route))
                    if new_distance < best_distance:
                        best = new_route
                        best_distance = new_distance
                        improved = True
        return Route(best)

    def select_parent(self):
        tournament = random.sample(self.population, self.tournament_size)
        return min(tournament, key=lambda r: self.calculate_complete_distance(r))

    def crossover(self, parent1, parent2):
        size = len(self.hospitals)
        start, end = sorted([random.randint(0, size), random.randint(0, size)])
        child = [None]*size

        child[start:end] = parent1.hospitals[start:end]

        current_pos = 0
        for hospital in parent2.hospitals:
            if hospital not in child:
                while current_pos < size and child[current_pos] is not None:
                    current_pos += 1
                if current_pos >= size:
                    break
                child[current_pos] = hospital

        return Route([h for h in child if h is not None])

    def mutate(self, route):
        mutation_type = random.choice(['swap', 'reverse', 'insert'])
        
        if mutation_type == 'swap':
            i, j = random.sample(range(len(route.hospitals)), 2)
            route.hospitals[i], route.hospitals[j] = route.hospitals[j], route.hospitals[i]
        
        elif mutation_type == 'reverse':
            start, end = sorted(random.sample(range(len(route.hospitals)), 2))
            route.hospitals[start:end+1] = route.hospitals[start:end+1][::-1]
        
        elif mutation_type == 'insert':
            idx = random.randint(0, len(route.hospitals)-1)
            route.hospitals.insert(random.randint(0, len(route.hospitals)-1), route.hospitals.pop(idx))
        
        route.calculate_distance()

    def get_final_route(self):
        return self.best_ever_route

    def get_route_string(self, route):
        return " -> ".join(h.name for h in route.hospitals) + f" -> {route.hospitals[0].name}"

    def get_complete_route_string(self, route):
        if not self.origin:
            return self.get_route_string(route)
        return (f"{self.origin.name} -> " + 
                " -> ".join(h.name for h in route.hospitals) + 
                f" -> {self.origin.name}")

