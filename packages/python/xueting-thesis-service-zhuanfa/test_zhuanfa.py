# A local test for this package
# Import from the src/ directory


import sys
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from xueting_thesis_service_zhuanfa import forward_event  
import requests  


# let each test configure how the mock server should respond.
def make_handler(status_code, response_body):
    class MockHandler(BaseHTTPRequestHandler):
        
        def log_message(self, *args, **kwargs):
            pass

        def do_POST(self):
            # Read the incoming request body 
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            received = json.loads(body) if body else {}

            
            payload = response_body(received) if callable(response_body) else response_body

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

    return MockHandler

# Start a HTTP server on a random port, return (server, url)
def start_mock_server(status_code, response_body):
    
    # port=0 means OS pick a free port to avoid collisions.
    server = HTTPServer(("127.0.0.1", 0), make_handler(status_code, response_body))
    port = server.server_address[1]
   
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}/"


passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"PASS  {name}")
        passed += 1
    else:
        print(f"FAIL  {name}  → {detail}")
        failed += 1


# Test 1: if successful forward: mock server print the event with a marker.
server, url = start_mock_server(
    200,
    lambda received: {"echoed": received, "processed_by_mock": True},
)
try:
    result = forward_event(url, {"id": "evt_001", "type": "test"})
    check("successful forwarded", result.get("processed_by_mock") is True)
    check("response contains echo?", result["echoed"]["id"] == "evt_001")
except Exception as e:
    check("successful forwarded", False, f"threw: {e}")
server.shutdown()


# Test 2: downstream server returns 500: produce error
server, url = start_mock_server(500, {"error": "boom"})
try:
    forward_event(url, {"id": "evt_002", "type": "test"})
    check("500 response?", False, "did not raise")
except requests.HTTPError:
    check("500 response?", True)
except Exception as e:
    check("500 response?", False, f"wrong exception type: {type(e).__name__}")
server.shutdown()

# Test 3: empty URL, produce ValueError
try:
    forward_event("", {"id": "x", "type": "y"})
    check("empty url?", False, "did not raise")
except ValueError:
    check("empty url?", True)

# Test 4: non-dict event, also produce ValueError.
try:
    forward_event("http://127.0.0.1:1/", "not a dict")
    check("non-dict event?", False, "did not raise")
except ValueError:
    check("non-dict event?", True)


# Print test results 
print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)