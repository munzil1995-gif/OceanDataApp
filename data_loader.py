"""
Shared data loading for the Ocean Data Finder.

Two sources, merged:
  1. Curated catalogue  -> data/Ocean_Open_Data_Finder.xlsx (ships with the repo)
  2. Community entries   -> a Google Sheet, rows where Status == "approved"

If the Google Sheet isn't configured (no secrets yet), the app still runs
perfectly on the curated catalogue alone — community loading just no-ops.
"""
from pathlib import Path
import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).resolve().parent / "data" / "Ocean_Open_Data_Finder.xlsx"
GLOBAL_SHEET = "GLOBAL_DATASETS"
INDIAN_OCEAN_SHEET = "INDIAN_OCEAN_DATASETS"


@st.cache_data(ttl=300)
def load_curated(scope: str = "Global") -> pd.DataFrame:
    sheet = INDIAN_OCEAN_SHEET if scope == "Indian Ocean" else GLOBAL_SHEET
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [c.strip() for c in df.columns]
    df["Entry_Source"] = "Curated"
    return df


@st.cache_data(ttl=120)
def load_community() -> pd.DataFrame:
    """Approved rows from the Google Sheet. Empty frame if not configured."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return pd.DataFrame()
    if "gcp_service_account" not in st.secrets or "sheet_id" not in st.secrets:
        return pd.DataFrame()
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        ws = client.open_by_key(st.secrets["sheet_id"]).sheet1
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df.columns = [c.strip() for c in df.columns]
        if "Status" in df.columns:
            df = df[df["Status"].astype(str).str.strip().str.lower() == "approved"]
        df["Entry_Source"] = "Community"
        return df
    except Exception:  # noqa: BLE001 — never let the sheet break the app
        return pd.DataFrame()


@st.cache_data(ttl=120)
def load_data(scope: str = "Global", include_community: bool = True) -> pd.DataFrame:
    curated = load_curated(scope)
    if not include_community:
        return curated
    community = load_community()
    if community.empty:
        return curated
    # Align community rows to curated columns (fill the rest blank)
    for col in curated.columns:
        if col not in community.columns:
            community[col] = ""
    community = community[[c for c in curated.columns if c in community.columns]]
    merged = pd.concat([curated, community], ignore_index=True)
    return merged


def scope_selector(location: str = "sidebar") -> str:
    target = st.sidebar if location == "sidebar" else st
    return target.radio(
        "🌐 Coverage",
        ["Global", "Indian Ocean"],
        help="Global = all datasets. Indian Ocean = regional subset only.",
    )
