package com.xueting.thesis;

import org.junit.jupiter.api.Test;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

public class ResponseGeneratorTest {

    @Test
    void CorrectResponseTest() {
        Map<String, Object> event = Map.of(
            "id", "evt_001",
            "type", "user.signup",
            "processed_by_python", true,
            "processed_by_java", true
        );
        Map<String, Integer> state = Map.of("user.signup", 1);

        Map<String, Object> result = ResponseGenerator.wrap(event, state);

        // Check if the values from specific fields are correct
        assertEquals("aggregated", result.get("status"));
        assertEquals("aggregate-event-http-api", result.get("received_by"));

        // The event and state should be shown in response
        assertNotNull(result.get("final_event"));
        assertNotNull(result.get("aggregation_state"));
    }

    @Test
    void ShowEventField() {
        Map<String, Object> event = Map.of("id", "evt_002", "type", "testtttttt");
        Map<String, Object> result = ResponseGenerator.wrap(event, new HashMap<>());

        @SuppressWarnings("unchecked")
        Map<String, Object> finalEvent = (Map<String, Object>) result.get("final_event");
        assertEquals("evt_002", finalEvent.get("id"));
        assertEquals("testtttttt", finalEvent.get("type"));
    }

    @Test
    void ShowAggregationState() {
        Map<String, Integer> state = Map.of("abc", 3, "bef", 1);
        Map<String, Object> result = ResponseGenerator.wrap(new HashMap<>(), state);

        @SuppressWarnings("unchecked")
        Map<String, Integer> wrappedState =
            (Map<String, Integer>) result.get("aggregation_state");
        assertEquals(3, wrappedState.get("abc"));
        assertEquals(1, wrappedState.get("bef"));
    }

    

    @Test
    void rejectNullInput() {
        assertThrows(IllegalArgumentException.class,
            () -> ResponseGenerator.wrap(null, new HashMap<>()));
        assertThrows(IllegalArgumentException.class,
            () -> ResponseGenerator.wrap(new HashMap<>(), null));
    }
}