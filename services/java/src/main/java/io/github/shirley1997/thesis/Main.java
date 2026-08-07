package io.github.shirley1997.thesis;

import io.github.shirley1997.thesis.EventAggregator;
import io.github.shirley1997.thesis.EventAggregator.AggregationResult;
import io.github.shirley1997.thesis.ResponseGenerator;

import io.javalin.Javalin;

import java.util.HashMap;
import java.util.Map;

public class Main {

    // counterState: a java map object, has key-value pairs inside. (event type -> count of this type)
    // Example: "user.login" -> 2
    // The counterState will be reset when the service restarts (so it will not record the event type forever)
    private static final Map<String, Integer> counterState = new HashMap<>();

    public static void main(String[] args) {
        // Start javalin web server on port 8080 (start java service) + define two route (endpoints): /health, /aggregate
        // In javalin 7, all routes must be registered inside config block (different grammar as javalin 6)
        Javalin.create(config -> {

            // Endpoint /health  -> check if the service is working
            // just like node.js service and python service, it will return a json including fields status and service name
            config.routes.get("/health", ctx -> ctx.json(Map.of(
                "status", "ok",
                "service", "aggregate-event-http-api"
            )));

            // Endpoint /aggregate  -> responsible for aggregating the event and return the aggregate results
            // use the functionality of the two java internal package: EventAggregator, ResponseGenerator
            config.routes.post("/aggregate", ctx -> {
                // use the context (ctx) of javalin to access the request body
                // Then convert the incoming JSON event sent by the Python service to a java map object 
                // Then put into a empty map object "event" 
                // Expected fields of event: id, type, timestamp, processed_by_python
                 @SuppressWarnings("unchecked")
                 Map<String, Object> event = ctx.bodyAsClass(Map.class);
                

                // Use aggregation function from the internal package xueting-thesis-event-juhe
                // returns a record object contaning updated counter state and processed event
                // java function usually returns one thing, for returning two things a record must be created
                AggregationResult result = EventAggregator.aggregate(counterState, event);

                // The java service first clears the current counterstate
                // then copy the updated counter state to the counterState in this service. 
                // the counter state is not saved in the internal package, but in this service
                counterState.clear();
                counterState.putAll(result.state());

                // Put the updated event and counter state as parts in response of java
                // the response is still a java map object, but will be convert to JSON using ctx (context) of jackson-databind
                // the response contains fields: status, received_by, final_event, aggregation_state
                Map<String, Object> response = ResponseGenerator.wrap(result.event(), result.state());

                // jackson converts the response (a java map object) back to JSON, send the response back to python service
                ctx.json(response);
            });

        }).start(8080);
    }
}