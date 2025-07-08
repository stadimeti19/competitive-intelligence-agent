# app.py

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
from contextlib import redirect_stdout # use this to capture print outputs

# --- configure autogen ---
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

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={
        "cache_seed": None, # set to None for fresh runs in UI, or a number for reproducibility
        "config_list": config_list,
        "temperature": 0,
    },
)

coding_work_dir = "coding"
os.makedirs(coding_work_dir, exist_ok=True) # create directory if it doesn't exist alr

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER", # set to "ALWAYS" for manual approval in terminal
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "executor": LocalCommandLineCodeExecutor(work_dir=coding_work_dir),
    },
)

# --- user defined message generator for blog post ---
def my_message_generator(sender, recipient, context):
    file_name = context.get("file_name")
    file_content = ""
    try:
        with open(file_name, mode="r", encoding="utf-8") as file:
            file_content = file.read()
    except FileNotFoundError:
        file_content = "No data found."
    return "Analyze the data and write a brief but engaging blog post. \n Data: \n" + file_content

# --- main method to run AutoGen chat ---
def run_autogen_task(task_message_1, task_message_2, file_for_blog_post=None):
    # use StringIO object to capture stdout
    output_capture = io.StringIO() 
    with redirect_stdout(output_capture):
        # task 1) initial stock comparison
        initial_chat_result = user_proxy.initiate_chat(
            assistant,
            message=task_message_1,
            summary_method="reflection_with_llm",
        )
        
        # task 2) plotting and saving data
        # autoGen's send() continues the conversation without returning a new chat_res object for that specific message.
        # the log is captured by redirect_stdout
        user_proxy.send( #
            recipient=assistant, #
            message=task_message_2, #
        ) #
        
        # task 3) blog post (if file provided)
        blog_post_summary = "No blog post generated."
        if file_for_blog_post:
            blog_chat_result = user_proxy.initiate_chat(
                recipient=assistant,
                message=my_message_generator,
                file_name=file_for_blog_post,
                summary_method="reflection_with_llm",
                summary_args={"summary_prompt": "Return the blog post in Markdown format."},
            )
            blog_post_summary = blog_chat_result.summary

    return output_capture.getvalue(), blog_post_summary

# --- streamlit UI ---
st.set_page_config(layout="wide") # use wide layout for better display

st.title("📈 AutoGen Stock Analysis & Blog Post Assistant")
st.markdown(""" #
This assistant uses AutoGen agents to: #
1.  Compare year-to-date (YTD) stock gains for META and TESLA. #
2.  Plot their YTD price changes and save data/plot files. #
3.  Analyze the generated data and write a blog post. #
""")

# initialize chat history and blog content in session state for persistence across reruns
if "chat_log" not in st.session_state:
    st.session_state.chat_log = "Click 'Run Assistant' to start the process.\n"
if "blog_post_content" not in st.session_state: #
    st.session_state.blog_post_content = "Blog post will appear here after generation."

st.subheader("Agent Conversation Log")
# display log in a non-editable text area
st.text_area("Live Log", st.session_state.chat_log, height=400, disabled=True, key="log_display")

# button to trigger the process
if st.button("Run Assistant", key="run_button"):
    st.session_state.chat_log = "--- Starting Agent Process ---\n" # reset log on new run
    
    # run the AutoGen task and capture output
    full_log_output, blog_final_content = run_autogen_task( #
        "What date is today? Compare the year-to-date gain for META and TESLA.", # initial message for task 1
        "Plot a chart of their stock price change YTD. Save the data to stock_price_ytd.csv, and save the plot to stock_price_ytd.png.", # message for task 2
        "coding/stock_price_ytd.csv" # file for task 3
    ) #
    
    st.session_state.chat_log = full_log_output # update the log in session state
    st.session_state.blog_post_content = blog_final_content # update blog post content
    st.rerun() # trigger a re-run of the script to update the UI with new logs and content

st.subheader("Generated Blog Post") #
st.markdown(st.session_state.blog_post_content) # display the blog post

st.subheader("Generated Files") #
col1, col2 = st.columns(2) # create columns for layout

# display Image
image_path = "coding/stock_price_ytd.png"
if os.path.exists(image_path):
    try: #
        with open(image_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode()
        col1.markdown(f'<img src="data:image/png;base64,{b64_img}" alt="Stock Price YTD Plot" style="width:100%;">', unsafe_allow_html=True)
        col1.caption("Stock Price YTD Plot")
    except Exception as e:
        col1.error(f"Error displaying image: {e}")
else:
    col1.warning("Plot not yet generated. Run the assistant.")

# download CSV file
csv_path = "coding/stock_price_ytd.csv"
if os.path.exists(csv_path):
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_data = f.read()
        col2.download_button(
            label="Download Stock Data CSV",
            data=csv_data,
            file_name="stock_price_ytd.csv",
            mime="text/csv",
        )
    except Exception as e:
        col2.error(f"Error reading CSV: {e}")
else:
    col2.warning("CSV data not yet generated. Run the assistant.")

st.markdown("---")