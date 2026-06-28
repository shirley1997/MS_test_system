# A local test for this package
# Import from the src/ directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from xueting_thesis_event_fengfu import enrich_event

# Count the passed, failed test cases
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


# Test 1: timestamp field and python process field are added to a normal event
event = {"id": "evt_001", "type": "user.signup"}
result = enrich_event(event)
check("adds timestamp", "timestamp" in result)
check("adds processed_by_python marker", result.get("processed_by_python") is True)
check("preserves original event id?", result["id"] == "evt_001")
check("preserves original event type?", result["type"] == "user.signup")


# Test 2: if the event is not dict object -> produce error
try:
    enrich_event("not a dict")
    check("rejects non-dict", False, "did not raise")
except TypeError:
    check("rejects non-dict", True)

# print test result
print(f"\n{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)