document.addEventListener("DOMContentLoaded", function() {
    const Contactmodal = document.getElementById("contactModal");
    const btnSendMessage = document.getElementById("contactUsButton");
    const formContact = document.getElementById("contactForm");
  
    btnSendMessage.onclick = function() {
      Contactmodal.style.display = "block";
    }
  
    formContact.onsubmit = function(e) {
      e.preventDefault();
      const message = document.getElementById("message").value;
      
      if (!message) {
        alert("Please enter a message.");
        return;
      }

      if (message.length > 2000) {
        alert("Message is too long. Please keep it under 2000 characters.");
        return;
      }
      const csrfToken = document.querySelector('input[name="csrf_token"]').value;
      fetch('/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({message: message}),
      })
      .then(response => response.json())
      .then(data => {
        alert(data.message);
        Contactmodal.style.display = "none";
        formContact.reset();
      })
      .catch((error) => {
        console.error('Error:', error);
        alert("An error occurred while sending your message. Please try again.");
      });
    }
  });