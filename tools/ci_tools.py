import autogen
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
import openai
from dotenv import load_dotenv
load_dotenv()

# --- LLM Configuration ---
try:
    config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")
    llm_config = {"config_list": config_list, "temperature": 0}
except (FileNotFoundError, ValueError):
    print("Warning: OAI_CONFIG_LIST not found or invalid. Using environment variables.")
    try:
        config_list = autogen.config_list_from_models(
            model_list=["gpt-3.5-turbo", "gpt-4"],
        )
        llm_config = {"config_list": config_list, "temperature": 0}
    except Exception as e:
        print(f"Fatal: Could not configure LLM. Please set up OAI_CONFIG_LIST or API keys. Error: {e}")
        llm_config = None

def get_llm_response(prompt):
    # Use OpenAI API directly for chat completion
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set.")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",  # or "gpt-4" or "gpt-3.5-turbo" as appropriate
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content

# --- Tool Functions ---
def duckduckgo_search(query: str, num_results: int = 8) -> str:
    print(f"--- Searching for: '{query}' ---")
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=num_results)]
        return json.dumps(results)
    except Exception as e:
        print(f"Error in duckduckgo_search: {e}")
        return json.dumps([])

def scrape_website(url: str) -> str:
    print(f"--- Scraping: {url} ---")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return json.dumps({"url": url, "content": text[:4000]})
    except Exception as e:
        print(f"Error scraping website {url}: {e}")
        return json.dumps({"url": url, "error": str(e)})

def generate_industry_competitors(industry: str, company_description: str) -> str:
    """
    Finds real competitors for a company or idea using web search and LLM-based filtering.
    Returns a JSON array of competitor names (validated by LLM).
    """
    print(f"--- Finding competitors for: '{company_description}' in '{industry}' ---")
    query = f"top competitors of {company_description} in {industry} industry"
    try:
        # Use DuckDuckGo search for real competitors
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=10)]
        import re
        candidates = set()
        for r in results:
            text = (r.get('title', '') + ' ' + r.get('body', ''))
            found = re.findall(r'([A-Z][A-Za-z0-9&\-. ]{2,})', text)
            for name in found:
                name_clean = name.strip().replace('\n', '').replace('\r', '')
                if (name_clean.lower() not in company_description.lower()
                    and name_clean.lower() not in industry.lower()
                    and len(name_clean) > 2
                    and not name_clean.lower().startswith('top ')
                    and not name_clean.lower().startswith('best ')
                    and not name_clean.lower().startswith('competitors')):
                    candidates.add(name_clean)
        candidates_list = list(candidates)
        print(f"--- Raw extracted candidates: {candidates_list} ---")
        # LLM-based filtering for valid company names
        llm_prompt = f"""
        Given the following list of extracted names from web search results about competitors in the {industry} industry for '{company_description}', return ONLY the valid company names (no phrases, no generic terms, no duplicates, no original company). Return as a JSON array of strings. If none are valid, return an empty array.
        
        Extracted: {json.dumps(candidates_list)}
        """
        filtered = get_llm_response(llm_prompt)
        # Try to parse the LLM output as JSON array
        try:
            if filtered.startswith('```json'):
                filtered = filtered[7:-3]
            elif filtered.startswith('```'):
                filtered = filtered[3:-3]
            competitors_list = json.loads(filtered)
            if not isinstance(competitors_list, list):
                competitors_list = []
        except Exception as e:
            print(f"Error parsing LLM competitor output: {e}")
            competitors_list = []
        print(f"--- LLM-filtered competitors: {competitors_list} ---")
        return json.dumps(competitors_list[:8])
    except Exception as e:
        print(f"Error finding competitors: {e}")
        return json.dumps([])

def search_company_info(company_name: str, query_type: str = "general") -> str:
    """
    Performs web search to find specific information about a company.
    The agent can use this to get real-time data about competitors.
    """
    print(f"--- Searching for {query_type} info about: {company_name} ---")
    
    queries = {
        "general": f"{company_name} company overview",
        "features": f"{company_name} features products services",
        "pricing": f"{company_name} pricing plans costs",
        "market": f"{company_name} market position competitors"
    }
    
    query = queries.get(query_type, f"{company_name} {query_type}")
    search_results = duckduckgo_search(query, num_results=5)
    
    return search_results

def get_company_website_data(company_name: str) -> str:
    """
    Attempts to find and scrape the company's official website for current information.
    """
    print(f"--- Getting website data for: {company_name} ---")
    
    # Search for official website
    website_query = f"{company_name} official website"
    search_results = json.loads(duckduckgo_search(website_query, 3))
    
    if not search_results:
        return json.dumps({"error": "No website found"})
    
    # Try to scrape the first result
    try:
        website_url = search_results[0].get('link', search_results[0].get('url', ''))
        if website_url:
            scraped_data = scrape_website(website_url)
            return scraped_data
    except Exception as e:
        print(f"Error scraping website: {e}")
    
    return json.dumps({"error": "Could not scrape website"})

