// Internal package xueting-thesis-event-jianding
// This package checks whether the incoming event has required fields for the receive-event-http-api service (node.js service)


// List of fields that every event should contain
const REQUIRED_FIELDS = ['id', 'type'];


// Function to check whether an event is valid, e.g. check whether the event is an object
// The event must not be null and must not be an array
function validateEvent(event) {
  const errors = [];

  if (event === null || typeof event !== 'object' || Array.isArray(event)) {
    return { valid: false, errors: ['Event must be a non-null object'] };
  }

  // Check required field of event
  for (const field of REQUIRED_FIELDS) {
    if (!(field in event)) {
      errors.push(`Missing required field: ${field}`);
      continue;
    }
    if (typeof event[field] !== 'string' || event[field].trim() === '') {
      errors.push(`Field "${field}" must be a non-empty string`);
    }
  }

  return { valid: errors.length === 0, errors };
}

// Export the function and required fields so other files can use them
module.exports = { validateEvent, REQUIRED_FIELDS };