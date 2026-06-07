import streamlit as st
from datetime import datetime
import uuid
import os

# Supabase setup
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Page config
st.set_page_config(page_title="Handle Tracker", page_icon="📋")

def get_supabase() -> Client:
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

def generate_edit_link(token: str, base_url: str = "") -> str:
    return f"{base_url}?page=edit&token={token}"

def render_submit_form(supabase: Client):
    st.title("📋 Submit Your Handle")
    st.write("Share where you spend the most time.")

    name = st.text_input("Your Name *", placeholder="Jane Smith")
    audience = st.text_input("Target Audience", placeholder="e.g. Gen Z women 18-24")
    platform = st.selectbox("Where do you spend the most time? *", ["TikTok", "Instagram", "Both"])

    tiktok_handle = None
    ig_handle = None

    if platform in ["TikTok", "Both"]:
        tiktok_handle = st.text_input("TikTok Handle", placeholder="without @").strip()
    if platform in ["Instagram", "Both"]:
        ig_handle = st.text_input("Instagram Handle", placeholder="without @").strip()

    submitted = st.button("Submit", type="primary", use_container_width=True)

    if submitted:
        if not name:
            st.error("Name is required")
            return

        token = str(uuid.uuid4())

        data = {
            "name": name.strip(),
            "audience": audience.strip() if audience.strip() else "",
            "platform": platform,
            "tiktok_handle": tiktok_handle if tiktok_handle else None,
            "instagram_handle": ig_handle if ig_handle else None,
            "edit_token": token,
            "created_at": datetime.utcnow().isoformat()
        }

        if supabase:
            result = supabase.table("handles").insert(data).execute()
            if result.data:
                st.success("Submitted!")
                st.info(f"Save this link to edit or delete later:\n\n{generate_edit_link(token, 'https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/')}")
                st.caption("Share this link with anyone who needs to edit/delete their entry.")
            else:
                st.error("Failed to save. Is Supabase configured?")
        else:
            st.error("Database not connected. Set SUPABASE_URL and SUPABASE_KEY env vars.")

def render_edit_form(supabase: Client, token: str):
    st.title("✏️ Edit Your Entry")

    if not supabase:
        st.error("Database not connected.")
        return

    result = supabase.table("handles").select("*").eq("edit_token", token).execute()

    if not result.data:
        st.error("Invalid or expired link.")
        return

    entry = result.data[0]

    st.write(f"**Name:** {entry['name']}")
    st.write(f"**Platform:** {entry['platform']}")

    if entry.get('tiktok_handle'):
        st.write(f"**TikTok:** @{entry['tiktok_handle']}")
    if entry.get('instagram_handle'):
        st.write(f"**Instagram:** @{entry['instagram_handle']}")

    st.divider()

    new_name = st.text_input("Name", value=entry['name'])
    new_audience = st.text_input("Target Audience", value=entry.get('audience', '') or '')
    new_platform = st.selectbox("Platform", ["TikTok", "Instagram", "Both"], index=["TikTok", "Instagram", "Both"].index(entry['platform']))

    new_tiktok = entry.get('tiktok_handle', '') or ''
    new_ig = entry.get('instagram_handle', '') or ''

    if new_platform in ["TikTok", "Both"]:
        new_tiktok = st.text_input("TikTok Handle", value=new_tiktok)
    if new_platform in ["Instagram", "Both"]:
        new_ig = st.text_input("Instagram Handle", value=new_ig)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            update_data = {
                "name": new_name.strip(),
                "audience": new_audience.strip(),
                "platform": new_platform,
                "tiktok_handle": new_tiktok.strip() if new_tiktok else None,
                "instagram_handle": new_ig.strip() if new_ig else None,
            }
            supabase.table("handles").update(update_data).eq("edit_token", token).execute()
            st.success("Saved!")
            st.rerun()

    with col2:
        if st.button("🗑️ Delete My Entry", use_container_width=True):
            supabase.table("handles").delete().eq("edit_token", token).execute()
            st.success("Deleted. Farewell!")
            st.info("You can submit again anytime.")

# Main
supabase = get_supabase()

query_params = st.query_params
page = query_params.get("page", "submit")
token = query_params.get("token", "")

if page == "edit" and token:
    render_edit_form(supabase, token)
else:
    render_submit_form(supabase)
