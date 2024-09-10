function openModal(title,footnote='') {
    const modalTitle = document.querySelector('.modal-title');
    const premiumModal = document.getElementById('premiumModal');
    modalTitle.innerHTML = title;
    const footnoteElement = document.querySelector('.modal-footnote');

    if (footnote && footnote.trim() !== '') {
        footnoteElement.textContent = footnote;
        footnoteElement.style.display = 'block';
    } else {
        footnoteElement.style.display = 'none';
    }

    premiumModal.style.display = 'block';
  }
