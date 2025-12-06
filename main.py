import streamlit as st
import openai
import json
import pandas as pd
from utils.tapology_via_gpt import fetch_tapology_data
from utils.sherdog_scraper import fetch_sherdog_profile
from utils.ufcstats_scraper import fetch_ufcstats
from utils.get_odds_via_gpt import get_fight_odds
from utils.fighter_merger import merge_fighter_profile
from utils.usage_limit import usage_ok
from utils.helpers import safe_json_load

# -----------------------------------------------------
#         STREAMLIT PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="UFC Fight Card Analyzer & Parlay Builder",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🥋 UFC Fight Card Analyzer & Parlay Builder (Advanced UI)")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# -----------------------------------------------------
#         LOAD PROMPTS
# -----------------------------------------------------
def load_prompt(path):
    with open(path, "r") as f:
        return f.read()

system_prompt = load_prompt("prompts/system_prompt.txt")
event_lookup_prompt = load_prompt("prompts/event_lookup_prompt.txt")
analysis_prompt = load_prompt("prompts/analysis_prompt.txt")


# -----------------------------------------------------
#       GPT CALL WRAPPER
# -----------------------------------------------------
def call_gpt(prompt):
    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return res["choices"][0]["message"]["content"]


# -----------------------------------------------------
#             EVENT LOOKUP
# -----------------------------------------------------
def lookup_next_event():
    raw = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": event_lookup_prompt}
        ],
        temperature=0
    )
    return safe_json_load(raw["choices"][0]["message"]["content"])


# -----------------------------------------------------
#             FIGHTER FULL PIPELINE
# -----------------------------------------------------
def process_fighter(name):
    st.markdown(f"### 🧩 Collecting data for **{name}**...")

    # Tapology (via GPT)
    with st.spinner(f"Pulling Tapology profile for {name}..."):
        tap = safe_json_load(fetch_tapology_data(name))

    # Sherdog
    with st.spinner(f"Searching Sherdog for {name}..."):
        # User may paste Sherdog URL OR we prompt GPT to find it
        # For now, default to GPT search:
        sherdog_url_prompt = f"Find the Sherdog URL for fighter: {name}. Return ONLY the URL."
        url_raw = call_gpt(sherdog_url_prompt)
        url = url_raw.strip()
        sd = fetch_sherdog_profile(url)

    # UFCStats
    with st.spinner(f"Fetching UFCStats profile for {name}..."):
        # GPT finds fighter ID
        id_prompt = f"Find the UFCStats fighter ID for: {name}. Return ONLY the ID string."
        fighter_id = call_gpt(id_prompt).strip()
        ufcstats = fetch_ufcstats(fighter_id)

    return tap, sd, ufcstats


# -----------------------------------------------------
#             FIGHT ANALYSIS CALL
# -----------------------------------------------------
def analyze_fights(merged_fighters, event_info):
    prompt = f"""
Event data:
{json.dumps(event_info, indent=2)}

Fighter merged datasets:
{json.dumps(merged_fighters, indent=2)}

Now perform full-card analysis using the analysis prompt.
"""
    return call_gpt(prompt)


