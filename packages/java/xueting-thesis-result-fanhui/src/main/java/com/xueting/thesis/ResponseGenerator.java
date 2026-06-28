// This internal package combines the processed event + counter state in one response


package com.xueting.thesis;

import java.util.HashMap;
import java.util.Map;

public class ResponseGenerator {

    /**
     * Build the final response 
     *
     * Example output:
     *   {
     *     "status": "aggregated",
     *     "received_by": "aggregate-event-http-api",
     *     "final_event": { ...},
     *     "aggregation_state": { event_type -> count, ... }
     *   }
     *
     * @param finalEvent       the processed event 
     * @param aggregationState the count of event types
     * @return a map, which will be serialized as the HTTP response JSON
     */
    public static Map<String, Object> wrap(
            Map<String, Object> finalEvent,
            Map<String, Integer> aggregationState) {

        
        if (finalEvent == null) {
            throw new IllegalArgumentException("finalEvent should not be null");
        }
        if (aggregationState == null) {
            throw new IllegalArgumentException("aggregationState should not be null");
        }

        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "aggregated");
        response.put("received_by", "aggregate-event-http-api");

        
        response.put("final_event", new HashMap<>(finalEvent));
        response.put("aggregation_state", new HashMap<>(aggregationState));

        return response;
    }
}