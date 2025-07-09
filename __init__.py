import threading

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from droneworld.Hospital import Hospital
from droneworld.Route import Route
from algorithm.GeneticAlgorithm import GeneticAlgorithm
from simulation.PerformDelivery import PerformDelivery

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

delivery_controller = PerformDelivery()
route_details = []  # This will be set by the optimize function
ALL_HOSPITALS = [
    Hospital("origin", 0, 0),
    Hospital("Chris_Hani_Baragwanath_JHB", 25, 100),
    Hospital("Addington_Durban", 30, 100),
    Hospital("Universitas_Bloemfontein", 100, 0),
    Hospital("Steve_Biko_Pretoria", 50, 75),
    Hospital("Tygerberg_CapeTown", 10, 90),
    Hospital("Charlotte_Maxeke_JHB", 80, 20),
    Hospital("King_Edward_VIII_Durban", 40, 60),
    Hospital("Pelonomi_Bloemfontein", 90, 30),
    Hospital("MediClinic_Sandton", 70, 40),
    Hospital("Netcare_Umhlanga", 45, 85),
    Hospital("Milpark_Hospital_JHB", 55, 95),
    Hospital("Stellenbosch_Hospital", 20, 50),
    Hospital("Paarl_Hospital", 35, 65),
    Hospital("Livingstone_Hospital_PE", 75, 25),
    Hospital("Nelson_Mandela_Hospital_Mthatha", 60, 35),
    Hospital("Polokwane_Provincial_Hospital", 85, 15),
    Hospital("George_Hospital", 15, 55),
    Hospital("Kimberley_Hospital", 95, 10),
]

ORIGIN = ALL_HOSPITALS[0]
SELECTABLE_HOSPITALS = ALL_HOSPITALS[1:]


def get_hospital_by_name(name):
    for hospital in ALL_HOSPITALS:
        if hospital.name == name:
            return hospital
    return None


@app.route('/')
def home():
    origin_data = {'name': ORIGIN.name, 'x': ORIGIN.x, 'y': ORIGIN.y}
    hospitals_data = [{'name': h.name, 'x': h.x, 'y': h.y} for h in SELECTABLE_HOSPITALS]
    return render_template('index.html', origin=origin_data, hospitals=hospitals_data)


# Add these routes to the Flask app

@app.route('/pause-delivery')
def pause_delivery():
    """Pause the current delivery simulation"""
    success = delivery_controller.pause_delivery()
    return jsonify({
        'success': success, 
        'message': 'Delivery paused' if success else 'Delivery was not running or already paused'
    })


@app.route('/continue-delivery')
def continue_delivery():
    """Continue the delivery after it was paused"""
    success = delivery_controller.continue_delivery()
    return jsonify({
        'success': success, 
        'message': 'Delivery continued' if success else 'Delivery was not paused'
    })


@app.route('/reroute')
def reroute_delivery():
    """Force a reroute of the current delivery path"""
    if delivery_controller.is_running and not delivery_controller.is_paused:
        # Get current position
        current_x, current_y = delivery_controller.drone.get_position()
        
        # Identify unvisited hospitals
        unvisited_hospitals = []
        for i in range(delivery_controller.drone.current_stop_index + 1, len(delivery_controller.drone.route)):
            if i < len(delivery_controller.drone.route):
                unvisited_hospitals.append(delivery_controller.drone.route[i])
        
        # If we still have hospitals to visit, reroute
        if unvisited_hospitals:
            delivery_controller.rerouting_in_progress = True
            
            # Find new route
            new_route = delivery_controller.router.find_best_route(
                unvisited_hospitals, 
                delivery_controller.hazards, 
                current_x, 
                current_y
            )
            
            # Update the drone's route
            delivery_controller.drone.set_route(new_route)
            
            # Update the current route for the frontend
            delivery_controller.current_route = new_route.copy()
            if delivery_controller.hazards:
                for hazard in delivery_controller.hazards:
                    delivery_controller.current_route.append(hazard)
            
            delivery_controller.rerouting_in_progress = False
            
            return jsonify({
                'success': True,
                'message': f'Rerouted with {len(new_route)} stops'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No remaining hospitals to visit'
            })
    else:
        return jsonify({
            'success': False,
            'message': 'Delivery not running or is paused'
        })

@app.route('/optimize', methods=['POST'])
def optimize():
    global route_details  # Add global reference so we can modify it

    selected_hospitals = request.json.get('selected_hospitals', [])
    hospitals = [get_hospital_by_name(name) for name in selected_hospitals]

    if len(hospitals) < 2:
        return jsonify({'success': False, 'message': 'Please select at least 2 hospitals.'})

    hospitals = [h for h in hospitals if h.name != ORIGIN.name]

    number_of_runs = 1
    generations_per_run = 100
    population_size = 100
    mutation_rate = 0.05

    best_overall_distance = float('inf')
    best_overall_route = None

    for run in range(number_of_runs):
        ga = GeneticAlgorithm(hospitals, population_size, mutation_rate, origin=ORIGIN)
        ga.evolve(generations_per_run)
        best_run_route = ga.get_final_route()
        complete_distance = ga.calculate_complete_distance(best_run_route)

        if complete_distance < best_overall_distance:
            best_overall_distance = complete_distance
            best_overall_route = Route(best_run_route.hospitals.copy())

    # Update the global route_details
    route_details = [{'stop': 1, 'name': ORIGIN.name, 'x': ORIGIN.x, 'y': ORIGIN.y}]
    for i, hospital in enumerate(best_overall_route.hospitals, 2):
        route_details.append({'stop': i, 'name': hospital.name, 'x': hospital.x, 'y': hospital.y})
    route_details.append(
        {'stop': len(best_overall_route.hospitals) + 2, 'name': f"{ORIGIN.name} (return)", 'x': ORIGIN.x,
         'y': ORIGIN.y})

    return jsonify({
        'success': True,
        'distance': round(best_overall_distance, 2),
        'route_string': ORIGIN.name + " -> " + " -> ".join(
            h.name for h in best_overall_route.hospitals) + f" -> {ORIGIN.name}",
        'route_details': route_details
    })


@app.route('/drone-status')
def drone_status():
    """Get the current status of the drone delivery"""
    status = delivery_controller.get_current_status()
    return jsonify(status)


@app.route('/stop-delivery')
def stop_delivery():
    """Stop the current delivery simulation"""
    delivery_controller.stop_delivery()
    return jsonify({'success': True, 'message': 'Delivery stopped'})


@app.route('/start-delivery')
def start_delivery():
    """Start the socket communication and render the delivery page."""
    global route_details  # Add global reference

    # Check if we have a valid route
    if not route_details:
        return jsonify({'success': False, 'message': 'No route available. Please optimize a route first.'}), 400

    def on_drone_update(status):
        socketio.emit('drone_update', status)

    def on_delivery_complete(status):
        socketio.emit('delivery_complete', status)

    # Set up callbacks and start delivery
    delivery_controller.register_update_callback(on_drone_update)
    delivery_controller.register_complete_callback(on_delivery_complete)
    delivery_controller.start_delivery(route_details)

    def start_socketio():
        # Start SocketIO in a separate thread
        socketio.run(app, debug=True, use_reloader=False)

    # Start the SocketIO server in a new thread when /start-delivery is accessed
    thread = threading.Thread(target=start_socketio)
    thread.daemon = True  # Making it a daemon thread to exit when main thread exits
    thread.start()

    return render_template('delivery.html')


if __name__ == '__main__':
    app.run(debug=True)