# -----------------------------------------------------
#             CONFIDENCE BAR UI
# -----------------------------------------------------
def confidence_bar(score):
    bar_color = "#34a853" if score >= 70 else "#fbbc05" if score >= 50 else "#ea4335"
    st.markdown(
        f"""
        <div style="height:20px; background:{bar_color}; width:{score}%;
            border-radius:5px; margin-bottom:10px;"></div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------------------------------
#                 TABS
# -----------------------------------------------------
tab1, tab2 = st.tabs(["🔥 Analyze Next UFC Event", "📅 Analyze Another Event"])

# =====================================================
# TAB 1 — AUTO ANALYZE NEXT EVENT
# =====================================================
with tab1:
    st.header("🔥 Auto Mode: Next UFC Event")
    st.write("Automatically fetches the next UFC event, fight card, fighter data, odds, and performs full analysis.")

    if st.button("Analyze Next UFC Event"):
        if not usage_ok():
            st.error("Daily usage limit reached (10 runs). Try again tomorrow.")
            st.stop()

        with st.spinner("Finding next UFC event..."):
            event_data = lookup_next_event()

        st.subheader(f"📅 {event_data['event_name']}")
        st.write(f"**Date:** {event_data['event_date']}")
        st.write(f"**Location:** {event_data['location']}")
        st.write("---")

        st.markdown("## 🥊 Fight Card")
        for fight in event_data["fight_card"]:
            st.markdown(f"- **{fight['fighter_a']}** vs **{fight['fighter_b']}**")

        st.write("---")
        st.markdown("## 🔍 Gathering Fighter Data + Odds")

        merged = {}

        for fight in event_data["fight_card"]:
            A, B = fight["fighter_a"], fight["fighter_b"]

            with st.spinner(f"Getting data for {A}..."):
                tapA, sdA, ufA = process_fighter(A)

            with st.spinner(f"Getting data for {B}..."):
                tapB, sdB, ufB = process_fighter(B)

            # Get Fight Odds (GPT Browsing)
            with st.spinner(f"Getting odds for {A} vs {B}..."):
                odds_raw = get_fight_odds(A, B)
                odds = safe_json_load(odds_raw)

            merged[f"{A}_vs_{B}"] = {
                A: merge_fighter_profile(A, tapA, sdA, ufA, odds),
                B: merge_fighter_profile(B, tapB, sdB, ufB, odds),
                "odds": odds
            }

        st.write("---")
        st.markdown("## 🧠 Running Full Analysis")

        with st.spinner("Analyzing fight card..."):
            analysis = analyze_fights(merged, event_data)

        st.markdown("## 📘 Full Report")
        st.markdown(analysis)

# =====================================================
# TAB 2 — CHOOSE OTHER EVENT
# =====================================================
with tab2:
    st.header("📅 Analyze Any UFC Event")
    st.write("Paste a UFC event URL (UFC.com, ESPN, Tapology, etc.)")

    event_url = st.text_input("Paste event URL here")

    if st.button("Analyze This Event"):
        if not usage_ok():
            st.error("Daily usage limit reached.")
            st.stop()

        # GPT extracts event info + fight card from the provided URL
        custom_prompt = f"""
Read this UFC event page:
{event_url}

Extract and return JSON ONLY:
- event_name
- event_date
- location
- fight_card (list of fighter matchups)
"""
        raw = call_gpt(custom_prompt)
        event_data = safe_json_load(raw)

        st.subheader(f"📅 {event_data['event_name']}")
        st.write(f"**Date:** {event_data['event_date']}")
        st.write(f"**Location:** {event_data['location']}")
        st.write("---")

        st.markdown("## 🥊 Fight Card")
        for fight in event_data["fight_card"]:
            st.markdown(f"- **{fight['fighter_a']}** vs **{fight['fighter_b']}**")

        st.write("---")
        st.markdown("## 🔍 Gathering Fighter Data + Odds")

        merged = {}

        for fight in event_data["fight_card"]:
            A, B = fight["fighter_a"], fight["fighter_b"]

            with st.spinner(f"Getting data for {A}..."):
                tapA, sdA, ufA = process_fighter(A)

            with st.spinner(f"Getting data for {B}..."):
                tapB, sdB, ufB = process_fighter(B)

            with st.spinner(f"Getting odds for {A} vs {B}..."):
                odds_raw = get_fight_odds(A, B)
                odds = safe_json_load(odds_raw)

            merged[f"{A}_vs_{B}"] = {
                A: merge_fighter_profile(A, tapA, sdA, ufA, odds),
                B: merge_fighter_profile(B, tapB, sdB, ufB, odds),
                "odds": odds
            }

        st.write("---")
        st.markdown("## 🧠 Running Full Analysis")

        with st.spinner("Analyzing fight card..."):
            analysis = analyze_fights(merged, event_data)

        st.markdown("## 📘 Full Report")
        st.markdown(analysis)
