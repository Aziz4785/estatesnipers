// Initialize the map on the "dubaiMap" div with a given center and zoom
var map = L.map('dubaiMap').setView([25.2048, 55.2708], 10); // Centered on Dubai

// Add a base layer to the map (OpenStreetMap tiles)
/*L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);*/
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors, © CARTO',
    maxZoom: 19
}).addTo(map);



let currentAreaId = null; 
document.addEventListener('DOMContentLoaded', function () {
    // Set the default checked radio button (in settings)
    document.getElementById('avgMeterPrice').checked = true;
    const elements = document.querySelectorAll('.scrollable-container');
    //initialisation of scrollable-containers
    elements.forEach(function(ele) {
        let pos = { top: 0, left: 0, x: 0, y: 0 };

        const mouseDownHandler = function(e) {
            ele.style.cursor = 'grabbing';
            ele.style.userSelect = 'none';

            pos = {
                left: ele.scrollLeft,
                top: ele.scrollTop,
                x: e.clientX,
                y: e.clientY,
            };

            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        };

        const mouseMoveHandler = function(e) {
            const dx = e.clientX - pos.x;
            const dy = e.clientY - pos.y;

            ele.scrollTop = pos.top - dy;
            ele.scrollLeft = pos.left - dx;
        };

        const mouseUpHandler = function() {
            ele.style.cursor = 'grab';
            ele.style.removeProperty('user-select');

            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);
        };

        ele.addEventListener('mousedown', mouseDownHandler);
    });
});

// load the .geojson file to display the areas
function applyGeoJSONLayer(currentLegend) {
    fetch('http://estatesnipers-1a1823af05ea.herokuapp.com/dubai-areas')
    .then(response => response.json())
    .then(data => {
        //data[0] contains legends of map and data[1] contains the areas
        const legends = data[0];
        console.log("received data : ",data[1])
        const features = data[1].map(item => ({
            type: 'Feature',
            properties: item, // Store all item properties directly
            geometry: item.geometry
        }));
        const featureCollection = {
            type: 'FeatureCollection',
            features: features
        };
        
        // Clear existing GeoJSON layer
        if (window.geoJSONLayer) {
            window.geoJSONLayer.remove();
        }
        
        // Apply new GeoJSON layer with dynamic fill color
        window.geoJSONLayer = L.geoJSON(featureCollection, {
            style: feature => areaStyle(feature, currentFillColor),
            onEachFeature: onEachFeature
        }).addTo(map);

        updateLegend(legends[currentLegend]);
    })
    .catch(error => console.log('Error:', error));
}

// Add a click event listener to the close button outside the onEachFeature function
document.getElementById('close-panel').addEventListener('click', function() {
    document.getElementById('info-panel').style.display = 'none';
});


let rowIdCounter = 0; // Counter to assign a unique row ID

function addRow(name, level, isParent, parentRowId = null, avgMeterPriceId = null) {
    //parent rows are rows that are expandable

    const rowId = `row-${rowIdCounter++}`;
    const row = tableBody.insertRow();
    row.setAttribute('data-row-id', rowId);
    row.setAttribute('data-level', level);

    if (parentRowId) {
        //if parent row hide all children
        row.setAttribute('data-parent-id', parentRowId);
        row.style.display = 'none';
    }

    const indent = '&nbsp;'.repeat(level * 5);
    let contentCellHtml = isParent ? `${indent}<span class="expand-arrow">▶&nbsp;</span>` : `${indent}`;
    contentCellHtml += `${name || "-"}`;

    if (isParent) {
        row.classList.add('expandable');
    }
    const contentCell = row.insertCell();
    contentCell.innerHTML = contentCellHtml;
    
    // Creating placeholders for the other values
    row.insertCell(); // Capital Appreciation 2018
    row.insertCell(); // Capital Appreciation 2013
    row.insertCell(); // ROI
    
    row.insertCell();// Placeholder for avg_meter_price_2013_2023
    return rowId;
}

function createSvgLineChart(dataPoints,chartId,startyear) {
    if (!dataPoints || !dataPoints.length) return '';

    const maxVal = Math.max(...dataPoints.filter(point => point !== null));
    const minVal = Math.min(...dataPoints.filter(point => point !== null));
    const height = 50; // SVG height
    const width = 100; // SVG width
    const pointWidth = width / (dataPoints.length - 1);

    let pathD = '';
    let moveToNext = true; // Flag to indicate when to move to the next point without drawing

    dataPoints.forEach((point, index) => {
        if (point !== null) {
            const x = pointWidth * index;
            const y = height - ((point - minVal) / (maxVal - minVal) * height);
            if (moveToNext) {
                pathD += `M ${x},${y} `; // Move to this point without drawing
                moveToNext = false; // Reset the flag as we now have a valid point
            } else {
                pathD += `L ${x},${y} `; // Draw line to this point
            }
        } else {
            moveToNext = true; // No point here, next valid point should move without drawing
        }
    });

    return `<svg class="clickable-chart" data-chart-id="${chartId}" onclick="openChartModal('${chartId}',${startyear},2023)" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <path d="${pathD.trim()}" stroke="blue" fill="none"/>
            </svg>`
}

