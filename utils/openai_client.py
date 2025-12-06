# utils/openai_client.py
from openai import OpenAI
import streamlit as st

# Global Client Instance
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
