import autogen
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
import openai

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
    Finds real competitors for a company or idea using web search only.
    NO HARDCODED COMPETITORS OR LLM-ONLY FALLBACKS ALLOWED.
    Returns a JSON array of competitor names.
    """
    print(f"--- Finding competitors for: '{company_description}' in '{industry}' ---")
    query = f"top competitors of {company_description} in {industry} industry"
    try:
        # Use DuckDuckGo search for real competitors
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=10)]
        # Extract company names from titles/snippets using regex or simple parsing
        import re
        competitors = set()
        for r in results:
            # Try to extract company names from title and body
            text = (r.get('title', '') + ' ' + r.get('body', ''))
            # Look for patterns like "X, Y, Z, and W" or lists
            found = re.findall(r'([A-Z][A-Za-z0-9&\-. ]{2,})', text)
            # Filter out the original company and generic words
            for name in found:
                name_clean = name.strip().replace('\n', '').replace('\r', '')
                if (name_clean.lower() not in company_description.lower()
                    and name_clean.lower() not in industry.lower()
                    and len(name_clean) > 2
                    and not name_clean.lower().startswith('top ')
                    and not name_clean.lower().startswith('best ')
                    and not name_clean.lower().startswith('competitors')):
                    competitors.add(name_clean)
        # Return up to 8 unique competitors
        competitors_list = list(competitors)[:8]
        print(f"--- Found competitors: {competitors_list} ---")
        return json.dumps(competitors_list)
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

def analyze_competitor_data(company_name: str, industry: str) -> str:
    """
    Comprehensive analysis tool that combines multiple data sources.
    The agent can use this to get a complete picture of a competitor.
    """
    print(f"--- Analyzing data for: {company_name} ---")
    
    # Get multiple data sources
    general_info = json.loads(search_company_info(company_name, "general"))
    features_info = json.loads(search_company_info(company_name, "features"))
    pricing_info = json.loads(search_company_info(company_name, "pricing"))
    website_data = json.loads(get_company_website_data(company_name))
    
    # Use GPT to synthesize the data
    synthesis_prompt = f"""
    Based on the following data sources, create a comprehensive analysis for {company_name} in the {industry} industry.
    
    General Info: {general_info}
    Features Info: {features_info}
    Pricing Info: {pricing_info}
    Website Data: {website_data}
    
    Return a JSON object with:
    {{
        "name": "{company_name}",
        "pricing_model": "Brief pricing description",
        "key_features": "Main features/offerings",
        "market_position": "Market position description",
        "target_audience": "Primary target audience",
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
        return json.dumps(analysis)
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        return json.dumps({
            "name": company_name,
            "pricing_model": "Information not available",
            "key_features": "Information not available",
            "market_position": "Information not available",
            "target_audience": "Information not available",
            "data_sources": 0
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