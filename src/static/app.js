
// Initialize the map on the "dubaiMap" div with a given center and zoom
 var map = L.map('dubaiMap').setView([25.2048, 55.2708], 10); // Centered on Dubai

// L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
//     attribution: '© OpenStreetMap contributors, © CARTO',
//     maxZoom: 19
// }).addTo(map);

L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 19
}).addTo(map);

const mainTableBody = document.querySelector('#mainTableBody');
const unlockTableBody = document.querySelector('#unlockTableBody');
const layersByAreaId = {};
const layersByParcelId = {};

let state = {
    currentFillColor: 'fillColorPrice',
    currentLegend: 'averageSalePrice',
    currentAreaId: null,
    currentParcelId: null
};
let currentMarker = null;
let cursorPosition = 0;

 function getCurrentFillColor() {
    return state.currentFillColor;
}
let allAreasData = null;
function getAllAreasData() {
    return allAreasData;
}

let allParcelsData = null;
function getAllParcelsData() {
    return allParcelsData;
}



 function getCurrentAreaId() {
    return state.currentAreaId;
}
function getCurrentParcelId() {
    return state.currentAreaId;
}

 function setCurrentAreaId(areaidd) {
    state.currentAreaId = areaidd;
}
function setCurrentParcelId(parcelId) {
    state.currentParcelId = parcelId;
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

const cursor = document.getElementById('cursor');
const verticalBar = document.querySelector('.vertical-bar');
const options = document.querySelectorAll('.option');

function moveCursor(position) {
    const maxPosition = options.length - 1;
    cursorPosition = Math.min(position, maxPosition);

    cursor.style.top = `${cursorPosition * 35}px`;

    showSpinner(); // Show the spinner before sending the request

    sendPositionToServer(position);

    const dropupMenu = document.getElementById('dropupMenu');
    const capitalAppreciationDiv = dropupMenu.querySelector('div[onclick="changeLegendTitle(\'Capital Appreciation\')"]');
    const grossRentalYieldDiv = dropupMenu.querySelector('div[onclick="changeLegendTitle(\'Gross Rental Yield\')"]');
    const acqDemandDiv = dropupMenu.querySelector('div[onclick="changeLegendTitle(\'Acquisition Demand\')"]');
    const acqDemandDivlOCKED = dropupMenu.querySelector('div[onclick="showPremiumMessage()"]');
    if (position === 1) {
        currentAreaData = null;
        // Remove the specified divs when position is 1
        if (capitalAppreciationDiv) capitalAppreciationDiv.remove();
        if (grossRentalYieldDiv) grossRentalYieldDiv.remove();
        if (acqDemandDiv) acqDemandDiv.remove();
        if (acqDemandDivlOCKED) acqDemandDivlOCKED.remove();
    } else if (position === 0) {
        allParcelsData = null;
        if (!capitalAppreciationDiv) {
            const newCapitalDiv = document.createElement('div');
            newCapitalDiv.setAttribute('onclick', "changeLegendTitle('Capital Appreciation')");
            newCapitalDiv.textContent = 'Capital appreciation 5Y';
            dropupMenu.appendChild(newCapitalDiv);
        }
        if (!grossRentalYieldDiv) {
            const newYieldDiv = document.createElement('div');
            newYieldDiv.setAttribute('onclick', "changeLegendTitle('Gross Rental Yield')");
            newYieldDiv.textContent = 'Gross Rental Yield';
            dropupMenu.appendChild(newYieldDiv);
        }
        
        if (!acqDemandDivlOCKED) {
            const newYieldDiv = document.createElement('div');
            newYieldDiv.className = 'locked-legend';
            newYieldDiv.setAttribute('onclick', 'showPremiumMessage()');
            newYieldDiv.innerHTML = 'Acquisition Demand <span id="lockIcon">🔒</span>';
            dropupMenu.appendChild(newYieldDiv);
        }
        else if(!acqDemandDiv){
            const newYieldDiv = document.createElement('div');
            newYieldDiv.setAttribute('onclick', "changeLegendTitle('Acquisition Demand')");
            newYieldDiv.textContent = 'Acquisition Demand';
            dropupMenu.appendChild(newYieldDiv);
        }
    }


}

function sendPositionToServer(position) {
    fetch('/update_position', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ position: position }),
    })
    .then(response => response.json())
    .then(data => {
        if(position ==1)
        {
            allParcelsData = data;
            applyProjectGeoJSONLayer();
        }
        else if(position==0)
        {
            allAreasData = data;
            applyGeoJSONLayer();
        }
        hideSpinner();
    })
    .catch((error) => {
        console.error('Error:', error);
        hideSpinner(); // Make sure to hide the spinner even if there's an error
    });
}

