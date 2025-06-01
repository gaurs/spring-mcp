package net.gaurs.mcpserver.models;

public record Student(
    String id,
    String name,
    String email,
    Integer age,
    Address address) {

    public Student(String id, Student student) {
        this(id, student.name(), student.email(), student.age(), student.address());
    }
}
