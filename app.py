import autogen
from autogen.coding import LocalCommandLineCodeExecutor
from datetime import date, datetime, timedelta
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import io
from io import StringIO
import os
import streamlit as st
import base64
from contextlib import redirect_stdout
import requests
from bs4 import BeautifulSoup
import json
import sys
import warnings
from dotenv import load_dotenv
load_dotenv()

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Import tool functions
from tools.ci_tools import (
    duckduckgo_search,
    scrape_website,
    generate_industry_competitors,
    search_company_info,
    get_company_website_data,
    analyze_competitor_data,
    collect_comprehensive_ci_data,
    playwright_scrape
)

# Add this utility function near the top (after imports)
def safe_display(val):
    import pandas as pd
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "n/a":
        return "N/A"
    return val

# autogen configuration - using newer API
try:
    llm_config = autogen.LLMConfig.from_json(path="OAI_CONFIG_LIST")
    config_list = llm_config.config_list
except FileNotFoundError:
    st.error("Error: OAI_CONFIG_LIST file not found. Please create it in the project root with your OpenAI API key.")
    st.stop()
except ValueError as e:
    st.error(f"Error loading OAI_CONFIG_LIST: {e}. Check your JSON format.")
    st.stop()

# Define tools for the AssistantAgent
llm_config_ci_analyst = {
        "config_list": config_list,
    "temperature": 0.1,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "generate_industry_competitors",
                "description": "Identifies relevant competitors for any company or idea using GPT knowledge. Use this FIRST to get a list of competitors.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "The industry to search for competitors in."},
                        "company_description": {"type": "string", "description": "A brief description of the company or idea to find similar competitors for."},
                    },
                    "required": ["industry", "company_description"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_company_info",
                "description": "Performs web search to find specific information about a company. Use for real-time data about competitors.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "The name of the company to search for."},
                        "query_type": {"type": "string", "description": "Type of info to search: 'general', 'features', 'pricing', or 'market'."},
                    },
                    "required": ["company_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_company_website_data",
                "description": "Finds and scrapes the company's official website for current information. Use for detailed company data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "The name of the company to get website data for."},
                    },
                    "required": ["company_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_competitor_data",
                "description": "Comprehensive analysis tool that combines multiple data sources for a complete picture of a competitor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "The name of the competitor to analyze."},
                        "industry": {"type": "string", "description": "The industry context for the analysis."},
                    },
                    "required": ["company_name", "industry"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "collect_comprehensive_ci_data",
                "description": "Main data collection tool that saves competitor data to CSV. Use this for each competitor after analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "The name of the competitor to collect data for."},
                        "industry": {"type": "string", "description": "The industry of the company."},
                    },
                    "required": ["company_name", "industry"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "duckduckgo_search",
                "description": "General web search tool. Use for finding news, articles, or specific information about companies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."},
                        "num_results": {"type": "integer", "description": "Number of results to return."},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scrape_website",
                "description": "Scrapes content from a specific URL. Use after finding relevant URLs via search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The full URL to scrape."},
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "playwright_scrape",
                "description": "Uses Playwright to fetch the fully rendered HTML of a page (for JavaScript-heavy sites). Returns the page content as text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The full URL to scrape using Playwright."},
                    },
                    "required": ["url"],
                },
            },
        },
    ],
}

# CI specialized agents with proper tool configuration
ci_analyst = autogen.AssistantAgent(
    name="ci_analyst",
    llm_config=llm_config_ci_analyst,
    system_message="""You are an expert Competitive Intelligence Analyst with access to multiple specialized tools.

    **TOOL SELECTION STRATEGY:**
    
    1. **Competitor Identification**: Use `generate_industry_competitors` to get a list of relevant competitors
    2. **Data Collection Options**:
       - Use `search_company_info` for quick, specific data (pricing, features, etc.)
       - Use `get_company_website_data` for detailed company information
       - Use `analyze_competitor_data` for comprehensive analysis combining multiple sources
       - Use `duckduckgo_search` for general research and news
       - Use `scrape_website` for specific URLs you find
    3. **Data Storage**: Use `collect_comprehensive_ci_data` to save analyzed data to CSV

    **WORKFLOW:**
    1. **Start**: Use `generate_industry_competitors` to identify competitors
    2. **For each competitor**: Choose appropriate tools based on what you need:
       - Quick info → `search_company_info`
       - Detailed analysis → `analyze_competitor_data`
       - Website data → `get_company_website_data`
    3. **Save results**: Use `collect_comprehensive_ci_data` to save data
    4. **Terminate**: End with "TERMINATE"

    **INTELLIGENT DECISIONS:**
    - Use `search_company_info` with different query_types (general, features, pricing, market)
    - Combine multiple tools for comprehensive analysis
    - Choose tools based on the type of information you need
    - Always save data with `collect_comprehensive_ci_data` after analysis

    Execute tools immediately and make intelligent choices about which tools to use for each task.
    """
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
        "playwright_scrape": playwright_scrape,
    }
)

