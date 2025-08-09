#!/usr/bin/env python3
"""OpenAI Chat wrapper script for MCP stdio toolbox."""

import json
import sys
import requests
import os
from typing import Dict, Any

def make_openai_request(message: str, model: str = "gpt-4", api_key: str = None, 
                       max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
    """Make request to OpenAI Chat Completions API."""
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("API key required: provide via --api-key or OPENAI_API_KEY env var")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    response.raise_for_status()
    return response.json()

def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Chat API wrapper")
    parser.add_argument("--message", required=True, help="Message to send")
    parser.add_argument("--model", default="gpt-4", help="Model to use")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--max-tokens", type=int, default=1000, help="Max tokens")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    
    args = parser.parse_args()
    
    try:
        result = make_openai_request(
            message=args.message,
            model=args.model,
            api_key=args.api_key,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            # Extract just the response text
            content = result["choices"][0]["message"]["content"]
            print(content.strip())
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()