
document.getElementById("settingsBtn").onclick = function() {
    document.getElementById("settingsModal").style.display = "block";
    retrieveListOrder();
};

// Function to retrieve and display the saved list order
function retrieveListOrder() {
    console.log("retrieveListOrder")
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
    console.log("rearrangeList : ",order)
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
    console.log("updateUIWithListOrder")
    const hierarchyList = document.getElementById("hierarchyList");
    hierarchyList.innerHTML = '';
    console.log("listOrder : ")
    console.log(listOrder)
    listOrder.forEach(item => {
        console.log("item : ",item)
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


let currentFillColor = 'fillColorPrice'; // Default value
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
        if (currentAreaId) {
            fetchAreaDetails(currentAreaId);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
};