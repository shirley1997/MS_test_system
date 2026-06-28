package com.xueting.thesis;

import org.junit.jupiter.api.Test;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

public class EventAggregatorTest {

    @Test
    void firstEventStartsCounterAtOne() {
        // Create an event object
        Map<String, Integer> state = new HashMap<>();
        Map<String, Object> event = Map.of("id", "evt_001", "type", "user.signup");

        EventAggregator.AggregationResult result =
            EventAggregator.aggregate(state, event);

        // The counter for this type should be 1
        assertEquals(1, result.state().get("user.signup"));
        // The processed event should have a field called "processed_by_java"
        assertEquals(true, result.event().get("processed_by_java"));
        // The original id should be preserved
        assertEquals("evt_001", result.event().get("id"));
    }

    @Test
    void secondEventOfSameType() {
        // Start with a state that already saw user.signup once (counter = 1)
        Map<String, Integer> state = new HashMap<>();
        state.put("user.signup", 1);

        Map<String, Object> event = Map.of("id", "evt_002", "type", "user.signup");
        EventAggregator.AggregationResult result =
            EventAggregator.aggregate(state, event);

        // Count should be 2 now 
        assertEquals(2, result.state().get("user.signup"));
    }

    @Test
    void differentTypeOfEvents() {
        Map<String, Integer> state = new HashMap<>();
        state.put("user.signup", 2);

        Map<String, Object> event = Map.of("id", "evt_123", "type", "user.login");
        EventAggregator.AggregationResult result =
            EventAggregator.aggregate(state, event);

        // The new type "user.login" starts with 1.
        assertEquals(1, result.state().get("user.login"));
        // The type "user.signup" doesn't increase
        assertEquals(2, result.state().get("user.signup"));
    }



    @Test
    void rejectsEventWithoutType() {
        Map<String, Integer> state = new HashMap<>();
        Map<String, Object> event = Map.of("id", "evt_044");  // Create an event with no "type"

        // Expect to produce error
        assertThrows(IllegalArgumentException.class,
            () -> EventAggregator.aggregate(state, event));
    }

    @Test
    void rejectsNullInput() {
        assertThrows(IllegalArgumentException.class,
            () -> EventAggregator.aggregate(null, Map.of("type", "x")));
        assertThrows(IllegalArgumentException.class,
            () -> EventAggregator.aggregate(new HashMap<>(), null));
    }
}