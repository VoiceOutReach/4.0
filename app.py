# Cleaned and updated Streamlit app with:
# - GPT prompt customization
# - Variable insertion without rerun crash
# - Sender name input with dynamic Cheers line
# - Fix for '[Your Name]' replacement
# - Messages now persist after voice generation

import streamlit as st
import pandas as pd
import openai
import requests
import os
from zipfile import ZipFile
from io import BytesIO

# Basic setup
st.set_page_config(page_title="VoiceOutReach.ai", layout="wide")
st.title("🎙️ VoiceOutReach.ai")

# Initialize API clients
client = openai.OpenAI()
eleven_api_key = st.secrets["ELEVEN_API_KEY"]
voice_id = st.secrets["VOICE_ID"]

# Upload CSV
uploaded_file = st.file_uploader("Upload your leads CSV", type=["csv"])
if not uploaded_file:
    st.stop()

# Sender name input
sender_name = st.text_input("Sender Name", value="Your Name")
if sender_name.strip().lower() == "your name":
    st.warning("⚠️ You haven't customized your sender name yet.")

# Read and normalize column names
df = pd.read_csv(uploaded_file)
df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("/", "_")
st.write("📊 Sample Data", df.head())

# Define alias map
alias_map = {
    "first_name": ["first_name", "name", "full_name"],
    "last_name": ["last_name"],
    "full_name": ["full_name"],
    "company_name": ["company_name"],
    "position": ["position", "title"],
    "hiring_for_job_title": ["hiring_for_job_title"],
    "job_description": ["job_description"],
    "location": ["location"],
    "industry": ["industry"],
    "job_location_city": ["job_location_city", "job_location"]
}

def resolve_var(row, key):
    for alias in alias_map.get(key, [key]):
        if alias in row:
            return str(row[alias])
    return ""

available_vars = df.columns.tolist()

# Initialize session state keys
if "gpt_prompt" not in st.session_state:
    st.session_state["gpt_prompt"] = ""

if "default_prompt_loaded" not in st.session_state:
    st.session_state["default_prompt_loaded"] = False

if "insert_var" not in st.session_state:
    st.session_state["insert_var"] = ""

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# UI layout
use_gpt = st.checkbox("Use GPT to generate full message")

# Insert default prompt only when GPT mode is turned on
default_prompt = """Write a casual LinkedIn message to {first_name}, who works as a {position} at {company_name}. I recently connected with them, and I noticed their team is hiring for a {hiring_for_job_title} role.

Reference something from the job description: {job_description}, and let them know I might have someone who’s a great fit. Keep it warm, conversational, and under 100 words — like something a recruiter would actually send.
"""

if use_gpt and not st.session_state["default_prompt_loaded"]:
    st.session_state["gpt_prompt"] = default_prompt
    st.session_state["default_prompt_loaded"] = True
elif not use_gpt:
    st.session_state["default_prompt_loaded"] = False

st.markdown("### 🧩 Insert Variables into Your Prompt")
cols = st.columns(len(available_vars))
for i, var in enumerate(available_vars):
    with cols[i]:
        if st.button(f"{{{var}}}", key=f"btn_{var}"):
            st.session_state["insert_var"] = f"{{{var}}}"

# Append variable to prompt if set (no rerun)
if st.session_state["insert_var"]:
    st.session_state["gpt_prompt"] += st.session_state["insert_var"]
    st.session_state["insert_var"] = ""

# Text prompt box
st.text_area("Custom GPT Prompt", key="gpt_prompt", height=150)

# Message preview logic
if st.button("📝 Generate Preview Messages"):
    messages = []
    style_degrees = [1.0, 0.6]

    for idx, row in df.iterrows():
        row = {k.lower().replace(" ", "_").replace("/", "_"): v for k, v in row.items()}
        vars = {key: resolve_var(row, key) for key in alias_map}

        if vars.get("first_name"):
            vars["first_name"] = str(vars["first_name"]).split()[0]
        else:
            vars["first_name"] = "there"

        try:
            prompt = st.session_state["gpt_prompt"].format(**vars)
        except KeyError as e:
            st.warning(f"⚠️ Missing variable in prompt: {e}")
            prompt = st.session_state["gpt_prompt"]

        if use_gpt:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            message = response.choices[0].message.content.strip()
        else:
            message = prompt

        message = message.replace("[Your Name]", sender_name)

        if "cheers" in message.lower() and sender_name.lower() not in message.lower():
            message = message.replace("Cheers", f"Cheers,\n{sender_name}")
        elif "cheers" not in message.lower() and sender_name.strip().lower() != "your name":
            message += f"\n\nCheers,\n{sender_name}"

        messages.append(message)

    st.session_state["messages"] = messages

# Show preview if messages exist
if st.session_state["messages"]:
    st.markdown("### 📝 Preview Text Messages Before Voice Generation")
    for i, msg in enumerate(st.session_state["messages"]):
        st.markdown(f"**{i+1}.** {msg}")

# Voice generation logic
if st.button("🎤 Generate Voice Notes"):
    if "messages" not in st.session_state or not st.session_state["messages"]:
        st.warning("⚠️ Please generate preview messages first.")
        st.stop()

    messages = st.session_state["messages"]
    os.makedirs("voice_notes", exist_ok=True)
    mp3_files = []
    style_degrees = [1.0, 0.6]

    for idx, row in df.iterrows():
        row = {k.lower().replace(" ", "_").replace("/", "_"): v for k, v in row.items()}
        vars = {key: resolve_var(row, key) for key in alias_map}

        if vars.get("first_name"):
            vars["first_name"] = str(vars["first_name"]).split()[0]
        else:
            vars["first_name"] = "there"

        message = messages[idx]
        style_degree = style_degrees[idx % len(style_degrees)]

        headers = {
            "xi-api-key": eleven_api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "text": message,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.7,
                "style_degree": style_degree
            }
        }

        res = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=payload
        )

        if res.status_code == 200:
            filename = f"voice_notes/{vars['first_name']}_{idx}.mp3"
            with open(filename, "wb") as f:
                f.write(res.content)
            mp3_files.append(filename)
        else:
            st.warning(f"❌ ElevenLabs error on row {idx}: {res.text}")

    st.markdown("### 🔊 Voice Note Previews")
    for mp3 in mp3_files:
        st.audio(mp3, format='audio/mp3')

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for mp3 in mp3_files:
            zipf.write(mp3, arcname=os.path.basename(mp3))
    zip_buffer.seek(0)

    st.download_button("📥 Download All Voice Notes", zip_buffer, "voice_notes.zip")
