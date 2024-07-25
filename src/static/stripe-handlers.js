 function initializeStripe() {
    return fetch("/config")
        .then((result) => result.json())
        .then((data) => {
            return Stripe(data.publicKey);
        });
}


 async function setupPremiumButton(buttonId, stripe) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.addEventListener('click', async function(event) {
            event.preventDefault();
            await handleStripeCheckout(stripe);
        });
    }
}

// Function to handle Stripe checkout
 async function handleStripeCheckout(stripe) {
    try {
        const sessionResponse = await fetch("/create-checkout-session");
        const sessionData = await sessionResponse.json();
        
        if (sessionData.error) {
            console.error('Error:', sessionData.error);
            return;
        }
        
        const result = await stripe.redirectToCheckout({ sessionId: sessionData.sessionId });
        
        if (result.error) {
            console.error(result.error.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}