// Close modal functionality
document.querySelector('.close').addEventListener('click', function() {
    document.getElementById('chartModal').style.display = 'none';
});

let chartDataMappings = {};

function processDictionary(dictionary, level = 0, parentRowId = null) {
    Object.entries(dictionary).forEach(([key, value]) => {
        //if the value is a dict with a single key "means", it is a leaf node

        // Check if the value is an object and not null or an array
        const isObject = value !== null && typeof value === 'object' && !Array.isArray(value);
        
        let hasChildren = false;

        if (isObject) {
            if (Object.keys(value).length === 1 && value.hasOwnProperty('means')) {
                hasChildren = false;
            } else {
                hasChildren = !value.avgCapitalAppreciation2018
                              && !value.avgCapitalAppreciation2013
                              && !value.avg_roi
                              && !value.avg_meter_price_2013_2023;
            }
        }
        if (hasChildren) {
            // Recursively process nested objects
            const currentRowId = addRow(key, level, hasChildren, parentRowId);
            processDictionary(value, level + 1, currentRowId);
        } else {
            // Leaf node, add price values
            if(key == "means")
            {
                const row = tableBody.querySelector(`[data-row-id="${parentRowId}"]`);
                if(value == null)
                {
                    value = "-";
                }
                else
                {
                    value = value[0]
                }
                row.cells[1].innerText = (value.avgCapitalAppreciation2018 || value.avgCapitalAppreciation2018 === 0) && !isNaN(value.avgCapitalAppreciation2018) ? (value.avgCapitalAppreciation2018 * 100).toFixed(2) : '-';
                row.cells[2].innerText = (value.avgCapitalAppreciation2013 || value.avgCapitalAppreciation2013 === 0) && !isNaN(value.avgCapitalAppreciation2013) ? (value.avgCapitalAppreciation2013 * 100).toFixed(2) : '-';
                row.cells[3].innerText = (value.avg_roi) && !isNaN(value.avg_roi) ? (value.avg_roi * 100).toFixed(2) : '-';
                row.cells[4].innerHTML = createSvgLineChart(value.avg_meter_price_2013_2023,parentRowId,2013);
                chartDataMappings[parentRowId] = value.avg_meter_price_2013_2023; 
            }
            else if(value.hasOwnProperty('means'))
            {
                const currentRowId = addRow(key, level, hasChildren, parentRowId);
                const row = tableBody.querySelector(`[data-row-id="${currentRowId}"]`);
                if(value == null)
                {
                    value = "-";
                }
                else
                {
                    value = value.means[0]
                }
                row.cells[1].innerText = (value.avgCapitalAppreciation2018 || value.avgCapitalAppreciation2018 === 0) && !isNaN(value.avgCapitalAppreciation2018) ? (value.avgCapitalAppreciation2018 * 100).toFixed(2) : '-';
                row.cells[2].innerText = (value.avgCapitalAppreciation2013 || value.avgCapitalAppreciation2013 === 0) && !isNaN(value.avgCapitalAppreciation2013) ? (value.avgCapitalAppreciation2013 * 100).toFixed(2) : '-';
                row.cells[3].innerText = (value.avg_roi || value.avg_roi === 0) && !isNaN(value.avg_roi) ? (value.avg_roi * 100).toFixed(2) : '-';
                row.cells[4].innerHTML = createSvgLineChart(value.avg_meter_price_2013_2023,currentRowId,2013);
                chartDataMappings[currentRowId] = value.avg_meter_price_2013_2023; 
            }
        }
    });
}


function openChartJsModal(dataArray) {
    const cleanedData = dataArray.map(value => value === null ? null : value);
    const ctx = document.getElementById('chartModal').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: cleanedData.length}, (_, i) => i + 1),
            datasets: [{
                label: 'Data',
                data: cleanedData,
                borderColor: 'blue',
                borderWidth: 2,
                fill: false
            }]
        }
    });

    document.getElementById('chartModal').style.display = 'block';
}

function hideIndirectChildren(parentRowId) {
    const childRows = tableBody.querySelectorAll(`tr[data-parent-id="${parentRowId}"]`);
    childRows.forEach(row => {
        row.style.display = 'none'; // Hide child
        hideIndirectChildren(row.getAttribute('data-row-id')); // Recurse to hide its children
    });
}

