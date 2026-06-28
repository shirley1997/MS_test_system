// Internal package xueting-thesis-service-fasong
// This package sends an event to the next service (python service) through HTTP POST.

// Async function to send an event to another service
async function forwardEvent(targetUrl, event) {
  if (typeof targetUrl !== 'string' || targetUrl.trim() === '') {
    throw new Error('targetUrl must be a non-empty string');
  }
  if (event === null || typeof event !== 'object') {
    throw new Error('event must be an object');
  }


  // Send the event to the next service with HTTP POST
  const response = await fetch(targetUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  });


  // Check whether the HTTP response status is successful
  if (!response.ok) {
    throw new Error(
      `Forward failed: ${response.status} ${response.statusText}`
    );
  }

  // Parse and return the JSON response from the target service (python service)
  return await response.json();
}

// Export the function so other files can use it.
module.exports = { forwardEvent };