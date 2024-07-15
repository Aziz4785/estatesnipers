document.getElementById("unlock-button-table").onclick = function() {
    openModal('Unlock all projects Today for $19.99');
};

function openModal(title) {
    const modalTitle = document.querySelector('.modal-title');
    const premiumModal = document.getElementById('premiumModal');
    modalTitle.textContent = title;
    premiumModal.style.display = 'block';
  }
