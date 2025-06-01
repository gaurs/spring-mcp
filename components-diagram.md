graph TD
    %% Main Components
    User[User/Developer]
    LMStudio[LM Studio\nPort: 1234\nModel: qwen/qwen2.5-vl-7b]
    PythonChatbot[Python Chatbot\n/bot/chatbot.py]
    SpringBootServer[Spring Boot Server\nPort: 8081]
    
    %% Spring Boot Server Components
    subgraph SpringBootComponents[Spring Boot Components]
        McpServerApp[McpServerApplication]
        StudentTools[StudentTools Service]
        StudentDetailsService[StudentDetailsService]
        Models[Data Models\nStudent, Address, Response]
        OpenApiConfig[OpenAPI Configuration]
        MCPProtocol[MCP Protocol Handler]
    end
    
    %% Python Chatbot Components
    subgraph ChatbotComponents[Python Chatbot Components]
        MCPClient[MCP Client]
        LMStudioClient[LM Studio Client]
        OutputFormatter[Output Formatter]
        InteractiveMode[Interactive Mode]
        StdioMode[Stdio Mode]
    end
    
    %% Interactions
    User -->|Interacts with| PythonChatbot
    PythonChatbot -->|Sends prompts to| LMStudio
    LMStudio -->|Returns completions| PythonChatbot
    PythonChatbot -->|Calls tools via MCP| SpringBootServer
    SpringBootServer -->|Returns tool results| PythonChatbot
    
    %% Internal Spring Boot Interactions
    McpServerApp -->|Configures| MCPProtocol
    McpServerApp -->|Registers| StudentTools
    StudentTools -->|Uses| StudentDetailsService
    StudentDetailsService -->|Uses| Models
    OpenApiConfig -->|Documents| SpringBootServer
    
    %% Internal Chatbot Interactions
    PythonChatbot -->|Uses| MCPClient
    PythonChatbot -->|Uses| LMStudioClient
    PythonChatbot -->|Uses| OutputFormatter
    PythonChatbot -->|Runs in| InteractiveMode
    PythonChatbot -->|Runs in| StdioMode
    
    %% Data Flow
    User -->|"1. Enters query"| PythonChatbot
    PythonChatbot -->|"2. Sends query"| LMStudio
    LMStudio -->|"3. Returns response\n(possibly with tool calls)"| PythonChatbot
    PythonChatbot -->|"4. If tool call needed,\nsends MCP request"| SpringBootServer
    SpringBootServer -->|"5. Executes tool\nand returns result"| PythonChatbot
    PythonChatbot -->|"6. Sends tool result"| LMStudio
    LMStudio -->|"7. Generates final response"| PythonChatbot
    PythonChatbot -->|"8. Shows response"| User
    
    %% Styling
    classDef springComponent fill:#b3e0ff,stroke:#0066cc,stroke-width:2px
    classDef pythonComponent fill:#ffcccc,stroke:#cc0000,stroke-width:2px
    classDef externalSystem fill:#d9f2d9,stroke:#006600,stroke-width:2px
    classDef user fill:#ffeb99,stroke:#cc9900,stroke-width:2px
    
    class SpringBootServer,SpringBootComponents,McpServerApp,StudentTools,StudentDetailsService,Models,OpenApiConfig,MCPProtocol springComponent
    class PythonChatbot,ChatbotComponents,MCPClient,LMStudioClient,OutputFormatter,InteractiveMode,StdioMode pythonComponent
    class LMStudio externalSystem
    class User user