function getListOrder() {
    //reads the current order of the list items and returns an array representing this order
    const listItems = document.querySelectorAll('#hierarchyList li');
    const order = Array.from(listItems).map((item, index) => ({
        order: index,
        text: item.getAttribute('data-id'),
    }));
    return order;
}

const tableBody = document.getElementById('nestedTable').getElementsByTagName('tbody')[0];


document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('expand-arrow')) {
        const clickedRow = e.target.closest('tr');
        if (clickedRow && clickedRow.classList.contains('expandable')) {
            const currentRowId = clickedRow.getAttribute('data-row-id');
            const childRows = tableBody.querySelectorAll(`tr[data-parent-id="${currentRowId}"]`);
  
            childRows.forEach(row => {
                if (row.style.display === 'none') {
                    row.style.display = ''; // Show direct child
                    e.target.innerHTML = '▼'; 
                } else {
                    row.style.display = 'none'; // Hide direct child
                    hideIndirectChildren(row.getAttribute('data-row-id')); // Recursively hide all indirect children
                    e.target.innerHTML = '▶'; 
                }
            });
        }
    }
});

// Function to style the GeoJSON layers
function areaStyle(feature, fillColorProperty) {
    return {
        fillColor: feature.properties[fillColorProperty], // Dynamic fill color based on the property
        weight: 0,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.7
    }; 
}


function openTab(evt, tabName) {
    // Declare all variables
    var i, tabcontent, tablinks;
    console.log("we call open tab")
    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";

    if (tabName === 'ProjectsDemand') {
        updateProjectsDemand();
    }
}

function updateProjectsDemand() {
    if (currentAreaId) {
        fetch(`https://estatesnipers-1a1823af05ea.herokuapp.com/get-demand-per-project?area_id=${currentAreaId}`)

            .then(response => response.json())
            .then(data => {
                var div = document.getElementById('ProjectsTableContainer'); // Get the div by its ID
                // Check if a table already exists and remove it
                var existingTable = div.querySelector('table');
                if (existingTable) {
                    div.removeChild(existingTable);
                }
                var table = generateTable(data);
                div.appendChild(table);
            })
            .catch(error => console.error('Error fetching project demand data:', error));
    }
}

