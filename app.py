import streamlit as st
from datetime import datetime
import uuid
import os
import re

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY", "")
EMAILJS_TO_EMAIL = os.getenv("EMAILJS_TO_EMAIL", "")

st.set_page_config(page_title="Social Handle Tracker", page_icon="📋")

def get_supabase() -> Client:
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

def generate_edit_link(token: str) -> str:
    return f"https://socialtracking-zsbtmpko27npe58rzbwkh8.streamlit.app?page=edit&token={token}"

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

        # Check if name+email combo already exists → update instead of insert
        existing = supabase.table("handles").select("edit_token,name").eq("email", email.strip().lower()).execute()
        
        if existing.data:
            # Update existing entry
            token = existing.data[0]["edit_token"]
            supabase.table("handles").update({
                "name": name.strip(),
                "audience": audience.strip(),
                "platform": platform,
                "tiktok_handle": tiktok,
                "instagram_handle": instagram,
            }).eq("edit_token", token).execute()
        else:
            # New entry
            token = str(uuid.uuid4())
            supabase.table("handles").insert({
                "name": name.strip(),
                "email": email.strip().lower(),
                "audience": audience.strip(),
                "platform": platform,
                "tiktok_handle": tiktok,
                "instagram_handle": instagram,
                "edit_token": token,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()

        link = generate_edit_link(token)
        st.success("Submitted!")
        st.info(f"**Save this link to edit or delete your entry:**\n\n{link}")
        st.caption("You'll also need this link if you forget it later — so bookmark it!")
        
        # Email notification via EmailJS (if configured)
        if EMAILJS_SERVICE_ID and EMAILJS_TEMPLATE_ID and EMAILJS_PUBLIC_KEY:
            st.info("📧 Want us to email you this link? Enter your email below.")
            email_for_link = st.text_input("Your email", key="email_link_send", value=email)
            if st.button("Send me the link via email"):
                st.session_state["email_sent"] = True

    # EmailJS emailer (shown after submit)
    if st.session_state.get("email_sent"):
        st.success("Check your inbox!")
        # EmailJS is client-side only — we pass the email to a JavaScript handler
        st.components.v1.html(f"""
        <script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
        <script>
          emailjs.init(""+'{EMAILJS_PUBLIC_KEY}'+"");
          emailjs.send(""+'{EMAILJS_SERVICE_ID}'+", ""+'{EMAILJS_TEMPLATE_ID}'+"", {{
            "to_email": ""+'{st.session_state.get("submit_email", "")}'+"",
            "edit_link": ""+'{generate_edit_link(st.session_state.get("submit_token", ""))}'+"",
            "from_email": ""+'{EMAILJS_TO_EMAIL}'+""
          }});
        </script>
        """, height=0)

# ─── EDIT PAGE ────────────────────────────────────────────────
def render_edit(token: str):
    st.title("✏️ Edit Your Entry")

    supabase = get_supabase()
    if not supabase:
        st.error("Database not connected.")
        return

    result = supabase.table("handles").select("*").eq("edit_token", token).execute()

    if not result.data:
        st.error("Invalid or expired link.")
        st.info("Use the 'Forgot my link' page to recover your edit link.")
        return

    entry = result.data[0]

    st.write(f"**Name:** {entry['name']}")
    st.write(f"**Email:** {entry['email']}")
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
            st.success("Saved!")
            st.rerun()

    with col2:
        if st.button("🗑️ Delete My Entry", use_container_width=True):
            supabase.table("handles").delete().eq("edit_token", token).execute()
            st.success("Deleted! You can submit again anytime.")
            st.info("[Submit a new entry →](/)", anchor=False)

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
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        filter_platform = st.selectbox("Filter by platform", ["All", "TikTok", "Instagram", "Both"])
    with col2:
        search = st.text_input("Search by name", placeholder="Type to filter...")

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

            handles = []
            if entry.get('tiktok_handle'):
                handles.append(f"TikTok: @{entry['tiktok_handle']}")
            if entry.get('instagram_handle'):
                handles.append(f"IG: @{entry['instagram_handle']}")
            
            for h in handles:
                st.markdown(f"  · {h}")
            
            st.divider()

    st.caption(f"{len(filtered)} people in the directory")

# ─── FORGOT LINK PAGE ──────────────────────────────────────────
def render_forgot():
    st.title("🔍 Forgot Your Edit Link?")

    email = st.text_input("Enter the email you used when submitting", placeholder="jane@email.com", key="forgot_email")

    if st.button("Send My Edit Link", type="primary", use_container_width=True):
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
            st.info("If you don't have an account yet, submit your handle below.")
            return

        token = result.data[0]["edit_token"]
        name = result.data[0]["name"]
        link = generate_edit_link(token)

        if EMAILJS_SERVICE_ID and EMAILJS_TEMPLATE_ID and EMAILJS_PUBLIC_KEY and EMAILJS_TO_EMAIL:
            # Send email via EmailJS
            st.components.v1.html(f"""
            <script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>
            <script>
              emailjs.init(""+'{EMAILJS_PUBLIC_KEY}'+"");
              emailjs.send(""+'{EMAILJS_SERVICE_ID}'+", ""+'{EMAILJS_TEMPLATE_ID}'+"", {{
                "to_email": ""+'{email}'+"",
                "to_name": ""+'{name}'+"",
                "edit_link": ""+'{link}'+"",
                "from_email": ""+'{EMAILJS_TO_EMAIL}'+""
              }});
            </script>
            """, height=0)
            st.success(f"📧 Link sent to **{email}**! Check your inbox (and spam).")
        else:
            # Fallback: show link directly
            st.warning("Email service not configured yet, but here's your link:")
            st.info(f"**{link}**")
            st.caption("Bookmark this to avoid losing it again!")

# ─── MAIN NAVIGATION ────────────────────────────────────────────
st.sidebar.title("📋 Handle Tracker")
st.sidebar.markdown("---")
page = st.query_params.get("page", "submit")
token = st.query_params.get("token", "")

if page == "edit" and token:
    render_edit(token)
elif page == "directory":
    render_directory()
elif page == "forgot":
    render_forgot()
else:
    nav = st.sidebar.radio("Go to", ["Submit", "View Directory", "Forgot My Link"])
    
    if nav == "Submit":
        st.session_state["email_sent"] = False
        st.session_state["submit_token"] = ""
        render_submit()
    elif nav == "View Directory":
        render_directory()
    elif nav == "Forgot My Link":
        render_forgot()
