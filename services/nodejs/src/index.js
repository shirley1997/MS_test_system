// HTTP API service: receives events and forwards them to the Python data processing service
// Part of the master thesis test environment 


// Import express package (public) and two internal packages
const express = require('express');
const { validateEvent } = require('xueting-thesis-event-jianding');
const { forwardEvent } = require('xueting-thesis-service-fasong');


const app = express();
const PORT = 3000;     // The node.js service runs on port 3000
const PYTHON_SERVICE_URL = 'http://localhost:5000/process';

// Parse incoming JSON request bodies
app.use(express.json());

// Health check endpoint, used to test whether the service is running. dev gets clear feedback
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'receive-event-http-api' });
});

// Main endpoint, receives an event and forwards it to the Python service
// Client sends POST requests to /events
app.post('/events', async (req, res) => {
  // 1. Validate event using the internal package "xueting-thesis-event-jianding"
  const validation = validateEvent(req.body);
  if (!validation.valid) {
    return res.status(400).json({
      status: 'invalid',
      errors: validation.errors,
    });
  }

  // 2. Forward event to the python service using the internal package "xueting-thesis-service-fasong"
  try {
    const downstream = await forwardEvent(PYTHON_SERVICE_URL, req.body);

    // Return success response to client. otherwise return code 502
    res.json({
      status: 'forwarded',
      received_by: 'receive-event-http-api',
      downstream,
    });
  } catch (err) {
    res.status(502).json({
      status: 'forward_failed',
      error: err.message,
    });
  }
});


// Start the server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`receive-event-http-api running on http://localhost:${PORT}`);
});