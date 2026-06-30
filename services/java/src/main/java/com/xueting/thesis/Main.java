package com.xueting.thesis;

import com.xueting.thesis.EventAggregator;
import com.xueting.thesis.EventAggregator.AggregationResult;
import com.xueting.thesis.ResponseGenerator;

import io.javalin.Javalin;

import java.util.HashMap;
import java.util.Map;

public class Main {

    // counter: event type -> how many times we have seen it
    // The counter will be reset when the service restarts (so it will not record the event type forever)
    private static final Map<String, Integer> counterState = new HashMap<>();

    public static void main(String[] args) {
        // Start javalin web server on port 8080 (start java service)
        // In javalin 7, all routes must be registered inside config block (different grammar as javalin 6)
        Javalin.create(config -> {

            // Endpoint /health  -> check if the service is working
            config.routes.get("/health", ctx -> ctx.result("java service is running"));

            // Endpoint /aggregate  -> help aggregate the event
            config.routes.post("/aggregate", ctx -> {
                // Parse the incoming JSON event sent by the Python service
                // Expected fields: id, type, timestamp, processed_by_python
                @SuppressWarnings("unchecked")
                Map<String, Object> event = ctx.bodyAsClass(Map.class);

                // Use aggregation function from the internal package xueting-thesis-event-juhe
                AggregationResult result = EventAggregator.aggregate(counterState, event);

                // Save the updated counter state to this service.
                counterState.clear();
                counterState.putAll(result.state());

                // Put the final event and counter state in response of java
                // Then the event contains fields: status, received_by, final_event, aggregation_state
                Map<String, Object> response = ResponseGenerator.wrap(result.event(), result.state());

                // Send the response back to python service
                ctx.json(response);
            });

        }).start(8080);
    }
}