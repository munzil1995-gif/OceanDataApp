import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from data_loader import load_data  # noqa: E402

st.set_page_config(page_title="Browse Data", layout="wide")

st.title("📊 Browse All Datasets")

# --- Coverage toggle ---
scope = st.sidebar.radio(
    "🌐 Coverage",
    ["Global", "Indian Ocean"],
    help="Global = all datasets. Indian Ocean = regional subset only.",
)
df = load_data(scope)

# --- Filters ---
col1, col2, col3 = st.columns(3)
variable = col1.selectbox("Variable", ["All"] + sorted(df["Variable"].dropna().unique()))
region = col2.selectbox("Region", ["All"] + sorted(df["Region"].dropna().unique()))
category = (
    col3.selectbox("Category", ["All"] + sorted(df["Category"].dropna().unique()))
    if "Category" in df.columns else "All"
)

col4, col5 = st.columns(2)
skill = (
    col4.selectbox("Skill Level", ["All"] + sorted(df["Skill_Level"].dropna().unique()))
    if "Skill_Level" in df.columns else "All"
)
latency = (
    col5.selectbox("Latency", ["All"] + sorted(df["Latency"].dropna().unique()))
    if "Latency" in df.columns else "All"
)

# --- Filtering ---
filtered = df.copy()
if variable != "All":
    filtered = filtered[filtered["Variable"] == variable]
if region != "All":
    filtered = filtered[filtered["Region"] == region]
if category != "All":
    filtered = filtered[filtered["Category"] == category]
if skill != "All":
    filtered = filtered[filtered["Skill_Level"] == skill]
if latency != "All":
    filtered = filtered[filtered["Latency"] == latency]

# --- Optional column picker ---
default_cols = [c for c in [
    "Dataset_Name", "Variable", "Category", "Source", "Region",
    "Platform", "Spatial_Resolution", "Time_Coverage", "Skill_Level",
    "Latency", "Login_Required", "Link"
] if c in filtered.columns]

with st.expander("⚙️ Choose columns to display"):
    chosen = st.multiselect("Columns", list(filtered.columns), default=default_cols)
show_cols = chosen if chosen else default_cols

# --- Table ---
st.dataframe(
    filtered[show_cols],
    use_container_width=True,
    column_config={"Link": st.column_config.LinkColumn("Link")} if "Link" in show_cols else None,
)

st.info(f"{len(filtered)} datasets displayed  ·  Coverage: {scope}")

# --- Download the current view ---
st.download_button(
    "⬇️ Download these results (CSV)",
    filtered[show_cols].to_csv(index=False).encode("utf-8"),
    file_name=f"ocean_datasets_{scope.lower().replace(' ', '_')}.csv",
    mime="text/csv",
)
