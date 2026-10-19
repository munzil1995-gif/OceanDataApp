import streamlit as st
import pandas as pd
import html
import sys
from pathlib import Path

# Allow importing the shared loader from the app root
sys.path.append(str(Path(__file__).resolve().parent.parent))
from data_loader import load_data  # noqa: E402

# --- Page Config ---
st.set_page_config(page_title="Search Data", layout="wide")

st.title("🔍 Search Ocean Data")

# --- Coverage toggle (Global vs Indian Ocean) ---
scope = st.sidebar.radio(
    "🌐 Coverage",
    ["Global", "Indian Ocean"],
    help="Global = all datasets. Indian Ocean = regional subset only.",
)
df = load_data(scope)

# --- Quick search ---
search_text = st.text_input("🔎 Quick search (e.g. oxygen, ssh, chlorophyll, monsoon)")

# --- Sidebar Filters ---
st.sidebar.header("Filters")

variable = st.sidebar.selectbox("Variable", ["All"] + sorted(df["Variable"].dropna().unique()))
region = st.sidebar.selectbox("Region", ["All"] + sorted(df["Region"].dropna().unique()))
platform = st.sidebar.selectbox("Platform", ["All"] + sorted(df["Platform"].dropna().unique()))


def optional_filter(label, column):
    if column in df.columns:
        return st.sidebar.selectbox(label, ["All"] + sorted(df[column].dropna().unique()))
    return "All"


skill = optional_filter("Skill Level", "Skill_Level")
latency = optional_filter("Latency", "Latency")
login = optional_filter("Login Required", "Login_Required")

# --- Comparison Feature ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Compare Datasets")
compare_list = st.sidebar.multiselect("Select datasets", df["Dataset_Name"].unique())

# --- Filtering ---
filtered = df.copy()

if search_text:
    search_cols = [c for c in ["Dataset_Name", "Variable", "Tags", "Use_Case"] if c in df.columns]
    mask = pd.Series(False, index=filtered.index)
    for c in search_cols:
        mask |= filtered[c].astype(str).str.contains(search_text, case=False, na=False)
    filtered = filtered[mask]

if variable != "All":
    filtered = filtered[filtered["Variable"] == variable]
if region != "All":
    filtered = filtered[filtered["Region"] == region]
if platform != "All":
    filtered = filtered[filtered["Platform"] == platform]
if skill != "All" and "Skill_Level" in df.columns:
    filtered = filtered[filtered["Skill_Level"] == skill]
if latency != "All" and "Latency" in df.columns:
    filtered = filtered[filtered["Latency"] == latency]
if login != "All" and "Login_Required" in df.columns:
    filtered = filtered[filtered["Login_Required"] == login]

filtered = filtered.sort_values(by="Dataset_Name")

# --- Results count ---
st.info(f"{len(filtered)} datasets found  ·  Coverage: {scope}")

# --- Colour maps -------------------------------------------------------------
CATEGORY_COLOR = {
    "Physics": "#185FA5",
    "Biogeochemistry": "#0F6E56",
    "Biology/Ecology": "#534AB7",
    "Cryosphere": "#0C447C",
}
SKILL_PILL = {
    "Beginner": ("#EAF3DE", "#27500A"),
    "Intermediate": ("#FAEEDA", "#633806"),
    "Advanced": ("#FCEBEB", "#791F1F"),
}


def get_icon(variable):
    var = str(variable).lower()
    if "temp" in var or "sst" in var:
        return "🌡️"
    elif "sal" in var or "sss" in var:
        return "🧂"
    elif "chl" in var or "phyto" in var:
        return "🌿"
    elif "oxygen" in var:
        return "🫧"
    elif "nitr" in var or "nutri" in var:
        return "🧪"
    elif "current" in var or "ssh" in var or "wave" in var:
        return "🌊"
    elif "ice" in var:
        return "❄️"
    elif "carbon" in var or "co2" in var:
        return "♻️"
    elif "bio" in var or "plankton" in var or "fish" in var:
        return "🐟"
    else:
        return "📊"


def field(row, col):
    return col in row.index and pd.notna(row[col]) and str(row[col]).strip() != ""


def esc(v):
    return html.escape(str(v)) if pd.notna(v) else ""


