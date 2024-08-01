
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

let state = {
    currentFillColor: 'fillColorPrice',
    currentLegend: 'averageSalePrice',
    currentAreaId: null
};

 function getCurrentFillColor() {
    return state.currentFillColor;
}
let allAreasData = null;
function getAllAreasData() {
    return allAreasData;
}


 function getCurrentAreaId() {
    return state.currentAreaId;
}

 function setCurrentAreaId(areaidd) {
    state.currentAreaId = areaidd;
}
 function setCurrentFillColor(color) {
    state.currentFillColor = color;
}
 function getCurrentLegend() {
    return state.currentLegend;
}

 function setCurrentLegend(legend) {
    state.currentLegend = legend;
}

/*Now, after the page load, a call will be made to /config, which will respond with the Stripe publishable key. 
We'll then use this key to create a new instance of Stripe.js.*/
document.addEventListener('DOMContentLoaded', function() {
    const upgradeButton = document.getElementById('upgradeButton');
    initializeStripe()
        .then((stripe) => {
            // Upgrade button (requires login check)
            upgradeButton.addEventListener('click', async function(event) {
                event.preventDefault();
                
                try {
                    const authResponse = await fetch('/check-auth');
                    const authData = await authResponse.json();
                    
                    if (authData.isAuthenticated) {
                        // User is logged in, proceed to Stripe checkout
                        await handleStripeCheckout(stripe);
                    } else {
                        // User is not logged in, show login modal
                        document.getElementById("premiumModal").style.display = 'none';
                        openLoginModal("Login", "login");
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            });

            // Setup the "Go Premium" button
            setupPremiumButton('goPremium', stripe);
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
    
    
    // document.getElementById('subscribeBtn').addEventListener('click', async function(event) {
    //     event.preventDefault();
    //     try {
    //         const authResponse = await fetch('/check-auth');
    //         const authData = await authResponse.json();
            
    //         if (authData.isAuthenticated) {
    //             // User is logged in, proceed to Stripe checkout
    //             await handleStripeCheckout(stripe);
    //         } else {
    //             // User is not logged in, show login modal
    //             document.getElementById("premiumModal").style.display = 'none';
    //             openLoginModal("Login to Subscribe", "login");
    //         }
    //     } catch (error) {
    //         console.error('Error:', error);
    //     }
    // });


});


// load the .geojson file to display the areas
 function applyGeoJSONLayer(currentLegend) {
    const data = allAreasData;
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
        style: feature => areaStyle(feature, getCurrentFillColor()),
        onEachFeature: onEachFeature
    }).addTo(map);

    updateLegend(legends[currentLegend],units[currentLegend]);
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
    row.setAttribute('data-name', name || "-");

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
        //contentCellHtml += ` <a href="#" class="pdf-icon"><img src="static/download.svg" alt="PDF" class="pdf-icon-img"></a>`;
        contentCellHtml += `<button class="pdf-icon"><img src="static/download.svg" alt="PDF" class="pdf-icon-img"></button>`;
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
    ['Capital Appreciation 2018', 'Capital Appreciation 2013', 'ROI', 'avg transaction value', 'avg_meter_price_2013_2023','Projected Capital Appreciation 5Y'].forEach(() => row.insertCell());

    return rowId;
}
// Event delegation for PDF icon clicks
document.addEventListener('click', function(event) {
    const pdfIcon = event.target.closest('.pdf-icon');
    if (pdfIcon) {
        event.preventDefault();
        const row = pdfIcon.closest('tr');
        const name = row.getAttribute('data-name');
        generatePDF(name);
    }
});

function generatePDF(name) {
    const currentData = getCurrentJsonData();
    const currentAreaData = getCurrentAreaData();
    fetch('/generate-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            section: name,
            data: currentData[name],
            area_data: currentAreaData
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Server error');
        }
        return response.blob();
    })
    .then(blob => {
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
        if (error.message !== 'Premium subscription required') {
            alert("An error occurred while generating the PDF. Please try again later.");
        }
    });
}

 function createSvgLineChart(dataPoints, chartId, startYear, endYear,chart_title,label_of_point ='avg meter sale price') {
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

    return `<svg class="clickable-chart" data-chart-id="${chartId}" onclick="openChartModal('${chartId}',${startYear},${endYear},'${chart_title}','${label_of_point}')" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <line x1="${padding}" y1="${xAxisY}" x2="${width - padding}" y2="${xAxisY}" stroke="black"/>
            <line x1="${yAxisX}" y1="${padding}" x2="${yAxisX}" y2="${height - padding}" stroke="black"/>
            <path d="${pathD.trim()}" stroke="blue" fill="none"/>
            <path d="${redPathD.trim()}" stroke="red" fill="none"/>
            </svg>`;
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
                              && !value.avg_actual_worth
                              && !value.avg_meter_price_2013_2023
                              && !value.avgCapitalAppreciation2013
                              && !value.avgCapitalAppreciation2029;
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
                row.cells[4].innerText = (value.avg_actual_worth) && !isNaN(value.avg_actual_worth) 
                ? Number(value.avg_actual_worth).toLocaleString('en-US', {maximumFractionDigits: 2}) 
                : '-';
                row.cells[5].innerHTML = createSvgLineChart(value.avg_meter_price_2013_2023,parentRowId,2013,2029,'Evolution of Meter Sale Price');
                row.cells[6].innerText = (value.avgCapitalAppreciation2029 || value.avgCapitalAppreciation2029 === 0) && !isNaN(value.avgCapitalAppreciation2029) ? (value.avgCapitalAppreciation2029 * 100).toFixed(2) : '-';
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
                row.cells[4].innerText = (value.avg_actual_worth) && !isNaN(value.avg_actual_worth) 
                ? Number(value.avg_actual_worth).toLocaleString('en-US', {maximumFractionDigits: 2}) 
                : '-';
                row.cells[5].innerHTML = createSvgLineChart(value.avg_meter_price_2013_2023,currentRowId,2013,2029,'Evolution of Meter Sale Price');
                row.cells[6].innerText = (value.avgCapitalAppreciation2029 || value.avgCapitalAppreciation2029 === 0) && !isNaN(value.avgCapitalAppreciation2029) ? (value.avgCapitalAppreciation2029 * 100).toFixed(2) : '-';
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
                row.cells[4].innerText = '99'; 
                row.cells[5].innerHTML = '<img src="static/lock_similar.svg" alt="Locked Chart" width="40" height="40">';
            }
        }
    });
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
    if (getCurrentAreaId()) {
        fetch(`/get-demand-per-project?area_id=${getCurrentAreaId()}`)

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
            updateAreaInfo(feature);
        }
    });
}

