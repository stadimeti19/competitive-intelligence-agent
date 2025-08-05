import os
import io
import pandas as pd
import re
from contextlib import redirect_stdout
from tools.ci_tools import (
    duckduckgo_search,
    scrape_website,
    generate_industry_competitors,
    search_company_info,
    get_company_website_data,
    analyze_competitor_data,
    collect_comprehensive_ci_data,
)
import autogen
from autogen.coding import LocalCommandLineCodeExecutor

def extract_revenue_value(revenue_str):
    """Extract numeric value from revenue string like '$31.797B' or '$31.797 billion'"""
    if pd.isna(revenue_str) or revenue_str == 'N/A':
        return None
    
    # Handle different formats
    patterns = [
        r'[\$]?([\d,]+\.?\d*)\s*[Bb]',  # $31.797B or 31.797B
        r'[\$]?([\d,]+\.?\d*)\s*billion',  # $31.797 billion
        r'[\$]?([\d,]+\.?\d*)\s*[Mm]',  # $540M
        r'[\$]?([\d,]+\.?\d*)\s*million'  # $540 million
    ]
    
    for pattern in patterns:
        match = re.search(pattern, revenue_str, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', ''))
            # Convert to billions for comparison
            if 'million' in revenue_str.lower() or 'M' in revenue_str.upper():
                value = value / 1000
            return value
    return None

def extract_market_share_value(share_str):
    """Extract numeric value from market share string like '45%' or '45.52%'"""
    if pd.isna(share_str) or share_str == 'N/A':
        return None
    
    match = re.search(r'(\d+(?:\.\d+)?)%', share_str)
    if match:
        return float(match.group(1))
    return None

def analyze_competitor_data_enhanced(df, company_input, industry):
    """Enhanced analysis of competitor data to generate specific insights"""
    
    # Extract revenue data
    revenue_data = []
    for _, row in df.iterrows():
        revenue_val = extract_revenue_value(row.get('revenue', 'N/A'))
        if revenue_val is not None:
            revenue_data.append({
                'name': row['name'],
                'revenue': revenue_val,
                'revenue_str': row.get('revenue', 'N/A')
            })
    
    # Extract market share data
    market_share_data = []
    for _, row in df.iterrows():
        share_val = extract_market_share_value(row.get('market_share', 'N/A'))
        if share_val is not None:
            market_share_data.append({
                'name': row['name'],
                'share': share_val,
                'share_str': row.get('market_share', 'N/A')
            })
    
    # Analyze pricing models
    pricing_models = df['pricing_model'].value_counts()
    
    # Analyze target audiences
    audiences = df['target_audience'].value_counts()
    
    # Generate specific key findings
    key_findings = [
        f"{company_input} operates in a highly competitive {industry} market with {len(df)} major competitors."
    ]
    
    if revenue_data:
        avg_revenue = sum(r['revenue'] for r in revenue_data) / len(revenue_data)
        top_revenue = max(revenue_data, key=lambda x: x['revenue'])
        key_findings.append(f"Revenue analysis: Average competitor revenue is ${avg_revenue:.1f}B, with {top_revenue['name']} leading at {top_revenue['revenue_str']}.")
    
    if market_share_data:
        top_share = max(market_share_data, key=lambda x: x['share'])
        key_findings.append(f"Market concentration: {top_share['name']} dominates with {top_share['share_str']} market share.")
    
    # Generate specific opportunities
    opportunities = []
    if len(pricing_models) > 1:
        opportunities.append(f"Pricing diversification: Competitors use {len(pricing_models)} different pricing approaches.")
    
    if len(audiences) > 1:
        opportunities.append(f"Market segmentation: Competitors target {len(audiences)} distinct customer segments.")
    
    opportunities.extend([
        f"Technology differentiation: Leverage {company_input}'s unique technical capabilities.",
        "Geographic expansion: Many competitors have limited global presence.",
        "Feature innovation: Identify gaps in competitor offerings."
    ])
    
    # Generate specific threats
    threats = []
    if market_share_data:
        high_share_count = len([m for m in market_share_data if m['share'] > 20])
        if high_share_count > 0:
            threats.append(f"Market concentration: {high_share_count} competitors hold significant market share (>20%).")
    
    threats.extend([
        f"Regulatory pressure: {industry} faces increasing compliance requirements.",
        "Technology disruption: Rapid innovation creates constant competitive pressure.",
        "Customer switching costs: Established competitors have strong customer lock-in."
    ])
    
    # Generate specific recommendations
    recommendations = []
    if revenue_data:
        top_revenue = max(revenue_data, key=lambda x: x['revenue'])
        recommendations.append(f"Revenue optimization: Analyze pricing strategies of top revenue generators like {top_revenue['name']}.")
    
    if market_share_data:
        top_share = max(market_share_data, key=lambda x: x['share'])
        recommendations.append(f"Market positioning: Focus on segments underserved by {top_share['name']}.")
    
    recommendations.extend([
        f"Feature differentiation: Identify unique capabilities not offered by competitors.",
        f"Partnership strategy: Explore alliances with complementary {industry} players.",
        "Technology investment: Maintain competitive advantage through innovation.",
        "Customer experience: Focus on areas where competitors underperform."
    ])
    
    # Generate market position summary
    market_position = f"{company_input} competes in the {industry} sector against {len(df)} major players. "
    if revenue_data:
        market_position += f"The competitive landscape shows revenue ranging from ${min(r['revenue'] for r in revenue_data):.1f}B to ${max(r['revenue'] for r in revenue_data):.1f}B. "
    if market_share_data:
        market_position += f"Market concentration varies significantly, with top players holding {', '.join([m['share_str'] for m in market_share_data[:2]])} market share. "
    market_position += f"Competitors use {len(pricing_models)} different pricing models and target {len(audiences)} distinct market segments, indicating opportunities for differentiation."
    
    return {
        "keyFindings": key_findings,
        "opportunities": opportunities,
        "threats": threats,
        "marketPosition": market_position,
        "recommendations": recommendations
    }

def run_ci_analysis(company_input, industry, target_audience, key_features, analysis_type):
    print(f"[CI] Starting analysis for: {company_input} in {industry}")
    # Clear old CI data before starting a new analysis
    csv_path = "coding/ci_analysis_data.csv"
    if os.path.exists(csv_path):
        print(f"[CI] Removing old CSV: {csv_path}")
        os.remove(csv_path)
    output_capture = io.StringIO()
    try:
        from tools.ci_tools import config_list
    except ImportError:
        config_list = []
    
    # Define tools for the agent
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_industry_competitors",
                "description": "Find competitors for a company or industry. Use this first to identify competitors.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "The industry to search in"},
                        "company_description": {"type": "string", "description": "Company name or description"}
                    },
                    "required": ["industry", "company_description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "collect_comprehensive_ci_data",
                "description": "Collect comprehensive data for a specific company including features, pricing, market position, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "The name of the company to analyze"},
                        "industry": {"type": "string", "description": "The industry the company operates in"}
                    },
                    "required": ["company_name", "industry"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "duckduckgo_search",
                "description": "Search the web for information using DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"},
                        "num_results": {"type": "integer", "description": "Number of results to return"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "scrape_website",
                "description": "Scrape content from a website URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to scrape"}
                    },
                    "required": ["url"]
                }
            }
        }
    ]
    
    llm_config_ci_analyst = {
        "config_list": config_list,
        "temperature": 0.1,
        "tools": tools,
    }
    ci_analyst = autogen.AssistantAgent(
        name="ci_analyst",
        llm_config=llm_config_ci_analyst,
        system_message="""You are an expert Competitive Intelligence Analyst with access to multiple specialized tools.

Your workflow should be:
1. First, use generate_industry_competitors to find competitors for the target company
2. For each competitor found, use collect_comprehensive_ci_data to gather detailed information
3. Use duckduckgo_search and scrape_website for additional research as needed

EXECUTE tools immediately when you need data. DO NOT DISCUSS - ACT.
Always call tools to get real data, never make up information.

When you have collected all the data, say "TERMINATE" to end the analysis."""
    )
    coding_work_dir = "coding"
    os.makedirs(coding_work_dir, exist_ok=True)
    data_collector = autogen.UserProxyAgent(
        name="data_collector",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        is_termination_msg=lambda x: x.get("content") and x.get("content").strip().endswith("TERMINATE"),
        code_execution_config={
            "executor": LocalCommandLineCodeExecutor(work_dir=coding_work_dir),
            "last_n_messages": 3,
        },
        function_map={
            "duckduckgo_search": duckduckgo_search,
            "scrape_website": scrape_website,
            "generate_industry_competitors": generate_industry_competitors,
            "search_company_info": search_company_info,
            "get_company_website_data": get_company_website_data,
            "analyze_competitor_data": analyze_competitor_data,
            "collect_comprehensive_ci_data": collect_comprehensive_ci_data,
        }
    )
    with redirect_stdout(output_capture):
        print(f"[CI] Initiating agent workflow...")
        try:
            conversation_result = data_collector.initiate_chat(
                ci_analyst,
                message=f"""Perform a {analysis_type} for:\nCompany Name: {company_input}\nIndustry: {industry}\nTarget Audience: {target_audience}\nKey Features: {key_features}\n\nUse the available tools to gather comprehensive data and generate a detailed report.\nStart by collecting background information, then identify competitors, and finally create a comprehensive analysis.\n""",
            )
            print(f"[CI] Agent workflow complete. Checking for CSV: {csv_path}")
        except Exception as e:
            print(f"[CI] Agent workflow error: {e}")
        summary = {
            "keyFindings": [],
            "opportunities": [],
            "threats": [],
            "marketPosition": "",
            "recommendations": []
        }
        if os.path.exists(csv_path):
            print(f"[CI] CSV found. Reading data...")
            try:
                df = pd.read_csv(csv_path)
                print(f"[CI] CSV loaded. Rows: {len(df)} Columns: {list(df.columns)}")
                if df.empty or 'name' not in df.columns:
                    print(f"[CI] CSV is empty or missing 'name' column.")
                    summary["keyFindings"] = ["Analysis complete, but no competitor data could be identified."]
                    return output_capture.getvalue(), summary
                if df['name'].str.contains('Competitor 1|Placeholder', case=False).any():
                    print(f"[CI] Placeholder data detected in CSV.")
                    summary["keyFindings"] = ["The analysis resulted in placeholder data. This can happen for very generic ideas where specific competitors could not be found via automated search. Please try a more specific query or a well-known company."]
                    return output_capture.getvalue(), summary
                
                # Use enhanced analysis
                enhanced_summary = analyze_competitor_data_enhanced(df, company_input, industry)
                summary.update(enhanced_summary)
                
            except Exception as e:
                print(f"[CI] Error reading CSV: {e}")
                summary["keyFindings"] = [f"Error reading data file: {e}"]
        else:
            print(f"[CI] CSV not found after agent run.")
            summary["keyFindings"] = ["Data file not found. Analysis may still be in progress."]
    return output_capture.getvalue(), summary 