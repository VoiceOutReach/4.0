
import streamlit as st
import pandas as pd
import openai
import requests
import os
from zipfile import ZipFile
from io import BytesIO

st.set_page_config(page_title="VoiceOutReach.ai", layout="wide")
st.title("🎙️ VoiceOutReach.ai")

client = openai.OpenAI()
eleven_api_key = st.secrets["ELEVEN_API_KEY"]
voice_id = st.secrets["VOICE_ID"]

uploaded_file = st.file_uploader("Upload your leads CSV", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)
df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("/", "_")
st.write("📊 Sample Data", df.head())

alias_map = {
    "first_name": ["first_name", "First_Name"],
    "last_name": ["last_name"],
    "full_name": ["full_name"],
    "company_name": ["company_name"],
    "position": ["position"],
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
st.markdown("### 🧩 Available Variables for GPT Prompt")
st.code(", ".join([f"{{{v}}}" for v in available_vars]), language="python")

use_gpt = st.checkbox("Use GPT to generate full message", value=True)

if "insert_var" not in st.session_state:
    st.session_state["insert_var"] = ""

if use_gpt:
    default_prompt = """Hi {first_name}, I noticed your role as a {position} at {company_name}. I'm working with a company hiring for {hiring_for_job_title}. Based on the job description — {job_description} — I think you’d really appreciate this opportunity. Want to hear more?"""
    gpt_prompt = st.text_area("Custom GPT Prompt", value=default_prompt, key="gpt_prompt", height=150)
else:
    template = st.text_area("Template Message", value="Hi {first_name}, I hope you're doing well. I noticed your work as a {position} at {company_name} and wanted to connect because we’re working with a team hiring for {hiring_for_job_title}. Thought it might be relevant!", height=150)

st.markdown("### 🧩 Insert Variables into Your Prompt")
cols = st.columns(len(available_vars))
for i, var in enumerate(available_vars):
    with cols[i]:
        if st.button(f"{{{var}}}", key=f"btn_{var}"):
            st.session_state["insert_var"] = f"{{{var}}}"

if st.session_state["insert_var"] and use_gpt:
    st.session_state["gpt_prompt"] += st.session_state["insert_var"]
    st.session_state["insert_var"] = ""
    st.experimental_rerun()

if st.button("🚀 Generate Messages + Voices"):
    os.makedirs("voice_notes", exist_ok=True)
    mp3_files = []
    messages = []
    style_degrees = [1.0, 0.6]

    for idx, row in df.iterrows():
        row = {k.lower().replace(" ", "_").replace("/", "_"): v for k, v in row.items()}
        vars = {key: resolve_var(row, key) for key in alias_map}

        if vars.get("first_name"):
            vars["first_name"] = str(vars["first_name"]).split()[0]
        else:
            vars["first_name"] = "there"

        if use_gpt:
            try:
                prompt = st.session_state["gpt_prompt"].format(**vars)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=100
                )
                message = f"Hi {vars['first_name']}, " + response.choices[0].message.content.strip()
            except Exception as e:
                message = f"[GPT Error] {e}"
        else:
            try:
                message = template.format(**vars)
            except:
                message = "[Formatting Error]"

        messages.append(message)

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
            headers=headers, json=payload)

        if res.status_code == 200:
            filename = f"voice_notes/{vars['first_name']}_{idx}.mp3"
            with open(filename, "wb") as f:
                f.write(res.content)
            mp3_files.append(filename)
        else:
            st.warning(f"❌ ElevenLabs error on row {idx}: {res.text}")

    df["final_message"] = messages

    st.markdown("### 🔊 Voice Note Previews")
    for mp3 in mp3_files:
        st.audio(mp3, format='audio/mp3')

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for mp3 in mp3_files:
            zipf.write(mp3, arcname=os.path.basename(mp3))
    zip_buffer.seek(0)

    st.download_button("📥 Download All Voice Notes", zip_buffer, "voice_notes.zip")

    st.markdown("### ✅ Preview Messages")
    cols_to_show = [col for col in ["first_name", "company_name", "final_message"] if col in df.columns]
    st.dataframe(df[cols_to_show])
