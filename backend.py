import os
import io
import pandas as pd
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

def run_ci_analysis(company_input, industry, target_audience, key_features, analysis_type):
    # Clear old CI data before starting a new analysis
    csv_path = "coding/ci_analysis_data.csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)
    output_capture = io.StringIO()
    try:
        from tools.ci_tools import config_list
    except ImportError:
        config_list = []
    llm_config_ci_analyst = {
        "config_list": config_list,
        "temperature": 0.1,
        "tools": [],
    }
    ci_analyst = autogen.AssistantAgent(
        name="ci_analyst",
        llm_config=llm_config_ci_analyst,
        system_message="""You are an expert Competitive Intelligence Analyst with access to multiple specialized tools.\nExecute tools immediately and make intelligent choices about which tools to use for each task."""
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
        conversation_result = data_collector.initiate_chat(
            ci_analyst,
            message=f"""Perform a {analysis_type} for:\nCompany Name: {company_input}\nIndustry: {industry}\nTarget Audience: {target_audience}\nKey Features: {key_features}\n\nUse the available tools to gather comprehensive data and generate a detailed report.\nStart by collecting background information, then identify competitors, and finally create a comprehensive analysis.\n""",
        )
        summary = {
            "keyFindings": [],
            "opportunities": [],
            "threats": [],
            "marketPosition": "",
            "recommendations": []
        }
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if df.empty or 'name' not in df.columns:
                    summary["keyFindings"] = ["Analysis complete, but no competitor data could be identified."]
                    return output_capture.getvalue(), summary
                if df['name'].str.contains('Competitor 1|Placeholder', case=False).any():
                    summary["keyFindings"] = ["The analysis resulted in placeholder data. This can happen for very generic ideas where specific competitors could not be found via automated search. Please try a more specific query or a well-known company."]
                    return output_capture.getvalue(), summary
                # Synthesize summary fields from the DataFrame
                summary["keyFindings"] = [
                    f"{company_input} competes with {len(df)} major competitors in {industry}.",
                    f"Top competitors: {', '.join(df['name'].head(3).tolist())}.",
                    f"Market dynamics show a competitive landscape in {industry}."
                ]
                summary["opportunities"] = [
                    "Expand into underserved market segments.",
                    "Leverage technology for differentiation.",
                    "Pursue strategic partnerships."
                ]
                summary["threats"] = [
                    "Intense competition from established players.",
                    "Potential regulatory changes.",
                    "Market saturation in core segments."
                ]
                summary["marketPosition"] = f"{company_input} is positioned among key competitors in the {industry} industry, with unique features and pricing strategies."
                summary["recommendations"] = [
                    f"Analyze pricing strategies of top competitors.",
                    f"Focus on unique features not offered by competitors.",
                    f"Target underserved segments in {industry}.",
                    f"Leverage technology to improve customer experience.",
                    f"Consider strategic partnerships in {industry}."
                ]
            except Exception as e:
                summary["keyFindings"] = [f"Error reading data file: {e}"]
        else:
            summary["keyFindings"] = ["Data file not found. Analysis may still be in progress."]
    return output_capture.getvalue(), summary 