def playwright_scrape(url: str) -> str:
    """
    Uses Playwright to fetch the fully rendered HTML of a page (for JavaScript-heavy sites).
    Returns the page content as text.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=15000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"Error using Playwright to scrape {url}: {e}"

def _extract_currency_from_text(text: str) -> str:
    import re
    patterns = [
        r'\$[\d\.,]+\s*(?:billion|million|B|M)?',
        r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:billion|million|B|M)\b',
        r'\b(?:revenue|sales|income)\s+of\s+\$*[\d\.,]+\s*(?:billion|million|B|M)?\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return "N/A"

def _extract_percentage_from_text(text: str) -> str:
    import re
    patterns = [
        r'(\d+(?:\.\d+)?)%\s*(?:market share)?',
        r'(\d+(?:\.\d+)?)\s*(?:percent|pct)\s*(?:market share)?'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return "N/A"

def analyze_competitor_data(company_name: str, industry: str) -> str:
    """
    Enhanced: Performs targeted searches for revenue and market share, uses regex to extract numbers, and falls back to LLM for qualitative fields.
    """
    print(f"--- Analyzing data for: {company_name} ---")
    # Get multiple data sources
    general_info = json.loads(search_company_info(company_name, "general"))
    features_info = json.loads(search_company_info(company_name, "features"))
    pricing_info = json.loads(search_company_info(company_name, "pricing"))
    website_data = json.loads(get_company_website_data(company_name))
    data_sources = ["general_info", "features_info", "pricing_info", "website_data"]
    # --- Targeted search for revenue ---
    revenue = "N/A"
    revenue_queries = [
        f"{company_name} annual revenue",
        f"{company_name} financial report",
        f"{company_name} earnings",
        f"{company_name} investor relations"
    ]
    for query in revenue_queries:
        search_results = duckduckgo_search(query, num_results=3)
        data_sources.append(f"DDG: {query}")
        revenue_candidate = _extract_currency_from_text(search_results)
        if revenue_candidate != "N/A":
            revenue = revenue_candidate
            break
    # --- Targeted search for market share ---
    market_share = "N/A"
    market_share_query = f"{company_name} market share {industry}"
    ms_results = duckduckgo_search(market_share_query, num_results=3)
    data_sources.append(f"DDG: {market_share_query}")
    ms_candidate = _extract_percentage_from_text(ms_results)
    if ms_candidate != "N/A":
        market_share = ms_candidate
    # --- LLM synthesis for qualitative fields ---
    synthesis_prompt = f"""
    Based on the following data sources, create a comprehensive analysis for {company_name} in the {industry} industry.
    General Info: {general_info}
    Features Info: {features_info}
    Pricing Info: {pricing_info}
    Website Data: {website_data}
    Return a JSON object with the following fields (fill with 'N/A' if not available):
    {{
        "name": "{company_name}",
        "pricing_model": "Brief pricing description",
        "key_features": "Main features/offerings",
        "market_position": "Market position description",
        "target_audience": "Primary target audience",
        "pricing_tiers": "List of main pricing tiers or typical price range (string)",
        "data_sources": "Number of data sources used"
    }}
    """
    try:
        analysis_str = get_llm_response(synthesis_prompt)
        analysis_str = analysis_str.strip()
        if analysis_str.startswith('```json'):
            analysis_str = analysis_str[7:-3]
        elif analysis_str.startswith('```'):
            analysis_str = analysis_str[3:-3]
        analysis = json.loads(analysis_str)
        # Insert extracted numbers
        analysis["revenue"] = revenue
        analysis["market_share"] = market_share
        analysis["data_sources"] = len(data_sources)
        return json.dumps(analysis)
    except Exception as e:
        print(f"Error in analysis: {e}")
        return json.dumps({
            "name": company_name,
            "pricing_model": "Information not available",
            "key_features": "Information not available",
            "market_position": "Information not available",
            "target_audience": "Information not available",
            "revenue": revenue,
            "market_share": market_share,
            "pricing_tiers": "N/A",
            "data_sources": len(data_sources)
        })

def collect_comprehensive_ci_data(company_name: str, industry: str) -> str:
    """
    The main data collection tool that the agent uses for each competitor.
    This combines multiple tools to get comprehensive data.
    """
    print(f"--- Collecting comprehensive data for: {company_name} ---")
    
    # Use the analysis tool to get comprehensive data
    analysis_result = analyze_competitor_data(company_name, industry)
    company_data = json.loads(analysis_result)
    
    # Save to CSV
    file_path = "coding/ci_analysis_data.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df_new_row = pd.DataFrame([company_data])
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = pd.concat([df, df_new_row], ignore_index=True)
    else:
        df = df_new_row
        
    df.to_csv(file_path, index=False)
    
    return f"Successfully collected and saved comprehensive data for {company_name}." 