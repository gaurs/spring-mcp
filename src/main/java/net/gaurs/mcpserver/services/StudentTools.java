package net.gaurs.mcpserver.services;

import net.gaurs.mcpserver.models.Response;
import net.gaurs.mcpserver.models.Student;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.stereotype.Service;

@Service
public class StudentTools {

    private final StudentDetailsService studentDetailsService;
    private final Logger logger = LoggerFactory.getLogger(getClass());

    public StudentTools(StudentDetailsService studentDetailsService) {
        this.studentDetailsService = studentDetailsService;
    }

    @Tool(name = "LIST_ALL_STUDENT_RECORDS", description = "return a list of all the student records available in application")
    public Response listAllStudents() {
        logger.info("Listing all students");
        var students = studentDetailsService.getAllStudents();

        if(students.isEmpty()){
            return new Response(false, "No students found", null);
        }

        return new Response(true, "List of all students", students);
    }

    @Tool(name = "ADD_STUDENT_RECORD", description = "add a new student record in the system")
    public Response addStudent(Student student){
        logger.info("Adding a new student {}", student);
        var newStudent =  studentDetailsService.add(student);

        if(null == newStudent){
            return new Response(false, "failed to add student record", null);
        }

        return new Response(true, "Student record added successfully", newStudent);
    }

    @Tool(name = "DELETE_STUDENT_RECORD", description = "delete a student record from the system")
    public Response deleteStudent(String id){
        logger.info("Deleting student by id {}", id);
        var deletedRecord = studentDetailsService.deleteStudentById(id);

        if(null == deletedRecord){
            return new Response(false, "failed to delete student record", null);
        }

        return new Response(true, "Student record deleted successfully", deletedRecord);
    }

    @Tool(name = "GET_STUDENT_RECORD", description = "get a student record from the system by unique id identifier")
    public Response getStudent(String id){
        logger.info("Getting student by id {}", id);
        var student = studentDetailsService.getStudentById(id);

        if(null == student){
            return new Response(false, "failed to get student record", null);
        }

        return new Response(true, "Student record retrieved successfully", student);
    }

}
