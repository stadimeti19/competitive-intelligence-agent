# Competitive Intelligence Assistant

A powerful competitive intelligence agent built with AutoGen and Streamlit that performs comprehensive market analysis and competitor research.

## Features

### 🔍 **Dynamic Input System**
- **Company Analysis**: Enter any company name (e.g., "Netflix", "Zoom")
- **Idea Research**: Describe new business ideas (e.g., "AI-powered meal planning app")
- **Context Parameters**: Specify industry, target audience, and key features
- **Analysis Types**: Choose from Competitor Analysis, Market Research, SWOT Analysis, or Full CI Report

### 🤖 **Specialized AI Agents**
- **CI Analyst**: Orchestrates research plans and synthesizes findings
- **Data Collector**: Performs web scraping, API calls, and data gathering
- **Multi-Agent Collaboration**: Seamless coordination between specialized agents

### 📊 **Comprehensive Outputs**
- **Executive Summary**: High-level insights and key findings
- **Competitor Profiles**: Detailed analysis of identified competitors
- **Feature Comparison Matrix**: Side-by-side feature analysis
- **Pricing Analysis**: Competitive pricing strategies
- **Market Positioning**: Visual positioning maps and analysis
- **SWOT Analysis**: Strengths, weaknesses, opportunities, threats
- **Strategic Recommendations**: Actionable insights and next steps

### 📁 **File Generation**
- **CSV Data Export**: Download structured competitor data
- **Visualization Plots**: Market positioning and analysis charts
- **Comprehensive Reports**: Markdown-formatted CI reports

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Create `OAI_CONFIG_LIST` file in project root:
   ```json
   [
     {
       "model": "gpt-4",
       "api_key": "your-openai-api-key"
     }
   ]
   ```

3. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

## Usage

1. **Enter Target**: Input a company name or describe your business idea
2. **Add Context**: Specify industry, target audience, and key features
3. **Choose Analysis**: Select the type of competitive intelligence analysis
4. **Run Analysis**: Click "Run CI Analysis" to start the automated process
5. **Review Results**: Examine the comprehensive report and generated files

## Architecture

### Agent Roles
- **CI Analyst**: Research planning and synthesis
- **Data Collector**: Web scraping and data gathering
- **Report Generator**: Comprehensive report creation

### Workflow
1. **Research Planning**: Agent creates step-by-step research plan
2. **Data Collection**: Automated competitor identification and data gathering
3. **Analysis**: Feature comparison, pricing analysis, market positioning
4. **Report Generation**: Comprehensive CI report with recommendations

## Example Use Cases

- **Startup Research**: Analyze competitors for a new SaaS product
- **Market Entry**: Research existing players before entering a market
- **Product Development**: Identify gaps and opportunities in current offerings
- **Strategic Planning**: Understand competitive landscape for business decisions

## Technical Stack

- **AutoGen**: Multi-agent orchestration and conversation management
- **Streamlit**: Web interface and user experience
- **BeautifulSoup**: Web scraping and data extraction
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualization and chart generation
