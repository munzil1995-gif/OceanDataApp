# Ocean Data Finder — Community Submissions Setup

The app works right now on the 190 curated datasets even with NO setup.
These steps switch ON the community "Contribute a dataset" feature.

## 1. Create the Google Sheet
Create a Google Sheet named **Ocean Data Finder — Submissions**.
In row 1, paste these headers (one per column, exact spelling):

Timestamp | Dataset_Name | Variable | Category | Resource_Type | Source | Region |
Spatial_Resolution | Time_Coverage | Format | Link | Use_Case | Skill_Level |
Tools | Notes | Submitter_Name | Submitter_Email | Status

Copy the **Sheet ID** from the URL: the long code between `/d/` and `/edit`.

## 2. Create a Google service account
1. https://console.cloud.google.com → new project "ocean-data-finder".
2. APIs & Services → Library → enable **Google Sheets API** and **Google Drive API**.
3. APIs & Services → Credentials → Create Credentials → **Service Account** → create.
4. Open it → **Keys** → Add Key → Create new key → **JSON**. A .json downloads. Keep it private.
5. Open the JSON, copy the `client_email` value.
6. In your Google Sheet → Share → paste that email → **Editor** → Share.

## 3. Add the credential to Streamlit (at deploy time)
In share.streamlit.io → your app → ⋮ → Settings → **Secrets**, paste:

```toml
sheet_id = "PASTE_YOUR_SHEET_ID_HERE"

[gcp_service_account]
# paste the ENTIRE contents of the JSON key file here, converted to TOML.
# Easiest: open the JSON, and for each "key": "value" line write  key = "value"
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

NOTE on `private_key`: keep it on ONE line with the `\n` sequences exactly as in the JSON.

## 4. How review works
- A visitor submits a dataset → it appears as a new row with **Status = pending**.
- Open the Google Sheet, check the row, and change **pending** to **approved** (or delete it).
- The website shows approved rows alongside the curated catalogue within ~2 minutes
  (a cache refresh), tagged so users can tell curated from community entries.

## 5. Local testing (optional)
To test on your own machine, put the same secrets in a file at:
`OceanDataApp/.streamlit/secrets.toml`
(Never commit that file to GitHub — add it to .gitignore.)
