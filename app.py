from flask import Flask, request, jsonify
import requests
import re
import json

app = Flask(__name__)

@app.route('/fact-check', methods=['POST'])
def fact_check():
    data = request.json
    if not data or 'claim' not in data:
        return jsonify({"error": "Missing claim in request"}), 400
    
    claim = data['claim']
    result = check_fact(claim)
    
    # Format as MCP payload
    mcp_payload = {
        "version": "1.0",
        "context": {
            "type": "fact_check",
            "claim": claim,
            "correct_answer": result["correct_answer"],
            "confidence": result["confidence"]
        }
    }
    
    return jsonify(mcp_payload)

def check_fact(claim):
    """
    Parse the claim and check it against Wikidata or other knowledge sources.
    Returns a dict with correct_answer and confidence.
    """
    # Simple pattern matching for common claim types
    # Example: "The capital of France is London"
    capital_pattern = re.compile(r"The capital of ([A-Za-z\s]+) is ([A-Za-z\s,\.]+)", re.IGNORECASE)
    match = capital_pattern.match(claim)
    
    if match:
        country = match.group(1).strip()
        claimed_capital = match.group(2).strip()
        return check_capital_claim(country, claimed_capital)
    
    # Add more patterns for other types of claims
    
    # Default fallback if no patterns match
    return {
        "correct_answer": "Unable to verify this claim",
        "confidence": 0.0
    }

def normalize_country_name(country):
    """Normalize country names to improve matching with Wikidata."""
    country_mapping = {
        "united states": "United States of America",
        "us": "United States of America",
        "usa": "United States of America",
        "uk": "United Kingdom",
        "great britain": "United Kingdom",
        "south korea": "Republic of Korea",
        "north korea": "Democratic People's Republic of Korea"
    }
    
    normalized = country.lower()
    if normalized in country_mapping:
        return country_mapping[normalized]
    return country

def normalize_capital_name(capital):
    """Normalize capital names to improve matching."""
    capital_mapping = {
        "washington": "Washington, D.C.",
        "washington dc": "Washington, D.C.",
        "washington d.c.": "Washington, D.C.",
        "new york": "New York City"
    }
    
    normalized = capital.lower()
    if normalized in capital_mapping:
        return capital_mapping[normalized]
    return capital

def check_capital_claim(country, claimed_capital):
    """Check if the claimed capital of a country is correct using Wikidata."""
    try:
        # Normalize country and capital names
        normalized_country = normalize_country_name(country)
        normalized_claimed_capital = normalize_capital_name(claimed_capital)
        
        # Simple hardcoded database for testing and fallback
        capital_database = {
            "france": "Paris",
            "germany": "Berlin",
            "japan": "Tokyo",
            "united states": "Washington, D.C.",
            "united states of america": "Washington, D.C.",
            "australia": "Canberra",
            "brazil": "Brasília",
            "canada": "Ottawa",
            "italy": "Rome",
            "spain": "Madrid",
            "united kingdom": "London",
            "china": "Beijing",
            "russia": "Moscow",
            "india": "New Delhi",
            "south korea": "Seoul",
            "republic of korea": "Seoul"
        }
        
        # First try our local database (faster and more reliable for testing)
        country_key = normalized_country.lower()
        if country_key not in capital_database:
            country_key = country.lower()
            
        if country_key in capital_database:
            actual_capital = capital_database[country_key]
            
            # Compare with claimed capital
            if normalized_claimed_capital.lower() == actual_capital.lower() or claimed_capital.lower() == actual_capital.lower():
                return {"correct_answer": f"Correct. The capital of {country} is {actual_capital}.", "confidence": 0.95}
            else:
                return {"correct_answer": f"Incorrect. The capital of {country} is {actual_capital}, not {claimed_capital}.", "confidence": 0.95}
        
        # If not in our database, try Wikidata as a fallback
        query = f"""
        SELECT ?capitalLabel WHERE {{
          ?country wdt:P31 wd:Q6256;  # instance of country
                  rdfs:label ?countryLabel;
                  wdt:P36 ?capital.   # capital
          ?capital rdfs:label ?capitalLabel.
          FILTER(LANG(?countryLabel) = "en")
          FILTER(LANG(?capitalLabel) = "en")
          FILTER(LCASE(?countryLabel) = LCASE("{normalized_country}") || LCASE(?countryLabel) = LCASE("{country}"))
        }}
        LIMIT 1
        """
        
        url = "https://query.wikidata.org/sparql"
        response = requests.get(
            url, 
            params={"query": query, "format": "json"},
            headers={"User-Agent": "FactCheckerMCP/1.0"}
        )
        
        if response.status_code != 200:
            return {"correct_answer": f"Error querying knowledge base: {response.status_code}", "confidence": 0.0}
        
        data = response.json()
        results = data.get("results", {}).get("bindings", [])
        
        if not results:
            # Try a more flexible search if the first one fails
            query = f"""
            SELECT ?country ?countryLabel ?capitalLabel WHERE {{
              ?country wdt:P31 wd:Q6256;  # instance of country
                      wdt:P36 ?capital.   # capital
              ?capital rdfs:label ?capitalLabel.
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
              FILTER(CONTAINS(LCASE(?countryLabel), LCASE("{country}")))
              FILTER(LANG(?capitalLabel) = "en")
            }}
            LIMIT 1
            """
            
            response = requests.get(
                url, 
                params={"query": query, "format": "json"},
                headers={"User-Agent": "FactCheckerMCP/1.0"}
            )
            
            if response.status_code != 200:
                return {"correct_answer": f"Could not find capital information for {country}", "confidence": 0.5}
                
            data = response.json()
            results = data.get("results", {}).get("bindings", [])
            
            if not results:
                return {"correct_answer": f"Could not find capital information for {country}", "confidence": 0.5}
        
        actual_capital = results[0]["capitalLabel"]["value"]
        
        # Normalize the actual capital for comparison
        normalized_actual_capital = normalize_capital_name(actual_capital)
        
        # Compare normalized versions for more accurate matching
        if normalized_actual_capital.lower() == normalized_claimed_capital.lower():
            return {"correct_answer": f"Correct. The capital of {country} is {actual_capital}.", "confidence": 0.95}
        else:
            return {"correct_answer": f"Incorrect. The capital of {country} is {actual_capital}, not {claimed_capital}.", "confidence": 0.95}
            
    except Exception as e:
        return {"correct_answer": f"Error checking fact: {str(e)}", "confidence": 0.0}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
