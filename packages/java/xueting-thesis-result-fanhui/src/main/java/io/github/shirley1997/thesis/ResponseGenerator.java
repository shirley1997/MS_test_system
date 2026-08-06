// This internal package combines the processed event + counter state + additional metadata + in one response 


package io.github.shirley1997.thesis;

import java.util.HashMap;
import java.util.Map;

public class ResponseGenerator {

    /**
     * Create the final response which should be sent to python service
     *
     * Example output:
     *   {
     *     "status": "aggregated",
     *     "received_by": "aggregate-event-http-api",
     *     "final_event": { ...},
     *     "aggregation_state": { event_type -> count, ... }
     *   }
     *
     * @param finalEvent       the processed event by java service
     * @param aggregationState the counter state of event types (e.g. "user.login" -> 2), a java map object
     * @return a java map project. later in java service, this map object will be serialized to the HTTP response JSON using jackson-databind
     */
    public static Map<String, Object> wrap(
            Map<String, Object> finalEvent,
            Map<String, Integer> aggregationState) {

        // validation: check the input event and counter state are not NULL, otherwise throw exception
        if (finalEvent == null) {
            throw new IllegalArgumentException("finalEvent should not be null");
        }
        if (aggregationState == null) {
            throw new IllegalArgumentException("aggregationState should not be null");
        }

        
        // create response (a java map object), put final event and aggregated counter state inside
        // together with "status" and "received_by" fields (additional metadata)
        Map<String, Object> response = new HashMap<>();
        response.put("status", "aggregated");
        response.put("received_by", "aggregate-event-http-api");

        // event and state copies are created -> only modified the copied version, not the original objects.
        response.put("final_event", new HashMap<>(finalEvent));
        response.put("aggregation_state", new HashMap<>(aggregationState));


        // return response (a java map object)
        return response;
    }
}