// The internal package for the java service: event aggregator
// Function: it takes the current state + event, returns new counter state and updated event.
// the counter state is a java hashmap object, it is stored inside java service's memory, not inside this package
// everytime the java service restarts, a new empty `HashMap` is created for counter state. (in java service code, not here)
// Therefore, all previous counter values are lost.

package io.github.shirley1997.thesis;

import java.util.HashMap;
import java.util.Map;

public class EventAggregator {

    /**
     * Aggregate one event into the counter state.
     *
     *   1. Validate input (event must contain "type")
     *   2. Add field "processed_by_java: true" for the event
     *   3. retrive the event type from event, then counter + 1 for this event type
     *
     * @param currentState the counter (event_type -> count).
     *                     create an empty java map object for the first event
     * @param event        a event object, must contain a non-empty "type" field
     * @return AggregationResult with the updated event and updated counter state
     */
    public static AggregationResult aggregate(
            Map<String, Integer> currentState,
            Map<String, Object> event) {
        // These checks prevent from working with a missing counter and a missing event
        if (currentState == null) {
            throw new IllegalArgumentException("currentState should not be null");
        }
        if (event == null) {
            throw new IllegalArgumentException("event should not be null");
        }

        // If event is not null, event must have a "type" field, which is a non-empty string, otherwise produce error
        Object typeObj = event.get("type");
        if (!(typeObj instanceof String) || ((String) typeObj).isEmpty()) {
            throw new IllegalArgumentException(
                "event must contain a non-empty 'type' string"
            );
        }

        // retrieve the type in an event to a string variable "type"
        String type = (String) typeObj;

        // copy the map object "event" to another map object "updated event", so only the "updated event" will be modified
        Map<String, Object> updatedEvent = new HashMap<>(event);
        // Add extra field to the updated event using put(). This field proves that the event is processed by java service
        updatedEvent.put("processed_by_java", true);

        // the original counter state is also copied to updatedState.
        // increase the count to 1 for this event type
        // getOrDefault returns 0 (default value) if a type hasn't been seen before
        Map<String, Integer> updatedState = new HashMap<>(currentState);
        updatedState.put(type, updatedState.getOrDefault(type, 0) + 1);


        // return two value, that's why a record object is needed here
        return new AggregationResult(updatedEvent, updatedState);
    }

    
    public record AggregationResult(
        Map<String, Object> event,
        Map<String, Integer> state
    ) {}
}