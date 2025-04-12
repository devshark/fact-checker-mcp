#!/usr/bin/env python3
"""
MCP Client for Fact Checker - Integrates with Ollama LLM

This script demonstrates how to use the Model Context Protocol (MCP) to integrate
a fact-checking service with an LLM running on Ollama.
"""

import argparse
import json
import re
import requests
import sys
import time
from typing import Dict, Any, Optional, List, Tuple

# Configuration
FACT_CHECKER_URL = "http://127.0.0.1:5000/fact-check"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "llama3"  # Using llama3 as default model

# Regular expression to detect potential factual claims about capitals
CAPITAL_CLAIM_PATTERN = re.compile(r"(?:the capital of|capital city of) ([A-Za-z\s]+) is ([A-Za-z\s,\.]+)", re.IGNORECASE)

class MCPClient:
    """Client for Model Context Protocol integration with Ollama"""
    
    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []
        
    def detect_factual_claims(self, text: str) -> List[str]:
        """Detect potential factual claims about capitals in the text"""
        claims = []
        
        # Find all matches for capital claims
        for match in CAPITAL_CLAIM_PATTERN.finditer(text):
            country = match.group(1).strip()
            city = match.group(2).strip()
            claim = f"The capital of {country} is {city}"
            claims.append(claim)
            
        return claims
    
    def verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verify a claim using the Fact Checker MCP server"""
        try:
            response = requests.post(
                FACT_CHECKER_URL,
                json={"claim": claim},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error verifying claim: {e}")
            return {
                "version": "1.0",
                "context": {
                    "type": "fact_check",
                    "claim": claim,
                    "correct_answer": f"Error verifying claim: {e}",
                    "confidence": 0.0
                }
            }
    
    def generate_llm_response(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float]:
        """Generate a response from Ollama LLM"""
        messages = self.conversation_history.copy()
        
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "temperature": self.temperature
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", ""), result.get("total_duration", 0) / 1000000000  # Convert ns to seconds
        except requests.RequestException as e:
            print(f"Error generating LLM response: {e}")
            return f"Error: {e}", 0
    
    def augment_with_fact_checking(self, prompt: str) -> str:
        """
        Process user prompt, detect claims, verify them with MCP,
        and augment the prompt with fact-checking information
        """
        # Detect factual claims in the prompt
        claims = self.detect_factual_claims(prompt)
        
        if not claims:
            return prompt
        
        # Verify each claim using the MCP server
        fact_check_results = []
        for claim in claims:
            print(f"Detected claim: {claim}")
            mcp_response = self.verify_claim(claim)
            fact_check_results.append(mcp_response)
            
            # Print the fact check result
            context = mcp_response.get("context", {})
            print(f"Fact check: {context.get('correct_answer')}")
            print(f"Confidence: {context.get('confidence')}")
            print()
        
        # Augment the prompt with fact-checking information
        augmented_prompt = prompt + "\n\n### Verified Facts:\n"
        for result in fact_check_results:
            context = result.get("context", {})
            augmented_prompt += f"- {context.get('claim')}: {context.get('correct_answer')}\n"
        
        return augmented_prompt
    
    def chat(self, system_prompt: Optional[str] = None):
        """Interactive chat session with fact-checking augmentation"""
        if system_prompt:
            print(f"System: {system_prompt}")
        
        print("\nFact-Checking MCP Client with Ollama")
        print(f"Using model: {self.model}")
        print("Type 'exit' or 'quit' to end the conversation")
        print("---------------------------------------------")
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                # Add to conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                
                # Check for factual claims and augment with fact-checking
                augmented_prompt = self.augment_with_fact_checking(user_input)
                
                # If claims were detected and verified, use the augmented prompt
                if augmented_prompt != user_input:
                    print("\n[MCP] Factual claims detected and verified")
                    
                    # Create a system message with the fact-checking information
                    fact_check_system = system_prompt or ""
                    fact_check_system += "\n\nIMPORTANT: Use the verified facts below to ensure your response is factually accurate:"
                    
                    # Extract just the verified facts part
                    verified_facts = augmented_prompt.split("### Verified Facts:\n")[1]
                    fact_check_system += "\n" + verified_facts
                    
                    # Generate response with the augmented system prompt
                    start_time = time.time()
                    response, duration = self.generate_llm_response(user_input, fact_check_system)
                    total_time = time.time() - start_time
                else:
                    # No claims detected, use the original prompt
                    start_time = time.time()
                    response, duration = self.generate_llm_response(user_input, system_prompt)
                    total_time = time.time() - start_time
                
                # Add to conversation history
                self.conversation_history.append({"role": "assistant", "content": response})
                
                # Print the response
                print(f"\nAssistant: {response}")
                print(f"\n[Response time: {total_time:.2f}s, LLM processing: {duration:.2f}s]")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")

def main():
    parser = argparse.ArgumentParser(description="MCP Client for Fact Checker with Ollama LLM")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for LLM generation (default: 0.7)")
    parser.add_argument("--system", help="System prompt for the LLM")
    args = parser.parse_args()
    
    # Default system prompt if none provided
    default_system_prompt = """You are a helpful assistant that provides accurate information.
When discussing facts about countries and capitals, you should be precise and correct.
If you're not sure about a fact, acknowledge your uncertainty."""

    system_prompt = args.system or default_system_prompt
    
    # Create and run the MCP client
    client = MCPClient(model=args.model, temperature=args.temperature)
    client.chat(system_prompt=system_prompt)

if __name__ == "__main__":
    main()
