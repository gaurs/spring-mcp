#!/usr/bin/env python3
"""
MCP Chatbot with LM Studio Integration
A chatbot that bridges LM Studio LLM with MCP servers via stdio/stdin
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_chatbot.log'),
        logging.StreamHandler(sys.stderr)  # Log to stderr to avoid interfering with stdio
    ]
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Regular colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

# Icons for different types of messages
class Icons:
    USER = "👤"
    ASSISTANT = "🤖"
    TOOL = "🔧"
    SUCCESS = "✅"
    ERROR = "❌"
    INFO = "ℹ️"
    LOADING = "⏳"
    CONNECTED = "🔗"
    DISCONNECTED = "🔌"

class OutputFormatter:
    """Handles formatting of output messages"""

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors

    def colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if not self.use_colors:
            return text
        return f"{color}{text}{Colors.RESET}"

    def format_user_prompt(self, message: str) -> str:
        """Format user input prompt"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prompt = f"{Icons.USER} {self.colorize('You', Colors.BRIGHT_CYAN)} {self.colorize(f'[{timestamp}]', Colors.DIM)}: "
        return prompt

    def format_assistant_prompt(self) -> str:
        """Format assistant response prompt"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prompt = f"{Icons.ASSISTANT} {self.colorize('Assistant', Colors.BRIGHT_GREEN)} {self.colorize(f'[{timestamp}]', Colors.DIM)}: "
        return prompt

    def format_tool_call(self, tool_name: str, arguments: Dict) -> str:
        """Format tool call information"""
        return (f"{Icons.TOOL} {self.colorize('Tool Call', Colors.YELLOW)}: "
                f"{self.colorize(tool_name, Colors.BRIGHT_YELLOW)}\n"
                f"   {self.colorize('Arguments:', Colors.DIM)} {self.format_json(arguments, indent=2, prefix='   ')}")

    def format_tool_result(self, tool_name: str, result: Dict) -> str:
        """Format tool result information"""
        success = "error" not in result or not result.get("error")
        icon = Icons.SUCCESS if success else Icons.ERROR
        status_color = Colors.BRIGHT_GREEN if success else Colors.BRIGHT_RED

        return (f"{icon} {self.colorize('Tool Result', status_color)}: "
                f"{self.colorize(tool_name, Colors.BRIGHT_YELLOW)}\n"
                f"   {self.format_json(result, indent=2, prefix='   ')}")

    def format_json(self, data: Any, indent: int = 2, prefix: str = "") -> str:
        """Format JSON data with colors and proper indentation"""
        if not isinstance(data, (dict, list)):
            return str(data)

        json_str = json.dumps(data, indent=indent, ensure_ascii=False)
        lines = json_str.split('\n')

        formatted_lines = []
        for line in lines:
            if line.strip():
                # Color JSON syntax
                colored_line = line
                if self.use_colors:
                    # Color strings (values in quotes)
                    import re
                    colored_line = re.sub(r'"([^"]*)":', f'"{Colors.BRIGHT_BLUE}\\1{Colors.RESET}":', colored_line)
                    colored_line = re.sub(r': "([^"]*)"', f': "{Colors.BRIGHT_WHITE}\\1{Colors.RESET}"', colored_line)
                    # Color numbers
                    colored_line = re.sub(r': (\d+)', f': {Colors.BRIGHT_MAGENTA}\\1{Colors.RESET}', colored_line)
                    # Color booleans
                    colored_line = re.sub(r': (true|false)', f': {Colors.BRIGHT_CYAN}\\1{Colors.RESET}', colored_line)

                formatted_lines.append(prefix + colored_line)
            else:
                formatted_lines.append("")

        return '\n'.join(formatted_lines)

    def format_status_message(self, message: str, status: str = "info") -> str:
        """Format status messages"""
        icons = {
            "info": Icons.INFO,
            "success": Icons.SUCCESS,
            "error": Icons.ERROR,
            "loading": Icons.LOADING,
            "connected": Icons.CONNECTED,
            "disconnected": Icons.DISCONNECTED
        }

        colors = {
            "info": Colors.BRIGHT_BLUE,
            "success": Colors.BRIGHT_GREEN,
            "error": Colors.BRIGHT_RED,
            "loading": Colors.BRIGHT_YELLOW,
            "connected": Colors.BRIGHT_GREEN,
            "disconnected": Colors.BRIGHT_RED
        }

        icon = icons.get(status, Icons.INFO)
        color = colors.get(status, Colors.WHITE)

        return f"{icon} {self.colorize(message, color)}"

    def format_separator(self, char: str = "─", length: int = 60) -> str:
        """Format a separator line"""
        return self.colorize(char * length, Colors.DIM)

    def format_header(self, title: str) -> str:
        """Format a header with decorative elements"""
        separator = "═" * 60
        return (f"{self.colorize(separator, Colors.BRIGHT_CYAN)}\n"
                f"{self.colorize(f'  {Icons.ASSISTANT} {title}', Colors.BRIGHT_WHITE)}\n"
                f"{self.colorize(separator, Colors.BRIGHT_CYAN)}")

    def format_stdio_response(self, response: str, tools_used: List[str] = None, available_tools: List[str] = None) -> Dict:
        """Format response for stdio mode with metadata"""
        result = {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "tools_available": available_tools or [],
                "tools_used": tools_used or []
            }
        }
        return result

@dataclass
class MCPMessage:
    """Represents an MCP protocol message"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict] = None
    result: Optional[Any] = None
    error: Optional[Dict] = None