function onEachFeature(feature, layer) {
    layer.on({
        click: function(e) {
            console.log("we call on each feature")
            // Clear the <tbody> of <table id="nestedTable"> at the beginning
            const tableBody = document.getElementById('nestedTable').getElementsByTagName('tbody')[0];
            tableBody.innerHTML = ''; // Clear existing rows

            currentAreaId = feature.properties.area_id;
            const areaName = feature.properties.name;
            const avgMeterSale  = feature.properties.averageSalePrice;
            const avgCA_5Y = feature.properties.avgCA_5Y ?(feature.properties.avgCA_5Y * 100).toFixed(2) : "-";
            const avgCA_10Y = feature.properties.avgCA_10Y ? (feature.properties.avgCA_10Y * 100).toFixed(2): "-";
            const avgROI = feature.properties.avg_roi ?(feature.properties.avg_roi* 100).toFixed(2) : "-";
            const supply_Finished_Pro = feature.properties.supply_finished_pro ? feature.properties.supply_finished_pro: "-";
            const supply_OffPlan_Pro = feature.properties.supply_offplan_pro ? feature.properties.supply_offplan_pro: "-";
            const supply_lands = feature.properties.supply_lands? feature.properties.supply_lands: "-";
            const aquisitionDemand_2023 = feature.properties.aquisitiondemand_2023 ? (feature.properties.aquisitiondemand_2023* 100).toFixed(2): "-";
            const rentalDemand_2023 = feature.properties.rentaldemand_2023 ? (feature.properties.rentaldemand_2023 * 100).toFixed(2): "-";
            // Set the initial content of the panel to show the area name and a loading message
            const panelContent = document.getElementById('panel-content');
            const areaInfo = document.getElementById('area_info');
            
            // Clear previous content and set up the areaName as a separate heading on top
            areaInfo.innerHTML = `<h2 class="area-title">${areaName}</h2>`;// areaName as a separate top element

            // Prepare the container for cards with statistical data
            const statsContainer = document.createElement('div');
            statsContainer.id = 'stats-container';
            statsContainer.style.display = 'flex';
            statsContainer.style.overflowX = 'auto'; // Enables horizontal scrolling for cards

            // Inserting individual cards for each piece of information
            statsContainer.innerHTML = `
            <div class="info-card">
  <div class="title">Avg. Meter Sale Price:</div>
  <div class="value">${avgMeterSale} AED</div>
</div>
            <div class="info-card">
  <div class="title">Avg. Capital Appr. 5Y:</div>
  <div class="value">${avgCA_5Y} %</div>
</div>
<div class="info-card">
  <div class="title">Avg. Capital Appr. 10Y:</div>
  <div class="value">${avgCA_10Y} %</div>
</div>
<div class="info-card">
  <div class="title">Avg. ROI:</div>
  <div class="value">${avgROI} %</div>
</div>
<div class="info-card supply-projects">
  <div class="title">Supply of Projects:</div>
  <div class="supply-details">
    <div class="supply-column">
      <div class="sub-title">Finished</div>
      <div class="value">${supply_Finished_Pro}</div>
    </div>
    <div class="supply-column">
      <div class="sub-title">Off Plan</div>
      <div class="value">${supply_OffPlan_Pro}</div>
    </div>
  </div>
</div>
<div class="info-card">
  <div class="title">Supply of Lands:</div>
  <div class="value">${supply_lands}</div>
  <button class="stats-button"><i class="fas fa-chart-pie"></i></button>
</div>
<div class="info-card">
  <div class="title">Acquisition Demand 2023:</div>
  <div class="value">${aquisitionDemand_2023} %</div>
</div>
<div class="info-card">
  <div class="title">Rental Demand 2023:</div>
  <div class="value">${rentalDemand_2023} %</div>
</div>
            `;

            // Append the container of cards to the panel content
            areaInfo.appendChild(statsContainer);
  
            const panel = document.getElementById('info-panel');
            panel.style.display = 'block';
            
            // Remove any existing error messages before fetching new data
            const existingErrorMessage = document.getElementById('error-message');
            if (existingErrorMessage) {
                existingErrorMessage.remove();
            }
            console.log("current area_id = ",currentAreaId)
            fetch(`http://estatesnipers-1a1823af05ea.herokuapp.com/get-area-details?area_id=${currentAreaId}`)
            .then(response => {
                if (!response.ok) { // Check if the response status is not OK (200-299)
                   if (response.status === 404) {
                    // Create a new error message
                    const errorElement = document.createElement('p');
                    errorElement.id = 'error-message'; // Assign an ID to the error element
                    errorElement.textContent = 'There is no data to display';
                    panelContent.appendChild(errorElement);
                  }
                  throw new Error('Network response was not ok.'); // Throw an error for other statuses or to stop processing
                }
                return response.json(); // Proceed with processing the response as JSON
              })
            .then(data => {
                const tableBody = document.getElementById('nestedTable').getElementsByTagName('tbody')[0];
                tableBody.innerHTML = ''; // Clear existing rows
                processDictionary(data); // Process and display the fetched data
            })
            .catch(error => {
                
                console.log('Error fetching area details:', error);
            });

            // If ProjectsDemand tab is active, refetch data with new area_id

            // Simulate a click on the "Details" button
            var evt = new MouseEvent("click", {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: 20,
            });

            var detailsButton = document.querySelector(".tablinks.active");
            detailsButton.dispatchEvent(evt);
            const statsButtons = statsContainer.querySelectorAll('.stats-button');
            statsButtons.forEach(button => {
                button.addEventListener('click', function() {
                    fetch(`http://estatesnipers-1a1823af05ea.herokuapp.com/get-lands-stats?area_id=${currentAreaId}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            renderLandStatsChart(data); 
                        })
                        .catch(error => {
                            console.log('Error fetching land stats:', error);
                        });
                });
            });

        }
    });
}

// Declare a variable outside of the function to hold the chart instance
function renderLandStatsChart(data) {
    const ctx = document.getElementById('landStatsChart').getContext('2d');

    // If there's an existing chart instance, destroy it
    if (window.myChartInstance) {
        window.myChartInstance.destroy();
    }


    // Prepare the data for the pie chart
    const labels = data.map(item => item.land_type_en || 'Unknown');
    const counts = data.map(item => item.count);

    // Instantiate the pie chart
    window.myChartInstance  = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'number of lands',
                data: counts,
                backgroundColor: [
                    'rgba(255, 99, 132)',
                    'rgba(54, 162, 235)',
                    'rgba(255, 206, 86)',
                    'rgba(46, 135, 43)',
                    'rgba(246, 15, 238)',
                    // Add more colors if needed
                ],
                borderColor: [
                    'rgba(0, 0, 0)',
                    // Add more border colors if needed
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Land Type Distribution'
                }
            }
        },
    });

    // Show the modal
    const chartModal = document.getElementById('chartModal');
    chartModal.style.display = 'block';

    // Close the modal when the close button is clicked
    const closeButton = document.querySelector('.close');
    closeButton.onclick = function() {
        chartModal.style.display = 'none';
    }
}
// On document ready or when initializing your app
applyGeoJSONLayer("averageSalePrice");

