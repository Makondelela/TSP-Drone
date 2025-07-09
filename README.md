# Drone Delivery Route Optimization System

An AI-powered medical delivery pathfinding system that optimizes drone routes for delivering medical supplies to multiple hospitals. The system uses genetic algorithms for route optimization, simulates drone deliveries in real-time, and handles weather hazards with dynamic rerouting.

## Features

* **Genetic Algorithm Optimization**: Finds the most efficient delivery route among selected hospitals
* **Weather Hazard Detection**: Identifies and avoids weather hazards during delivery
* **Real-time Drone Simulation**: Visualizes drone movement and delivery progress
* **Dynamic Rerouting**: Automatically recalculates paths when hazards are detected
* **Interactive Dashboard**: User-friendly interface for hospital selection and route visualization

## Project Structure

```
drone-delivery-system/
├── algorithm/                 # Optimization algorithms
│   ├── GeneticAlgorithm.py    # Genetic algorithm implementation
│   └── HeuristicSearch.py     # A* search for hazard avoidance
├── droneworld/                # Domain models
│   ├── Drone.py               # Drone movement and status tracking
│   ├── Hospital.py            # Hospital location model
│   ├── Route.py               # Route representation
│   ├── Reroute.py             # Hazard avoidance logic
│   └── WeatherHazard.py       # Weather hazard modeling
├── simulation/                # Delivery simulation
│   └── PerformDelivery.py     # Main simulation controller
├── static/                    # Frontend assets
│   ├── delivery.js            # Delivery tracking logic
│   ├── script.js              # Route optimization UI
│   └── styles.css             # Application styling
├── templates/                 # HTML templates
│   ├── delivery.html          # Delivery tracking page
│   └── index.html             # Main application page
├── __init__.py                # Flask application setup
└── README.md                  # Project documentation
```

## Getting Started

### Prerequisites

* Python 3.8+
* Node.js (for Socket.IO)
* Flask
* Flask-SocketIO

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/drone-delivery-system.git
   cd drone-delivery-system
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-socketio
   ```

4. **Run the application**
   ```bash
   python __init__.py
   ```

5. **Access the application**
   
   Open your browser and navigate to: `http://localhost:5000`

## Usage

### Hospital Selection
* Select hospitals from the list
* Use "Select All" or "Deselect All" for bulk operations

### Route Optimization
* Click "Optimize Route" to calculate the most efficient path
* View optimized route details and visualization

### Start Delivery
* Click "Start Delivery" to begin the simulation
* Track drone progress in real-time on the map
* Monitor delivery status in the route table

## Features in Action

* **Weather Hazard Detection**: The system automatically detects and highlights weather hazards
* **Dynamic Rerouting**: When hazards are encountered, the drone reroutes to avoid them
* **Progress Tracking**: Real-time progress bar shows delivery completion percentage
* **Notifications**: System alerts for hazard detection and delivery milestones

## Customization

* **Hospital locations**: Modify hospital coordinates in `__init__.py`
* **Drone speed**: Adjust movement parameters in `Drone.py`
* **Hazard parameters**: Configure weather conditions in `WeatherHazard.py`
* **Algorithm settings**: Tweak optimization parameters in `GeneticAlgorithm.py`

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request


