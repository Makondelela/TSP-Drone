// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const selectAllBtn = document.getElementById('selectAll');
    const deselectAllBtn = document.getElementById('deselectAll');
    const optimizeBtn = document.getElementById('optimizeRoute');
    const hospitalCheckboxes = document.querySelectorAll('.hospital-checkbox');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const results = document.getElementById('results');
    const noSelection = document.getElementById('noSelection');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const totalDistance = document.getElementById('totalDistance');
    const routeSequence = document.getElementById('routeSequence');
    const routeMap = document.getElementById('routeMap');
    const routeSummary = document.getElementById('routeSummary');
    const summaryHeader = document.querySelector('.summary-header');

    // Summary panel state management
    let isSummaryCollapsed = true;
    

    // Toggle summary collapse/expand when header is clicked
    summaryHeader.addEventListener('click', function() {
        isSummaryCollapsed = !isSummaryCollapsed;
        routeSummary.classList.toggle('collapsed', isSummaryCollapsed);
    });

    // Select/Deselect all functionality
    selectAllBtn.addEventListener('click', function() {
        hospitalCheckboxes.forEach(checkbox => checkbox.checked = true);
    });

    deselectAllBtn.addEventListener('click', function() {
        hospitalCheckboxes.forEach(checkbox => checkbox.checked = false);
    });

    // Optimize route handler
    optimizeBtn.addEventListener('click', async function() {
        const selectedHospitals = Array.from(hospitalCheckboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);

        if (selectedHospitals.length < 2) {
            showError('Please select at least 2 hospitals for route optimization.');
            return;
        }

        // Reset UI states
        noSelection.classList.add('hidden');
        results.classList.add('hidden');
        errorMessage.classList.add('hidden');
        routeSummary.classList.remove('hidden');
        routeSummary.classList.remove('collapsed');
        loadingIndicator.classList.remove('hidden');

        try {
            const response = await fetch('/optimize', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ selected_hospitals: selectedHospitals })
            });

            loadingIndicator.classList.add('hidden');
            
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            
            const data = await response.json();
            
            if (data.success) {
                displayResults(data);
            } else {
                showError(data.message || 'An error occurred during route optimization.');
            }
        } catch (error) {
            loadingIndicator.classList.add('hidden');
            showError('An error occurred: ' + error.message);
        }
    });

    // Display results
    // Update the displayResults function to also show the start delivery button
    function displayResults(data) {
        totalDistance.textContent = data.distance.toFixed(2) + ' km';
        
        routeSequence.innerHTML = '';
        data.route_details.forEach(hospital => {
            const li = document.createElement('li');
            li.textContent = `Stop ${hospital.stop}: ${hospital.name.replace(/_/g, ' ')}`;
            routeSequence.appendChild(li);
        });

        drawRouteMap(data.route_details);
        results.classList.remove('hidden');
        routeSummary.classList.remove('hidden');
        routeSummary.classList.add('collapsed');
        noSelection.classList.add('hidden');
        
        // Make sure the Start Delivery button is visible and has the current route data
        const startDeliveryBtn = document.getElementById('startDeliveryBtn');
        startDeliveryBtn.href = `/start-delivery`;
    }

    // Canvas drawing functions
    function drawRouteMap(routeDetails) {
        const ctx = routeMap.getContext('2d');
        const width = routeMap.width;
        const height = routeMap.height;
        
        ctx.clearRect(0, 0, width, height);

        // Ensure there are coordinates to draw
        if (!routeDetails || routeDetails.length === 0) {
            return;
        }

        // Extract coordinates
        const coords = routeDetails.map(h => ({x: parseFloat(h.x), y: parseFloat(h.y)}));
        
        // Calculate bounds
        const minX = Math.min(...coords.map(c => c.x));
        const maxX = Math.max(...coords.map(c => c.x));
        const minY = Math.min(...coords.map(c => c.y));
        const maxY = Math.max(...coords.map(c => c.y));
        
        // Add padding for better visualization
        const padding = 50;
        
        // Calculate scale factors (protect against zero division)
        const rangeX = maxX - minX || 1;
        const rangeY = maxY - minY || 1;
        const scaleX = (width - padding*2) / rangeX;
        const scaleY = (height - padding*2) / rangeY;

        // Transformation functions
        const transform = {
            x: x => padding + (x - minX) * scaleX,
            y: y => height - padding - (y - minY) * scaleY
        };

        // Draw grid and axes
        drawGrid(ctx, width, height, padding, transform, minX, maxX, minY, maxY);
        
        // Draw route path
        ctx.strokeStyle = '#3498db';
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        // Start at origin
        const firstPoint = {x: routeDetails[0].x, y: routeDetails[0].y};
        ctx.moveTo(transform.x(firstPoint.x), transform.y(firstPoint.y));
        
        // Connect all points in sequence
        for (let i = 1; i < routeDetails.length; i++) {
            const point = {x: routeDetails[i].x, y: routeDetails[i].y};
            ctx.lineTo(transform.x(point.x), transform.y(point.y));
        }
        
        // Connect back to origin if it's a round trip
        if (routeDetails.length > 2) {
            const lastPoint = routeDetails[routeDetails.length - 1];
            const firstPoint = routeDetails[0];
            
            // Only connect back if they're different points
            if (lastPoint.x !== firstPoint.x || lastPoint.y !== firstPoint.y) {
                ctx.lineTo(transform.x(firstPoint.x), transform.y(firstPoint.y));
            }
        }
        
        ctx.stroke();

        // Draw points
        routeDetails.forEach((hospital, index) => {
            drawHospitalPoint(ctx, transform, hospital, index === 0);
        });
    }

    function drawGrid(ctx, width, height, padding, transform, minX, maxX, minY, maxY) {
        ctx.strokeStyle = '#ddd';
        ctx.lineWidth = 1;
        
        // Draw axes
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding); // X-axis
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding); // Y-axis
        ctx.stroke();

        // Calculate grid step size based on data range
        const rangeX = maxX - minX;
        const rangeY = maxY - minY;
        
        const stepX = Math.ceil(rangeX / 5);  // 5 steps on X-axis
        const stepY = Math.ceil(rangeY / 5);  // 5 steps on Y-axis

        // Grid lines and labels
        ctx.strokeStyle = '#eee';
        ctx.fillStyle = '#888';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        // X-axis grid lines and labels
        for (let x = Math.floor(minX/stepX) * stepX; x <= maxX; x += stepX) {
            const xPos = transform.x(x);
            ctx.beginPath();
            ctx.moveTo(xPos, padding);
            ctx.lineTo(xPos, height - padding);
            ctx.stroke();
            ctx.fillText(x.toString(), xPos, height - padding + 15);
        }
        
        // Y-axis grid lines and labels
        ctx.textAlign = 'right';
        for (let y = Math.floor(minY/stepY) * stepY; y <= maxY; y += stepY) {
            const yPos = transform.y(y);
            ctx.beginPath();
            ctx.moveTo(padding, yPos);
            ctx.lineTo(width - padding, yPos);
            ctx.stroke();
            ctx.fillText(y.toString(), padding - 10, yPos + 5);
        }
    }

    function drawHospitalPoint(ctx, transform, hospital, isOrigin) {
        const x = transform.x(parseFloat(hospital.x));
        const y = transform.y(parseFloat(hospital.y));
        
        // Draw point
        ctx.fillStyle = isOrigin ? '#e74c3c' : '#3498db';
        ctx.beginPath();
        ctx.arc(x, y, isOrigin ? 8 : 6, 0, Math.PI * 2);
        ctx.fill();

        // Stop number
        ctx.fillStyle = 'white';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(hospital.stop.toString(), x, y);

        // Hospital name
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        
        const label = hospital.name.replace(/_/g, ' ');
        const displayName = label.length > 15 ? label.substring(0, 12) + '...' : label;
        
        ctx.fillText(displayName, x, y + 15);
    }

    // Error handling
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
        results.classList.add('hidden');
        routeSummary.classList.add('hidden');
        noSelection.classList.add('hidden');
    }
});