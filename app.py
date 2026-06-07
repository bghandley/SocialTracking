import streamlit as st
from datetime import datetime, timezone
import uuid
import re

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

st.set_page_config(page_title="Social Handle Tracker", page_icon="📋")

def get_supabase() -> Client:
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

def generate_edit_link(token: str) -> str:
    return f"https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=edit&token={token}"

def validate_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

# ─── SUBMIT PAGE ───────────────────────────────────────────────
def render_submit():
    st.title("📋 Submit Your Handle")
    st.write("Tell us where you spend the most time.")

    name = st.text_input("Your Name *", placeholder="Jane Smith", key="submit_name")
    email = st.text_input("Your Email *", placeholder="jane@email.com", key="submit_email")
    audience = st.text_input("Target Audience", placeholder="e.g. Gen Z women 18-24", key="submit_audience")
    platform = st.selectbox("Where do you spend the most time? *", ["TikTok", "Instagram", "Both"], key="submit_platform")

    tiktok = st.text_input("TikTok Handle", placeholder="without @", key="submit_tiktok").strip() if platform in ["TikTok", "Both"] else None
    instagram = st.text_input("Instagram Handle", placeholder="without @", key="submit_ig").strip() if platform in ["Instagram", "Both"] else None

    if st.button("Submit", type="primary", use_container_width=True):
        if not name or not email:
            st.error("Name and email are required.")
            return
        if not validate_email(email):
            st.error("Please enter a valid email.")
            return

        supabase = get_supabase()
        if not supabase:
            st.error("Database not connected.")
            return

        existing = supabase.table("handles").select("edit_token,name").eq("email", email.strip().lower()).execute()
        
        if existing.data:
            token = existing.data[0]["edit_token"]
            supabase.table("handles").update({
                "name": name.strip(),
                "audience": audience.strip(),
                "platform": platform,
                "tiktok_handle": tiktok,
                "instagram_handle": instagram,
            }).eq("edit_token", token).execute()
        else:
            token = str(uuid.uuid4())
            supabase.table("handles").insert({
                "name": name.strip(),
                "email": email.strip().lower(),
                "audience": audience.strip(),
                "platform": platform,
                "tiktok_handle": tiktok,
                "instagram_handle": instagram,
                "edit_token": token,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

        link = generate_edit_link(token)
        st.success("✅ Submitted!")
        st.info(f"**Save this link to edit or delete your entry:**\n\n{link}")
        st.caption("Bookmark it now — you'll need this link to make changes later.")

    st.divider()
    st.write("**Navigation**")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("👥 View All Handles", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=directory", use_container_width=True)
    with col2:
        st.link_button("🔑 Forgot My Link", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=forgot", use_container_width=True)

# ─── EDIT PAGE ────────────────────────────────────────────────
def render_edit(token: str):
    supabase = get_supabase()
    if not supabase:
        st.error("Database not connected.")
        return

    result = supabase.table("handles").select("*").eq("edit_token", token).execute()

    if not result.data:
        st.error("❌ Invalid or expired link.")
        st.info("Use the 'Forgot My Link' page to recover your edit link.")
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("🔑 Forgot My Link", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=forgot", use_container_width=True)
        with col2:
            st.link_button("📋 Submit New", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)
        return

    entry = result.data[0]

    st.title("✏️ Edit Your Entry")
    st.write(f"**Name:** {entry['name']}  ·  **Email:** {entry['email']}")
    st.write(f"**Platform:** {entry['platform']}")
    if entry.get('tiktok_handle'):
        st.write(f"**TikTok:** @{entry['tiktok_handle']}")
    if entry.get('instagram_handle'):
        st.write(f"**Instagram:** @{entry['instagram_handle']}")

    st.divider()

    new_name = st.text_input("Name", value=entry['name'], key="edit_name")
    new_email = st.text_input("Email", value=entry.get('email','') or '', key="edit_email")
    new_audience = st.text_input("Target Audience", value=entry.get('audience','') or '', key="edit_audience")
    new_platform = st.selectbox("Platform", ["TikTok", "Instagram", "Both"], 
                                index=["TikTok", "Instagram", "Both"].index(entry['platform']), key="edit_platform")

    new_tiktok = entry.get('tiktok_handle','') or ''
    new_ig = entry.get('instagram_handle','') or ''

    if new_platform in ["TikTok", "Both"]:
        new_tiktok = st.text_input("TikTok Handle", value=new_tiktok, key="edit_tiktok")
    if new_platform in ["Instagram", "Both"]:
        new_ig = st.text_input("Instagram Handle", value=new_ig, key="edit_ig")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            supabase.table("handles").update({
                "name": new_name.strip(),
                "email": new_email.strip().lower(),
                "audience": new_audience.strip(),
                "platform": new_platform,
                "tiktok_handle": new_tiktok.strip() or None,
                "instagram_handle": new_ig.strip() or None,
            }).eq("edit_token", token).execute()
            st.success("✅ Saved!")
            st.rerun()

    with col2:
        if st.button("🗑️ Delete My Entry", use_container_width=True):
            supabase.table("handles").delete().eq("edit_token", token).execute()
            st.success("✅ Deleted! You can submit again anytime.")
            st.link_button("📋 Submit Again", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button("🏠 Home", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)
    with col_b:
        st.link_button("👥 View All", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=directory", use_container_width=True)

# ─── DIRECTORY PAGE ────────────────────────────────────────────
def render_directory():
    st.title("👥 Handle Directory")
    st.write("Everyone in the group and where they spend their time.")

    supabase = get_supabase()
    if not supabase:
        st.error("Database not connected.")
        return

    result = supabase.table("handles").select("name,audience,platform,tiktok_handle,instagram_handle").order("created_at", desc=True).execute()

    if not result.data:
        st.info("No entries yet. Be the first to submit!")
        st.link_button("📋 Submit Your Handle", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)
        return

    col1, col2 = st.columns(2)
    with col1:
        filter_platform = st.selectbox("Filter by platform", ["All", "TikTok", "Instagram", "Both"], key="filter_platform")
    with col2:
        search = st.text_input("Search by name", placeholder="Type to filter...", key="search_name")

    filtered = result.data
    if filter_platform != "All":
        filtered = [r for r in filtered if r.get('platform') == filter_platform]
    if search:
        filtered = [r for r in filtered if search.lower() in r.get('name','').lower()]

    st.divider()

    for entry in filtered:
        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{entry['name']}**")
                if entry.get('audience'):
                    st.caption(f"Target: {entry['audience']}")
            with col_b:
                badge = entry['platform']
                color = {"TikTok": "🔴", "Instagram": "📸", "Both": "🔴📸"}.get(badge, "")
                st.markdown(f"{color} {badge}")

            if entry.get('tiktok_handle'):
                handle = entry['tiktok_handle'].strip().lstrip('@')
                st.markdown(f"  · [TikTok: @{handle}](https://www.tiktok.com/@{handle})")
            if entry.get('instagram_handle'):
                handle = entry['instagram_handle'].strip().lstrip('@')
                st.markdown(f"  · [IG: @{handle}](https://www.instagram.com/{handle})")
            
            st.divider()

    st.caption(f"{len(filtered)} people in the directory")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("📋 Submit Your Handle", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)
    with col2:
        st.link_button("🔑 Forgot My Link", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=forgot", use_container_width=True)

# ─── FORGOT LINK PAGE ──────────────────────────────────────────
def render_forgot():
    st.title("🔍 Forgot Your Edit Link?")
    st.write("Enter the email you used when submitting.")

    email = st.text_input("Your Email", placeholder="jane@email.com", key="forgot_email")

    if st.button("Find My Link", type="primary", use_container_width=True):
        if not validate_email(email):
            st.error("Please enter a valid email.")
            return

        supabase = get_supabase()
        if not supabase:
            st.error("Database not connected.")
            return

        result = supabase.table("handles").select("edit_token,name").eq("email", email.strip().lower()).execute()

        if not result.data:
            st.warning("No entry found for that email. Did you use a different one?")
            st.link_button("📋 Submit Instead", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)
            return

        token = result.data[0]["edit_token"]
        name = result.data[0]["name"]
        link = generate_edit_link(token)

        st.success(f"✅ Found entry for **{name}**!")
        st.info(f"**Your edit/delete link:**\n\n{link}")
        st.caption("Bookmark this link — you'll need it to edit or delete your entry later.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("📋 Submit / Update", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/", use_container_width=True)
    with col2:
        st.link_button("👥 View All Handles", "https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app/?page=directory", use_container_width=True)

# ─── MAIN ──────────────────────────────────────────────────────
page = st.query_params.get("page", "submit")
token = st.query_params.get("token", "")

if page == "edit" and token:
    render_edit(token)
elif page == "directory":
    render_directory()
elif page == "forgot":
    render_forgot()
else:
    render_submit()