# method to run CI analysis
def run_ci_analysis(company_input, industry, target_audience, key_features, analysis_type):
    # Clear old CI data before starting a new analysis
    csv_path = "coding/ci_analysis_data.csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)
    output_capture = io.StringIO() 
    with redirect_stdout(output_capture):
        # Initiate the conversation with the CI analyst
        conversation_result = data_collector.initiate_chat(
            ci_analyst,
            message=f"""Perform a {analysis_type} for:
            Company Name: {company_input}
            Industry: {industry}
            Target Audience: {target_audience}
            Key Features: {key_features}
            
            Use the available tools to gather comprehensive data and generate a detailed report.
            Start by collecting background information, then identify competitors, and finally create a comprehensive analysis.
            """,
        )
        
        # Generate report from collected data
        report_summary = "No data available for analysis."
        csv_path = "coding/ci_analysis_data.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)

                # ---- NEW: Add this validation block ----
                if df.empty or 'name' not in df.columns:
                    report_summary = "Analysis complete, but no competitor data could be identified."
                    st.session_state.key_findings = "No competitor data was found for the given query."
                    st.session_state.competitor_matrix = pd.DataFrame()
                    return output_capture.getvalue(), report_summary

                # Heuristic to check for placeholder data
                if df['name'].str.contains('Competitor 1|Placeholder', case=False).any():
                    report_summary = "The analysis resulted in placeholder data. This can happen for very generic ideas where specific competitors could not be found via automated search. Please try a more specific query or a well-known company."
                    st.session_state.key_findings = "Analysis found only placeholder data."
                    st.session_state.competitor_matrix = pd.DataFrame()
                    return output_capture.getvalue(), report_summary
                # ---- END of new validation block ----

                # Populate session state with actual data
                st.session_state.key_findings = f"""
                - **Market Position**: {company_input} competes with {len(df)} major competitors
                - **Top Competitors**: {', '.join(df['name'].head(3).tolist())}
                - **Market Dynamics**: Analysis shows competitive landscape in {industry}
                """

                # Revenue range handling
                if 'revenue' in df.columns and pd.api.types.is_numeric_dtype(df['revenue']):
                    min_revenue = df['revenue'].min()
                    max_revenue = df['revenue'].max()
                else:
                    min_revenue = max_revenue = 0
                st.session_state.key_findings += f"- **Revenue Range**: ${min_revenue:.1f}B - ${max_revenue:.1f}B\n"
                
                st.session_state.competitor_matrix = df
                
                # Handle missing columns gracefully
                market_share_col = 'market_share' if 'market_share' in df.columns else None
                if 'pricing' in df.columns:
                    pricing_col = 'pricing'
                elif 'features' in df.columns:
                    pricing_col = 'features'
                else:
                    pricing_col = None

                st.session_state.market_positioning = f"""
                **Market Share Analysis:**
                - {safe_display(df.iloc[0]['name'])}: {safe_display(df.iloc[0].get(market_share_col, 'N/A'))}% market share
                - {safe_display(df.iloc[1]['name'])}: {safe_display(df.iloc[1].get(market_share_col, 'N/A'))}% market share  
                - {safe_display(df.iloc[2]['name'])}: {safe_display(df.iloc[2].get(market_share_col, 'N/A'))}% market share
                
                **Pricing Strategy:**
                - {safe_display(df.iloc[0]['name'])}: {safe_display(df.iloc[0][pricing_col] if pricing_col and pricing_col in df.columns else 'N/A')}
                - {safe_display(df.iloc[1]['name'])}: {safe_display(df.iloc[1][pricing_col] if pricing_col and pricing_col in df.columns else 'N/A')}
                - {safe_display(df.iloc[2]['name'])}: {safe_display(df.iloc[2][pricing_col] if pricing_col and pricing_col in df.columns else 'N/A')}
                """
                
                st.session_state.recommendations = f"""
                **Strategic Recommendations for {company_input}:**
                
                1. **Competitive Pricing**: Analyze pricing strategies of {df.iloc[0]['name']} and {df.iloc[1]['name']}
                2. **Feature Differentiation**: Focus on unique features not offered by competitors
                3. **Market Expansion**: Target underserved segments in {industry}
                4. **Technology Investment**: Leverage technology to improve customer experience
                5. **Partnership Opportunities**: Consider strategic partnerships in {industry}
                """
                
                report_summary = f"""# Competitive Intelligence Report for {company_input}

## Executive Summary
Comprehensive analysis of {company_input} in the {industry} industry.

## Key Findings
- **Market Position**: {company_input} competes with {len(df)} major competitors
- **Top Competitors**: {', '.join(df['name'].head(3).tolist())}
- **Market Dynamics**: Analysis shows competitive landscape in {industry}

## Recommendations
Based on the collected data, strategic recommendations have been generated for {company_input}.
"""
            except Exception as e:
                report_summary = f"Error reading data file: {e}"
        else:
            report_summary = "Data file not found. Analysis may still be in progress."

    # Remove old plot if it exists
    plot_path = "coding/ci_analysis_plot.png"
    if os.path.exists(plot_path):
        os.remove(plot_path)

    # Generate and save updated plot for revenue and market share
    if not df.empty and 'name' in df.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        plotted = False
        # Revenue Bar Chart
        if 'revenue' in df.columns and df['revenue'].apply(lambda x: str(x).replace('.', '', 1).isdigit()).any():
            df_plot = df[df['revenue'].apply(lambda x: str(x).replace('.', '', 1).isdigit())]
            if not df_plot.empty:
                df_plot.loc[:, 'revenue'] = df_plot['revenue'].astype(float)
                ax.bar(df_plot['name'], df_plot['revenue'], color='skyblue')
                ax.set_title('Competitor Revenue Comparison')
                ax.set_ylabel('Revenue (USD)')
                ax.set_xticklabels(df_plot['name'], rotation=30, ha='right')
                plotted = True
        # Market Share Pie Chart (if revenue not available or as second plot)
        if not plotted and 'market_share' in df.columns and df['market_share'].apply(lambda x: str(x).replace('.', '', 1).isdigit()).any():
            df_share = df[df['market_share'].apply(lambda x: str(x).replace('.', '', 1).isdigit())]
            if not df_share.empty:
                df_share.loc[:, 'market_share'] = df_share['market_share'].astype(float)
                ax.pie(df_share['market_share'], labels=df_share['name'], autopct='%1.1f%%')
                ax.set_title('Market Share Distribution')
                plotted = True
        if plotted:
            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close(fig)

    return output_capture.getvalue(), report_summary

