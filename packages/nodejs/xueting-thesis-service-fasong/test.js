// Import Node.js built-in HTTP module. use it to create test cases
const http = require('node:http');

// Import the function that need to be tested
const { forwardEvent } = require('./index.js');

// Start a mock server on a random free port
// The handler defines how the mock server should respond
function startMockServer(handler) {
  return new Promise((resolve) => {
    // Create a simple HTTP server
    const server = http.createServer((req, res) => {
      
      let body = '';

      // Collect incoming request data
      req.on('data', (chunk) => (body += chunk));

      // When the full request body is received, call the test handler
      req.on('end', () => handler(req, res, body));
    });

    // Listen on port 0 : choose any currently free port automatically
    server.listen(0, '127.0.0.1', () => {
      // Get the real port chosen by the system.
      const { port } = server.address();

      resolve({ server, url: `http://127.0.0.1:${port}/` });
    });
  });
}

// Main async test runner
async function run() {
  // Count passed and failed test cases
  let passed = 0;
  let failed = 0;

  // Case 1: test successful forwarding case
  {
    // Start a mock server that returns a successful JSON response.
    const { server, url } = await startMockServer((req, res, body) => {
      // Parse the event sent by forwardEvent
      const received = JSON.parse(body);

      // Return HTTP 200 with JSON content
      res.writeHead(200, { 'Content-Type': 'application/json' });

      // Echo the received event back to the caller.
      res.end(JSON.stringify({ echoed: received, processed_by_mock: true }));
    });

    try {
      // Call forwardEvent with a valid event
      const result = await forwardEvent(url, { id: 'evt_001', type: 'test' });

      // Check whether the mock server response is correct
      const ok =
        result.processed_by_mock === true &&
        result.echoed.id === 'evt_001';

      // Print test result
      console.log(`${ok ? 'PASS' : 'FAIL'}  successful forward  → ${JSON.stringify(result)}`);

      // Update counters
      ok ? passed++ : failed++;
    } catch (err) {
      console.log(`FAIL  successful forward  → threw: ${err.message}`);
      failed++;
    }

    // Stop the mock server after this test case
    server.close();
  }

  // Case 2: test when the service returns HTTP 500
  {
    // Start a mock server that always returns 500
    const { server, url } = await startMockServer((req, res) => {
      res.writeHead(500);
      res.end('boom');
    });

    try {
      // This should throw an error because response is not OK.
      await forwardEvent(url, { id: 'evt_002', type: 'test' });

      // If no error is thrown, the test failed
      console.log('FAIL  500 response  → did not throw');
      failed++;
    } catch (err) {
      // Check whether the error message contains the 500 status code.
      const ok = err.message.includes('500');

      // Print test result and update counters
      console.log(`${ok ? 'PASS' : 'FAIL'}  500 response  → threw: ${err.message}`);
      ok ? passed++ : failed++;
    }
  
    server.close();
  }

  // Case 3: test invalid target service URL
  {
    try {
      // Empty URL should produce error
      await forwardEvent('', { id: 'x', type: 'y' });

      console.log('FAIL  empty url  → did not throw');
      failed++;
    } catch (err) {
      // Error is expected here
      console.log(`PASS  empty url  → threw: ${err.message}`);
      passed++;
    }
  }

  // Case 4: test invalid event object
  {
    try {
      // null event should produce error
      await forwardEvent('http://127.0.0.1:1/', null);

      // If no error is thrown, the test failed
      console.log('FAIL  null event  → did not throw');
      failed++;
    } catch (err) {
      // Error is expected here
      console.log(`PASS  null event  → threw: ${err.message}`);
      passed++;
    }
  }

  // Print final test results
  console.log(`\n${passed} passed, ${failed} failed`);

  // Exit with 0 if all tests passed, exit with 1 if any test failed
  process.exit(failed === 0 ? 0 : 1);
}

// Start running all tests
run();