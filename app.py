
import streamlit as st
import pandas as pd
import openai
import requests
import os
from zipfile import ZipFile
from io import BytesIO

st.set_page_config(page_title="VoiceOutReach.ai", layout="wide")
st.title("🎙️ VoiceOutReach.ai")

# API Keys from secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
eleven_api_key = st.secrets["ELEVEN_API_KEY"]
voice_id = st.secrets["VOICE_ID"]

# Upload CSV
uploaded_file = st.file_uploader("Upload your leads CSV", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)
st.write("📊 Sample Data", df.head())

# Show available variables
available_vars = df.columns.str.lower().str.replace(" ", "_").tolist()
st.markdown("### 🧩 Available Variables for GPT Prompt")
st.code(", ".join([f"{{{v}}}" for v in available_vars]), language="python")

# GPT or Template toggle
use_gpt = st.checkbox("Use GPT to generate full message", value=True)

# GPT Prompt or Template Message
if use_gpt:
    gpt_prompt = st.text_area("Custom GPT Prompt", value="""
Write a LinkedIn message to {first_name}, who is a {position} at {company_name}.
I have a candidate for the {hiring_for_job_title} role. Keep it under 60 words.
""", height=150)
else:
    template = st.text_area("Template Message", value="""
Hi {first_name}, I saw you're hiring for {hiring_for_job_title} at {company_name}.
{quick_jd} Let's connect!
""", height=150)

# Generate button
if st.button("🚀 Generate Messages + Voices"):
    os.makedirs("voice_notes", exist_ok=True)
    mp3_files = []
    messages = []

    for idx, row in df.iterrows():
        vars = {col.lower().replace(" ", "_"): str(row[col]) for col in df.columns}
        vars["first_name"] = vars.get("first_name") or vars.get("name", "").split(" ")[0]

        if use_gpt:
            prompt = gpt_prompt.format(**vars)
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,
                    max_tokens=100
                )
                message = response.choices[0].message["content"].strip()
            except Exception as e:
                message = f"[GPT Error] {e}"
        else:
            vars["quick_jd"] = "You're looking for someone with relevant skills."
            try:
                message = template.format(**vars)
            except:
                message = "[Formatting Error]"

        messages.append(message)

        # ElevenLabs request
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
                "style_degree": 0.6
            }
        }
        res = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers, json=payload)

        if res.status_code == 200:
            filename = f"voice_notes/{vars['first_name']}_{idx}.mp3"
            with open(filename, "wb") as f:
                f.write(res.content)
            mp3_files.append(filename)
        else:
            st.warning(f"❌ ElevenLabs error on row {idx}: {res.text}")

    df["final_message"] = messages

    # Zip download
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for mp3 in mp3_files:
            zipf.write(mp3, arcname=os.path.basename(mp3))
    zip_buffer.seek(0)

    st.download_button("📥 Download All Voice Notes", zip_buffer, "voice_notes.zip")

    st.markdown("### ✅ Preview Messages")
    st.dataframe(df[["first_name", "company_name", "final_message"]])
