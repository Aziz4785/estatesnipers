function generateTable(data) {
    var table = document.createElement('table');

    // Create the table header
    var thead = document.createElement('thead');
    var headerRow = document.createElement('tr');
    ['Project', 'Internal Demand 2023 %', 'External Demand 2023 %','External Demand 2018-2023'].forEach((headerText, index) => {
        var header = document.createElement('th');
        if (index === 1) { // For 'Internal Demand 2023 %'
            header.innerHTML = headerText + ' <span class="info-icon info-icon-internal" tabindex="0">i</span>';
        } else if (index === 2) { // For 'External Demand 2023 %'
            header.innerHTML = headerText + ' <span class="info-icon info-icon-external" tabindex="0">i</span>';
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
/*document.getElementById('legendTitle').addEventListener('click', function() {
    const dropdownMenu = document.getElementById('dropdownMenu');
    dropdownMenu.style.display = dropdownMenu.style.display === 'none' ? 'block' : 'none';
    const arrow = document.getElementById('arrow');
    arrow.style.transform = dropdownMenu.style.display === 'block' ? 'rotate(180deg)' : 'rotate(0deg)';
});*/

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
    console.log("changeLegendTitle()");
    // Handle the change of legend content based on the selected title
    currentFillColor = "fillColorPrice";
    currentLegend = "averageSalePrice";
    console.log("title",title);
    switch (title) {
        case 'Average meter price':
        currentFillColor = "fillColorPrice";
        currentLegend = "averageSalePrice";
        break;
        case 'Capital Appreciation':
        currentFillColor = "fillColorCA5";
        currentLegend = "avgCA_5Y";
        break;
        case 'Gross Rental ROI':
        currentFillColor = "fillColorRoi";
        currentLegend = "avg_roi";
        break;
        case 'Acquisition Demand':
        currentFillColor = "fillColorAquDemand";
        currentLegend = "aquisitiondemand_2023";
        break;
    }

    // Apply the GeoJSON layer with the new legend
    applyGeoJSONLayer(currentLegend);
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

function openChartModal(chartId, start_year, end_year,title) {
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