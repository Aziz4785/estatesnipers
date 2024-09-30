 function generateTable(data) {
    var table = document.createElement('table');

    // Create the table header
    var thead = document.createElement('thead');
    var headerRow = document.createElement('tr');
    ['Project', 'Internal Demand 2024 %', 'External Demand 2024 %','External Demand 2019-2024'].forEach((headerText, index) => {
        var header = document.createElement('th');
        if (index === 1) { // For 'Internal Demand 2024 %'
            header.innerHTML = headerText + `<span class="info-icon info-icon-internal" tabindex="0" data-tooltip="(Number of transaction in the project in year 2024) / (Number of units in the project) * 100"">i</span>`;
        } else if (index === 2) { // For 'External Demand 2024 %'
            header.innerHTML = headerText + ' <span class="info-icon info-icon-external" tabindex="0" data-tooltip="(Number of transaction in the project in year 2024) /(Total number of transactions in 2024) * 100">i</span>';
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
        [item.project_name_en, item.internaldemand2024, item.externaldemand2024, item.externalDemandYears].forEach((value, index) => {
            var cell = document.createElement('td');
            cell.textContent = value;
            if (index === 3) { 
   
                cell.innerHTML = createSvgLineChart(value, row_id,2019,2024,'Evolution of External Demand','External Demand');
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

function getParcelIdsFromProjectId(projectId) {
    return fetch(`/get_parcels/${projectId}`)
        .then(response => response.json())
        .then(data => data.parcel_ids);
}


function highlightParcels(parcelIds) {
    let layersToHighlight = [];

    // Iterate over each layer in the GeoJSON layer
    const parcelIdStrings = parcelIds.map(id => id.toString());

    window.geoJSONLayer.eachLayer(function(layer) {
        const parcelId = layer.feature.properties.parcel_id;

        // Check if the current parcel_id is in the list
        if (parcelIdStrings.includes(parcelId)) {
            // Change the style of the polygon
            layer.setStyle({
                fillOpacity: 0.7, // Adjust opacity as needed
                color: 'white',     // Outline color
                weight: 4,         // Outline width
                opacity: 1
            });

            // Add the layer to the list for adjusting the map view
            layersToHighlight.push(layer);
        }
    });

    // If any layers were highlighted, adjust the map view
    if (layersToHighlight.length > 0) {
        const group = L.featureGroup(layersToHighlight);
        map.fitBounds(group.getBounds());
    } else {
        console.warn('No parcels found with the specified IDs.');
    }
}

 function highlightFeature(e) {
    const layer = e.target;

    // Reset style for all layers
    window.geoJSONLayer.eachLayer(function(layer) {
        window.geoJSONLayer.resetStyle(layer);
    });

    // Set the style for the clicked layer
    layer.setStyle({
        weight: 4,
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
}

function centerMapOnAddress(address) {
    fetch('/geocode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address: address })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Geocoding server error: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.lat && data.lon) {
            // Center the map on the coordinates and set the zoom level
            map.setView([data.lat, data.lon], 15);

            // Add a marker at the location
            L.marker([data.lat, data.lon]).addTo(map)
                .bindPopup(data.address)
                .openPopup();
        } else {
            alert('Address not found: ' + address);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
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

function closeModal_v2() {
    const modalv2 = document.getElementById('myModal_v2');
    modalv2.style.display = 'none';
}
function populateTabContent(tabId, data) {
    // Get the tab content div
    const tabContentDiv = document.getElementById(tabId);
    
    // Clear any existing content
    tabContentDiv.innerHTML = `<h3> Recent ${tabId} Contracts </h3>`;
    
    // Create a wrapper div for horizontal scrolling
    let scrollDiv = document.createElement('div');
    scrollDiv.style.overflowX = 'auto'; // Enable horizontal scrolling
    scrollDiv.style.width = '100%'; // Make sure it takes the full width

    // Create a table
    let table = document.createElement('table');
    table.border = '1';
    table.style.width = '100%';

    // Create table header
    let thead = document.createElement('thead');
    let headerRow = document.createElement('tr');
    
    // Assuming all rows have the same keys
    if (data.length > 0) {
        Object.keys(data[0]).forEach(key => {
            let th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    let tbody = document.createElement('tbody');
    data.forEach(row => {
        let tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            let td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    // Append the table to the scrollable div
    scrollDiv.appendChild(table);

    // Append the scrollable div to the tab content div
    tabContentDiv.appendChild(scrollDiv);
}
function openTab_v2(evt, tabName) {
    var i, tabcontent, tablinks;
    
    // Hide all tab contents
    tabcontent = document.getElementsByClassName("tabcontent_modalv2");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    
    // Remove the active class from all tab links
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    
    // Show the current tab content and add an "active" class to the clicked tab
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

 function showPremiumMessage() {
    openModal('Access all content today for $49.99');
}

// Helper function to get the parent row attribute based on the parent row ID
function getParentRowAttribute(currentRow, parentRowId, attributeName) {
    let parentRow = document.querySelector(`tr[data-row-id="${parentRowId}"]`);
    return parentRow ? parentRow.getAttribute(attributeName) : null;
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
        { color: 'rgb(192, 0, 0, 0.7)', label: `> ${averageSalePrice[2]} ${unit}` },
        { color: 'rgb(223, 82, 82, 0.7)', label: `${averageSalePrice[2]} ${unit} - ${averageSalePrice[1]} ${unit}` },
        { color: 'rgb(82, 82, 223, 0.7)', label: `${averageSalePrice[1]} ${unit} - ${averageSalePrice[0]} ${unit}` },
        { color: 'rgb(0, 0, 192, 0.7)', label: `< ${averageSalePrice[0]} ${unit}` }
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
            setCurrentLegend("aquisitiondemand_2024");
            break;
        case 'Remove Filers':
            setCurrentFillColor("blank");
            setCurrentLegend("blank");
            break;
    }

    if (cursorPosition ==0)
    {
        applyGeoJSONLayer();
    }
    else if(cursorPosition==1)
    {
        applyProjectGeoJSONLayer();
    }
    
}

function createCard(cardInfo) {
    const card = document.createElement('div');
    if (cardInfo.type == 'supply')
    {
        card.className = 'info-card supply-projects';
    }
    else 
    {
        card.className = 'info-card';
    }
    
    if (cardInfo.locked) {
      card.classList.add('locked-card');
    }
    if (cardInfo.id == 'card8')
    {
        card.classList.add('lastcard');
    }
    card.id = cardInfo.id;
  
    const titleDiv = document.createElement('div');
    titleDiv.className = 'title';
    titleDiv.textContent = cardInfo.title;
    if(card.id=='card8')
        {
            const tooltipText = "Fraction of long-term rented units in the area";
            titleDiv.innerHTML = `${cardInfo.title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
        }
        else if(card.id=='card7')
        {
            const tooltipText = "Fraction of sold units in the area"
            titleDiv.innerHTML = `${cardInfo.title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
        }
        else if(card.id=='card9')
        {
            const tooltipText = "Number of sales contracts in the last 12 months"
            titleDiv.innerHTML = `${cardInfo.title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
        }
        else if(card.id =='card10')
        {
            const tooltipText = "Total value of all sales transactions within the last 12 months in millions AED"
            titleDiv.innerHTML = `${cardInfo.title} <span class="info-icon info-icon-internal" tabindex="0" data-tooltip="${tooltipText}">i</span>`;
        }

    card.appendChild(titleDiv);
  
    const valueDiv = document.createElement('div');
    valueDiv.className = 'value';
    valueDiv.textContent = cardInfo.value || '';
    if (cardInfo.type != 'supply')
    {
        card.appendChild(valueDiv);
    }
    if (cardInfo.type === 'lands')
    {
        const landButton = document.createElement('button');
        landButton.id = 'land-chart-button';
        landButton.className = 'stats-button';
        landButton.innerHTML = '<i class="fas fa-chart-pie"></i>';
        landButton.addEventListener('click', function() {
            fetch(`/get-lands-stats?area_id=${getCurrentAreaId()}`)
              .then(response => {
                if (response.status === 204) {
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
        card.appendChild(landButton);
    } 
    

    // Handle special card types
    if (cardInfo.type === 'supply') {
      const supplyDetails = document.createElement('div');
      supplyDetails.className = 'supply-details';
  
      const finishedColumn = document.createElement('div');
      finishedColumn.className = 'supply-column';
      const finishedTitle = document.createElement('div');
      finishedTitle.className = 'sub-title';
      finishedTitle.textContent = 'Finished';
      const finishedValue = document.createElement('div');
      finishedValue.className = 'value finished-value';
      finishedValue.textContent = cardInfo.finishedValue || '-';
      finishedColumn.appendChild(finishedTitle);
      finishedColumn.appendChild(finishedValue);
  
      const offPlanColumn = document.createElement('div');
      offPlanColumn.className = 'supply-column';
      const offPlanTitle = document.createElement('div');
      offPlanTitle.className = 'sub-title';
      offPlanTitle.textContent = 'Off Plan';
      const offPlanValue = document.createElement('div');
      offPlanValue.className = 'value offplan-value';
      offPlanValue.textContent = cardInfo.offPlanValue || '-';
      offPlanColumn.appendChild(offPlanTitle);
      offPlanColumn.appendChild(offPlanValue);
  
      supplyDetails.appendChild(finishedColumn);
      supplyDetails.appendChild(offPlanColumn);
      card.appendChild(supplyDetails);
    }
  
    // Add lock icon if the card is locked
    if (cardInfo.locked) {
      const lockIconCard = document.createElement('div');
      lockIconCard.className = 'lock-icon-card';
      const lockIcon = document.createElement('img');
      lockIcon.src = 'static/lock_similar.svg';
      lockIcon.alt = 'Lock Icon';
      lockIcon.width = 40;
      lockIcon.height = 40;
      lockIcon.style.cursor = 'pointer';
      lockIcon.addEventListener('click', () => {
        openModal('Unlock all details Today for $49.99');
      });
      lockIconCard.appendChild(lockIcon);
      card.appendChild(lockIconCard);
    }
  
    return card;
  }

function showSpinner() {
    const spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        z-index: 1000;
    `;

    const keyframes = `
        @keyframes spin {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
        }
    `;

    const style = document.createElement('style');
    style.textContent = keyframes;
    document.head.appendChild(style);
    document.body.appendChild(spinner);
}

// Function to hide the loading spinner
function hideSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
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
    fetch('/check_premium')
    .then(response => response.json())
    .then(data => {
        if (data.isPremium) {

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
                                if (dataIndex >= dataset.length - (end_year-2024)) {
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
        else{
            openModal('Get access to future meter sale price chart by upgrading to premium');
        }
    }).catch(error => {
        console.error('Error checking premium status:', error);
        // In case of error, default to non-premium behavior
        openModal('Get access to future meter sale price chart by upgrading to premium');
    });
}