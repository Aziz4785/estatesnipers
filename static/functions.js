function generateTable(data) {
    var table = document.createElement('table');
    table.setAttribute('border', '1');

    // Create the table header
    var thead = document.createElement('thead');
    var headerRow = document.createElement('tr');
    ['Project', 'Internal Demand 2023', 'External Demand 2023'].forEach(headerText => {
        var header = document.createElement('th');
        header.textContent = headerText;
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
        [item.project_name_en, item.internalDemand2023, item.externalDemand2023, item.externalDemandYears].forEach((value, index) => {
            var cell = document.createElement('td');
            cell.textContent = value;
            if (index === 3) { 
   
                cell.innerHTML = createSvgLineChart(value, row_id);
            } else {
                cell.textContent = value;
            }
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    return table;
}