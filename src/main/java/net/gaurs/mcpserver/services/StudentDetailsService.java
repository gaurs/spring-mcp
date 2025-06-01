package net.gaurs.mcpserver.services;

import net.gaurs.mcpserver.models.Student;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class StudentDetailsService {

    private final Map<String, Student> studentRepository = new ConcurrentHashMap<>();
    private final Logger logger = LoggerFactory.getLogger(getClass());

    // 1. Get all students
    public List<Student> getAllStudents() {
        logger.info("Getting all students");
        return List.copyOf(studentRepository.values());
    }

    // 2. Get student by id
    public Student getStudentById(String id){
        logger.info("Getting student by id {}", id);
        return studentRepository.get(id);
    }

    // 3. Create student by id
    public Student add(Student student){
        logger.info("adding a new student {}", student);
        var newRecord = new Student(UUID.randomUUID().toString(), student);
        studentRepository.put(newRecord.id(), newRecord);
        return newRecord;
    }

    // 4. Delete student by id
    public Student deleteStudentById(String id){
        logger.info("Deleting student by id {}", id);
        return studentRepository.remove(id);
    }
}
