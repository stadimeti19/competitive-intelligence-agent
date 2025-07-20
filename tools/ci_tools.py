import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import random
import os

def duckduckgo_search(query: str, num_results: int = 5) -> str:
    """Performs a DuckDuckGo web search and returns a summary of top results."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        results = []
        if data.get('Abstract'):
            results.append({
                'title': data.get('Abstract'),
                'url': data.get('AbstractURL'),
                'snippet': data.get('AbstractText')
            })
        for topic in data.get('RelatedTopics', [])[:num_results-1]:
            if isinstance(topic, dict) and topic.get('Text'):
                results.append({
                    'title': topic.get('Text', ''),
                    'url': topic.get('FirstURL', ''),
                    'snippet': topic.get('Text', '')
                })
        return str(results)
    except Exception as e:
        return f"Search error: {e}"

def get_wikipedia_info(query: str) -> str:
    """Fetches concise background information for a given entity from Wikipedia."""
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': 1
        }
        response = requests.get(search_url, params=search_params)
        data = response.json()
        if data['query']['search']:
            page_id = data['query']['search'][0]['pageid']
            content_params = {
                'action': 'query',
                'format': 'json',
                'prop': 'extracts',
                'pageids': page_id,
                'exintro': True,
                'explaintext': True
            }
            content_response = requests.get(search_url, params=content_params)
            content_data = content_response.json()
            extract = content_data['query']['pages'][str(page_id)]['extract']
            return {
                'company': query,
                'wikipedia_summary': extract[:500] + '...' if len(extract) > 500 else extract,
                'source': 'Wikipedia'
            }
        else:
            return {'company': query, 'error': 'No Wikipedia page found'}
    except Exception as e:
        return {'company': query, 'error': f'Wikipedia API error: {e}'}

def scrape_website(url: str) -> str:
    """Fetches and returns the main textual content from a given URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
        }
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        main_content = ""
        for tag in ['main', 'article', 'div[class*="content"]', 'div[class*="main"]']:
            content = soup.select_one(tag)
            if content:
                main_content = content.get_text(separator=' ', strip=True)
                break
        if not main_content:
            main_content = soup.get_text(separator=' ', strip=True)
        main_content = ' '.join(main_content.split())[:2000]
        return {
            'url': url,
            'title': soup.title.get_text() if soup.title else '',
            'content': main_content,
            'status': 'success'
        }
    except Exception as e:
        return {
            'url': url,
            'error': str(e),
            'status': 'error'
        }

def generate_industry_competitors(industry: str, company_description: str) -> str:
    """Identifies and generates a list of key competitors for a given industry and target company/idea description."""
    industry_competitors = {
        'streaming': [
            {'name': 'Netflix', 'pricing': '$8.99-$17.99', 'features': 'Original content, Global reach', 'subscribers': 220, 'revenue': 31.5},
            {'name': 'Disney+', 'pricing': '$7.99', 'features': 'Disney content, Family focus', 'subscribers': 150, 'revenue': 8.4},
            {'name': 'Amazon Prime Video', 'pricing': '$8.99', 'features': 'Prime membership, Diverse content', 'subscribers': 200, 'revenue': 35.2},
            {'name': 'HBO Max', 'pricing': '$9.99', 'features': 'HBO content, Premium quality', 'subscribers': 80, 'revenue': 5.8},
            {'name': 'Hulu', 'pricing': '$5.99-$11.99', 'features': 'TV shows, Ad-supported option', 'subscribers': 45, 'revenue': 3.2},
            {'name': 'Apple TV+', 'pricing': '$4.99', 'features': 'Apple originals, High quality', 'subscribers': 25, 'revenue': 1.8}
        ],
        'financial services': [
            {'name': 'Vanguard', 'pricing': '0.03%-0.20%', 'features': 'Low-cost index funds, Retirement planning', 'market_share': 25, 'revenue': 8.5},
            {'name': 'Charles Schwab', 'pricing': '$0-$4.95', 'features': 'Commission-free trading, Research tools', 'market_share': 20, 'revenue': 7.2},
            {'name': 'Fidelity Investments', 'pricing': '$0-$4.95', 'features': 'Low-cost funds, Retirement planning tools', 'market_share': 18, 'revenue': 6.8},
            {'name': 'T. Rowe Price', 'pricing': '0.50%-1.25%', 'features': 'Active management, Research', 'market_share': 15, 'revenue': 5.1},
            {'name': 'BlackRock', 'pricing': '0.03%-0.50%', 'features': 'iShares ETFs, Institutional', 'market_share': 12, 'revenue': 4.9}
        ]
    }
    
    if industry.lower() in industry_competitors:
        competitors = industry_competitors[industry.lower()]
    else:
        competitors = [
            {'name': f'{industry} Competitor 1', 'pricing': '$10-$50', 'features': 'Core features', 'market_share': 30, 'revenue': 1.0},
            {'name': f'{industry} Competitor 2', 'pricing': '$15-$75', 'features': 'Advanced features', 'market_share': 25, 'revenue': 0.8},
            {'name': f'{industry} Competitor 3', 'pricing': '$5-$25', 'features': 'Budget option', 'market_share': 20, 'revenue': 0.5},
            {'name': f'{industry} Competitor 4', 'pricing': '$20-$100', 'features': 'Premium features', 'market_share': 15, 'revenue': 1.2}
        ]
    return str(competitors)

