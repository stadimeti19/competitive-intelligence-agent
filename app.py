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

# Import tool functions
sys.path.append('tools')
from ci_tools import (
    duckduckgo_search,
    get_wikipedia_info,
    scrape_website,
    generate_industry_competitors,
    collect_comprehensive_ci_data
)

# autogen configuration
try:
    config_list = autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
    )
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
                "name": "duckduckgo_search",
                "description": "Performs a DuckDuckGo web search and returns a summary of top results. Useful for general research, finding company info, news, or competitor websites.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query."},
                        "num_results": {"type": "integer", "description": "Number of top results to return."},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_wikipedia_info",
                "description": "Fetches concise background information for a given entity from Wikipedia.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The entity name to search on Wikipedia."},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scrape_website",
                "description": "Fetches and returns the main textual content from a given URL. Use this after finding a relevant URL via search.",
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
                "name": "generate_industry_competitors",
                "description": "Identifies and generates a list of key competitors for a given industry and target company/idea description.",
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
                "name": "collect_comprehensive_ci_data",
                "description": "Collects extensive competitive intelligence data for a given company and industry. This involves multiple sub-queries and aggregations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "The name of the company to analyze."},
                        "industry": {"type": "string", "description": "The industry of the company."},
                    },
                    "required": ["company_name", "industry"],
                },
            },
        },
    ],
}

# CI specialized agents with proper tool configuration
ci_analyst = autogen.AssistantAgent(
    name="ci_analyst",
    llm_config=llm_config_ci_analyst,
    system_message="""You are an expert Competitive Intelligence Analyst.
    Your goal is to provide comprehensive, data-driven competitive analyses for companies or new business ideas.
    You have access to powerful tools to gather information:
    - `duckduckgo_search(query)`: For general web research, finding company websites, news, and initial competitor identification.
    - `get_wikipedia_info(query)`: To get concise background information from Wikipedia.
    - `scrape_website(url)`: To extract the main text content from any given URL.
    - `generate_industry_competitors(industry, company_description)`: To specifically identify competitors within a given industry.
    - `collect_comprehensive_ci_data(company_name, industry)`: To collect extensive competitive intelligence data.

    Always prioritize using these tools to gather facts before drawing conclusions or generating reports.
    Break down tasks into logical, executable steps. When you decide to use a tool, output ONLY the tool call in the correct format.
    Once all necessary data is collected, synthesize it into the requested report format. If you need a file to be created or read, directly output the Python code to do so within a code block.
    """
)

coding_work_dir = "coding"
os.makedirs(coding_work_dir, exist_ok=True)

data_collector = autogen.UserProxyAgent(
    name="data_collector",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content") and x.get("content").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "executor": LocalCommandLineCodeExecutor(work_dir=coding_work_dir),
    },
)

# Register the functions for execution
data_collector.register_for_execution(name="duckduckgo_search")(duckduckgo_search)
data_collector.register_for_execution(name="get_wikipedia_info")(get_wikipedia_info)
data_collector.register_for_execution(name="scrape_website")(scrape_website)
data_collector.register_for_execution(name="generate_industry_competitors")(generate_industry_competitors)
data_collector.register_for_execution(name="collect_comprehensive_ci_data")(collect_comprehensive_ci_data)

# method to run CI analysis
def run_ci_analysis(company_input, industry, target_audience, key_features, analysis_type):
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
        if os.path.exists("coding/ci_analysis_data.csv"):
            try:
                with open("coding/ci_analysis_data.csv", mode="r", encoding="utf-8") as file:
                    file_content = file.read()
                report_summary = f"""# Competitive Intelligence Report for {company_input}

## Executive Summary
Comprehensive analysis of {company_input} in the {industry} industry.

## Data Collected
{file_content}

## Key Findings
- Company analysis completed
- Competitor data gathered
- Market positioning analyzed

## Recommendations
Based on the collected data, strategic recommendations have been generated for {company_input}.
"""
            except FileNotFoundError:
                report_summary = "Data file not found."

    return output_capture.getvalue(), report_summary

# --- streamlit UI ---
st.set_page_config(layout="wide")

st.title("🔍 AutoGen Competitive Intelligence Assistant")
st.markdown("""
This assistant uses AutoGen agents to perform comprehensive competitive intelligence analysis:
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

st.markdown("---")