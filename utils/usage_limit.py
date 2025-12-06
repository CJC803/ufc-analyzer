import streamlit as st
import datetime

MAX_RUNS_PER_DAY = 10

def usage_ok():
    today = str(datetime.date.today())
    used = st.session_state.get("usage", {})

    if today not in used:
        used[today] = 0

    if used[today] >= MAX_RUNS_PER_DAY:
        return False

    used[today] += 1
    st.session_state["usage"] = used
    return True
