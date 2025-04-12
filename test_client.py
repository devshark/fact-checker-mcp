import requests
import json
import sys
import time

def test_fact_checker(claim):
    """
    Test the fact checker MCP server with a given claim.
    """
    url = "http://127.0.0.1:5000/fact-check"
    payload = {"claim": claim}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("\nMCP Response:")
        print(json.dumps(result, indent=2))
        
        # Extract the relevant parts
        context = result.get("context", {})
        print("\nFact Check Result:")
        print(f"Claim: {context.get('claim')}")
        print(f"Correct Answer: {context.get('correct_answer')}")
        print(f"Confidence: {context.get('confidence')}")
        
        # Determine if the claim was correct or incorrect
        correct_answer = context.get('correct_answer', '')
        if "Incorrect" in correct_answer:
            print("Status: ❌ INCORRECT CLAIM")
        elif "Correct" in correct_answer:
            print("Status: ✅ CORRECT CLAIM")
        else:
            print("Status: ❓ UNKNOWN")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def run_test_suite():
    """Run a comprehensive test suite with both correct and incorrect claims."""
    
    # Test pairs: (claim, expected_correctness)
    # where expected_correctness is True for correct claims, False for incorrect
    test_cases = [
        # Correct claims
        ("The capital of France is Paris", True),
        ("The capital of Japan is Tokyo", True),
        ("The capital of Germany is Berlin", True),
        
        # Incorrect claims
        ("The capital of France is London", False),
        ("The capital of Japan is Beijing", False),
        ("The capital of Australia is Sydney", False),  # It's Canberra
        ("The capital of Brazil is Rio de Janeiro", False),  # It's Brasília
        ("The capital of Canada is Toronto", False),  # It's Ottawa
        
        # Edge cases
        ("The capital of United States is Washington, D.C.", True),  # Should handle "United States" correctly
        ("The capital of United States is Washington DC", True),  # Alternative spelling
        ("The capital of South Korea is Seoul", True)
    ]
    
    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "errors": 0
    }
    
    print("=== RUNNING COMPREHENSIVE TEST SUITE ===")
    print(f"Testing {len(test_cases)} claims ({sum(1 for _, exp in test_cases if exp)} correct, {sum(1 for _, exp in test_cases if not exp)} incorrect)")
    
    for i, (claim, expected_correct) in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] Testing: {claim}")
        print(f"Expected: {'Correct' if expected_correct else 'Incorrect'}")
        
        try:
            result = test_fact_checker(claim)
            if not result:
                results["errors"] += 1
                continue
                
            correct_answer = result.get("context", {}).get("correct_answer", "")
            actual_correct = "Correct" in correct_answer
            actual_incorrect = "Incorrect" in correct_answer
            
            if (expected_correct and actual_correct) or (not expected_correct and actual_incorrect):
                print("Test Result: ✅ PASS")
                results["passed"] += 1
            else:
                print("Test Result: ❌ FAIL")
                print(f"  Expected: {'Correct' if expected_correct else 'Incorrect'}")
                print(f"  Actual: {correct_answer}")
                results["failed"] += 1
                
            # Add a small delay to avoid overwhelming the Wikidata API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error during test: {e}")
            results["errors"] += 1
    
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Errors: {results['errors']}")
    print(f"Success rate: {results['passed']/results['total']*100:.1f}%")
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-suite":
            run_test_suite()
        else:
            # Use claim from command line argument
            claim = " ".join(sys.argv[1:])
            test_fact_checker(claim)
    else:
        # Use default test claims with both correct and incorrect examples
        test_claims = [
            "The capital of France is Paris",     # Correct
            "The capital of Japan is Tokyo",      # Correct
            "The capital of Australia is Sydney", # Incorrect (it's Canberra)
            "The capital of Brazil is Rio de Janeiro", # Incorrect (it's Brasília)
            "The capital of Italy is Rome",       # Correct
            "The capital of Spain is Barcelona"   # Incorrect (it's Madrid)
        ]
        
        print("Testing multiple claims...")
        for claim in test_claims:
            print(f"\nTesting: {claim}")
            test_fact_checker(claim)
            # Add a small delay to avoid overwhelming the Wikidata API
            time.sleep(0.5)
