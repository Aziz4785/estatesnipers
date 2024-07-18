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

const mainTableBody = document.querySelector('#mainTableBody');
const unlockTableBody = document.querySelector('#unlockTableBody');
const layersByAreaId = {};
let currentFillColor = 'fillColorPrice'; // Default value
/*Now, after the page load, a call will be made to /config, which will respond with the Stripe publishable key. 
We'll then use this key to create a new instance of Stripe.js.*/
document.addEventListener('DOMContentLoaded', function() {
    const upgradeButton = document.getElementById('upgradeButton');
    const goPremiumButton = document.querySelector("#goPremium");

    fetch("/config")
        .then((result) => result.json())
        .then((data) => {
            const stripe = Stripe(data.publicKey);

            // Function to handle Stripe checkout
            async function handleStripeCheckout() {
                try {
                    const sessionResponse = await fetch("/create-checkout-session");
                    const sessionData = await sessionResponse.json();
                    
                    if (sessionData.error) {
                        console.error('Error:', sessionData.error);
                        return;
                    }
                    
                    const result = await stripe.redirectToCheckout({ sessionId: sessionData.sessionId });
                    
                    if (result.error) {
                        console.error(result.error.message);
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            // Upgrade button (requires login check)
            upgradeButton.addEventListener('click', async function(event) {
                event.preventDefault();
                
                try {
                    const authResponse = await fetch('/check-auth');
                    const authData = await authResponse.json();
                    
                    if (authData.isAuthenticated) {
                        // User is logged in, proceed to Stripe checkout
                        await handleStripeCheckout();
                    } else {
                        // User is not logged in, show login modal
                        document.getElementById("premiumModal").style.display = 'none';
                        openLoginModal("Login to Upgrade", "login");
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            });

            if (goPremiumButton) {
                // Go Premium button (directly to checkout)
                goPremiumButton.addEventListener('click', async function(event) {
                    event.preventDefault();
                    await handleStripeCheckout();
                });
            }
        })
        .catch((error) => {
            console.error("Error fetching Stripe config:", error);
        });
});


document.getElementById('toggle-fullscreen').addEventListener('click', function() {
    var panel = document.getElementById('info-panel');
    panel.classList.toggle('fullscreen'); 
});

let currentJsonData = null;
let currentAreaData = null;
let currentAreaId = null; 

document.addEventListener('DOMContentLoaded', function () {
    // Set the default checked radio button (in settings)
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
    fetch('/dubai-areas')
    .then(response => response.json())
    .then(data => {
        //data[0] contains legends of map and data[1] contains the areas and data[2]  contain units
        const legends = data[0];
        const units = data[2];
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

        updateLegend(legends[currentLegend],units[currentLegend]);
    })
    .catch(error => console.log('Error:', error));
}

// Add a click event listener to the close button outside the onEachFeature function
document.getElementById('close-panel').addEventListener('click', function() {
    document.getElementById('info-panel').style.display = 'none';
});


let rowIdCounter = 0; // Counter to assign a unique row ID
let fakeLineAdded = 0;
function addRow(name, level, isParent, parentRowId = null, avgMeterPriceId = null,fake_line = false) {
    //parent rows are rows that are expandable

    const rowId = `row-${rowIdCounter++}`;
    let row;

    if (fake_line && fakeLineAdded >= 2) {
        row = unlockTableBody.insertRow();
    } else {
        row = mainTableBody.insertRow();
    }
        
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

    // Add PDF icon if the row is a root row (i.e., it has no parent)
    if (!parentRowId && fake_line==false ) {
        contentCellHtml += ` <a href="#" class="pdf-icon"><img src="static/download.svg" alt="PDF" class="pdf-icon-img"></a>`;
    }
    if (fake_line) {
        row.classList.add('blurry-row');
        fakeLineAdded++;
    }
    if (isParent || fake_line) {
        row.classList.add('expandable');
    }
    const contentCell = row.insertCell();
    contentCell.innerHTML = contentCellHtml;
    if (!parentRowId) {
        contentCell.classList.add('content-cell');
    }
    //contentCell.classList.add('content-cell'); // Add a class for additional styling if needed
    // Creating placeholders for the other values
    row.insertCell(); // Capital Appreciation 2018
    row.insertCell(); // Capital Appreciation 2013
    row.insertCell(); // ROI
    row.insertCell(); //avg transaction value
    row.insertCell();// Placeholder for avg_meter_price_2013_2023

     // Add event listener for PDF icon if it's a root row
     if (!parentRowId) {
        const pdfIcon = contentCell.querySelector('.pdf-icon');
        if (pdfIcon) {
            pdfIcon.addEventListener('click', function(event) {
                event.preventDefault();
                // Get the current JSON data
                const currentData = getCurrentJsonData(); 
                const currentAreaData = getCurrentAreaData(); 
                fetch('/generate-pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        section: name || "-",
                        data: currentData[name || "-"],
                        area_data: currentAreaData
                    })
                })
                .then(response => {
                    console.log('Response status:', response.status);
                    if (response.status === 403) {
                        return response.json().then(data => {
                            console.log('403 response data:', data);
                            openModal("Download as PDF is a premium feature");
                            //throw new Error('Premium subscription required');
                        });
                    } else if (!response.ok) {
                        return response.text().then(text => {
                            console.log('Error response:', text);
                            throw new Error('Server error');
                        });
                    }
                    return response.blob();
                })
                .then(blob => {
                    if (!blob) {
                        throw new Error('No blob received from server');
                    }
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `${name || "-"}_report.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (error !== 'Premium subscription required') {
                        alert("An error occurred.");
                    }
                });
            });
        }
    }
    return rowId;
}
function createSvgLineChart(dataPoints, chartId, startYear, endYear,chart_title) {
    if (!dataPoints || !dataPoints.length) return '';

    const maxVal = Math.max(...dataPoints.filter(point => point !== null));
    const minVal = Math.min(Math.min(...dataPoints.filter(point => point !== null)), 0);
    const height = 50; // SVG height
    const width = 100; // SVG width
    const padding = 5; // Padding around the chart to ensure the path doesn't touch the edges
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    const pointWidth = chartWidth / (dataPoints.length - 1);

    let pathD = ''; // Path for the main line chart
    let redPathD = ''; // Path for the last 5 points
    let moveToNext = true; // Flag to indicate when to move to the next point without drawing
    let lastBluePointX, lastBluePointY; // Keep track of the last non-null point in the blue line

    dataPoints.forEach((point, index) => {
        if (point !== null) {
            const x = padding + pointWidth * index;
            const y = padding + chartHeight - ((point - minVal) / (maxVal - minVal) * chartHeight);

            if (index < dataPoints.length - Math.max(0,(endYear-2024))) {
                if (moveToNext) {
                    pathD += `M ${x},${y} `;
                    moveToNext = false;
                } else {
                    pathD += `L ${x},${y} `;
                }
                lastBluePointX = x;
                lastBluePointY = y;
            } else {
                if (redPathD === '') {
                    redPathD += `M ${lastBluePointX},${lastBluePointY} L ${x},${y} `; // Connect the last blue point to the first red point
                } else {
                    redPathD += `L ${x},${y} `;
                }
            }
        } else {
            moveToNext = true;
        }
    });

    // Create the axis lines
    const xAxisY = padding + chartHeight;
    const yAxisX = padding;

    return `<svg class="clickable-chart" data-chart-id="${chartId}" onclick="openChartModal('${chartId}',${startYear},${endYear},'${chart_title}')" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <line x1="${padding}" y1="${xAxisY}" x2="${width - padding}" y2="${xAxisY}" stroke="black"/>
            <line x1="${yAxisX}" y1="${padding}" x2="${yAxisX}" y2="${height - padding}" stroke="black"/>
            <path d="${pathD.trim()}" stroke="blue" fill="none"/>
            <path d="${redPathD.trim()}" stroke="red" fill="none"/>
            </svg>`;
}
/*
function createSvgLineChart3(dataPoints, chartId, startYear, endYear,chart_title) {
    if (!dataPoints || !dataPoints.length) return '';

    const maxVal = Math.max(...dataPoints.filter(point => point !== null));
    const minVal = Math.min(Math.min(...dataPoints.filter(point => point !== null)), 0);
    const height = 50; // SVG height
    const width = 100; // SVG width
    const padding = 5; // Padding around the chart to ensure the path doesn't touch the edges
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    const pointWidth = chartWidth / (dataPoints.length - 1);

    let pathD = ''; // Path for the main line chart (blue)
    let redPathD = ''; // Path for the last 5 points (red)
    let moveToNext = true; // Flag to indicate when to move to the next point without drawing

    dataPoints.forEach((point, index) => {
        if (point !== null) {
            const x = padding + pointWidth * index;
            const y = padding + chartHeight - ((point - minVal) / (maxVal - minVal) * chartHeight);
            if (index >= dataPoints.length - 5) {
                // Connect the blue and red paths seamlessly
                if (redPathD === '') {
                    if (pathD) {
                        redPathD = pathD.trim() + ` L ${x},${y}`;
                    } else {
                        redPathD = `M ${x},${y}`;
                    }
                } else {
                    redPathD += ` L ${x},${y}`;
                }
            } else {
                if (moveToNext) {
                    pathD += `M ${x},${y} `;
                    moveToNext = false;
                } else {
                    pathD += `L ${x},${y} `;
                }
            }
        } else {
            moveToNext = true;
        }
    });

    // Create the axis lines
    const xAxisY = padding + chartHeight;
    const yAxisX = padding;

    return `<svg class="clickable-chart" data-chart-id="${chartId}" onclick="openChartModal('${chartId}',${startYear},${endYear},${chart_title})" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <line x1="${padding}" y1="${xAxisY}" x2="${width - padding}" y2="${xAxisY}" stroke="black"/>
            <line x1="${yAxisX}" y1="${padding}" x2="${yAxisX}" y2="${height - padding}" stroke="black"/>
            <path d="${pathD.trim()}" stroke="blue" fill="none"/>
            <path d="${redPathD.trim()}" stroke="red" fill="none"/>
            </svg>`;
}*/
/*
function createSvgLineChart2(dataPoints, chartId, startYear, endYear,chart_title) {
    if (!dataPoints || !dataPoints.length) return '';

    const maxVal = Math.max(...dataPoints.filter(point => point !== null));
    const minVal = Math.min(...dataPoints.filter(point => point !== null));
    const height = 50; // SVG height
    const width = 100; // SVG width
    const padding = 10; // Padding around the chart to ensure the path doesn't touch the edges
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    const pointWidth = chartWidth / (dataPoints.length - 1);

    let pathD = ''; // Path for the line chart
    let moveToNext = true; // Flag to indicate when to move to the next point without drawing

    // Generate the complete path
    dataPoints.forEach((point, index) => {
        if (point !== null) {
            const x = padding + pointWidth * index;
            const y = padding + chartHeight - ((point - minVal) / (maxVal - minVal) * chartHeight);
            if (moveToNext) {
                pathD += `M ${x},${y} `;
                moveToNext = false;
            } else {
                pathD += `L ${x},${y} `;
            }
        } else {
            moveToNext = true; // Move to the next point without drawing a line for null values
        }
    });

    // Determine where to start the red path
    const redStartIndex = Math.max(dataPoints.length - 5, 0);
    let redPathD = '';
    let redMoveToNext = true;

    for (let i = redStartIndex; i < dataPoints.length; i++) {
        const point = dataPoints[i];
        if (point !== null) {
            const x = padding + pointWidth * i;
            const y = padding + chartHeight - ((point - minVal) / (maxVal - minVal) * chartHeight);
            if (redMoveToNext) {
                redPathD += `M ${x},${y} `;
                redMoveToNext = false;
            } else {
                redPathD += `L ${x},${y} `;
            }
        }
    }

    // Create the axis lines
    const xAxisY = padding + chartHeight;
    const yAxisX = padding;

    return `<svg class="clickable-chart" data-chart-id="${chartId}" onclick="openChartModal('${chartId}',${startYear},${endYear},${chart_title})" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <line x1="${padding}" y1="${xAxisY}" x2="${width - padding}" y2="${xAxisY}" stroke="black"/>
            <line x1="${yAxisX}" y1="${padding}" x2="${yAxisX}" y2="${height - padding}" stroke="black"/>
            <path d="${pathD.trim()}" stroke="blue" fill="none"/>
            <path d="${redPathD.trim()}" stroke="red" fill="none"/>
            </svg>`;
}*/
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
                              && !value.avg_actual_worth
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
                const row = mainTableBody.querySelector(`[data-row-id="${parentRowId}"]`);
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
                row.cells[4].innerText = (value.avg_actual_worth) && !isNaN(value.avg_actual_worth) ? (value.avg_actual_worth).toFixed(2) : '-';
                row.cells[5].innerHTML = createSvgLineChart(value.avg_meter_price_2013_2023,parentRowId,2013,2029,'Evolution of Meter Sale Price');
                chartDataMappings[parentRowId] = value.avg_meter_price_2013_2023; 
            }
            else if(value.hasOwnProperty('means'))
            {
                const currentRowId = addRow(key, level, hasChildren, parentRowId);
                const row = mainTableBody.querySelector(`[data-row-id="${currentRowId}"]`);
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
                row.cells[4].innerText = (value.avg_actual_worth || value.avg_actual_worth === 0) && !isNaN(value.avg_actual_worth) ? (value.avg_actual_worth).toFixed(2) : '-';
                row.cells[5].innerHTML = createSvgLineChart(value.avg_meter_price_2013_2023,currentRowId,2013,2029,'Evolution of Meter Sale Price');
                chartDataMappings[currentRowId] = value.avg_meter_price_2013_2023; 
            }
            else if(key.includes("locked project"))
            {
                
                const currentRowId = addRow(key, level, hasChildren, parentRowId,null,true);
                let row = unlockTableBody .querySelector(`[data-row-id="${currentRowId}"]`);
                
                if (!row) {
                    row = mainTableBody.querySelector(`[data-row-id="${currentRowId}"]`);
                }
                row.cells[1].innerText = '99';
                row.cells[2].innerText = '99';
                row.cells[3].innerText = '99'; 
                row.cells[4].innerHTML = '<img src="static/lock_similar.svg" alt="Locked Chart" width="40" height="40">';
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
    const childRows = mainTableBody.querySelectorAll(`tr[data-parent-id="${parentRowId}"]`);
    childRows.forEach(row => {
        row.style.display = 'none'; // Hide child
        hideIndirectChildren(row.getAttribute('data-row-id')); // Recurse to hide its children
    });
}

function getListOrderFromUI() {
    //reads the current order of the list items and returns an array representing this order
    const listItems = document.querySelectorAll('#hierarchyList li');
    const order = Array.from(listItems).map((item, index) => ({
        order: index,
        text: item.getAttribute('data-id'),
    }));
    return order;
}

document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('expand-arrow')) {
        const clickedRow = e.target.closest('tr');
        if (clickedRow && clickedRow.classList.contains('expandable')) {
            const currentRowId = clickedRow.getAttribute('data-row-id');
            const childRows = mainTableBody.querySelectorAll(`tr[data-parent-id="${currentRowId}"]`);
  
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
        fetch(`/get-demand-per-project?area_id=${currentAreaId}`)

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
    const areaId = feature.properties.area_id;
    layersByAreaId[areaId] = layer; // Store layer by area_id

    layer.on({
        click: function(e) {
            highlightFeature(e);
            mainTableBody.innerHTML = ''; // Clear existing rows
            currentAreaId = feature.properties.area_id;
            // Create a copy of feature.properties without the "geometry" property
            const { geometry, ...propertiesWithoutGeometry } = feature.properties;
            currentAreaData = propertiesWithoutGeometry; // Save as global variable for later
            
            currentAreaId = feature.properties.area_id;
            const areaName = feature.properties.name;
            const areaInfo = document.getElementById('area_info');
            const areaTitleH2 = document.getElementById('area-title');
            // Clear previous content and set up the areaName as a separate heading on top
            areaTitleH2.innerHTML = areaName;// areaName as a separate top element

            const variableNames = feature.properties.variableNames;
            const variableValues = feature.properties.variableValues;
            const variableunits = feature.properties.variableUnits;
            const variableSpecial= feature.properties.variableSpecial;
            const cards = document.querySelectorAll('.info-card');
            let array_index = 0;
            // Loop through each card and populate with the corresponding variable name and value
            cards.forEach((card) => {
                // Ensure we have a corresponding variable name and value
                

                if(card.id=='card5' && variableNames.length >5)
                {
                    const supplyCard = document.getElementById('card5');
                    if (supplyCard) {
                        supplyCard.querySelector('.title').textContent ='Supply of Projects:';
                        const finishedValue = variableNames.includes('supply_finished_pro') ? variableValues[4] : "-";
                        const offplanValue = variableNames.includes('supply_offplan_pro') ? variableValues[5] : "-";
                        supplyCard.querySelector('.finished-value').textContent = finishedValue;
                        supplyCard.querySelector('.offplan-value').textContent = offplanValue;
                        supplyCard.classList.remove('locked-card');  // Remove locked-card class
                        array_index+=2;

                        const wrapper = supplyCard.closest('.info-card-wrapper');
                        // Remove the lock icon
                        if(wrapper){
                            const lockIcon = wrapper.querySelector('.lock-icon-card');
                            if (lockIcon) {
                                lockIcon.remove();
                            }
                            // Move the card outside of the wrapper
                            wrapper.parentNode.insertBefore(supplyCard, wrapper);
                            // Remove the empty wrapper
                            wrapper.remove();
                        }

                    }
                }
                else if(card.id=='card6' && variableNames.length >5)
                {
                    const landsCard = document.getElementById('card6');
                    if (landsCard) {
                        landsCard.querySelector('.title').textContent ='Supply of Lands:';
                        const landsValue = variableNames.includes('supply_lands') ? variableValues[6] : "-";
                        landsCard.querySelector('.value').textContent = landsValue;
                        landsCard.classList.remove('locked-card');  // Remove locked-card class

                        const wrapper = landsCard.closest('.info-card-wrapper');
                        // Remove the lock icon
                        if(wrapper){
                            const lockIcon = wrapper.querySelector('.lock-icon-card');
                            if (lockIcon) {
                                lockIcon.remove();
                            }
                            // Move the card outside of the wrapper
                            wrapper.parentNode.insertBefore(landsCard, wrapper);
                            // Remove the empty wrapper
                            wrapper.remove();
                        }


                        array_index++;
                    }
                    
                }
                else if(variableSpecial[array_index]==0)
                {
                    const title = variableNames[array_index];
                    let value = variableValues[array_index];
                    card.querySelector('.title').textContent = title;
                    if(variableunits[array_index]=="%")
                    {
                        card.querySelector('.value').textContent= `${(value * 100).toFixed(2)} %`;
                    }
                    else if(variableunits[array_index]=="AED")
                    {
                        card.querySelector('.value').textContent= `${value} AED`;
                    }
                    else{
                        card.querySelector('.value').textContent = value;
                    }
                    
                    card.classList.remove('locked-card');  // Remove locked-card class
                    const wrapper = card.closest('.info-card-wrapper');
                    // Remove the lock icon
                    if(wrapper){
                        const lockIcon = wrapper.querySelector('.lock-icon-card');
                        if (lockIcon) {
                            lockIcon.remove();
                        }
                        // Move the card outside of the wrapper
                        wrapper.parentNode.insertBefore(card, wrapper);
                        // Remove the empty wrapper
                        wrapper.remove();
                    }
                

                    array_index++;
                }
        });
           
            // Append the container of cards to the panel content
            const statsContainer = document.getElementById('stats-container');
            areaInfo.appendChild(statsContainer);

            const panel = document.getElementById('info-panel');
            panel.style.display = 'block';
            
            // Remove any existing error messages before fetching new data
            const existingErrorMessage = document.getElementById('error-message');
            if (existingErrorMessage) {
                existingErrorMessage.remove();
            }
            
            // Use the new fetchAreaDetails function
            fetchAreaDetails(currentAreaId);

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
            const landbutton = document.getElementById('land-chart-button');
            landbutton.addEventListener('click', function() {
                    fetch(`/get-lands-stats?area_id=${currentAreaId}`)
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

        }
    });
}


function fetchAreaDetails(areaId) {
   // const tableBody = document.getElementById('nestedTable').getElementsByTagName('tbody')[0];
    mainTableBody.innerHTML = ''; // Clear existing rows

    const loader = document.querySelector('.loader');
    loader.style.display = 'grid'; // Display loader
    
    fetch(`/get-area-details?area_id=${areaId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    const errorElement = document.createElement('p');
                    errorElement.id = 'error-message';
                    errorElement.textContent = 'There is no data to display';
                    document.getElementById('panel-content').appendChild(errorElement);
                }
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            currentJsonData = data; // Save the fetched data
            const tableBody = document.getElementById('nestedTable').getElementsByTagName('tbody')[0];
            tableBody.innerHTML = ''; // Clear existing rows
            processDictionary(data); // Process and display the fetched data
            positionOverlay();
            window.addEventListener('resize', positionOverlay);
        })
        .catch(error => {
            console.log('Error fetching area details:', error);
        })
        .finally(() => {
            loader.style.display = 'none'; // Hide loader
        });
}






document.addEventListener('DOMContentLoaded', function() {
    var profileButton = document.getElementById('profileButton');
    if (profileButton) {
        profileButton.addEventListener('click', function() {
            var dropdown = document.getElementById('dropdown');
            if (dropdown.style.display === 'none' || dropdown.style.display === '') {
                dropdown.style.display = 'block';
            } else {
                dropdown.style.display = 'none';
            }
        });
    }
});
// Close the dropdown if the user clicks outside of it
window.onclick = function(event) {
    if (!event.target.matches('.profile-button')) {
        var dropdowns = document.getElementsByClassName("dropdown-content");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.style.display === 'block') {
                openDropdown.style.display = 'none';
            }
        }
    }
}
document.addEventListener('DOMContentLoaded', function() {
    var loginmodal = document.getElementById("loginModal");
    var btn = document.getElementById("loginButton");
    var span = document.getElementsByClassName("close")[0];
    var messageDiv = document.getElementById("messageInfo");

    if (btn) {
        btn.onclick = function() {
            openLoginModal('Login', 'login');
        }
    }

    document.addEventListener('click', function(event) {
        if (event.target && event.target.id == 'showRegisterForm') {
            event.preventDefault();
            openLoginModal('Register', 'register');
        } else if (event.target && event.target.id == 'showLoginForm') {
            event.preventDefault();
            openLoginModal('Login', 'login');
        }
    });
    // Show the modal if the show_modal parameter is true
    var showModal = document.body.getAttribute('data-show-modal') === 'True';
    if (showModal) {
        //loginmodal.style.display = "block";
        // Show the appropriate form based on the form parameter
        var formToShow = document.body.getAttribute('data-form');
        if (formToShow === 'register') {
            openLoginModal('Register', 'register');
        } else {
            openLoginModal('Login', 'login');
        }
    }

    // Display the message if there is one
    var message = document.body.getAttribute('data-message');
    if (message) {
        messageDiv.textContent = message;
        messageDiv.style.display = "block";
    }

    

});

$(function() {
    const searchInput = $("#search");
    const searchResults = $("#search-results");
    searchInput.on("input", function() {
        const query = $(this).val();
        if (query.length >= 2) {
          $.getJSON("/search", { q: query }, function(data) {
            displayResults(data);
          });
        } else {
          searchResults.hide().empty();
        }
      });

    function displayResults(results) {
        console.log("results : ",results)
    searchResults.empty();
    
    if (results.length === 0) {
      searchResults.hide();
      return;
    }

    results.forEach(item => {
      const resultItem = $("<div>")
        .addClass("search-item")
        .addClass(item.type);

      const itemName = $("<span>")
        .addClass("item-name")
        .text(item.name);

      const itemType = $("<span>")
        .addClass("item-type")
        .text(item.type);

      resultItem.append(itemName, itemType);

      if (item.type === 'project') {
        const itemArea = $("<div>")
          .addClass("item-area")
          .text(item.area_name);
        resultItem.append(itemArea);
      }

      resultItem.on("click", function() {
        if (item.type === 'project') {
          simulateClick(item.id);
        } else if (item.type === 'area') {
            simulateClick(item.id);
        }
        searchInput.val(item.name);
        searchResults.hide();
      });

      searchResults.append(resultItem);
    });

    searchResults.show();
  }

  $(document).on("click", function(event) {
    if (!$(event.target).closest(".search-container").length) {
      searchResults.hide();
    }
  });
});

function getCurrentJsonData() {
    return currentJsonData;
}
function getCurrentAreaData() {
    return currentAreaData;
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

