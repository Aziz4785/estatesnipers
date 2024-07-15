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
      
      fetch('/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
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
      });
    }
  });