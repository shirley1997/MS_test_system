# When use "import xueting_thesis_service_zhuanfa", python runs this file
# has one function: forward_event(target_url, event)


import requests  # Must use dependency

# Use POST to send an event to the next service (java service)
def forward_event(target_url, event):
  
    # Validate input
    if not isinstance(target_url, str) or target_url.strip() == "":
        raise ValueError("target_url must be a non-empty string")
    if not isinstance(event, dict):
        raise ValueError("event must be a dict")

    # Send the POST request. (with timeout)
    # json=event can automatically serializes the dict to JSON and sets Content-Type: application/json
    
    response = requests.post(target_url, json=event, timeout=10)

    response.raise_for_status()

    # Return the response
    return response.json()