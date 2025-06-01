package net.gaurs.mcpserver.models;

public record Response(Boolean success,
                       String message,
                       Object data) {
}
