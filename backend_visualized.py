import os
import io
import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
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

def create_revenue_chart(revenue_data, company_input, industry):
    if not revenue_data:
        return None
    
    try:
        # Filter out very small values to make the chart more readable
        max_revenue = max(r['revenue'] for r in revenue_data)
        min_threshold = max_revenue * 0.001  # Only show companies with at least 0.1% of max revenue
        
        filtered_data = [r for r in revenue_data if r['revenue'] >= min_threshold]
        
        if len(filtered_data) < 2:
            return None
        
        plt.figure(figsize=(12, 6))
        names = [r['name'] for r in filtered_data]
        revenues = [r['revenue'] for r in filtered_data]
        
        # Use logarithmic scale for better visualization
        plt.yscale('log')
        
        bars = plt.bar(range(len(names)), revenues, color='skyblue', edgecolor='navy', alpha=0.7)
        for i, name in enumerate(names):
            if company_input.lower() in name.lower():
                bars[i].set_color('orange')
                bars[i].set_alpha(0.9)
        
        plt.title(f'Revenue Comparison - {industry} Market (Log Scale)', fontsize=16, fontweight='bold')
        plt.xlabel('Companies', fontsize=12)
        plt.ylabel('Revenue (Billions USD, Log Scale)', fontsize=12)
        plt.xticks(range(len(names)), names, rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, revenue in enumerate(revenues):
            if revenue >= 1:  # Show as billions
                label = f'${revenue:.1f}B'
            elif revenue >= 0.001:  # Show as millions
                label = f'${revenue*1000:.1f}M'
            else:  # Show as thousands
                label = f'${revenue*1000000:.1f}K'
            
            plt.text(i, revenue * 1.1, label, ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        plt.subplots_adjust(bottom=0.22, top=0.92)
        plt.savefig('coding/revenue_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        return 'coding/revenue_comparison.png'
        
    except Exception as e:
        print(f"[CI] Error generating revenue chart: {e}")
        return None

def create_market_share_chart(market_share_data, company_input, industry):
    if not market_share_data:
        return None
    plt.figure(figsize=(10, 8))
    names = [m['name'] for m in market_share_data]
    shares = [m['share'] for m in market_share_data]
    colors = plt.cm.Set3(np.linspace(0, 1, len(names)))
    wedges, texts, autotexts = plt.pie(shares, labels=names, autopct='%1.1f%%', colors=colors, startangle=90)
    for i, name in enumerate(names):
        if company_input.lower() in name.lower():
            wedges[i].set_alpha(0.8)
            wedges[i].set_linewidth(3)
    plt.title(f'Market Share Distribution - {industry}', fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.subplots_adjust(top=0.92)
    plt.savefig('coding/market_share.png', dpi=300, bbox_inches='tight')
    plt.close()
    return 'coding/market_share.png'

def create_pricing_model_chart(df, company_input, industry):
    pricing_counts = df['pricing_model'].value_counts()
    if len(pricing_counts) == 0:
        return None
    plt.figure(figsize=(12, 6))
    models = pricing_counts.index
    counts = pricing_counts.values
    bars = plt.bar(range(len(models)), counts, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
    plt.title(f'Pricing Model Distribution - {industry}', fontsize=16, fontweight='bold')
    plt.xlabel('Pricing Models', fontsize=12)
    plt.ylabel('Number of Companies', fontsize=12)
    plt.xticks(range(len(models)), models, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    for i, count in enumerate(counts):
        plt.text(i, count + 0.1, str(count), ha='center', va='bottom', fontweight='bold')
    plt.subplots_adjust(bottom=0.22, top=0.9)
    plt.savefig('coding/pricing_models.png', dpi=300, bbox_inches='tight')
    plt.close()
    return 'coding/pricing_models.png'

FEATURE_DEFINITIONS = [
    ("AI / Machine Learning", ["ai", "artificial intelligence", "machine learning", "ml", "predictive", "generative ai", "ai agents"]),
    ("Automation", ["automation", "automated", "workflow automation", "business process automation", "automated workflows"]),
    ("Analytics / Reporting", ["analytics", "reporting", "dashboard", "insights", "business intelligence", "performance reporting"]),
    ("Mobile App", ["mobile app", "ios app", "android app", "mobile platform", "mobile access"]),
    ("Online Dashboard / Portal", ["web dashboard", "online dashboard", "online portal", "client portal", "web platform", "self-service portal"]),
    ("API / Integrations", ["api", "developer api", "integration", "integrations", "connectors", "third-party connectors", "webhooks"]),
    ("Security", ["security", "encryption", "sso", "single sign-on", "mfa", "multi-factor authentication", "2fa", "access control"]),
    ("Compliance / Risk", ["compliance", "risk management", "regulatory", "audit", "governance", "supervision"]),
    ("Admin Controls", ["admin controls", "administration", "permissions", "roles", "user management", "policy management"]),
    ("Collaboration", ["collaboration", "team collaboration", "shared workspace", "comments", "mentions"]),
    ("Communication / Messaging", ["messaging", "chat", "team communication", "instant messaging", "video conferencing", "calling", "meetings"]),
    ("Document / File Sharing", ["file sharing", "document sharing", "docs", "knowledge base", "content management"]),
    ("Task / Project Management", ["task management", "project management", "kanban", "to-do", "work management", "deadline", "roadmap"]),
    ("Workflow Management", ["workflow", "workflow management", "process management", "approval workflow", "business process"]),
    ("Customer Support", ["customer support", "support ticket", "help desk", "live chat", "service desk", "customer service"]),
    ("CRM / Sales", ["crm", "sales pipeline", "lead management", "sales automation", "contact management"]),
    ("Marketing", ["marketing automation", "campaign", "email marketing", "ads", "seo", "content marketing"]),
    ("E-commerce", ["e-commerce", "ecommerce", "online store", "checkout", "cart", "marketplace"]),
    ("Payments", ["payment processing", "online payments", "instant payments", "settlement", "billing", "invoicing"]),
    ("Subscription / Billing", ["subscription", "recurring billing", "billing", "pricing tiers", "usage-based pricing"]),
    ("Inventory / Operations", ["inventory", "stock auditing", "supply chain", "operations", "asset management", "field service"]),
    ("HR / People", ["hr", "human resources", "employee", "payroll", "recruiting", "onboarding", "workforce"]),
    ("Education / Learning", ["education", "learning management", "lms", "courses", "training", "students"]),
    ("Healthcare", ["healthcare", "clinical", "patient", "ehr", "emr", "medical", "care management"]),
    ("Developer Tools", ["developer tools", "devtools", "sdk", "cli", "code", "deployment", "developer platform"]),
    ("Data Platform", ["data platform", "data warehouse", "data lake", "etl", "data pipeline", "database"]),
    ("Cloud / Infrastructure", ["cloud", "infrastructure", "hosting", "kubernetes", "serverless", "devops"]),
    ("Open Source / Self Hosted", ["open-source", "open source", "self-hosted", "self hosted", "on-premise", "on premise"]),
    ("Enterprise Features", ["enterprise", "enterprise-grade", "scalable", "governance", "sla", "dedicated support"]),
    ("Investment Management", ["investment management", "asset management", "managed portfolio", "portfolio management"]),
    ("Brokerage / Trading", ["brokerage", "stock trading", "trading platform", "trade stocks", "securities trading", "self-directed investing"]),
    ("Retirement Planning", ["retirement", "401k", "401 k", "ira", "pension", "retirement account"]),
    ("Wealth Advisory", ["wealth management", "financial advisor", "financial advisory", "advisory services", "advisor network"]),
    ("Mutual Funds", ["mutual fund", "mutual funds", "fund family"]),
    ("ETFs", ["etf", "exchange traded fund", "exchange-traded fund"]),
    ("Research & Market Data", ["research", "market data", "analyst research", "investment research", "screeners"]),
    ("Financial Planning Tools", ["financial planning", "planning tools", "goal planning", "retirement calculator", "portfolio analysis"]),
    ("Mobile App", ["mobile app", "ios app", "android app", "mobile investing", "mobile banking"]),
    ("Online Dashboard / Portal", ["web dashboard", "online dashboard", "online portal", "client portal", "web platform", "online account"]),
    ("Tax Planning", ["tax planning", "tax optimization", "tax-loss harvesting", "tax loss harvesting"]),
    ("Cash Management", ["cash management", "sweep account", "money market", "banking services"]),
    ("Banking", ["banking", "bank account", "checking account", "savings account"]),
    ("Credit Cards", ["credit card", "credit cards"]),
    ("Fraud Protection", ["fraud protection", "fraud detection", "fraud monitoring", "account protection"]),
    ("Cryptocurrency", ["cryptocurrency", "crypto", "digital assets", "bitcoin"]),
]

GENERIC_FEATURE_WORDS = {
    "features",
    "platform",
    "solution",
    "services",
    "products",
    "capabilities",
    "support",
    "including",
    "include",
    "offers",
    "provides",
    "strong",
    "broad",
    "advanced",
    "enterprise",
}


def _normalize_feature_text(value):
    value = "" if value is None or pd.isna(value) else str(value)
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _feature_status(text, terms):
    if not text or text == "n a" or "information not available" in text:
        return 0.5
    normalized_terms = [_normalize_feature_text(t) for t in terms]
    if any(term and term in text for term in normalized_terms):
        return 1.0
    for term in normalized_terms:
        if not term:
            continue
        negative_patterns = [
            f"no {term}",
            f"without {term}",
            f"does not offer {term}",
            f"not offer {term}",
            f"{term} not available",
            f"{term} unavailable",
        ]
        if any(p in text for p in negative_patterns):
            return 0.0
    return 0.5


def _title_case_feature(value):
    return " ".join(word.capitalize() for word in value.split())


def _dynamic_feature_definitions(df):
    chunks = []
    for _, row in df.iterrows():
        source = " ".join(str(row.get(col, "")) for col in ["key_features", "market_position"])
        chunks.extend(re.split(r"[.;:|()\n]+|,\s+|\s+plus\s+|\s+and\s+", source, flags=re.I))

    counts = {}
    for chunk in chunks:
        words = [
            word
            for word in _normalize_feature_text(chunk).split()
            if word not in GENERIC_FEATURE_WORDS
        ]
        if len(words) < 2 or len(words) > 5:
            continue
        phrase = " ".join(words)
        if len(phrase) < 8 or len(phrase) > 60:
            continue
        counts[phrase] = counts.get(phrase, 0) + 1

    existing_terms = {_normalize_feature_text(term) for _, terms in FEATURE_DEFINITIONS for term in terms}
    ranked = sorted(
        ((phrase, count) for phrase, count in counts.items() if count >= 2 and phrase not in existing_terms),
        key=lambda item: (-item[1], item[0]),
    )
    return [(_title_case_feature(phrase), [phrase]) for phrase, _ in ranked[:10]]


def create_feature_matrix_chart(df, company_input, industry):
    competitor_names = []
    company_texts = []
    for _, row in df.iterrows():
        competitor_names.append(str(row.get('name', 'Unknown')))
        company_texts.append(
            _normalize_feature_text(
                " ".join(
                    str(row.get(col, ""))
                    for col in [
                        "key_features",
                        "market_position",
                        "target_audience",
                        "pricing_model",
                        "pricing_tiers",
                    ]
                )
            )
        )

    feature_definitions = FEATURE_DEFINITIONS + _dynamic_feature_definitions(df)
    active_features = []
    feature_matrix = []
    for label, terms in feature_definitions:
        feature_row = []
        for text in company_texts:
            feature_row.append(_feature_status(text, terms))
        if any(v != 0.5 for v in feature_row):
            active_features.append(label)
            feature_matrix.append(feature_row)

    if not feature_matrix:
        return None

    matrix = np.array(feature_matrix).T
    plt.figure(figsize=(max(12, len(active_features) * 0.65), max(7, len(competitor_names) * 0.55)))
    cmap = mcolors.ListedColormap(["#ef4444", "#d1d5db", "#22c55e"])
    bounds = [-0.25, 0.25, 0.75, 1.25]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    im = plt.imshow(matrix, cmap=cmap, norm=norm, aspect='auto')
    plt.xticks(range(len(active_features)), active_features, rotation=45, ha='right')
    plt.yticks(range(len(competitor_names)), competitor_names)
    cbar = plt.colorbar(im, ticks=[0, 0.5, 1])
    cbar.set_ticklabels(['Explicitly Unavailable', 'Not Found in Sources', 'Available'])
    plt.title(f'Feature Availability Matrix - {industry}', fontsize=16, fontweight='bold')
    plt.subplots_adjust(left=0.12, right=0.92, bottom=0.2, top=0.92)
    plt.savefig('coding/feature_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    return 'coding/feature_matrix.png'

def extract_revenue_value(revenue_str):
    if not isinstance(revenue_str, str):
        return None
    
    revenue_str = revenue_str.lower().strip()
    
    # Handle different formats
    try:
        # Remove common prefixes and clean up
        clean_str = revenue_str.replace('$', '').replace(',', '').replace(' ', '')
        
        # Handle billion formats
        if 'billion' in revenue_str or 'b' in revenue_str:
            # Extract the number before 'b' or 'billion'
            if 'billion' in revenue_str:
                num_str = revenue_str.split('billion')[0].replace('$', '').replace(',', '').strip()
            else:
                num_str = revenue_str.split('b')[0].replace('$', '').replace(',', '').strip()
            return float(num_str) * 1000
        
        # Handle million formats
        elif 'million' in revenue_str or 'm' in revenue_str:
            if 'million' in revenue_str:
                num_str = revenue_str.split('million')[0].replace('$', '').replace(',', '').strip()
            else:
                num_str = revenue_str.split('m')[0].replace('$', '').replace(',', '').strip()
            return float(num_str) / 1000
        
        # Handle trillion formats
        elif 'trillion' in revenue_str or 't' in revenue_str:
            if 'trillion' in revenue_str:
                num_str = revenue_str.split('trillion')[0].replace('$', '').replace(',', '').strip()
            else:
                num_str = revenue_str.split('t')[0].replace('$', '').replace(',', '').strip()
            return float(num_str) * 1000000
        
        # Try to parse as a plain number (assume billions if large)
        else:
            num = float(clean_str)
            if num > 1000:  # Assume it's already in millions
                return num / 1000
            else:
                return num
                
    except (ValueError, AttributeError):
        return None
    
    return None

def extract_market_share_value(market_share_str):
    if isinstance(market_share_str, str):
        market_share_str = market_share_str.lower()
        if '%' in market_share_str:
            try:
                return float(market_share_str.replace('%', '').replace(',', '')) / 100
            except ValueError:
                pass
        elif 'share' in market_share_str:
            try:
                return float(market_share_str.replace('share', '').replace(',', '')) / 100
            except ValueError:
                pass
    return None

# Rename the original function
def _original_analyze_competitor_data_enhanced(df, company_input, industry):
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

def analyze_competitor_data_enhanced(df, company_input, industry):
    summary = _original_analyze_competitor_data_enhanced(df, company_input, industry)
    # Generate visualizations
    revenue_data = []
    for _, row in df.iterrows():
        raw_revenue = row.get('revenue', 'N/A')
        revenue_val = extract_revenue_value(raw_revenue)
        if revenue_val is not None:
            revenue_data.append({'name': row['name'], 'revenue': revenue_val})
    market_share_data = []
    for _, row in df.iterrows():
        share_val = extract_market_share_value(row.get('market_share', 'N/A'))
        if share_val is not None:
            market_share_data.append({'name': row['name'], 'share': share_val})
    
    charts = {}
    try:
        if revenue_data:
            charts['revenue'] = create_revenue_chart(revenue_data, company_input, industry)
    except Exception as e:
        print(f"[CI] Error generating revenue chart: {e}")
    
    try:
        if market_share_data:
            charts['market_share'] = create_market_share_chart(market_share_data, company_input, industry)
    except Exception as e:
        print(f"[CI] Error generating market share chart: {e}")
    
    try:
        charts['pricing_models'] = create_pricing_model_chart(df, company_input, industry)
    except Exception as e:
        print(f"[CI] Error generating pricing models chart: {e}")
    
    try:
        charts['feature_matrix'] = create_feature_matrix_chart(df, company_input, industry)
    except Exception as e:
        print(f"[CI] Error generating feature matrix chart: {e}")
    
    summary['charts'] = charts
    return summary

def run_ci_analysis(company_input, industry, target_audience, key_features, analysis_type):
    print(f"[CI] Starting analysis for: {company_input} in {industry}")
    # Clear old CI data before starting a new analysis
    csv_path = "coding/ci_analysis_data.csv"
    if os.path.exists(csv_path):
        print(f"[CI] Removing old CSV: {csv_path}")
        os.remove(csv_path)
    
    # Clear old chart files
    chart_files = ['coding/revenue_comparison.png', 'coding/market_share.png', 
                   'coding/pricing_models.png', 'coding/feature_matrix.png']
    for chart_file in chart_files:
        if os.path.exists(chart_file):
            os.remove(chart_file)
    
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
            "recommendations": [],
            "charts": {}
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
                
                # Use enhanced analysis with charts
                enhanced_summary = analyze_competitor_data_enhanced(df, company_input, industry)
                summary.update(enhanced_summary)
                
            except Exception as e:
                print(f"[CI] Error reading CSV: {e}")
                error_msg = str(e).replace('$', 'USD ').replace('^', '').replace('ParseException:', '').replace('USD ', 'USD ')
                summary["keyFindings"] = [f"Error reading data file: {error_msg}"]
                # Generate charts even if there's an error
                try:
                    enhanced_summary = analyze_competitor_data_enhanced(df, company_input, industry)
                    summary.update(enhanced_summary)
                except Exception as chart_error:
                    print(f"[CI] Error generating charts: {chart_error}")
                    summary["charts"] = {}
        else:
            print(f"[CI] CSV not found after agent run.")
            summary["keyFindings"] = ["Data file not found. Analysis may still be in progress."]
    return output_capture.getvalue(), summary
