import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
from datetime import datetime, date
import os
import base64
import requests

GITHUB_TOKEN = "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"
REPO_OWNER = "ljbentertainment"
REPO_NAME = "Daily-Log"
FILE_PATH = "daily_log.csv"
BRANCH = "main"  # or your branch name

def get_file_sha():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()["sha"]
    else:
        return None

def update_csv_on_github(df, commit_message="Update daily_log.csv"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    sha = get_file_sha()
    if not sha:
        st.error("Failed to get file SHA from GitHub.")
        return False

    # Convert DataFrame to CSV string
    csv_string = df.to_csv(index=False)

    # Encode content in base64
    content_encoded = base64.b64encode(csv_string.encode()).decode()

    data = {
        "message": commit_message,
        "content": content_encoded,
        "sha": sha,
        "branch": BRANCH
    }

    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200 or response.status_code == 201:
        return True
    else:
        st.error(f"Failed to update file: {response.json()}")
        return False






CSV_FILE = "daily_log.csv"

# Final columns
COLUMNS = [
    "Date", "Weekday", "Ordinary Day", "Screen Time", "Study Time", "Study Quality (1-10)",
    "Meditation", "Morning Study", "Morning Phone", "Lunch Phone", "Dinner Phone", 
    "Running", "P", "Morning Wake Up Hour", "Notes", "Plan/Strategies"
]

def hhmm_to_decimal(val):
    try:
        if isinstance(val, str) and ':' in val:
            h, m = map(int, val.split(':'))
            return round(h + m / 60, 2)
        return float(val)  # in case it's already a number string
    except:
        return val

# Load or create CSV
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["Date"] = pd.to_datetime(df["Date"])

    # Convert "Morning Wake Up Hour" column if it's in HH:MM string format
    if "Morning Wake Up Hour" in df.columns:
        df["Morning Wake Up Hour"] = df["Morning Wake Up Hour"].apply(hhmm_to_decimal)
else:
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(CSV_FILE, index=False)

# Set up Streamlit
st.set_page_config(page_title="Daily Log", layout="wide")
st.title("📊 Daily Log Tracker")

# Date filter
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", df["Date"].min() if not df.empty else date.today())
with col2:
    end_date = st.date_input("End Date", df["Date"].max() if not df.empty else date.today())

filtered_df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]

# Recent Logs
st.subheader("🕒 Recent Logs")
if not df.empty:
    st.dataframe(df.sort_values("Date", ascending=False).head(3), use_container_width=True)
else:
    st.info("No entries yet!")

# Line charts
if not filtered_df.empty:
    st.subheader("📈 Time-Based Charts")
    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=filtered_df["Date"], y=filtered_df["Screen Time"], mode='lines+markers'))
        fig1.update_layout(title="Screen Time", xaxis_title="Date", yaxis_title="Hours")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=filtered_df["Date"], y=filtered_df["Study Time"], mode='lines+markers'))
        fig2.update_layout(title="Study Time", xaxis_title="Date", yaxis_title="Hours")
        st.plotly_chart(fig2, use_container_width=True)

# Correlation heatmap
if len(filtered_df) > 1:
    st.subheader("🔍 Correlation Heatmap")
    numeric_df = filtered_df.select_dtypes(include='number')
    if not numeric_df.empty:
        corr = numeric_df.corr()
        heatmap = ff.create_annotated_heatmap(
            z=corr.values,
            x=list(corr.columns),
            y=list(corr.index),
            colorscale='RdBu',
            showscale=True
        )
        heatmap.update_layout(title="Numerical Correlation Heatmap")
        st.plotly_chart(heatmap, use_container_width=True)
    else:
        st.info("No numeric data to show correlation.")

# Entry Form
st.subheader("📝 Add New Entry")

with st.form("log_form", clear_on_submit=True):
    entry_date = st.date_input("Date", value=date.today())
    
    # Time inputs for Screen Time, Study Time, and Morning Wake Up Hour
    screen_time_t = st.time_input("Screen Time (HH: MM) ", value=datetime.strptime("00:00", "%H:%M").time())
    study_time_t = st.time_input("Study Time (HH: MM)", value=datetime.strptime("00:00", "%H:%M").time())
    wakeup_time = st.time_input("Morning Wake Up Hour", value=datetime.strptime("08:00", "%H:%M").time())

    def time_to_decimal(t):
        return round(t.hour + t.minute / 60, 2)

    # Convert time inputs to decimal hours
    screen_time = time_to_decimal(screen_time_t)
    study_time = time_to_decimal(study_time_t)
    wakeup_decimal = time_to_decimal(wakeup_time)

    entry = {
        "Date": entry_date,
        "Weekday": pd.to_datetime(entry_date).strftime("%A"),
        "Ordinary Day": st.selectbox("Ordinary Day", ["Yes", "No"]),
        "Screen Time": screen_time,
        "Study Time": study_time,
        "Study Quality (1-10)": st.slider("Study Quality", 1, 10),
        "Meditation": st.selectbox("Meditation", ["Yes", "No"]),
        "Morning Study": st.selectbox("Morning Study", ["Yes", "No"]),
        "Morning Phone": st.selectbox("Morning Phone", ["Yes", "No"]),
        "Lunch Phone": st.selectbox("Lunch Phone", ["Yes", "No"]),
        "Dinner Phone": st.selectbox("Dinner Phone", ["Yes", "No"]),
        "Running": st.selectbox("Running", ["Yes", "No"]),
        "P": st.selectbox("P", ["Yes", "No"]),
        "Morning Wake Up Hour": wakeup_decimal,
        "Notes": st.text_area("Notes"),
        "Plan/Strategies": st.text_area("Plan/Strategies")
    }

    submitted = st.form_submit_button("Add Entry")

if submitted:
    entry["Date"] = pd.to_datetime(entry["Date"])
    new_row = pd.DataFrame([entry])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    st.success(f"✅ Entry for {entry['Date'].date()} saved!")
