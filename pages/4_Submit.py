import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from urllib.parse import urlparse

st.set_page_config(page_title="Contribute a Dataset", layout="wide")

st.title("➕ Contribute a Dataset")
st.markdown(
    "Know an open ocean dataset or tool that isn't listed? Add it here. "
    "Submissions are reviewed before they appear in the finder, so other "
    "researchers can trust what they find."
)

# --- Google Sheets connection (lazy, fails soft) --------------------------
def get_worksheet():
    """Return the submissions worksheet, or None if not configured yet."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None, "libraries"
    if "gcp_service_account" not in st.secrets or "sheet_id" not in st.secrets:
        return None, "secrets"
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["sheet_id"])
        return sh.sheet1, None
    except Exception as e:  # noqa: BLE001
        return None, str(e)


# Column order MUST match the Google Sheet header row exactly.
SHEET_COLUMNS = [
    "Timestamp", "Dataset_Name", "Variable", "Category", "Resource_Type",
    "Source", "Region", "Spatial_Resolution", "Time_Coverage", "Format",
    "Link", "Use_Case", "Skill_Level", "Tools", "Notes",
    "Submitter_Name", "Submitter_Email", "Status",
]

CATEGORIES = ["Physics", "Biogeochemistry", "Biology/Ecology", "Cryosphere", "Other"]
RESOURCE_TYPES = [
    "Global Portal / Repository", "Regional/Thematic Portal", "Satellite Product",
    "In-situ Platform", "Model / Reanalysis", "Derived / Compilation", "Toolbox", "Other",
]
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"]


def valid_url(u: str) -> bool:
    try:
        p = urlparse(u.strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:  # noqa: BLE001
        return False


# --- Form ------------------------------------------------------------------
with st.form("submit_dataset", clear_on_submit=True):
    st.subheader("Dataset details")
    c1, c2 = st.columns(2)
    name = c1.text_input("Dataset name *", placeholder="e.g. CMEMS Global Ocean Physics Reanalysis")
    source = c2.text_input("Source / provider *", placeholder="e.g. Copernicus Marine Service")

    c3, c4, c5 = st.columns(3)
    variable = c3.text_input("Variable", placeholder="e.g. Temperature, Chlorophyll")
    category = c4.selectbox("Category", CATEGORIES)
    resource_type = c5.selectbox("Resource type", RESOURCE_TYPES)

    c6, c7, c8 = st.columns(3)
    region = c6.text_input("Region", placeholder="e.g. Global, Indian Ocean")
    spatial = c7.text_input("Spatial resolution", placeholder="e.g. 0.25°")
    timecov = c8.text_input("Time coverage", placeholder="e.g. 1993–Present")

    c9, c10 = st.columns(2)
    fmt = c9.text_input("Format", placeholder="e.g. NetCDF, CSV")
    skill = c10.selectbox("Skill level", SKILL_LEVELS)

    link = st.text_input("Link (URL) *", placeholder="https://…")
    use_case = st.text_area("Use case / description", placeholder="What is this dataset good for?")
    tools = st.text_input("Suggested tools", placeholder="e.g. copernicusmarine, xarray")
    notes = st.text_input("Notes", placeholder="Anything else worth knowing")

    st.subheader("About you (optional)")
    s1, s2 = st.columns(2)
    sub_name = s1.text_input("Your name", placeholder="So we can credit you")
    sub_email = s2.text_input("Your email", placeholder="Only used if we need to clarify")

    submitted = st.form_submit_button("Submit for review")

if submitted:
    # Validation
    errors = []
    if not name.strip():
        errors.append("Dataset name is required.")
    if not source.strip():
        errors.append("Source is required.")
    if not link.strip() or not valid_url(link):
        errors.append("A valid http(s) link is required.")
    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    ws, problem = get_worksheet()
    if ws is None:
        if problem == "secrets":
            st.warning(
                "Submissions aren't connected to the review sheet yet. "
                "Your entry wasn't saved — please try again later."
            )
        elif problem == "libraries":
            st.warning("Submission service is still being set up. Please try again later.")
        else:
            st.error(f"Could not reach the submissions sheet: {problem}")
        st.stop()

    row = {
        "Timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "Dataset_Name": name.strip(), "Variable": variable.strip(),
        "Category": category, "Resource_Type": resource_type,
        "Source": source.strip(), "Region": region.strip(),
        "Spatial_Resolution": spatial.strip(), "Time_Coverage": timecov.strip(),
        "Format": fmt.strip(), "Link": link.strip(), "Use_Case": use_case.strip(),
        "Skill_Level": skill, "Tools": tools.strip(), "Notes": notes.strip(),
        "Submitter_Name": sub_name.strip(), "Submitter_Email": sub_email.strip(),
        "Status": "pending",
    }
    try:
        ws.append_row([row[c] for c in SHEET_COLUMNS], value_input_option="USER_ENTERED")
        st.success(
            "✅ Thank you! Your dataset has been submitted and will appear in the "
            "finder once it's reviewed. You're helping the whole community."
        )
        st.balloons()
    except Exception as e:  # noqa: BLE001
        st.error(f"Something went wrong saving your submission: {e}")

st.divider()
st.caption(
    "All submissions are reviewed by the Ocean Data Finder team before publication. "
    "By submitting, you confirm the resource is openly available and the link is correct."
)