def pill(text, bg, fg):
    return (
        f'<span style="font-size:12px; background:{bg}; color:{fg}; '
        f'padding:3px 9px; border-radius:8px; white-space:nowrap;">{esc(text)}</span>'
    )


def render_card(row):
    cat = str(row.get("Category", "")).strip()
    accent = CATEGORY_COLOR.get(cat, "#5F5E5A")
    icon = get_icon(row["Variable"])

    # metadata line: Source · Region · Resolution · Coverage
    meta_bits = [row.get("Source"), row.get("Region"),
                 row.get("Spatial_Resolution"), row.get("Time_Coverage")]
    meta = " · ".join(esc(b) for b in meta_bits if pd.notna(b) and str(b).strip())

    # pills
    pills = []
    if field(row, "Skill_Level"):
        bg, fg = SKILL_PILL.get(str(row["Skill_Level"]).strip(), ("#F1EFE8", "#444441"))
        pills.append(pill(row["Skill_Level"], bg, fg))
    if field(row, "Latency"):
        pills.append(pill(row["Latency"], "#E6F1FB", "#0C447C"))
    if field(row, "Format"):
        pills.append(pill(row["Format"], "#F1EFE8", "#444441"))
    if field(row, "Login_Required") and str(row["Login_Required"]).lower() == "yes":
        pills.append(pill("Login", "#FAEEDA", "#633806"))
    pills_html = "".join(pills)

    link_html = ""
    if field(row, "Link"):
        link_html = (
            f'<a href="{esc(row["Link"])}" target="_blank" '
            f'style="display:inline-block; margin-top:10px; font-size:13px; '
            f'color:{accent}; text-decoration:none;">🔗 Open dataset</a>'
        )

    return (
        f'<div style="background:rgba(128,128,128,0.06); '
        f'border:0.5px solid rgba(128,128,128,0.25); '
        f'border-left:3px solid {accent}; border-radius:0; '
        f'padding:14px 16px; margin-bottom:12px;">'
        f'<div style="font-weight:600; font-size:15px; margin-bottom:4px; '
        f'color:var(--text-color, inherit);">'
        f'{icon} {esc(row["Dataset_Name"])}</div>'
        f'<div style="font-size:13px; margin-bottom:10px; '
        f'color:var(--text-color, inherit); opacity:0.65;">{meta}</div>'
        f'<div style="display:flex; gap:6px; flex-wrap:wrap;">{pills_html}</div>'
        f'{link_html}'
        f'</div>'
    )


# --- GRID LAYOUT (2 columns) ---
cols = st.columns(2)

for i, (_, row) in enumerate(filtered.iterrows()):
    col = cols[i % 2]
    with col:
        st.markdown(render_card(row), unsafe_allow_html=True)
        with st.expander("📊 More details"):
            if field(row, "Use_Case"):
                st.write(f"**Use Case:** {row['Use_Case']}")
            if field(row, "Depth"):
                st.write(f"**Depth:** {row['Depth']}")
            if field(row, "Temporal_Resolution"):
                st.write(f"**Temporal Res:** {row['Temporal_Resolution']}")
            if field(row, "Update_Frequency"):
                st.write(f"**Update Frequency:** {row['Update_Frequency']}")
            if field(row, "Tools"):
                st.write(f"**Suggested tools:** {row['Tools']}")
            if field(row, "License"):
                st.write(f"**License:** {row['License']}")
            if field(row, "DOI"):
                st.write(f"**DOI:** {row['DOI']}")
            if field(row, "Citation"):
                st.write(f"**Citation:** {row['Citation']}")
            if field(row, "Link_Checked"):
                st.write(f"**Link last recorded:** {row['Link_Checked']}")
            if field(row, "Notes"):
                st.write(f"**Notes:** {row['Notes']}")

# --- Comparison Output ---
if len(compare_list) >= 2:
    st.markdown("## ⚖️ Dataset Comparison")
    compare_cols = [c for c in [
        "Dataset_Name", "Variable", "Source", "Spatial_Resolution",
        "Temporal_Resolution", "Region", "Platform", "Skill_Level",
        "Latency", "Login_Required", "License"
    ] if c in df.columns]
    compare_df = df[df["Dataset_Name"].isin(compare_list)]
    st.dataframe(compare_df[compare_cols], use_container_width=True)

# --- Empty ---
if len(filtered) == 0:
    st.warning("No datasets found. Try clearing a filter or the search box.")
