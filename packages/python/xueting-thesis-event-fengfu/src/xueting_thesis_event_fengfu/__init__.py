# This file is the package
# When use "import xueting_thesis_event_fengfu", python runs this file

from datetime import datetime, timezone


def enrich_event(event):
    """
    Add extra fields to an event. This event is validated by service that it is a JSON
    in this method enrich_event(), the event must be a dict so it can be used to add extra field

    Takes the event like {"id": "evt_001", "type": "user.signup"}
    Returns the same dict but add two new fields:
      - timestamp: current UTC time
      - processed_by_python: True (proves that this event went through python service)
    """
    # Check if it is a dict 
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")

    enriched = dict(event)

    # Add UTC timestamp and python process field for the event
    enriched["timestamp"] = datetime.now(timezone.utc).isoformat()
    enriched["processed_by_python"] = True

    return enriched