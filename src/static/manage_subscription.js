import { handleStripeCheckout } from './stripe-handlers.js';

document.addEventListener('DOMContentLoaded', function () {
        document.getElementById('subscribeBtn').addEventListener('click', async function(event) {
        event.preventDefault();
        console.log("we click on subscribeBtn")
        try {
            const authResponse = await fetch('/check-auth');
            const authData = await authResponse.json();
            
            if (authData.isAuthenticated) {
                // User is logged in, proceed to Stripe checkout
                await handleStripeCheckout(stripe);
            } else {
                // User is not logged in, show login modal
                document.getElementById("premiumModal").style.display = 'none';
                openLoginModal("Login to Subscribe", "login");
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
    });