class MCPClient:
    """Client for communicating with MCP servers via subprocess"""

    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.process = None
        self.message_id = 0

    async def start(self):
        """Start the MCP server process"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Started MCP server: {' '.join(self.server_command)}")

            # Initialize the connection
            await self.initialize()

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def initialize(self):
        """Initialize MCP connection"""
        # Send initialize request
        init_request = MCPMessage(
            id=str(self.message_id),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "mcp-chatbot",
                    "version": "1.0.0"
                }
            }
        )

        response = await self.send_request(init_request)
        if response and not response.error:
            logger.info("MCP server initialized successfully")

            # Try to send initialized notification, but don't fail if not supported
            try:
                initialized_notification = MCPMessage(
                    method="notifications/initialized",
                    params={}
                )
                await self.send_notification(initialized_notification)
                logger.info("Sent initialized notification")
            except Exception as e:
                logger.warning(f"Could not send initialized notification (this may be normal): {e}")
        else:
            raise Exception(f"Failed to initialize MCP server: {response.error if response else 'No response'}")

    async def send_request(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Send a request and wait for response"""
        if not self.process:
            raise Exception("MCP server not started")

        self.message_id += 1
        if message.id is None:
            message.id = str(self.message_id)

        # Send message
        message_dict = {k: v for k, v in message.__dict__.items() if v is not None}
        message_json = json.dumps(message_dict)
        logger.debug(f"Sending: {message_json}")

        self.process.stdin.write((message_json + '\n').encode())
        await self.process.stdin.drain()

        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=10.0
            )
            if response_line:
                response_text = response_line.decode().strip()
                logger.debug(f"Raw response: {response_text}")

                if response_text:
                    try:
                        response_data = json.loads(response_text)
                        response = MCPMessage(
                            jsonrpc=response_data.get("jsonrpc", "2.0"),
                            id=response_data.get("id"),
                            method=response_data.get("method"),
                            params=response_data.get("params"),
                            result=response_data.get("result"),
                            error=response_data.get("error")
                        )
                        logger.debug(f"Parsed response: {response.__dict__}")
                        return response
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse response JSON: {e}")
                        logger.error(f"Raw response was: {response_text}")
                        return None
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for MCP server response")
            return None

        return None

    async def send_notification(self, message: MCPMessage):
        """Send a notification (no response expected)"""
        if not self.process:
            raise Exception("MCP server not started")

        message_dict = {k: v for k, v in message.__dict__.items() if v is not None}
        message_json = json.dumps(message_dict)
        logger.debug(f"Sending notification: {message_json}")

        self.process.stdin.write((message_json + '\n').encode())
        await self.process.stdin.drain()

    async def list_tools(self) -> List[Dict]:
        """List available tools from MCP server"""
        request = MCPMessage(
            method="tools/list",
            params={}
        )

        response = await self.send_request(request)
        if response and not response.error:
            tools = response.result.get('tools', []) if response.result else []
            logger.info(f"Successfully retrieved {len(tools)} tools from MCP server")
            return tools
        else:
            logger.error(f"Failed to list tools: {response.error if response else 'No response'}")
            logger.error(f"Full response: {response.__dict__ if response else 'None'}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool on the MCP server"""
        request = MCPMessage(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )

        response = await self.send_request(request)
        if response and not response.error:
            return response.result
        else:
            error_msg = response.error if response else 'No response'
            logger.error(f"Failed to call tool {tool_name}: {error_msg}")
            return {"error": str(error_msg)}

    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("MCP server stopped")

class LMStudioClient:
    """Client for communicating with LM Studio via HTTP API"""

    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url
        self.conversation_history = []

    async def chat_completion(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        """Send chat completion request to LM Studio"""
        import aiohttp

        payload = {
            "model": "local-model",  # LM Studio uses this for local models
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/v1/chat/completions",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"LM Studio API error: {response.status} - {error_text}")
                        return {"error": f"API error: {response.status}"}
        except Exception as e:
            logger.error(f"Failed to connect to LM Studio: {e}")
            return {"error": f"Connection failed: {e}"}

class MCPChatBot:
    """Main chatbot class that orchestrates MCP and LM Studio"""

    def __init__(self, mcp_server_command: List[str], lm_studio_url: str = "http://localhost:1234", use_colors: bool = True):
        self.mcp_client = MCPClient(mcp_server_command)
        self.lm_studio = LMStudioClient(lm_studio_url)
        self.available_tools = []
        self.conversation_history = []
        self.formatter = OutputFormatter(use_colors)
        self.tools_used_in_conversation = []

    async def start(self):
        """Start the chatbot"""
        logger.info("Starting MCP Chatbot...")

        # Start MCP server
        await self.mcp_client.start()

        # Get available tools
        self.available_tools = await self.mcp_client.list_tools()
        logger.info(f"Available tools: {[tool['name'] for tool in self.available_tools]}")

        if not self.available_tools:
            logger.warning("No tools available from MCP server!")
            # Try to debug by checking server stderr
            if self.mcp_client.process and self.mcp_client.process.stderr:
                try:
                    stderr_data = await asyncio.wait_for(
                        self.mcp_client.process.stderr.read(1024),
                        timeout=1.0
                    )
                    if stderr_data:
                        logger.error(f"MCP Server stderr: {stderr_data.decode()}")
                except asyncio.TimeoutError:
                    pass

        # Add system message with tool information
        system_message = self.create_system_message()
        self.conversation_history.append(system_message)

        logger.info("MCP Chatbot started successfully!")

    def create_system_message(self) -> Dict:
        """Create system message with tool descriptions"""
        tool_descriptions = []
        for tool in self.available_tools:
            desc = f"- {tool['name']}: {tool.get('description', 'No description available')}"
            if 'inputSchema' in tool:
                properties = tool['inputSchema'].get('properties', {})
                if properties:
                    params = ", ".join(properties.keys())
                    desc += f" (Parameters: {params})"
            tool_descriptions.append(desc)

        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"

        return {
            "role": "system",
            "content": f"""You are an AI assistant with access to MCP (Model Context Protocol) tools. 
You can use these tools to help answer q`uestions and perform tasks.

Available tools:
{tools_text}

When you need to use a tool, respond with a function call. The user will execute the tool and provide you with the results.
Be helpful, accurate, and use the appropriate tools when needed to provide comprehensive answers."""
        }

    def convert_tools_for_openai(self) -> List[Dict]:
        """Convert MCP tools to OpenAI function format"""
        openai_tools = []
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                }
            }

            if "inputSchema" in tool:
                openai_tool["function"]["parameters"] = tool["inputSchema"]

            openai_tools.append(openai_tool)

        return openai_tools

    async def process_message(self, user_input: str) -> str:
        """Process a user message and return response"""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})

        # Prepare tools for LM Studio
        openai_tools = self.convert_tools_for_openai()

        # Get response from LM Studio
        response = await self.lm_studio.chat_completion(
            messages=self.conversation_history,
            tools=openai_tools if openai_tools else None
        )

        if "error" in response:
            return f"Error: {response['error']}"

        assistant_message = response["choices"][0]["message"]
        tools_used_this_turn = []

        # Check if the assistant wants to use a tool
        if assistant_message.get("tool_calls"):
            # Process tool calls
            tool_results = []
            for tool_call in assistant_message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                logger.info(f"Calling tool: {function_name} with args: {arguments}")
                tools_used_this_turn.append(function_name)

                result = await self.mcp_client.call_tool(function_name, arguments)
                tool_results.append(f"Tool {function_name} result: {json.dumps(result, indent=2)}")

            # Add tool results to conversation and get final response
            self.conversation_history.append(assistant_message)
            self.conversation_history.append({
                "role": "user",
                "content": f"Tool results:\n" + "\n".join(tool_results)
            })

            # Get final response
            final_response = await self.lm_studio.chat_completion(messages=self.conversation_history)
            if "error" in final_response:
                return f"Error in final response: {final_response['error']}"

            final_message = final_response["choices"][0]["message"]
            self.conversation_history.append(final_message)

            # Track tools used
            self.tools_used_in_conversation.extend(tools_used_this_turn)

            return final_message["content"]
        else:
            # No tools needed, return the response
            self.conversation_history.append(assistant_message)
            return assistant_message["content"]

    async def run_interactive(self):
        """Run interactive chat loop"""
        print(self.formatter.format_header("MCP Chatbot with LM Studio"))
        print()
        print(self.formatter.format_status_message("Chatbot started successfully!", "success"))
        print(self.formatter.format_status_message(f"Connected to LM Studio at {self.lm_studio.base_url}", "connected"))
        print(self.formatter.format_status_message(f"Available tools: {', '.join([tool['name'] for tool in self.available_tools]) if self.available_tools else 'None'}", "info"))
        print()
        print(self.formatter.colorize("Type 'quit', 'exit', or 'bye' to end the conversation", Colors.DIM))
        print(self.formatter.format_separator())
        print()

        try:
            while True:
                try:
                    # Show user prompt
                    user_prompt = self.formatter.format_user_prompt("")
                    user_input = input(user_prompt).strip()

                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print()
                        print(self.formatter.format_status_message("Goodbye! 👋", "info"))
                        break

                    if not user_input:
                        continue

                    print()

                    # Show assistant prompt and processing indicator
                    assistant_prompt = self.formatter.format_assistant_prompt()
                    print(assistant_prompt, end="", flush=True)
                    print(self.formatter.format_status_message("Processing...", "loading"))

                    # Process the message
                    response = await self.process_message(user_input)

                    # Clear the processing line and show response
                    print(f"\r{assistant_prompt}", end="")

                    # Format and display the response
                    formatted_response = self.formatter.colorize(response, Colors.WHITE)
                    print(formatted_response)

                    print()
                    print(self.formatter.format_separator())
                    print()

                except KeyboardInterrupt:
                    print()
                    print(self.formatter.format_status_message("Interrupted by user", "info"))
                    break
                except Exception as e:
                    print()
                    print(self.formatter.format_status_message(f"Error processing message: {e}", "error"))
                    logger.error(f"Error in interactive loop: {e}")
                    print()

        finally:
            await self.stop()

    async def run_stdio(self):
        """Run in stdio/stdin mode for integration with other systems"""
        logger.info("Running in stdio mode")
        logger.info(f"Available tools at startup: {[tool['name'] for tool in self.available_tools]}")

        try:
            while True:
                line = sys.stdin.readline()
                if not line:  # EOF
                    break

                user_input = line.strip()
                if not user_input:
                    continue

                logger.info(f"Processing user input: {user_input}")

                try:
                    response = await self.process_message(user_input)

                    # Get tools used in the last turn
                    current_tools = list(set(self.tools_used_in_conversation))
                    tools_in_last_turn = [tool for tool in current_tools if tool not in getattr(self, '_previous_tools', [])]

                    # Format enhanced response for stdio
                    result = self.formatter.format_stdio_response(
                        response=response,
                        tools_used=tools_in_last_turn,
                        available_tools=[tool['name'] for tool in self.available_tools]
                    )

                    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)

                    # Update previous tools for next comparison
                    self._previous_tools = current_tools.copy()

                except Exception as e:
                    error_response = {
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "tools_available": [tool['name'] for tool in self.available_tools],
                            "error_type": type(e).__name__
                        }
                    }
                    print(json.dumps(error_response, indent=2), flush=True)
                    logger.error(f"Error processing stdio message: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in stdio mode: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Stop the chatbot"""
        logger.info("Stopping MCP Chatbot...")
        await self.mcp_client.stop()
        logger.info("MCP Chatbot stopped")

async def main():
    parser = argparse.ArgumentParser(description="MCP Chatbot with LM Studio Integration")
    parser.add_argument("--mcp-command", required=True,
                        help="Command to start MCP server (e.g., 'java -jar myapp.jar')")
    parser.add_argument("--lm-studio-url", default="http://localhost:1234",
                        help="LM Studio API URL (default: http://localhost:1234)")
    parser.add_argument("--mode", choices=["interactive", "stdio"], default="interactive",
                        help="Run mode: interactive (console) or stdio (for integration)")
    parser.add_argument("--no-colors", action="store_true",
                        help="Disable colored output (useful for terminals without color support)")

    args = parser.parse_args()

    # Parse the MCP command string into a list
    import shlex
    mcp_command = shlex.split(args.mcp_command)

    chatbot = MCPChatBot(mcp_command, args.lm_studio_url, use_colors=not args.no_colors)

    try:
        await chatbot.start()

        if args.mode == "interactive":
            await chatbot.run_interactive()
        else:
            await chatbot.run_stdio()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Install required dependencies
    try:
        import aiohttp
    except ImportError:
        print("Please install required dependencies:")
        print("pip install aiohttp")
        sys.exit(1)

    asyncio.run(main())