# --- streamlit UI ---
st.set_page_config(layout="wide")

st.title("Competitive Intelligence Assistant")
st.markdown("""
Perform comprehensive competitive intelligence analysis:
1. Research and identify competitors for your company or idea
2. Analyze competitor features, pricing, and market positioning
3. Generate detailed reports with strategic insights and recommendations
""")

# improved input section
st.subheader("Competitive Intelligence Analysis")

# fields for input for CI analysis
company_name = st.text_input("Company Name or Idea Description", 
                           placeholder="e.g., Netflix, or 'AI-powered meal planning app'")

col1, col2, col3 = st.columns(3)
industry = col1.text_input("Industry", placeholder="e.g., SaaS, E-commerce, FinTech")
target_audience = col2.text_input("Target Audience", placeholder="e.g., Small Businesses, Gen Z, Enterprise")
key_features = col3.text_input("Key Features", placeholder="e.g., Video streaming, AI recommendations")

analysis_type = st.selectbox("Analysis Type", 
                           ["Competitor Analysis", "Market Research", "SWOT Analysis", "Full CI Report"])

# initialize chat history and CI report content in session state for persistence across reruns
if "chat_log" not in st.session_state:
    st.session_state.chat_log = "Click 'Run CI Analysis' to start the process.\n"
if "ci_report_content" not in st.session_state:
    st.session_state.ci_report_content = "CI report will appear here after generation."

st.subheader("Agent Conversation Log")
# display log in a non-editable text area
st.text_area("Live Log", st.session_state.chat_log, height=400, disabled=True, key="log_display")

# button to trigger the process
if st.button("Run CI Analysis", key="run_button"):
    if not company_name:
        st.error("Please enter a company name or idea description.")
    else:
        st.session_state.chat_log = "--- Starting CI Analysis Process ---\n"
    
        # run the CI analysis and capture output
        full_log_output, ci_final_content = run_ci_analysis(
            company_name,
            industry,
            target_audience,
            key_features,
            analysis_type
        )
        
        st.session_state.chat_log = full_log_output
        st.session_state.ci_report_content = ci_final_content
        st.rerun()

