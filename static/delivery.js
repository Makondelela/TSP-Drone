// Connect to WebSocket
const socket = io();
let routeDetails = [];
let deliveryHistory = [];

// Get initial drone status
fetch('/drone-status')
    .then(response => response.json())
    .then(data => {
        if (data.route && data.route.length > 0) {
            routeDetails = data.route;
            updateMap();
            updateDronePosition(data);
            updateStatusInfo(data);
            updateRouteTable(data);
        }
    });

// Listen for real-time updates
socket.on('drone_update', function(data) {
    updateDronePosition(data);
    updateStatusInfo(data);
    updateRouteTable(data);
    
    // Check if we've arrived at a new stop
    if (data.history && data.history.length > deliveryHistory.length) {
        const newStop = data.history[data.history.length - 1];
        showNotification(`Arrived at ${newStop.name}`);
        deliveryHistory = data.history;
    }
});

socket.on('delivery_complete', function(data) {
    updateDronePosition(data);
    updateStatusInfo(data);
    updateRouteTable(data);
    showNotification('Delivery Complete! Drone has returned to origin.');
});

function updateMap() {
    const mapContainer = document.getElementById('map-container');
    const width = mapContainer.offsetWidth;
    const height = mapContainer.offsetHeight;
    
    // Clear existing elements except drone
    const elementsToRemove = document.querySelectorAll('.path, .hospital, .weather-hazard');
    elementsToRemove.forEach(el => el.remove());
    
    // Calculate scale factors
    const maxX = Math.max(...routeDetails.map(h => h.x));
    const maxY = Math.max(...routeDetails.map(h => h.y));
    const scaleX = (width - 20) / maxX;
    const scaleY = (height - 20) / maxY;
    
    // Add hospitals and hazards
    routeDetails.forEach((point, index) => {
        const mapX = point.x * scaleX + 10;
        const mapY = height - (point.y * scaleY + 10);
        
        // Render weather hazards
        if (point.type === 'weatherHazard') {
            // Create weather hazard element
            const hazardElement = document.createElement('div');
            hazardElement.className = 'weather-hazard';
            
            // Add hazard type as additional class for styling
            hazardElement.classList.add(point.hazard_type);
            hazardElement.classList.add(point.intensity);
            
            hazardElement.style.left = `${mapX}px`;
            hazardElement.style.top = `${mapY}px`;
            hazardElement.style.width = `${point.width * scaleX}px`;
            hazardElement.style.height = `${point.height * scaleY}px`;
            hazardElement.title = point.name;
            
            // Create label
            const label = document.createElement('div');
            label.className = 'hazard-label';
            label.textContent = point.name;
            hazardElement.appendChild(label);
            
            mapContainer.appendChild(hazardElement);
            return; // Skip adding hospital element for hazards
        }
        
        // Add hospitals
        const hospitalElement = document.createElement('div');
        hospitalElement.className = 'hospital';
        if (index === 0 || index === routeDetails.length - 1) {
            hospitalElement.classList.add('origin');
        }
        hospitalElement.style.left = `${mapX}px`;
        hospitalElement.style.top = `${mapY}px`;
        hospitalElement.title = point.name;
        
        const label = document.createElement('div');
        label.style.position = 'absolute';
        label.style.left = '8px';
        label.style.top = '8px';
        label.style.fontSize = '10px';
        label.textContent = point.name;
        hospitalElement.appendChild(label);
        
        mapContainer.appendChild(hospitalElement);
    });
    
    // Draw paths between stops (excluding hazards)
    const routePointsOnly = routeDetails.filter(point => !point.type || point.type !== 'weatherHazard');
    
    for (let i = 0; i < routePointsOnly.length - 1; i++) {
        const start = routePointsOnly[i];
        const end = routePointsOnly[i + 1];
        
        const startX = start.x * scaleX + 10;
        const startY = height - (start.y * scaleY + 10);

        const endX = end.x * scaleX + 10;
        const endY = height - (end.y * scaleY + 10);
        
        const dx = endX - startX;
        const dy = endY - startY;
        const length = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx) * 180 / Math.PI;
        
        const path = document.createElement('div');
        path.className = 'path';
        path.style.width = `${length}px`;
        path.style.left = `${startX}px`;
        path.style.top = `${startY}px`;
        path.style.transform = `rotate(${angle}deg)`;
        
        mapContainer.appendChild(path);
    }
}

