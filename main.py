import streamlit as st
import json
import pandas as pd

from utils.openai_client import client
from utils.tapology_via_gpt import fetch_tapology_data
from utils.sherdog_scraper import fetch_sherdog_profile
from utils.ufcstats_scraper import fetch_ufcstats
from utils.get_odds_via_gpt import get_fight_odds
from utils.fighter_merger import merge_fighter_profile
from utils.usage_limit import usage_ok
from utils.helpers import safe_json_load


# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="UFC Fight Card Analyzer (Advanced)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🥋 UFC Fight Card Analyzer & Parlay Builder")


# -----------------------------------------------------
# LOAD PROMPTS
# -----------------------------------------------------
def load_prompt(path):
    with open(path, "r") as f:
        return f.read()

system_prompt = load_prompt("prompts/system_prompt.txt")
event_lookup_prompt = load_prompt("prompts/event_lookup_prompt.txt")
analysis_prompt = load_prompt("prompts/analysis_prompt.txt")


# -----------------------------------------------------
# GPT WRAPPER
# -----------------------------------------------------
def call_gpt(prompt):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content


# -----------------------------------------------------
# EVENT LOOKUP (NEXT UFC EVENT)
# -----------------------------------------------------
def lookup_next_event():
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": event_lookup_prompt}],
        temperature=0
    )
    return safe_json_load(res.choices[0].message.content)


# -----------------------------------------------------
# PROCESS SINGLE FIGHTER
# -----------------------------------------------------
def process_fighter(name):
    st.markdown(f"### 🧩 Collecting data for **{name}**...")

    # Tapology (GPT Browsing)
    with st.spinner(f"Pulling Tapology profile for {name}..."):
        tap = safe_json_load(fetch_tapology_data(name))

    # Sherdog — GPT finds the URL
    with st.spinner(f"Searching Sherdog for {name}..."):
        url_lookup_prompt = f"Find the Sherdog URL for fighter: {name}. Return ONLY the full URL."
        url = call_gpt(url_lookup_prompt).strip()
        sd = fetch_sherdog_profile(url)

    # UFCStats
    with st.spinner(f"Fetching UFCStats profile for {name}..."):
        id_prompt = f"Find the UFCStats fighter ID for: {name}. Return ONLY the ID."
        fighter_id = call_gpt(id_prompt).strip()
        ufcstats = fetch_ufcstats(fighter_id)

    return tap, sd, ufcstats


# -----------------------------------------------------
# ANALYSIS PIPELINE
# -----------------------------------------------------
def analyze_fights(merged_fighters, event_info):
    prompt = f"""
Event Data:
{json.dumps(event_info, indent=2)}

Merged Fighters:
{json.dumps(merged_fighters, indent=2)}

Perform full fight analysis using the analysis prompt.
"""
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content


# -----------------------------------------------------
# CONFIDENCE BAR UI
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
# TABS UI
# -----------------------------------------------------
tab1, tab2 = st.tabs(["🔥 Next UFC Event", "📅 Analyze Any Event"])

# =====================================================
# TAB 1 — AUTO MODE
# =====================================================
with tab1:
    st.header("🔥 Auto Mode — Next UFC Event")

    if st.button("Analyze Next UFC Event"):
        if not usage_ok():
            st.error("Daily usage limit reached (10 analyses). Try tomorrow.")
            st.stop()

        with st.spinner("Fetching next UFC event..."):
            event_data = lookup_next_event()

        st.subheader(f"📅 {event_data['event_name']}")
        st.write(f"**Date:** {event_data['event_date']}")
        st.write(f"**Location:** {event_data['location']}")
        st.write("---")

        merged = {}

        for fight in event_data["fight_card"]:
            A = fight["fighter_a"]
            B = fight["fighter_b"]

            with st.spinner(f"Processing {A}..."):
                tapA, sdA, ufA = process_fighter(A)

            with st.spinner(f"Processing {B}..."):
                tapB, sdB, ufB = process_fighter(B)

            with st.spinner(f"Getting odds for {A} vs {B}..."):
                odds = safe_json_load(get_fight_odds(A, B))

            merged[f"{A}_vs_{B}"] = {
                A: merge_fighter_profile(A, tapA, sdA, ufA, odds),
                B: merge_fighter_profile(B, tapB, sdB, ufB, odds),
                "odds": odds
            }

        st.markdown("## 🧠 Full Card Analysis")
        with st.spinner("Running final analysis..."):
            analysis_output = analyze_fights(merged, event_data)

        st.markdown(analysis_output)


# =====================================================
# TAB 2 — CUSTOM EVENT
# =====================================================
with tab2:
    st.header("📅 Analyze Any UFC Event")

    event_url = st.text_input("Paste a UFC event URL:")

    if st.button("Analyze This Event"):
        if not usage_ok():
            st.error("Daily usage limit reached.")
            st.stop()

        custom_prompt = f"""
Read this UFC event page:
{event_url}

Extract and return JSON ONLY:
- event_name
- event_date
- location
- fight_card
"""
        raw = call_gpt(custom_prompt)
        event_data = safe_json_load(raw)

        st.subheader(event_data["event_name"])
        merged = {}

        for fight in event_data["fight_card"]:
            A = fight["fighter_a"]
            B = fight["fighter_b"]

            tapA, sdA, ufA = process_fighter(A)
            tapB, sdB, ufB = process_fighter(B)

            odds = safe_json_load(get_fight_odds(A, B))

            merged[f"{A}_vs_{B}"] = {
                A: merge_fighter_profile(A, tapA, sdA, ufA, odds),
                B: merge_fighter_profile(B, tapB, sdB, ufB, odds),
                "odds": odds
            }

        with st.spinner("Running full analysis..."):
            analysis_output = analyze_fights(merged, event_data)

        st.markdown(analysis_output)