# improved output sections
st.subheader("Competitive Intelligence Report")
st.markdown(st.session_state.ci_report_content)

# Add visualizations for revenue and market share if available
st.subheader("Competitor Analysis")
csv_path = "coding/ci_analysis_data.csv"
if os.path.exists(csv_path):
    try:
        df = pd.read_csv(csv_path)
        st.dataframe(df)
        # Revenue Bar Chart
        if "revenue" in df.columns and df["revenue"].apply(lambda x: str(x).replace('.', '', 1).isdigit()).any():
            st.markdown("**Revenue Comparison (USD, as reported):**")
            df_revenue = df[df["revenue"].apply(lambda x: str(x).replace('.', '', 1).isdigit())]
            df_revenue.loc[:, 'revenue'] = df_revenue['revenue'].astype(float)
            st.bar_chart(df_revenue.set_index("name")["revenue"])
        # Market Share Pie Chart
        if "market_share" in df.columns and df["market_share"].apply(lambda x: str(x).replace('.', '', 1).isdigit()).any():
            st.markdown("**Market Share Distribution (%):**")
            df_share = df[df["market_share"].apply(lambda x: str(x).replace('.', '', 1).isdigit())]
            df_share.loc[:, 'market_share'] = df_share['market_share'].astype(float)
            st.pyplot(
                plt.figure(figsize=(6, 3))
            )
            plt.pie(df_share["market_share"], labels=df_share["name"], autopct="%1.1f%%")
            plt.title("Market Share Distribution")
            st.pyplot(plt)
        # Pricing Tiers Table
        if "pricing_tiers" in df.columns:
            st.markdown("**Pricing Tiers:**")
            st.dataframe(df[["name", "pricing_tiers"]])
    except Exception as e:
        st.error(f"Error loading competitor data: {e}")
else:
    st.info("Competitor data will appear here after analysis.")

# add new sections for better organization
col1, col2 = st.columns(2)

with col1:
    st.subheader("Key Findings")
    if "key_findings" in st.session_state:
        st.markdown(st.session_state.key_findings)
    else:
        st.info("Key findings will appear here after analysis.")
    
    st.subheader("Competitor Matrix")
    if "competitor_matrix" in st.session_state:
        st.dataframe(st.session_state.competitor_matrix)
    else:
        st.info("Competitor matrix will appear here after analysis.")

with col2:
    st.subheader("Market Positioning")
    if "market_positioning" in st.session_state:
        st.markdown(st.session_state.market_positioning)
    else:
        st.info("Market positioning analysis will appear here after analysis.")
    
    st.subheader("Strategic Recommendations")
    if "recommendations" in st.session_state:
        st.markdown(st.session_state.recommendations)
    else:
        st.info("Strategic recommendations will appear here after analysis.")

st.subheader("Generated Files")
col1, col2 = st.columns(2)

# display CI Analysis Image
image_path = "coding/ci_analysis_plot.png"
if os.path.exists(image_path):
    try:
        with open(image_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode()
        col1.markdown(f'<img src="data:image/png;base64,{b64_img}" alt="CI Analysis Plot" style="width:100%;">', unsafe_allow_html=True)
        col1.caption("Competitive Intelligence Analysis Plot")
        col1.success("✅ Visualization generated successfully!")
    except Exception as e:
        col1.error(f"Error displaying image: {e}")
else:
    col1.warning("CI analysis plot not yet generated. Run the analysis.")

# download CI Analysis CSV file
csv_path = "coding/ci_analysis_data.csv"
if os.path.exists(csv_path):
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_data = f.read()
        col2.download_button(
            label="Download CI Analysis Data CSV",
            data=csv_data,
            file_name="ci_analysis_data.csv",
            mime="text/csv",
        )
    except Exception as e:
        col2.error(f"Error reading CSV: {e}")
else:
    col2.warning("CI analysis data not yet generated. Run the analysis.")

# --- Add PDF download option for the report ---
import tempfile
from fpdf import FPDF

def generate_pdf_report(report_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in report_text.splitlines():
        pdf.multi_cell(0, 10, line)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    return tmp_file.name

if st.session_state.ci_report_content and st.session_state.ci_report_content != "CI report will appear here after generation.":
    pdf_path = generate_pdf_report(st.session_state.ci_report_content)
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label="Download Full Report (PDF)",
            data=pdf_file.read(),
            file_name="ci_report.pdf",
            mime="application/pdf",
        )

st.markdown("---")