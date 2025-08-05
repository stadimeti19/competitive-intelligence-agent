from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import pandas as pd
import numpy as np
from tools.ci_tools import *
from backend_visualized import run_ci_analysis
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_json_value(value):
    """Convert value to JSON-safe format"""
    if pd.isna(value) or value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return "N/A"
        return value
    return str(value)

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    # Map frontend fields to backend function
    company_name = data.get("companyName") or data.get("company_name")
    industry = data.get("industry")
    target_audience = data.get("targetAudience") or data.get("target_audience", "")
    key_features = data.get("keyFeatures") or data.get("key_features", "")
    analysis_type = data.get("analysisType") or data.get("analysis_type", "Full CI Report")
    # Call the CI agent logic
    log, report = run_ci_analysis(company_name, industry, target_audience, key_features, analysis_type)
    # Load the CSV and parse for competitors, features, pricing, etc.
    csv_path = "coding/ci_analysis_data.csv"
    competitors = []
    features = []
    pricing = []
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if not df.empty and 'name' in df.columns:
                # Convert DataFrame to list of competitor objects
                competitors = []
                for _, row in df.iterrows():
                    competitor = {
                        "name": safe_json_value(row.get('name', 'Unknown')),
                        "pricing_model": safe_json_value(row.get('pricing_model', 'N/A')),
                        "key_features": safe_json_value(row.get('key_features', 'N/A')),
                        "market_position": safe_json_value(row.get('market_position', 'N/A')),
                        "target_audience": safe_json_value(row.get('target_audience', 'N/A')),
                        "revenue": safe_json_value(row.get('revenue', 'N/A')),
                        "market_share": safe_json_value(row.get('market_share', 'N/A')),
                        "pricing_tiers": safe_json_value(row.get('pricing_tiers', 'N/A')),
                        "data_sources": safe_json_value(row.get('data_sources', 0))
                    }
                    competitors.append(competitor)
                
                # Extract features for the feature matrix
                features = []
                for _, row in df.iterrows():
                    if 'key_features' in row and pd.notna(row['key_features']) and row['key_features'] != 'N/A':
                        features.append({
                            "name": safe_json_value(row['name']),
                            "features": safe_json_value(row['key_features'])
                        })
                
                # Extract pricing data
                pricing = []
                for _, row in df.iterrows():
                    if 'pricing_model' in row and pd.notna(row['pricing_model']) and row['pricing_model'] != 'N/A':
                        pricing.append({
                            "name": safe_json_value(row['name']),
                            "model": safe_json_value(row['pricing_model']),
                            "tiers": safe_json_value(row.get('pricing_tiers', 'N/A')),
                            "revenue": safe_json_value(row.get('revenue', 'N/A'))
                        })
        except Exception as e:
            print(f"Error parsing CSV: {e}")
    
    return {
        "summary": report,
        "competitors": competitors,
        "features": features,
        "pricing": pricing,
        "log": log,
    }

@app.get("/charts/{chart_type}")
async def get_chart(chart_type: str):
    chart_path = f"coding/{chart_type}.png"
    if os.path.exists(chart_path):
        return FileResponse(chart_path)
    return {"error": "Chart not found"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 