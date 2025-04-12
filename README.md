# Fact Checker MCP Server

This is a Model Context Protocol (MCP) server that verifies simple factual claims by checking them against knowledge sources like Wikidata.

## Features

- Accepts claims in natural language
- Verifies the accuracy of the claim
- Returns an MCP-compliant response with the claim, correct answer, and confidence score
- Includes an MCP client that integrates with Ollama LLM

## MCP Payload Format

```json
{
  "version": "1.0",
  "context": {
    "type": "fact_check",
    "claim": "The capital of France is London",
    "correct_answer": "Incorrect. The capital of France is Paris, not London.",
    "confidence": 0.95
  }
}
```

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the server:
   ```
   python app.py
   ```

## Usage

### Server API

Send a POST request to the `/fact-check` endpoint with a JSON payload containing the claim:

```bash
curl -X POST http://localhost:5000/fact-check \
  -H "Content-Type: application/json" \
  -d '{"claim": "The capital of France is London"}'
```

### MCP Client with Ollama Integration

The project includes an MCP client that demonstrates integration with Ollama LLM:

1. Make sure Ollama is installed and running:
   ```
   ollama serve
   ```

2. Run the demo script:
   ```
   bash run_demo.sh
   ```

3. Or run the client directly:
   ```
   python mcp_client.py --model llama3
   ```

The client will:
- Detect factual claims about capitals in your prompts
- Verify these claims using the MCP server
- Augment the LLM's knowledge with accurate information
- Ensure the LLM provides factually correct responses

## Testing

### Basic Testing

Run the test client with a specific claim:

```bash
python test_client.py "The capital of France is Paris"
```

Or run the default test suite with multiple claims:

```bash
python test_client.py
```

### Comprehensive Test Suite

Run the comprehensive test suite that includes both correct and incorrect claims:

```bash
python test_client.py --test-suite
```

### Unit Tests

Run the unit tests to verify the server's functionality:

```bash
python -m unittest test_unit.py
```

## Supported Claim Types

Currently, the server can verify:
- Capital city claims (e.g., "The capital of [Country] is [City]")

More claim types will be added in future updates.

## Extending the Server

To add support for new types of claims:
1. Add a new pattern matching regex in the `check_fact()` function
2. Implement a corresponding verification function similar to `check_capital_claim()`

## License

[MIT](LICENSE)

## Author

&copy; Anthony Lim