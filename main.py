from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from tools.ci_tools import *
from backend import run_ci_analysis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    # Map frontend fields to backend function
    company_name = data.get("companyName")
    industry = data.get("industry")
    target_audience = data.get("targetAudience", "")
    key_features = data.get("keyFeatures", "")
    analysis_type = data.get("analysisType", "Full CI Report")
    # Call the CI agent logic
    log, report = run_ci_analysis(company_name, industry, target_audience, key_features, analysis_type)
    # Optionally, load the CSV and parse for competitors, features, pricing, etc.
    csv_path = "coding/ci_analysis_data.csv"
    competitors = []
    features = []
    pricing = []
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        competitors = df.to_dict(orient="records")
        # You can add more parsing for features/pricing if needed
    return {
        "summary": report,
        "competitors": competitors,
        "features": features,
        "pricing": pricing,
        "log": log,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 