verticalBar.addEventListener('click', (event) => {
    const rect = verticalBar.getBoundingClientRect();
    const y = event.clientY - rect.top;
    const position = Math.floor(y / (rect.height / 3));
    moveCursor(position);
});

options.forEach((option) => {
    option.addEventListener('click', () => {
        const position = parseInt(option.getAttribute('data-position'));
        moveCursor(position);
    });
});
        
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
let currentParcelData = null;

document.getElementById('area-pdf-icon').addEventListener('click', function() {
    let currentData;
    let parcelData;
    if (cursorPosition == 0) {
        currentData = getCurrentAreaData();
    } else if (cursorPosition == 1) {
        currentData = getCurrentParcelData();
        parcelData = getCurrentJsonData();
    }
    // Create and show loading bar
    const loadingBar = document.createElement('div');
    loadingBar.style.width = '0%';
    loadingBar.style.height = '5px';
    loadingBar.style.backgroundColor = 'blue';
    loadingBar.style.position = 'fixed';
    loadingBar.style.top = '0';
    loadingBar.style.left = '0';
    loadingBar.style.transition = 'width 0.5s';
    document.body.appendChild(loadingBar);

    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 10;
        loadingBar.style.width = `${Math.min(progress, 90)}%`;
    }, 500);

    // Make an AJAX request to the server
    // Make an AJAX request to the server
    fetch('/generate-MAIN-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            mainData: currentData,
            cP: cursorPosition,  // Send the cursor position too
            pData: parcelData
        })
    })
    .then(response => response.blob())
    .then(blob => {
        // Create a new Blob object using the response data
        var url = window.URL.createObjectURL(blob);
        
        // Create a link element
        var link = document.createElement('a');
        link.href = url;
        link.download = 'report.pdf';
        
        // Append to the document body
        document.body.appendChild(link);
        
        // Programmatically click the link to trigger the download
        link.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
        
        // Complete the loading bar
        loadingBar.style.width = '100%';
        setTimeout(() => {
            document.body.removeChild(loadingBar);
            clearInterval(progressInterval);
        }, 500);
    })
    .catch(error => {
        console.error('Error:', error);
        // Remove loading bar on error
        document.body.removeChild(loadingBar);
        clearInterval(progressInterval);
    });
});



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


function applyProjectGeoJSONLayer() {
    const data = getAllParcelsData();
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
        style: feature => featureStyle(feature, getCurrentFillColor(),"project"),
        onEachFeature: onEachFeature
    }).addTo(map);

    updateLegend(legends[getCurrentLegend()],units[getCurrentLegend()]);
}


// load the .geojson file to display the areas
 function applyGeoJSONLayer() {
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
        style: feature => featureStyle(feature, getCurrentFillColor()),
        onEachFeature: onEachFeature
    }).addTo(map);

    updateLegend(legends[getCurrentLegend()],units[getCurrentLegend()]);
}


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
        contentCellHtml += `<button class="pdf-icon"><img src="static/pdf-icon2_black.svg" alt="PDF" class="pdf-icon-img"></button>`;
    }
    if (fake_line) {
        row.classList.add('blurry-row');
        fakeLineAdded++;
    }
    if (isParent || fake_line) {
        row.classList.add('expandable');
    }
    else if(!isParent)
    {
        contentCellHtml += `<button class="recent_trans_icon"><img src="static/table.svg" alt="list" class="recent_trans_icon_img"></button>`;
    }
    const contentCell = row.insertCell();
    contentCell.innerHTML = contentCellHtml;
    if (!parentRowId) {
        contentCell.classList.add('root-cell');
    }
    else if(!isParent){
        contentCell.classList.add('content-cell');
    }
    //contentCell.classList.add('root-cell'); // Add a class for additional styling if needed
    // Creating placeholders for the other values
    ['Capital Appreciation 2019', 'Capital Appreciation 2014', 'ROI', 'avg transaction value', 'avg_meter_price_2014_2024','Projected Capital Appreciation 5Y'].forEach(() => row.insertCell());

    return rowId;
}

