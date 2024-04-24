
document.getElementById("settingsBtn").onclick = function() {
    document.getElementById("settingsModal").style.display = "block";
};

document.querySelector(".close-button").onclick = function() {
    document.getElementById("settingsModal").style.display = "none";
};

window.onclick = function(event) {
    if (event.target == document.getElementById("settingsModal")) {
        document.getElementById("settingsModal").style.display = "none";
    }
};

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


let currentFillColor = 'fillColorPrice'; // Default value
// Save settings button functionality
document.getElementById("saveSettings").onclick = function() {

    const selectedColorMapping = document.querySelector('input[name="colorMapping"]:checked').value;
    currentFillColor = selectedColorMapping; 
    let currentLegend = "averageSalePrice"
    if(selectedColorMapping == 0)
    {
        currentFillColor = "fillColorPrice"
        currentLegend = "averageSalePrice"
    }
    else if (selectedColorMapping==1)
    {
        currentFillColor ="fillColorCA5"
        currentLegend = "avgCA_5Y"
    }
    else if (selectedColorMapping==2)
    {
        currentFillColor="fillColorRoi"
        currentLegend = "avg_roi"
    }
    else if (selectedColorMapping== 3)
    {
        currentFillColor ="fillColorAquDemand"
        currentLegend = "aquisitiondemand_2023"
    }
    
    applyGeoJSONLayer(currentLegend); // Reapply the GeoJSON layer with the new fill color

    
    const listOrder = getListOrder();
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
    })
    .catch(error => {
        console.error('Error:', error);
    });
};