document.getElementById("unlock-button-table").onclick = function() {
    openModal('Unlock all projects Today for $9.99');
};

document.querySelector(".premium-close").onclick = function() {
    console.log("we click on close-button")
    document.getElementById("premiumModal").style.display = "none";
};

window.onclick = function(event) {
    if (event.target == document.getElementById("premiumModal")) {
        document.getElementById("premiumModal").style.display = "none";
    }
};
function openModal(title) {
    const modalTitle = document.querySelector('.modal-title');
    const premiumModal = document.getElementById('premiumModal');
    modalTitle.textContent = title;
    premiumModal.style.display = 'block';
  }