function updateAreaInfo(feature) {
    mainTableBody.innerHTML = ''; // Clear existing rows
    setCurrentAreaId(feature.properties.area_id);
    // Create a copy of feature.properties without the "geometry" property
    const { geometry, ...propertiesWithoutGeometry } = feature.properties;
    currentAreaData = propertiesWithoutGeometry; // Save as global variable for later
    
    setCurrentAreaId(feature.properties.area_id);
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

                const landbutton = document.getElementById('land-chart-button');
                landbutton.addEventListener('click', function() {
                        fetch(`/get-lands-stats?area_id=${getCurrentAreaId()}`)
                            .then(response => {
                                if (response.status === 204) {
                                    // No content for non-premium users, do nothing
                                    return null;
                                }
                                if (!response.ok) {
                                    throw new Error('Network response was not ok');
                                }
                                return response.json();
                            })
                            .then(data => {
                                if (data) {
                                    renderLandStatsChart(data);
                                }
                            })
                            .catch(error => {
                                console.log('Error fetching land stats:', error);
                            });
                    });

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
            if(card.id=='card8')
            {
                const tooltipText = "Fraction of long-term rented units in the area";
                card.querySelector('.title').innerHTML = `${title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
            }
            else if(card.id=='card7')
            {
                const tooltipText = "Fraction of sold units in the area"
                card.querySelector('.title').innerHTML = `${title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
            }
            else
            {
                card.querySelector('.title').textContent = title;
            }
            
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
    fetchAreaDetails(getCurrentAreaId());

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
}
// Save settings button functionality
document.getElementById("saveSettings").onclick = function() {
    const listOrder = getListOrderFromUI();
    document.getElementById("settingsModal").style.display = "none";
    
    fetch('/save-list-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ listOrder: listOrder })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok.');
        }
        return response.json();
    })
    .then(data => {
        // After successfully saving the settings, refetch the area details
        if (getCurrentAreaId()) {
            fetchAreaDetails(getCurrentAreaId());
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
};

function fetchAreaDetails(areaId) {
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

    const togglePassword = document.querySelectorAll('.toggle-password');
    
    togglePassword.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('input');
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            
            // Toggle eye icon
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
        });
    });
    
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

    // Function to close a modal
    function closeModal(modal) {
        modal.style.display = "none";
    }
    // Get all modals and close buttons
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-button');
    // Attach event listeners to each close button
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    // Optional: Close the modal if the user clicks outside of the modal content
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });
    document.getElementById("unlock-button-table").onclick = function() {
        openModal('Unlock all projects Today for <span class="old-price">$19.99</span> $9.99 <span style="font-size: 0.7em;">*</span>');
    };

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
// On document ready or when initializing your app
document.addEventListener('DOMContentLoaded', () => {
    allAreasData = serverSideData;
    applyGeoJSONLayer("averageSalePrice");
});



