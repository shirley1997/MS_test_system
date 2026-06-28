// The internal package for the java service: event aggregator
// Function: it takes the current state + event, returns new state.
// State stores in the service, not in this package.

package com.xueting.thesis;

import java.util.HashMap;
import java.util.Map;

public class EventAggregator {

    /**
     * Aggregate one event into the counter state.
     *
     *   1. Validate input (event must contain "type")
     *   2. Add field "processed_by_java: true" for the event
     *   3. counter + 1 for this event type
     *
     * @param currentState the counter (event_type -> count).
     *                     create an empty map for the first event
     * @param event        the event object, must contain a non-empty "type" field
     * @return AggregationResult with the updated event and updated counter state
     */
    public static AggregationResult aggregate(
            Map<String, Integer> currentState,
            Map<String, Object> event) {

        if (currentState == null) {
            throw new IllegalArgumentException("currentState should not be null");
        }
        if (event == null) {
            throw new IllegalArgumentException("event should not be null");
        }

        // Event must have a "type" field, which is a non-empty string, otherwise produce error
        Object typeObj = event.get("type");
        if (!(typeObj instanceof String) || ((String) typeObj).isEmpty()) {
            throw new IllegalArgumentException(
                "event must contain a non-empty 'type' string"
            );
        }
        String type = (String) typeObj;

        
        Map<String, Object> updatedEvent = new HashMap<>(event);
        // Add extra field to the event, prove that the event is processed by java service
        updatedEvent.put("processed_by_java", true);

        // increase the count to 1 for this event type
        // getOrDefault returns 0 if a type hasn't been seen before
        Map<String, Integer> updatedState = new HashMap<>(currentState);
        updatedState.put(type, updatedState.getOrDefault(type, 0) + 1);


        return new AggregationResult(updatedEvent, updatedState);
    }

    
    public record AggregationResult(
        Map<String, Object> event,
        Map<String, Integer> state
    ) {}
}