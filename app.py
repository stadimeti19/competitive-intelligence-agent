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
sys.path.append('coding')
from ci_data_collector import (
    duckduckgo_search, 
    get_wikipedia_info, 
    scrape_website, 
    collect_comprehensive_ci_data,
    collect_netflix_competitors,
    collect_generic_competitors
)

# autogen configuration
try:
    config_list = autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
    )
except FileNotFoundError:
    st.error("Error: OAI_CONFIG_LIST file not found. Please create it in the project root with your OpenAI API key.") #
    st.stop()
except ValueError as e:
    st.error(f"Error loading OAI_CONFIG_LIST: {e}. Check your JSON format.")
    st.stop()

# CI specialized agents
ci_analyst = autogen.AssistantAgent(
    name="ci_analyst",
    system_message="""You are a competitive intelligence analyst. Your role is to:
    1. Understand the user's request (company or idea)
    2. Formulate a research plan using free tools (DuckDuckGo search, Wikipedia API, web scraping)
    3. Delegate data collection tasks to the data_collector agent
    4. Synthesize findings into actionable insights
    5. Generate comprehensive reports with clear recommendations
    
    When planning research, specify which free tools to use:
    - duckduckgo_search() for competitor discovery
    - get_wikipedia_info() for company background
    - scrape_website() for detailed competitor data
    - collect_comprehensive_ci_data() for complete analysis""",
    llm_config={
        "cache_seed": None,
        "config_list": config_list,
        "temperature": 0.1,
    },
)

coding_work_dir = "coding"
os.makedirs(coding_work_dir, exist_ok=True) # create directory if it doesn't exist alr

data_collector = autogen.UserProxyAgent(
    name="data_collector",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=5,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "executor": LocalCommandLineCodeExecutor(work_dir=coding_work_dir),
    },
    system_message="""You are a data collection specialist with access to free tools. You MUST execute code immediately when asked to collect data. Available functions:

1. duckduckgo_search(query) - Free web search for competitor discovery
2. get_wikipedia_info(company_name) - Free company background info
3. scrape_website(url) - Free web scraping for competitor data
4. collect_comprehensive_ci_data(company_name, industry) - Complete CI data collection
5. collect_netflix_competitors() - Netflix-specific analysis
6. collect_generic_competitors(company_name, industry) - Generic competitor analysis

When asked to collect data, immediately call these functions and save results to CSV files. Do not just discuss the plan - EXECUTE the data collection.""",
)

# Register the free tool functions with the data collector agent
data_collector.register_function(
    function_map={
        "duckduckgo_search": duckduckgo_search,
        "get_wikipedia_info": get_wikipedia_info,
        "scrape_website": scrape_website,
        "collect_comprehensive_ci_data": collect_comprehensive_ci_data,
        "collect_netflix_competitors": collect_netflix_competitors,
        "collect_generic_competitors": collect_generic_competitors,
    }
)

# CI message generator for comprehensive reports
def my_ci_message_generator(sender, recipient, context):
    file_name = context.get("file_name")
    file_content = ""
    try:
        with open(file_name, mode="r", encoding="utf-8") as file:
            file_content = file.read()
    except FileNotFoundError:
        file_content = "No data found."
    return f"""Analyze the competitive intelligence data and generate a comprehensive report including:
    1. Executive Summary
    2. Competitor Profiles
    3. Feature Comparison Matrix
    4. Pricing Analysis
    5. Market Positioning
    6. SWOT Analysis
    7. Strategic Recommendations
    
    Data: {file_content}"""

# method to run CI analysis
def run_ci_analysis(company_input, industry, target_audience, key_features, analysis_type):
    # use StringIO object to capture stdout
    output_capture = io.StringIO() 
    with redirect_stdout(output_capture):
        # task 1) research planning
        planning_result = data_collector.initiate_chat(
            ci_analyst,
            message=f"""Analyze this request and create a research plan using free tools:
            Company/Idea: {company_input}
            Industry: {industry}
            Target Audience: {target_audience}
            Key Features: {key_features}
            Analysis Type: {analysis_type}
            
            Create a step-by-step plan using:
            - duckduckgo_search() for competitor discovery
            - get_wikipedia_info() for company background
            - scrape_website() for detailed competitor data
            - collect_comprehensive_ci_data() for complete analysis""",
            summary_method="reflection_with_llm",
        )
        
        # task 2) data collection and analysis
        data_collector.send(
            recipient=ci_analyst,
            message=f"""Execute the research plan immediately using free tools:
            1. Use collect_comprehensive_ci_data('{company_input}', '{industry}') for complete analysis
            2. Use duckduckgo_search('competitors of {company_input} {industry}') for competitor discovery
            3. Use get_wikipedia_info('{company_input}') for company background
            4. Save all structured data to 'ci_analysis_data.csv' and generate plots
            
            IMPORTANT: Execute these functions immediately, do not just discuss the plan.""",
        )
        
        # task 3) report generation
        report_summary = "No data available for analysis."
        if os.path.exists("coding/ci_analysis_data.csv"):
            report_result = data_collector.initiate_chat(
                recipient=ci_analyst,
                message=my_ci_message_generator,
                file_name="coding/ci_analysis_data.csv",
                summary_method="reflection_with_llm",
                summary_args={"summary_prompt": "Generate a comprehensive CI report in Markdown format with clear sections and actionable insights."},
            )
            report_summary = report_result.summary

    return output_capture.getvalue(), report_summary

# --- streamlit UI ---
st.set_page_config(layout="wide") # use wide layout for better display

st.title("🔍 AutoGen Competitive Intelligence Assistant")
st.markdown(""" #
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
if "ci_report_content" not in st.session_state: #
    st.session_state.ci_report_content = "CI report will appear here after generation."

st.subheader("Agent Conversation Log")
# display log in a non-editable text area
st.text_area("Live Log", st.session_state.chat_log, height=400, disabled=True, key="log_display")

# button to trigger the process
if st.button("Run CI Analysis", key="run_button"):
    if not company_name:
        st.error("Please enter a company name or idea description.")
    else:
        st.session_state.chat_log = "--- Starting CI Analysis Process ---\n" # reset log on new run
        
        # run the CI analysis and capture output
        full_log_output, ci_final_content = run_ci_analysis( #
            company_name, # company/idea input
            industry, # industry context
            target_audience, # target audience
            key_features, # key features
            analysis_type # analysis type
        ) #
        
        st.session_state.chat_log = full_log_output # update the log in session state
        st.session_state.ci_report_content = ci_final_content # update CI report content
        st.rerun() # trigger a re-run of the script to update the UI with new logs and content

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

st.subheader("Generated Files") #
col1, col2 = st.columns(2) # create columns for layout

# display CI Analysis Image
image_path = "coding/ci_analysis_plot.png"
if os.path.exists(image_path):
    try: #
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