# UFC Fight Card Analyzer & Parlay Builder

This is a free Streamlit app that:
- Retrieves the next UFC event
- Pulls fighter data from Tapology (via GPT browsing)
- Scrapes Sherdog for early-career data
- Scrapes UFCStats for official metrics
- Retrieves fight odds via GPT
- Merges all fighter data
- Runs a GPT-powered analysis
- Outputs predictions, confidence scores, and parlays

## Features
- Free hosting (Streamlit Cloud)
- Uses GPT-4o-mini for ultra-low cost analysis
- Supports Tapology + Sherdog + UFCStats
- Built-in usage caps
- Clean UI

## Deploying
1. Fork this repo to your GitHub
2. Go to https://share.streamlit.io
3. Create new app
4. Point to `main.py`
5. Add your OpenAI API key in secrets:
   OPENAI_API_KEY = "yourkey"
6. Run