// Event delegation for recent transactions clicks
document.addEventListener('click', function(event) {
    const listIcon = event.target.closest('.recent_trans_icon');
    if (listIcon) {
        event.preventDefault();

        //show modal:
        const modalv2 = document.getElementById('myModal_v2');
        modalv2.style.display = 'block';
        // Automatically click the "Sales" tab button when the modal is displayed
        document.querySelector('.tablink[onclick="openTab_v2(event, \'Sales\')"]').click();

        let currentRow = listIcon.closest('tr');
        
        let data = {};

        while (currentRow) {
            let rowType = currentRow.getAttribute('type');
            let rowName = currentRow.getAttribute('data-name');
            
            // Add the type and its value to the JSON object
            if (rowType && rowName) {
                data[rowType] = rowName;
            }

            // Move to the parent row
            let parentRowId = currentRow.getAttribute('data-parent-id');
            if (!parentRowId) break; // No more parents, exit the loop
            currentRow = document.querySelector(`tr[data-row-id="${parentRowId}"]`);
        }

         // Fetch both sales and rents data
         Promise.all([
            fetch('/get-recent-transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            }).then(response => response.json()),

            fetch('/get-recent-rents', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            }).then(response => response.json())
        ])
        .then(([salesData, rentsData]) => {
            // Populate Sales tab
            populateTabContent('Sales', salesData.result);
            // Populate Rents tab
            populateTabContent('Rents', rentsData.result);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
});

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
    // Check if currentAreaData is valid
    if (!currentAreaData || typeof currentAreaData !== 'object' || Object.keys(currentAreaData).length === 0) {
        console.error('Invalid or empty currentAreaData');
        alert('Error: Area data is not available. Please try again.');
    }

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
        alert("An error occurred while generating the PDF. Please try again later.");
    });
}

 function createSvgLineChart(dataPoints, chartId, startYear, endYear,chart_title,label_of_point ='avg meter sale price',blurFuture=false) {
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
    let blurredPathD = ''; // Path for the blurred part (2026-2029)
    let moveToNext = true; // Flag to indicate when to move to the next point without drawing
    let lastBluePointX, lastBluePointY; // Keep track of the last non-null point in the blue line


    if(blurFuture)
    {
        dataPoints.forEach((point, index) => {
            if (point !== null) {
                const x = padding + pointWidth * index;
                const y = padding + chartHeight - ((point - minVal) / (maxVal - minVal) * chartHeight);
                if (index < dataPoints.length - Math.max(0, (endYear - 2024))) {
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
    
        // Calculate the x-coordinate for the start of the blur (2025)
        const blurStartX = padding + pointWidth * (2025 - startYear);
    
        // Create the axis lines
        const xAxisY = padding + chartHeight;
        const yAxisX = padding;
    
        return `<svg class="clickable-chart" data-chart-id="${chartId}" onclick="openChartModal('${chartId}',${startYear},${endYear},'${chart_title}','${label_of_point}')" width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <defs>
        <filter id="whiteGrainyBlur">
            <feTurbulence type="fractalNoise" baseFrequency="0.2" numOctaves="2" result="noise"/>
            <feColorMatrix in="noise" type="matrix" values="1 0 0 0 0
                                                            1 0 0 0 0
                                                            1 0 0 0 0
                                                            0 0 0 0.5 0" result="whiteNoise"/>
            <feComposite in="whiteNoise" in2="SourceGraphic" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" result="grainMix"/>
            <feGaussianBlur in="grainMix" stdDeviation="1.5" result="blurred"/>
            <feBlend in="SourceGraphic" in2="blurred" mode="screen"/>
        </filter>
    </defs>
            <line x1="${padding}" y1="${xAxisY}" x2="${width - padding}" y2="${xAxisY}" stroke="black"/>
            <line x1="${yAxisX}" y1="${padding}" x2="${yAxisX}" y2="${height - padding}" stroke="black"/>
            <path d="${pathD.trim()}" stroke="blue" fill="none"/>
            <path d="${redPathD.trim()}" stroke="red" fill="none"/>
            <rect x="${blurStartX}" y="${padding}" width="${width - blurStartX - padding}" height="${chartHeight}" fill="grey" opacity="0.97" filter="url(#whiteGrainyBlur)"/>
        </svg>`;
    }
    else 
    {
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
                hasChildren = !value.avgCapitalAppreciation2019
                              && !value.avgCapitalAppreciation2014
                              && !value.avg_roi
                              && !value.avg_actual_worth
                              && !value.avg_meter_price_2014_2024
                              && !value.avgCapitalAppreciation2014
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
                const attributeName = value && typeof value === 'object' && typeof value.type === 'string'
                ? value.type
                : 'defaultAttribute';
                row.setAttribute("type", attributeName);

                row.cells[1].innerText = (value.avgCapitalAppreciation2019 || value.avgCapitalAppreciation2019 === 0) && !isNaN(value.avgCapitalAppreciation2019) ? (value.avgCapitalAppreciation2019 * 100).toFixed(2) : '-';
                row.cells[2].innerText = (value.avgCapitalAppreciation2014 || value.avgCapitalAppreciation2014 === 0) && !isNaN(value.avgCapitalAppreciation2014) ? (value.avgCapitalAppreciation2014 * 100).toFixed(2) : '-';
                row.cells[3].innerText = (value.avg_roi) && !isNaN(value.avg_roi) ? (value.avg_roi * 100).toFixed(2) : '-';
                row.cells[4].innerText = (value.avg_actual_worth) && !isNaN(value.avg_actual_worth) 
                ? Number(value.avg_actual_worth).toLocaleString('en-US', {maximumFractionDigits: 2}) 
                : '-';
                row.cells[5].innerHTML = createSvgLineChart(value.avg_meter_price_2014_2024,parentRowId,2014,2029,'Evolution of Meter Sale Price','avg meter sale price',!isPremiumUser);
                
                if (value.avgCapitalAppreciation2029 == -999) { //if the value is -999, it means that the user is not a premium user
                    row.cells[6].innerHTML = '<div class="blurred-content">Blurred</div>';
                } else {
                    row.cells[6].innerText = (value.avgCapitalAppreciation2029 || value.avgCapitalAppreciation2029 === 0) && !isNaN(value.avgCapitalAppreciation2029) ? (value.avgCapitalAppreciation2029 * 100).toFixed(2) : '-';
                }
                chartDataMappings[parentRowId] = value.avg_meter_price_2014_2024; 
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
                const attributeName = value && typeof value === 'object' && typeof value.type === 'string'
                ? value.type
                : 'defaultAttribute';
                row.setAttribute("type", attributeName);
                
                row.cells[1].innerText = (value.avgCapitalAppreciation2019 || value.avgCapitalAppreciation2019 === 0) && !isNaN(value.avgCapitalAppreciation2019) ? (value.avgCapitalAppreciation2019 * 100).toFixed(2) : '-';
                row.cells[2].innerText = (value.avgCapitalAppreciation2014 || value.avgCapitalAppreciation2014 === 0) && !isNaN(value.avgCapitalAppreciation2014) ? (value.avgCapitalAppreciation2014 * 100).toFixed(2) : '-';
                row.cells[3].innerText = (value.avg_roi || value.avg_roi === 0) && !isNaN(value.avg_roi) ? (value.avg_roi * 100).toFixed(2) : '-';
                row.cells[4].innerText = (value.avg_actual_worth) && !isNaN(value.avg_actual_worth) 
                ? Number(value.avg_actual_worth).toLocaleString('en-US', {maximumFractionDigits: 2}) 
                : '-';
                row.cells[5].innerHTML = createSvgLineChart(value.avg_meter_price_2014_2024,currentRowId,2014,2029,'Evolution of Meter Sale Price','avg meter sale price',!isPremiumUser);
                if (value.avgCapitalAppreciation2029 == -999) { //if the value is -999, it means that the user is not a premium user
                    row.cells[6].innerHTML = '<div class="blurred-content">Blurred</div>';
                } else {
                    row.cells[6].innerText = (value.avgCapitalAppreciation2029 || value.avgCapitalAppreciation2029 === 0) && !isNaN(value.avgCapitalAppreciation2029) ? (value.avgCapitalAppreciation2029 * 100).toFixed(2) : '-';
                }
                chartDataMappings[currentRowId] = value.avg_meter_price_2014_2024; 
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
function featureStyle(feature, fillColorProperty,type="area") {
    if (type=="project")
    {
        if (fillColorProperty == "blank") {
            return {
                fillColor: 'transparent',
                weight: 1,
                opacity: 0.1,
                color: 'black',
                fillOpacity: 0.7
            }; 
        }
        return {
            fillColor: feature.properties[fillColorProperty], // Dynamic fill color based on the property
            weight: 1,
            opacity: 0.1,
            color: 'black',
            fillOpacity: 0.85
        }; 
    }
    if (fillColorProperty == "blank") {
        return {
            fillColor: 'transparent',
            weight: 2,
            opacity: 1,
            color: 'black',
            fillOpacity: 0.4
        }; 
    }
    return {
        fillColor: feature.properties[fillColorProperty], // Dynamic fill color based on the property
        weight: 2,
        opacity: 1,
        color: 'black',
        fillOpacity: 0.4
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
    if(cursorPosition==0)
    {
        const areaId = feature.properties.area_id;
        layersByAreaId[areaId] = layer; // Store layer by area_id
        layer.on({
            click: function(e) {
                highlightFeature(e);
                updateAreaInfo(feature);
            }
        });
    }
    else if(cursorPosition==1)
    {
        const parcelId = feature.properties.parcel_id;
        layersByParcelId[parcelId] = layer; // Store layer by area_id
        layer.on({
            click: function(e) {
                highlightFeature(e);
                updateParcelInfo(feature);
            }
        });
    }
    
    
}

function updateParcelInfo(feature) {
    mainTableBody.innerHTML = ''; // Clear existing rows
    setCurrentParcelId(feature.properties.parcel_id);
    // Create a copy of feature.properties without the "geometry" property
    const { geometry, ...propertiesWithoutGeometry } = feature.properties;
    currentParcelData = propertiesWithoutGeometry; // Save as global variable for later

    const projectName = feature.properties.name;
    const areaInfo = document.getElementById('area_info');
    const areaTitleH2 = document.getElementById('area-title');
    const buttonToRemove = document.querySelector('#panel-content .tab button[onclick*="ProjectsDemand"]');
    if (buttonToRemove) {
        buttonToRemove.remove();
    }

    areaTitleH2.innerHTML = projectName;

    const variableNames = feature.properties.variableNames;
    const variableValues = feature.properties.variableValues;
    const variableunits = feature.properties.variableUnits;
    const variableSpecial= feature.properties.variableSpecial;
    const cards = document.querySelectorAll('.info-card');

    const statsContainer = document.getElementById('stats-container');
    statsContainer.innerHTML = '';
    const cardData = [
        { id: 'card1', title: 'Locked', value: '99', locked: false },
      ];
      offset_on_index =0;
      cardData.forEach((cardInfo, index) => {
        if (!cardInfo.locked && variableSpecial[index+offset_on_index] === 0) {
          cardInfo.title = variableNames[index+offset_on_index];

          let value = variableValues[index+offset_on_index];
          if (variableunits[index+offset_on_index] === '%') {
            cardInfo.value = `${(value * 100).toFixed(2)} %`;
          } else if (variableunits[index+offset_on_index] === 'AED') {
            cardInfo.value = `${value} AED`;
          } else if (variableunits[index+offset_on_index] === 'm AED') {
            cardInfo.value = `${value.toFixed(2)} M AED`;
          } else {
            cardInfo.value = value;
          }
        }
        else if(cardInfo.id =='card5')
        {
            offset_on_index=1;
        }
        else if(cardInfo.id =='card6') //todo :use the special variable is better than id
        {
            cardInfo.title = 'Supply of Lands:';
            cardInfo.value = variableValues[index+offset_on_index];
        }

        const card = createCard(cardInfo);
        statsContainer.appendChild(card);
      });


   /* let array_index = 0;

    // Loop through each card and populate with the corresponding variable name and value
    cards.forEach((card) => {
            if(card.id !='card1')
            {
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
            
                card.remove();
            }
            if(variableSpecial[array_index]==0)
            {
                const title = variableNames[array_index];
                let value = variableValues[array_index];

                if(card.id =='card1')
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
                else if(variableunits[array_index] == "m AED")
                {
                    card.querySelector('.value').textContent= `${value.toFixed(2)} M AED`;
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
    const statsContainer = document.getElementById('stats-container');*/
    areaInfo.appendChild(statsContainer);

    const panel = document.getElementById('info-panel');
    panel.style.display = 'block';
    
    // Remove any existing error messages before fetching new data
    const existingErrorMessage = document.getElementById('error-message');
    if (existingErrorMessage) {
        existingErrorMessage.remove();
    }

    fetchMoreDetails(getCurrentParcelId(),"parcel",projectName);


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
    const statsContainer = document.getElementById('stats-container');
    statsContainer.innerHTML = '';
    const cardData = [
        { id: 'card1', title: 'Locked', value: '99', locked: false },
        { id: 'card2', title: 'Locked', value: '99', locked: false },
        { id: 'card3', title: 'Locked', value: '99', locked: false },
        { id: 'card4', title: 'Locked', value: '99', locked: false },
        { id: 'card9', title: 'Locked', value: '99', locked: false },
        { id: 'card10', title: 'Locked', value: '99', locked: false },
        { id: 'card11', title: 'Locked', value: '99', locked: false },
        // Add more cards as needed
        {
          id: 'card5',
          type: 'supply',
          title: 'Supply of Projects:',
          finishedValue: variableValues[7],
          offPlanValue: variableValues[8],
          locked: false
        },
        {
        id: 'card6',
        type: 'lands',
        title: 'Supply of Lands:',
        value: '99',
        locked: false
        },
        {
        id: 'card7',
        title: 'Locked',
        value: '99',
        locked: false
        },
        {
        id: 'card8',
        title: 'Locked:',
        value: '99',
        locked: false
        },
        // Include other special cards similarly
      ];
      offset_on_index =0;
      cardData.forEach((cardInfo, index) => {
        if (!cardInfo.locked && variableSpecial[index+offset_on_index] === 0) {
          cardInfo.title = variableNames[index+offset_on_index];
          let value = variableValues[index+offset_on_index];
          if (variableunits[index+offset_on_index] === '%') {
            cardInfo.value = `${(value * 100).toFixed(2)} %`;
          } else if (variableunits[index+offset_on_index] === 'AED') {
            cardInfo.value = `${value} AED`;
          } else if (variableunits[index+offset_on_index] === 'm AED') {
            cardInfo.value = `${value.toFixed(2)} M AED`;
          } else {
            cardInfo.value = value;
          }
        }
        else if(cardInfo.id =='card5')
        {
            offset_on_index=1;
        }
        else if(cardInfo.id =='card6') //todo :use the special variable is better than id
        {
            cardInfo.title = 'Supply of Lands:';
            cardInfo.value = variableValues[index+offset_on_index];
        }

        const card = createCard(cardInfo);
        statsContainer.appendChild(card);
      });

    let array_index = 0;
    // Loop through each card and populate with the corresponding variable name and value
    /*cards.forEach((card) => {
        // Ensure we have a corresponding variable name and value
        
        if(card.id=='card5' && variableNames.length >8)
        {
            const supplyCard = document.getElementById('card5');
            if (supplyCard) {
                supplyCard.querySelector('.title').textContent ='Supply of Projects:';
                const finishedValue = variableNames.includes('supply_finished_pro') ? variableValues[7] : "-";
                const offplanValue = variableNames.includes('supply_offplan_pro') ? variableValues[8] : "-";
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
        else if(card.id=='card6' && variableNames.length >8)
        {
            const landsCard = document.getElementById('card6');
            if (landsCard) {
                landsCard.querySelector('.title').textContent ='Supply of Lands:';
                const landsValue = variableNames.includes('supply_lands') ? variableValues[9] : "-";
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
            else if(card.id=='card9')
            {
                const tooltipText = "Number of sales contracts in the last 12 months"
                card.querySelector('.title').innerHTML = `${title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
            }
            else if(card.id =='card10')
            {
                const tooltipText = "Total value of all sales transactions within the last 12 months in millions AED"
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
            else if(variableunits[array_index] == "m AED")
            {
                card.querySelector('.value').textContent= `${value.toFixed(2)} M AED`;
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
});*/
    
    // Append the container of cards to the panel content
    areaInfo.appendChild(statsContainer);

    const panel = document.getElementById('info-panel');
    panel.style.display = 'block';
    
    // Remove any existing error messages before fetching new data
    const existingErrorMessage = document.getElementById('error-message');
    if (existingErrorMessage) {
        existingErrorMessage.remove();
    }
    
    // Use the new fetchMoreDetails function
    fetchMoreDetails(getCurrentAreaId(),"area");

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
            fetchMoreDetails(getCurrentAreaId(),"area");
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
};

function fetchMoreDetails(iD,HierarchyType,grouped_project) {
    mainTableBody.innerHTML = ''; // Clear existing rows
    const loader = document.querySelector('.loader');
    loader.style.display = 'grid'; // Display loader
    
    let url = `/get-more-details?id=${iD}&hierarchy_type=${HierarchyType}`;
    if (grouped_project) {
        url += `&grouped_project=${grouped_project}`;
    }

    fetch(url)
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
    const yieldCalcbutton = document.getElementById('yieldCalculatorButton');
    if(yieldCalcbutton)
    {
        yieldCalcbutton.addEventListener('click', function() {
            window.location.href = '/cashflow_calc';
        });
    }

    const assetIdentifierButton = document.getElementById('assetIdentifierButton');
    if(assetIdentifierButton)
    {
        assetIdentifierButton.addEventListener('click', function() {
            window.location.href = '/asset_identification';
        });
    }


    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('open_premium_modal') === 'True') {
        openModal('This is a Premium Feature');
    }


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
        if (modal) {
            modal.style.display = "none";
        }
    }

    // Get all modals
    const modals = document.querySelectorAll('.modal');

    // Attach event listeners to each modal
    modals.forEach(modal => {
        // Find the close button within this modal
        const closeButton = modal.querySelector('.close-button');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                closeModal(modal);
            });
        }

        // Close the modal if the user clicks outside of the modal content
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });

    document.getElementById("unlock-button-table").onclick = function() {
        openModal('Unlock all projects Today for $49.99');
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
  
    // Add keypress event listener for Enter key
    searchInput.on("keypress", function(e) {
      if (e.which === 13) { // Enter key code
        e.preventDefault();
        const query = $(this).val();
        if (query.length > 0) {
          centerMapOnAddress(query);
        }
        searchResults.hide();
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
          .addClass(item.type)
          .addClass(item.project_id);
  
        const itemName = $("<span>")
          .addClass("item-name")
          .text(item.name);
  
        const itemType = $("<span>")
          .addClass("item-type")
          .text(item.type);
  
        if (cursorPosition != 1 || item.type != 'area') {
          resultItem.append(itemName, itemType);
        }
  
        if (item.type === 'project') {
          const itemArea = $("<div>")
            .addClass("item-area")
            .text(item.area_name);
          resultItem.append(itemArea);
        }
  
        resultItem.on("click", function() {
          if (cursorPosition == 0) {
            if (item.type === 'project' || item.type === 'area') {
              simulateClick(item.id);
            }
          } else if (cursorPosition == 1) {
            if (item.type === 'project') {
              getParcelIdsFromProjectId(item.project_id)
                .then(parcelIds => {
                  highlightParcels(parcelIds);
                })
                .catch(error => console.error('Error:', error));
            }
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
function getCurrentParcelData(){
    return currentParcelData;
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
    applyGeoJSONLayer();
});


