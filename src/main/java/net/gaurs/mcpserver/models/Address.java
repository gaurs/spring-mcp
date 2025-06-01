package net.gaurs.mcpserver.models;

public record Address(
    Integer pincode,
    String city,
    String state
) {
}