def create_comprehensive_plots(df, company_name, industry, plot_path: str):
    """Create comprehensive visualization plots for CI analysis."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    if 'pricing' in df.columns:
        prices = []
        for p in df['pricing']:
            try:
                price = float(str(p).split('-')[0].replace('$', '').replace(',', ''))
                prices.append(price)
            except:
                prices.append(0)
        ax1.bar(df['name'], prices)
        ax1.set_title('Pricing Comparison')
        ax1.set_ylabel('Price ($)')
        ax1.tick_params(axis='x', rotation=45)
    if 'subscribers' in df.columns:
        ax2.pie(df['subscribers'], labels=df['name'], autopct='%1.1f%%')
        ax2.set_title('Market Share (Subscribers)')
    elif 'revenue' in df.columns:
        ax2.pie(df['revenue'], labels=df['name'], autopct='%1.1f%%')
        ax2.set_title('Market Share (Revenue)')
    feature_counts = [len(str(f).split(',')) for f in df.get('features', [])]
    ax3.bar(df['name'], feature_counts)
    ax3.set_title('Feature Count Comparison')
    ax3.set_ylabel('Number of Features')
    ax3.tick_params(axis='x', rotation=45)
    if 'subscribers' in df.columns or 'revenue' in df.columns:
        y_values = df.get('subscribers', df.get('revenue', [1]*len(df)))
        ax4.scatter(prices, y_values, s=100, alpha=0.7)
        ax4.set_xlabel('Price ($)')
        ax4.set_ylabel('Market Size')
        ax4.set_title('Competitive Positioning')
        for i, name in enumerate(df['name']):
            ax4.annotate(name, (prices[i], y_values[i]), xytext=(5, 5), textcoords='offset points')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

def collect_comprehensive_ci_data(company_name: str, industry: str) -> str:
    """Collects extensive competitive intelligence data for a given company and industry."""
    search_query = f"top competitors of {company_name} {industry}"
    search_results = duckduckgo_search(search_query)
    wiki_info = get_wikipedia_info(company_name)
    competitors = generate_industry_competitors(industry, company_name)
    df = pd.DataFrame(eval(competitors))
    
    # Save to coding directory
    csv_path = 'coding/ci_analysis_data.csv'
    plot_path = 'coding/ci_analysis_plot.png'
    
    # Ensure coding directory exists
    os.makedirs('coding', exist_ok=True)
    
    df.to_csv(csv_path, index=False)
    create_comprehensive_plots(df, company_name, industry, plot_path)
    
    return {
        'company': company_name,
        'industry': industry,
        'search_results': search_results,
        'wikipedia_info': wiki_info,
        'competitors': competitors
    } 