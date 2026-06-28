
// Import the validateEvent function from index.js
const { validateEvent } = require('./index.js');


// Define test cases. Each case has a name, an input event and the expected validation result.
const cases = [
  {
    name: 'valid event',
    input: { id: 'evt_001', type: 'user.signup' },
    expectValid: true,
  },
  {
    name: 'missing type',
    input: { id: 'evt_002' },
    expectValid: false,
  },
  {
    name: 'empty id',
    input: { id: '', type: 'user.signup' },
    expectValid: false,
  },
  {
    name: 'not an object',
    input: 'this is a fake event',
    expectValid: false,
  },
];


// Counters for test results
let passed = 0;
let failed = 0;


// Run all test cases
for (const c of cases) {
  const result = validateEvent(c.input);
  const ok = result.valid === c.expectValid;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${c.name}  → ${JSON.stringify(result)}`);  // Print PASS or FAIL with the test name and validation result
  ok ? passed++ : failed++;
}


// Print final test result
console.log(`\n${passed} passed, ${failed} failed`);

// Exit with code 0 if all tests passed. Exit with code 1 if at least one test failed.
process.exit(failed === 0 ? 0 : 1);