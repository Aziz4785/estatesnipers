function openModal(title) {
    const modalTitle = document.querySelector('.modal-title');
    const premiumModal = document.getElementById('premiumModal');
    modalTitle.textContent = title;
    premiumModal.style.display = 'block';
  }
