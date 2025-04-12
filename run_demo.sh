#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fact Checker MCP Demo with Ollama ===${NC}"
echo -e "${YELLOW}This demo shows how to use the Model Context Protocol to integrate"
echo -e "a fact-checking service with an LLM running on Ollama.${NC}"
echo

# Check if Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo -e "${RED}Flask is not installed. Installing...${NC}"
    pip install flask
fi

# Check if requests is installed
if ! python -c "import requests" &> /dev/null; then
    echo -e "${RED}Requests is not installed. Installing...${NC}"
    pip install requests
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/version &> /dev/null; then
    echo -e "${RED}Ollama is not running. Please start Ollama first.${NC}"
    echo "Run: ollama serve"
    exit 1
fi

# Start the Fact Checker MCP server in the background
echo -e "${GREEN}Starting Fact Checker MCP server...${NC}"
python app.py &
SERVER_PID=$!

# Wait for the server to start
echo "Waiting for server to start..."
sleep 2

# Make the MCP client executable
chmod +x mcp_client.py

# Run the MCP client
echo -e "${GREEN}Starting MCP client...${NC}"
echo -e "${YELLOW}Try asking questions with factual claims about capitals, like:${NC}"
echo -e "${YELLOW}- Tell me about France. The capital of France is Paris.${NC}"
echo -e "${YELLOW}- I think the capital of Australia is Sydney.${NC}"
echo -e "${YELLOW}- The capital of United States is New York.${NC}"
echo

# Get available models
MODELS=$(ollama list | awk 'NR>1 {print $1}' | sed 's/:.*$//')
DEFAULT_MODEL="llama3"

# Check if the default model exists, otherwise use the first available model
if ! echo "$MODELS" | grep -q "$DEFAULT_MODEL"; then
    DEFAULT_MODEL=$(echo "$MODELS" | head -n 1)
fi

echo -e "${BLUE}Available models:${NC}"
echo "$MODELS" | tr '\n' ' '
echo -e "\n"

# Ask which model to use
echo -e "${YELLOW}Which model would you like to use? (default: $DEFAULT_MODEL)${NC}"
read -p "> " MODEL_CHOICE

if [ -z "$MODEL_CHOICE" ]; then
    MODEL_CHOICE=$DEFAULT_MODEL
fi

# Run the client
python mcp_client.py --model $MODEL_CHOICE

# Clean up
echo -e "${GREEN}Stopping Fact Checker MCP server...${NC}"
kill $SERVER_PID

echo -e "${BLUE}Demo completed.${NC}"
