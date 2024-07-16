document.addEventListener('DOMContentLoaded', function() {
    // Function to close a modal
    function closeModal(modal) {
        modal.style.display = "none";
    }

    // Get all modals and close buttons
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-button');

    // Attach event listeners to each close button
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });

    // Optional: Close the modal if the user clicks outside of the modal content
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });


    document.getElementById("unlock-button-table").onclick = function() {
        openModal('Unlock all projects Today for $19.99');
    };
});
