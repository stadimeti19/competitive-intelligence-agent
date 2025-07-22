# Competitive Intelligence Assistant

A powerful competitive intelligence agent with a modern React frontend and Python FastAPI backend. It performs comprehensive market analysis and competitor research using LLMs, web scraping, and dynamic data extraction.

## Features

- **Automated Research:** Enter a company name or business idea and get a full CI report.
- **Competitor Identification:** Finds real, up-to-date competitors in any industry.
- **Data Collection:** Gathers company overviews, features, pricing, market share, revenue, and more.
- **Analysis & Synthesis:** Generates executive summaries, feature matrices, pricing tables, market positioning, SWOT, and recommendations.
- **Modern UI:** Interactive, business-friendly dashboard built with React, Tailwind, and shadcn-ui.

## Project Structure

```
CodeAssistant/
  backend.py           # Backend CI agent logic (run_ci_analysis)
  main.py              # FastAPI backend API
  requirements.txt     # Python dependencies
  tools/               # Custom tool functions for scraping, search, etc.
  coding/              # Output data (CSV, plots)
  frontend/            # React frontend app (Vite, TypeScript, Tailwind)
```

## How to Run

### 1. **Backend (FastAPI + Python)**

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Install Playwright (for dynamic scraping):
```bash
pip install playwright
playwright install
```

Start the backend API:
```bash
uvicorn main:app --reload
```
- The backend will run at http://localhost:8000

### 2. **Frontend (React + Vite)**

Install Node.js dependencies:
```bash
cd frontend
npm install
```

Start the React development server:
```bash
npm run dev
```
- The frontend will run at http://localhost:5173 (or similar)

### 3. **Usage**
- Open the frontend in your browser.
- Enter a company name, industry, and other details.
- Click "Start Analysis" to generate a full CI report.
- View executive summary, competitor cards, feature matrix, pricing, and more.

## API Contract
- The frontend sends a POST request to `/analyze` with the form data.
- The backend returns a structured JSON with summary, competitors, features, pricing, and logs.

## Technologies Used
- **Frontend:** React, Vite, TypeScript, Tailwind CSS, shadcn-ui
- **Backend:** FastAPI, Python, Pandas, Playwright, LLMs (OpenAI), DuckDuckGo Search

## Notes
- Streamlit is no longer used. All UI is handled by the React app.
- For production, set proper CORS and API keys.

## Example Workflow
1. User enters "Netflix" and selects "Streaming" as industry.
2. Frontend sends request to backend.
3. Backend runs agent, scrapes data, generates report.
4. Frontend displays interactive dashboard with all results.

---

For further customization or deployment, see the code comments or ask for help!
