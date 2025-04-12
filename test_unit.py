import unittest
from unittest.mock import patch, MagicMock
import json
import sys
sys.path.append('.')
from app import app, check_fact, check_capital_claim

class TestFactCheckerMCP(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_missing_claim(self):
        """Test that the API returns an error when no claim is provided."""
        response = self.app.post('/fact-check', 
                                json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('app.check_fact')
    def test_valid_claim_format(self, mock_check_fact):
        """Test that a valid claim returns the expected MCP format."""
        mock_check_fact.return_value = {
            "correct_answer": "Test answer",
            "confidence": 0.9
        }
        
        response = self.app.post('/fact-check', 
                                json={"claim": "Test claim"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check MCP format
        self.assertIn('version', data)
        self.assertEqual(data['version'], '1.0')
        self.assertIn('context', data)
        self.assertIn('type', data['context'])
        self.assertEqual(data['context']['type'], 'fact_check')
        self.assertIn('claim', data['context'])
        self.assertEqual(data['context']['claim'], 'Test claim')
        self.assertIn('correct_answer', data['context'])
        self.assertIn('confidence', data['context'])
    
    def test_check_fact_capital_pattern(self):
        """Test that the capital pattern is correctly identified."""
        # Test with a valid capital claim
        result = check_fact("The capital of TestCountry is TestCity")
        self.assertIn('correct_answer', result)
        self.assertIn('confidence', result)
    
    def test_check_fact_unknown_pattern(self):
        """Test that unknown claim patterns return appropriate response."""
        result = check_fact("This is not a recognized claim pattern")
        self.assertEqual(result['correct_answer'], "Unable to verify this claim")
        self.assertEqual(result['confidence'], 0.0)
    
    @patch('app.requests.get')
    def test_check_capital_claim_correct(self, mock_get):
        """Test checking a correct capital claim."""
        # Mock the Wikidata API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "capitalLabel": {
                            "value": "TestCity"
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        result = check_capital_claim("TestCountry", "TestCity")
        self.assertIn("Correct", result['correct_answer'])
        self.assertGreater(result['confidence'], 0.9)
    
    @patch('app.requests.get')
    def test_check_capital_claim_incorrect(self, mock_get):
        """Test checking an incorrect capital claim."""
        # Mock the Wikidata API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "bindings": [
                    {
                        "capitalLabel": {
                            "value": "RealCapital"
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        result = check_capital_claim("TestCountry", "WrongCapital")
        self.assertIn("Incorrect", result['correct_answer'])
        self.assertIn("RealCapital", result['correct_answer'])
        self.assertGreater(result['confidence'], 0.9)
    
    @patch('app.requests.get')
    def test_check_capital_claim_api_error(self, mock_get):
        """Test handling of API errors."""
        # Mock an API error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = check_capital_claim("TestCountry", "TestCity")
        self.assertIn("Error", result['correct_answer'])
        self.assertEqual(result['confidence'], 0.0)
    
    @patch('app.requests.get')
    def test_check_capital_claim_no_results(self, mock_get):
        """Test handling when no results are found."""
        # Mock empty results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "bindings": []
            }
        }
        mock_get.return_value = mock_response
        
        result = check_capital_claim("NonExistentCountry", "TestCity")
        self.assertIn("Could not find capital information", result['correct_answer'])
        self.assertEqual(result['confidence'], 0.5)

if __name__ == '__main__':
    unittest.main()
