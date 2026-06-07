# Handle Tracker - Minimal Setup Guide

## What this does
- People submit their TikTok/Instagram handle + name + target audience
- They get a unique link to edit or delete their entry later
- Everything stored in Supabase (free tier)

## Step 1: Create Supabase Database

1. Go to https://supabase.com and create a free account
2. Create a new project
3. Go to **SQL Editor** in the left sidebar
4. Paste the contents of `supabase_setup.sql` and run it
5. Go to **Settings > API** and copy your:
   - `Project URL`
   - `anon public` API key

## Step 2: Deploy to Streamlit Cloud

1. Create a GitHub repo and upload `app.py` and `requirements.txt`
2. Go to https://streamlit.io/cloud and connect your GitHub
3. Deploy the repo
4. In Streamlit Cloud settings, add these **Secrets**:
   ```
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```
5. Find your Streamlit URL (e.g., `https://your-app.streamlit.app`)

## Step 3: Update the Edit Link Base URL

In `app.py`, replace `YOUR_APP_URL` with your actual Streamlit URL:
```python
st.info(f"Save this link to edit or delete later:\n\n{generate_edit_link(token, 'https://your-app.streamlit.app')}")
```

## Step 4: Share

Share the Streamlit app URL with your group. When someone submits, they'll see a link to edit/delete their entry.

## Fields
- Name (required)
- Target Audience (optional) - e.g. "Gen Z women 18-24"
- Platform: TikTok / Instagram / Both
- Handle (based on platform selected)

## Cost
- Supabase: Free (500MB database, 2GB transfer)
- Streamlit: Free (community cloud)
- Total: $0 forever