function updateDronePosition(data) {
    if (!data.current_location) return;
    
    const drone = document.getElementById('drone');
    const mapContainer = document.getElementById('map-container');
    const width = mapContainer.offsetWidth;
    const height = mapContainer.offsetHeight;
    
    // Calculate scale factors
    const maxX = Math.max(...routeDetails.map(h => h.x));
    const maxY = Math.max(...routeDetails.map(h => h.y));
    const scaleX = (width - 20) / maxX;
    const scaleY = (height - 20) / maxY;
    
    const x = data.current_location[0] * scaleX + 10;
    const y = height - (data.current_location[1] * scaleY + 10);
    
    // Animate the drone movement
    drone.style.transition = 'left 0.2s ease-out, top 0.2s ease-out';
    drone.style.left = `${x}px`;
    drone.style.top = `${y}px`;
    
    // Check if drone is in a hazard area
    if (data.hazards && data.hazards.length > 0) {
        let inHazard = false;
        const droneX = data.current_location[0];
        const droneY = data.current_location[1];
        
        data.hazards.forEach(hazard => {
            // Simple bounding box check
            if (
                droneX >= hazard.x - hazard.width/2 && 
                droneX <= hazard.x + hazard.width/2 &&
                droneY >= hazard.y - hazard.height/2 && 
                droneY <= hazard.y + hazard.height/2
            ) {
                inHazard = true;
                showNotification(`Warning: Drone entering ${hazard.name} zone!`);
                
                // Add visual indication that drone is in hazard
                drone.classList.add('in-hazard');
            }
        });
        
        if (!inHazard) {
            drone.classList.remove('in-hazard');
        }
    }
}

function updateStatusInfo(data) {
    const progressBar = document.getElementById('progress-bar');
    const progress = Math.min(Math.round(data.progress), 100);
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${progress}%`;
    
    // Update weather hazard info if available
    const weatherInfo = document.getElementById('weather-info');
    if (weatherInfo && data.hazards && data.hazards.length > 0) {
        const hazardsList = data.hazards.map(h => 
            `<div class="hazard-item ${h.hazard_type} ${h.intensity}">
                <span class="hazard-name">${h.name}</span>
            </div>`
        ).join('');
        
        weatherInfo.innerHTML = `
            <h4>Weather Hazards</h4>
            <div class="hazards-list">${hazardsList}</div>
        `;
        weatherInfo.style.display = 'block';
    } else if (weatherInfo) {
        weatherInfo.style.display = 'none';
    }
}

function updateRouteTable(data) {
    if (!data.route || data.route.length === 0) return;
    
    const tableBody = document.getElementById('route-body');
    tableBody.innerHTML = '';
    
    data.route.forEach((stop, index) => {
        // Skip hazards in the route table
        if (stop.type === 'weatherHazard') return;
        
        const row = document.createElement('tr');
        
        // Determine stop status
        let statusText = 'Pending';
        let statusClass = '';
        let arrivalTime = '-';
        
        // Check if this stop is completed
        const historyEntry = data.history?.find(h => h.stop === index);
        if (historyEntry) {
            statusText = 'Completed';
            statusClass = 'stop-completed';
            arrivalTime = historyEntry.time;
        } 
        // Check if this is the current destination
        else if (index === data.stops_completed + 1) {
            statusText = 'In Progress';
            statusClass = 'current-stop';
        }
        
        row.innerHTML = `
            <td>(${stop.x},${stop.y})</td>
            <td>${stop.name}</td>
            <td class="${statusClass}">${statusText}</td>
            <td>${arrivalTime}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function showNotification(message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.style.display = 'block';
    notification.style.animation = 'none';
    setTimeout(() => {
        notification.style.animation = 'fadeOut 5s forwards';
    }, 10);
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}

// Resize handler for responsive map
window.addEventListener('resize', updateMap);