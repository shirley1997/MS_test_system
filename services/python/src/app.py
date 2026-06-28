# The Python service (process-event-http-api)
# Receives events from the node.js service, adds extra fields to the event, then sends to the java service 

from flask import Flask, request, jsonify

# Import the internal packages which are published on Nexus

from xueting_thesis_event_fengfu import enrich_event
from xueting_thesis_service_zhuanfa import forward_event


app = Flask(__name__)

JAVA_SERVICE_URL = "http://localhost:8080/aggregate"


# Health check endpoint, used to test whether the service is running. dev gets clear feedback
@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service="process-event-http-api")


# Main endpoint, receives an event from node.js service, add fields to the event and sends to java service
@app.route("/process", methods=["POST"])
def process():
    
    # Parse the incoming JSON body
    event = request.get_json(silent=True)

    if event is None:
        return jsonify(status="invalid", error="request body must be JSON"), 400

    # 1: adds timestamp field and processed_by_python: true field to the event 
    # using the internal package "xueting-thesis-event-fengfu"
    try:
        enriched = enrich_event(event)
    except TypeError as e:
        # enrich_event raises TypeError for non-dict input.
        return jsonify(status="invalid", error=str(e)), 400


    # 2: send the processed event to the java service 
    # using the internal package "xueting-thesis-service-zhuanfa"
    try:
        downstream = forward_event(JAVA_SERVICE_URL, enriched)
        return jsonify(
            status="forwarded",
            received_by="process-event-http-api",
            sent_to_java=enriched,
            downstream=downstream,
        )
    except Exception as e:
        return jsonify(
            status="forward_failed",
            received_by="process-event-http-api",
            sent_to_java=enriched,  
            error=str(e),
        ), 502


# Start the server 
if __name__ == "__main__":
    # 0.0.0.0 = listen on all network interfaces 
    app.run(host="0.0.0.0", port=5000, debug=False)