package net.gaurs.mcpserver;

import net.gaurs.mcpserver.services.StudentTools;
import org.springframework.ai.support.ToolCallbacks;
import org.springframework.ai.tool.ToolCallback;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.util.List;

@SpringBootApplication
public class McpServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(McpServerApplication.class, args);
    }


    @Bean
    ToolCallbackProvider userTools(StudentTools studentTools) {
        return MethodToolCallbackProvider
                .builder()
                .toolObjects(studentTools)
                .build();
    }

    @Bean
    public List<ToolCallback> weatherTools(StudentTools service) {
        return List.of(ToolCallbacks.from(service));
    }

}
