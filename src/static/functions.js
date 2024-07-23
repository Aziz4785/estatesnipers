import { map ,getCurrentAreaId,setCurrentAreaId,layersByAreaId,setCurrentFillColor,applyGeoJSONLayer,chartDataMappings } from './app.js';

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
   
                cell.innerHTML = createSvgLineChart(value, row_id,2018,2023,'Evolution of External Demand');
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

export function highlightFeature(e) {
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
export function showPremiumMessage() {
    /*const premiumMessage = document.getElementById('premiumMessage');
    premiumMessage.style.display = 'block';
    setTimeout(() => {
        premiumMessage.style.display = 'none';
    }, 3000);  // Show the message for 3 seconds*/
    openModal('Access all content today for $19.99');
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

export function updateLegend(averageSalePrice, unit) {
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

export function changeLegendTitle(title) {
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


export function simulateClick(areaId) {
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

export function openLoginModal(title, formToShow = 'login') {
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


export function openChartModal(chartId, start_year, end_year,title) {
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
                label: 'avg meter sale price', // Chart label
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