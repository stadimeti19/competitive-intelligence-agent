#!/usr/bin/env python3
"""Test script to verify the CI tools work correctly"""

import sys
sys.path.append('tools')
from ci_tools import duckduckgo_search, get_wikipedia_info, generate_industry_competitors

def test_tools():
    print("Testing CI Tools...")
    
    # Test 1: DuckDuckGo search
    print("\n1. Testing DuckDuckGo search...")
    search_result = duckduckgo_search("Fidelity Investments competitors")
    print(f"Search result: {search_result[:200]}...")
    
    # Test 2: Wikipedia info
    print("\n2. Testing Wikipedia info...")
    wiki_result = get_wikipedia_info("Fidelity Investments")
    print(f"Wikipedia result: {wiki_result}")
    
    # Test 3: Industry competitors
    print("\n3. Testing industry competitors...")
    competitors = generate_industry_competitors("Financial Services", "Fidelity Investments")
    print(f"Competitors: {competitors[:200]}...")
    
    print("\n✅ All tools working correctly!")

if __name__ == "__main__":
    test_tools() 