document.addEventListener("DOMContentLoaded", function() {
    const Contactmodal = document.getElementById("contactModal");
    const btnSendMessage = document.getElementById("contactUsButton");
    const formContact = document.getElementById("contactForm");
  
    btnSendMessage.onclick = function() {
      Contactmodal.style.display = "block";
    }
  
    formContact.onsubmit = function(e) {
      e.preventDefault();
      const message = document.getElementById("message").value;
      
      if (!message) {
        alert("Please enter a message.");
        return;
      }

      if (message.length > 2000) {
        alert("Message is too long. Please keep it under 2000 characters.");
        return;
      }

      fetch('/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({message: message}),
      })
      .then(response => response.json())
      .then(data => {
        alert(data.message);
        Contactmodal.style.display = "none";
        formContact.reset();
      })
      .catch((error) => {
        console.error('Error:', error);
        alert("An error occurred while sending your message. Please try again.");
      });
    }
  });
 function generateTable(data) {
    var table = document.createElement('table');

    // Create the table header
    var thead = document.createElement('thead');
    var headerRow = document.createElement('tr');
    ['Project', 'Internal Demand 2023 %', 'External Demand 2023 %','External Demand 2018-2023'].forEach((headerText, index) => {
        var header = document.createElement('th');
        if (index === 1) { // For 'Internal Demand 2023 %'
            header.innerHTML = headerText + `<span class="info-icon info-icon-internal" tabindex="0" data-tooltip="(Number of transaction in the project in year 2023) / (Number of units in the project) * 100"">i</span>`;
        } else if (index === 2) { // For 'External Demand 2023 %'
            header.innerHTML = headerText + ' <span class="info-icon info-icon-external" tabindex="0" data-tooltip="(Number of transaction in the project in year 2023) /(Total number of transactions in 2023) * 100">i</span>';
        } else {
            header.textContent = headerText;
        }
        headerRow.appendChild(header);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Populate the table body
    var tbody = document.createElement('tbody');
    data.forEach(item => {
        var row = document.createElement('tr');
        var row_id =  `project-${item.project_name_en}`
        row.setAttribute('id',row_id);
        [item.project_name_en, item.internaldemand2023, item.externaldemand2023, item.externalDemandYears].forEach((value, index) => {
            var cell = document.createElement('td');
            cell.textContent = value;
            if (index === 3) { 
   
                cell.innerHTML = createSvgLineChart(value, row_id,2018,2023,'Evolution of External Demand','External Demand');
                chartDataMappings[row_id] = value; 
            } 
            else if(index > 0){
                cell.textContent = (value*100).toFixed(2);
            }
            else {
                cell.textContent = value;
            }
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    return table;
}

 function highlightFeature(e) {
    const layer = e.target;

    // Reset style for all layers
    window.geoJSONLayer.eachLayer(function(layer) {
        window.geoJSONLayer.resetStyle(layer);
    });

    // Set the style for the clicked layer
    layer.setStyle({
        weight: 3,
        color: 'white',
        dashArray: '',
        fillOpacity: 0.7
    });

    // Ensure the clicked area is brought to the front
    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }

    // Center the map on the clicked area
    map.fitBounds(layer.getBounds(),{ maxZoom: 12 });
    // Center the map on the clicked area with a specific zoom level
    //const bounds = layer.getBounds();
    //const center = bounds.getCenter();
    //map.setView(center, map.getZoom() > 16 ? map.getZoom() : 16); // Set a specific zoom level or use current zoom level if it's already greater
}


 function positionOverlay() {
  const tbody = document.getElementById('myTableBody');
  if(tbody)
  {
    const rows = tbody.getElementsByTagName('tr');
    const overlay = document.getElementById('unlockOverlay');
    
    if (rows.length >= 8) {
        const eighthLastRow = rows[rows.length - 8];
        const rect = eighthLastRow.getBoundingClientRect();
        overlay.style.top = `${rect.top}px`;
        overlay.style.height = `${rect.height * 8}px`;
    }
  }
}
 function showPremiumMessage() {
    openModal('Access all content today for <span class="old-price">$19.99</span> $9.99 <span style="font-size: 0.7em;">*</span>');
}

function createInfoCard(title, value) {
    const template = document.getElementById('info-card-template');
    const card = template.content.cloneNode(true);
    card.querySelector('.title').textContent = title;
    card.querySelector('.value').textContent = value;
    return card;
}
function createLandsCard(value) {
    const template = document.getElementById('lands-card-template');
    const card = template.content.cloneNode(true);
    card.querySelector('.value').textContent = value;
    return card;
}
function createSupplyCard(finishedValue, offplanValue) {
    const template = document.getElementById('supply-card-template');
    const card = template.content.cloneNode(true);
    card.querySelector('.finished-value').textContent = finishedValue;
    card.querySelector('.offplan-value').textContent = offplanValue;
    return card;
}

 function updateLegend(averageSalePrice, unit) {
    const legendContent = document.getElementById('legendContent');
    legendContent.innerHTML = ''; // Clear previous contents
    const colors = [
        { color: 'rgb(192, 0, 0)', label: `> ${averageSalePrice[2]} ${unit}` },
        { color: 'rgb(223, 82, 82)', label: `${averageSalePrice[2]} ${unit} - ${averageSalePrice[1]} ${unit}` },
        { color: 'rgb(82, 82, 223)', label: `${averageSalePrice[1]} ${unit} - ${averageSalePrice[0]} ${unit}` },
        { color: 'rgb(0, 0, 192)', label: `< ${averageSalePrice[0]} ${unit}` }
    ];

    colors.forEach(col => {
        // Create the container for the color square and the label
        const legendItem = document.createElement('div');
        legendItem.style.display = 'flex';
        legendItem.style.alignItems = 'center';
        legendItem.style.marginBottom = '4px';
        
        // Create the color square
        const colorSquare = document.createElement('div');
        colorSquare.style.width = '15px';
        colorSquare.style.height = '15px';
        colorSquare.style.backgroundColor = col.color;
        colorSquare.style.marginRight = '8px';
        
        // Create the label text
        const labelText = document.createElement('span');
        labelText.textContent = col.label;
        labelText.style.fontSize = '16px';
        labelText.style.fontWeight = 'bold';
        
        // Append the color square and label text to the container
        legendItem.appendChild(colorSquare);
        legendItem.appendChild(labelText);
        
        // Append the container to the legend content
        legendContent.appendChild(legendItem);
    });
}

let isMenuOpen = false;

document.getElementById('legendTitle').addEventListener('click', toggleMenu);

function toggleMenu() {
  isMenuOpen = !isMenuOpen;
  document.getElementById('dropupMenu').style.display = isMenuOpen ? 'block' : 'none';
  document.getElementById('arrow').style.transform = isMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)';
}

 function changeLegendTitle(title) {
    document.getElementById('legendTitle').children[0].textContent = title;
    toggleMenu(); // Close the menu after selection
    // Handle the change of legend content based on the selected title
    setCurrentFillColor("fillColorPrice");
    setCurrentLegend("averageSalePrice");
    switch (title) {
        case 'Average meter price':
        setCurrentFillColor("fillColorPrice");
        setCurrentLegend("averageSalePrice");
        break;
        case 'Capital Appreciation':
        setCurrentFillColor("fillColorCA5");
        setCurrentLegend("avgCA_5Y");
        break;
        case 'Gross Rental Yield':
        setCurrentFillColor("fillColorRoi");
        setCurrentLegend("avg_roi");
        break;
        case 'Acquisition Demand':
        setCurrentFillColor("fillColorAquDemand");
        setCurrentLegend("aquisitiondemand_2023");
        break;
    }

    applyGeoJSONLayer(getCurrentLegend());
}


 function simulateClick(areaId) {
    const layer = layersByAreaId[areaId];
    if (layer) {
        // Create a synthetic event
        const event = {
            target: layer,
            latlng: layer.getBounds().getCenter()
        };
        // Call the click handler
        highlightFeature(event);
        mainTableBody.innerHTML = ''; // Clear existing rows
        setCurrentAreaId(areaId); // Set currentAreaId to the simulated area's ID

        // Fire a click event on the layer
        layer.fire('click', {
            latlng: layer.getBounds().getCenter(),
            layer: layer
        });
        
    } else {
        console.log(`No layer found for area_id: ${areaId}`);
    }
}

function clearData() {
    // Clear the <tbody> of <table id="nestedTable">
    const tableBody = document.getElementById('nestedTable').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = '';

    // Clear the panel content
    const panelContent = document.getElementById('panel-content');
    panelContent.innerHTML = '';

    // Clear area information
    const areaInfo = document.getElementById('area_info');
    areaInfo.innerHTML = '';
}

 function openLoginModal(title, formToShow = 'login') {
    var loginModal = document.getElementById("loginModal");
    var modalTitle = document.getElementById("modalTitle");
    var loginForm = document.getElementById("loginForm");
    var registerForm = document.getElementById("registerForm");
    var toggleFormText = document.getElementById("toggleFormText");

    modalTitle.textContent = title;
    loginModal.style.display = "block";
    if (formToShow === 'register') {
        loginForm.style.display = "none";
        registerForm.style.display = "block";
        toggleFormText.innerHTML = 'Already have an account? <a href="#" id="showLoginForm">Login</a>';
    } else {
        loginForm.style.display = "block";
        registerForm.style.display = "none";
        toggleFormText.innerHTML = 'Don\'t have an account? <a href="#" id="showRegisterForm">Register</a>';
    }
}


 function openChartModal(chartId, start_year, end_year,title,label_of_point = 'avg meter sale price') {
    // Fetch the dataset based on the chartId or directly pass the dataset
    const dataset = chartDataMappings[chartId];
    if (!dataset) {
        console.error('Dataset not found for chartId:', chartId);
        return;
    }

    // Labels for the x-axis
    const labels = Array.from({ length: end_year - start_year + 1 }, (v, i) => i + start_year);

    // Ensure the canvas context is clear before drawing a new chart
    const ctx = document.getElementById('landStatsChart').getContext('2d');

    // If there's an existing chart instance, destroy it to avoid overlay issues
    if (window.myChartInstance) {
        window.myChartInstance.destroy();
    }

    // Create a new chart instance
    window.myChartInstance = new Chart(ctx, {
        type: 'line', // Define the type of chart you want
        data: {
            labels: labels, // Years from start_year to end_year
            datasets: [{
                label: label_of_point, // Chart label
                data: dataset, // The dataset array from the mapping
                fill: false, // Determines whether the chart should be filled
                borderColor: 'rgb(36, 22, 235)', // Line color for the main part
                tension: 0.2, // Line smoothness
                segment: {
                    borderColor: ctx => {
                        // Change the last 5 points to red
                        const dataIndex = ctx.p0DataIndex;
                        if (dataIndex >= dataset.length - (end_year-2023)) {
                            return 'rgb(255, 0, 0)'; // Red color
                        }
                        return 'rgb(36, 22, 235)'; // Original color
                    }
                }
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false // Disable legend
                },
                title: {
                    display: true, // Enable title
                    text: title, // Title text
                    color: 'black', // Title color
                    font: {
                        size: 16 // Title font size
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true // Ensures the y-axis starts at 0
                }
            }
        }
    });

    // Show the modal
    document.getElementById('chartModal').style.display = 'block';
}
function openModal(title,footnote="Until 31/08/2024 then 19.99 $") {
    const modalTitle = document.querySelector('.modal-title');
    const premiumModal = document.getElementById('premiumModal');
    modalTitle.innerHTML = title;
    const footnoteElement = document.querySelector('.modal-footnote');

    if (footnote && footnote.trim() !== '') {
        footnoteElement.textContent = footnote;
        footnoteElement.style.display = 'block';
    } else {
        footnoteElement.style.display = 'none';
    }

    premiumModal.style.display = 'block';
  }


document.getElementById("settingsBtn").onclick = function() {
    document.getElementById("settingsModal").style.display = "block";
    retrieveListOrder();
};

// Function to retrieve and display the saved list order
function retrieveListOrder() {
    fetch('/get-list-order')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok.');
        }
        return response.json();
    })
    .then(data => {
        const orderArray = data.listOrder;
        rearrangeList(orderArray);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

 // Function to rearrange the list based on the order
 function rearrangeList(order) {
    const listItems = Array.from(hierarchyList.children);
    const sortedItems = order.map(id => listItems.find(item => item.dataset.id === id.toString()));
    
    // Clear the current list
    hierarchyList.innerHTML = '';
    
    // Append the sorted items
    sortedItems.forEach(item => {
        if (item) {
            hierarchyList.appendChild(item);
        }
    });
}

// Function to update the UI with the retrieved list order
function updateUIWithListOrder(listOrder) {
    const hierarchyList = document.getElementById("hierarchyList");
    hierarchyList.innerHTML = '';
    listOrder.forEach(item => {
        const li = document.createElement('li');
        li.draggable = true;
        li.dataset.id = item.id;
        li.innerHTML = `<span class="drag-handle">■</span> ${item.text}`;
        hierarchyList.appendChild(li);
    });
}


// Drag and drop functionality for hierarchy list
const listItems = document.querySelectorAll('#hierarchyList li');
let dragSrcEl = null;

function handleDragStart(e) {
    this.classList.add('dragging');
    dragSrcEl = this;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.outerHTML);
    // Removed style change for opacity or any other style manipulation
}

function handleDragOver(e) {
    e.preventDefault(); // Necessary for allowing a drop.
    this.classList.add('over');
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    // Remove 'over' class from all potential drop targets
    listItems.forEach(function(item) {
        item.classList.remove('over');
    });
}

function handleDragEnter(e) {
    // Optionally, add visual feedback on drag enter.
}

function handleDragLeave(e) {
    // Optionally, reverse visual feedback when drag leaves an element.
}

function handleDrop(e) {
    e.stopPropagation(); // Prevent default action (open as link for some elements).
    e.preventDefault();
    if (dragSrcEl !== this) {
        // Remove the dragged element from its original position
        dragSrcEl.remove();
        // Add the dragged element to its new position
        let dropHTML = e.dataTransfer.getData('text/html');
        this.insertAdjacentHTML('beforebegin', dropHTML);
        let dropElem = this.previousSibling;
        addDnDEvents(dropElem);
    }
    return false;
}

function handleDragEnd(e) {
    this.style.opacity = '1';  // Reset the opacity of the drag source.
    listItems.forEach(function (item) {
        item.classList.remove('over');
    });
}

function addDnDEvents(elem) {
    elem.addEventListener('dragstart', handleDragStart, false);
    elem.addEventListener('dragover', handleDragOver, false);
    elem.addEventListener('dragenter', handleDragEnter, false);
    elem.addEventListener('dragleave', handleDragLeave, false);
    elem.addEventListener('drop', handleDrop, false);
    elem.addEventListener('dragend', handleDragEnd, false);
}

listItems.forEach(addDnDEvents);




 function initializeStripe() {
    return fetch("/config")
        .then((result) => result.json())
        .then((data) => {
            return Stripe(data.publicKey);
        });
}


 async function setupPremiumButton(buttonId, stripe) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.addEventListener('click', async function(event) {
            event.preventDefault();
            await handleStripeCheckout(stripe);
        });
    }
}

// Function to handle Stripe checkout
 async function handleStripeCheckout(stripe) {
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