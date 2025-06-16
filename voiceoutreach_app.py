import streamlit as st
import pandas as pd
import openai
import requests
import os
import random
import base64
from zipfile import ZipFile
from io import BytesIO

# 🌟 GitHub upload function
def upload_to_github(filename, repo_path):
    import base64
    import requests

    with open(filename, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    api_url = (
        f"https://api.github.com/repos/"
        f"{st.secrets['GITHUB_USERNAME']}/"
        f"{st.secrets['GITHUB_REPO']}/contents/{repo_path}"
    )

    headers = {
        "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json"
    }

    get_res = requests.get(api_url, headers=headers)
    sha = get_res.json().get("sha") if get_res.status_code == 200 else None

    data = {
        "message": f"Add {os.path.basename(filename)}",
        "branch": st.secrets["GITHUB_BRANCH"],
        "content": b64_content
    }
    if sha:
        data["sha"] = sha

    # ✅ Add this block at the end
    try:
        put_res = requests.put(api_url, headers=headers, json=data)
        if put_res.status_code not in (200, 201):
            st.error(f"❌ GitHub upload failed: {put_res.status_code}")
            st.code(put_res.text, language='json')
    except Exception as e:
        st.error("🚨 Failed to connect to GitHub.")
        st.code(str(e))

try:
    put_res = requests.put(api_url, headers=headers, json=data)
    if put_res.status_code not in (200, 201):
        st.error(f"❌ GitHub upload failed: {put_res.status_code}")
        st.code(put_res.text, language='json')
except Exception as e:
    st.error("🚨 Failed to connect to GitHub.")
    st.code(str(e))


# 🧠 Voice pacing helpers
def enhance_pacing(text):
    text = text.replace('. ', '.\n')
    text = text.replace(', ', ',\n')
    for trigger in ["Hi ", "Hey ", "Thanks", "Let me know", "I noticed"]:
        text = text.replace(trigger, f"{trigger}\n")
    return text

def split_long_sentences(text, max_words=15):
    sentences = text.split(". ")
    broken = []
    for s in sentences:
        words = s.split()
        if len(words) > max_words:
            mid = len(words) // 2
            broken.append(" ".join(words[:mid]) + ".")
            broken.append(" ".join(words[mid:]))
        else:
            broken.append(s)
    return ". ".join(broken)

# 🚀 Streamlit app setup
st.set_page_config(page_title="VoiceOutReach.ai", layout="wide")
st.title("🎙️ VoiceOutReach.ai")

client = openai.OpenAI()
eleven_api_key = st.secrets["ELEVEN_API_KEY"]
voice_id = st.secrets["VOICE_ID"]

uploaded_file = st.file_uploader("Upload your leads CSV", type=["csv"])
if not uploaded_file:
    st.stop()

sender_name = st.text_input("Sender Name", value="Your Name")
if sender_name.strip().lower() == "your name":
    st.warning("⚠️ You haven't customized your sender name yet.")

df = pd.read_csv(uploaded_file)
df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("/", "_")
st.write("📊 Sample Data", df.head())

alias_map = {
    "first_name": ["first_name", "name", "full_name"],
    "company_name": ["company_name"],
    "position": ["position", "title"],
    "hiring_for_job_title": ["hiring_for_job_title"],
    "job_description": ["job_description"],
}

def resolve_var(row, key):
    for alias in alias_map.get(key, [key]):
        if alias in row:
            return str(row[alias])
    return ""

available_vars = df.columns.tolist()

# 🔄 Session State
if "gpt_prompt" not in st.session_state:
    st.session_state["gpt_prompt"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 🧠 Prompt UI
use_gpt = st.checkbox("Use GPT to generate full message")

def_prompt = """Write a casual LinkedIn message to {first_name}, who works as a {position} at {company_name}. I recently connected with them, and I noticed their team is hiring for a {hiring_for_job_title} role.

Reference something from the job description: {job_description}, and let them know I might have someone who’s a great fit. Keep it warm, conversational, and under 100 words — like something a recruiter would actually send."""

if use_gpt and not st.session_state.get("default_prompt_loaded", False):
    st.session_state["gpt_prompt"] = def_prompt
    st.session_state["default_prompt_loaded"] = True
elif not use_gpt:
    st.session_state["default_prompt_loaded"] = False

st.markdown("### 🧩 Insert Variables into Your Prompt")
cols = st.columns(len(available_vars))
for i, var in enumerate(available_vars):
    with cols[i]:
        if st.button(f"{{{var}}}", key=f"btn_{var}"):
            st.session_state["gpt_prompt"] += f"{{{var}}}"

st.text_area("Custom GPT Prompt", key="gpt_prompt", height=150)

# 📝 Generate preview messages
if st.button("📝 Generate Preview Messages"):
    messages = []
    for idx, row in df.iterrows():
        row = {k.lower().replace(" ", "_").replace("/", "_"): v for k, v in row.items()}
        vars = {key: resolve_var(row, key) for key in alias_map}
        vars["first_name"] = vars.get("first_name", "there").split()[0]

        try:
            prompt = st.session_state["gpt_prompt"].format(**vars)
        except KeyError as e:
            st.warning(f"Missing variable in prompt: {e}")
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

        if "cheers" not in message.lower() and sender_name.strip().lower() != "your name":
            message += f"\n\nCheers,\n{sender_name}"

        messages.append(message)

    st.session_state["messages"] = messages

# 💬 Preview section
if st.session_state["messages"]:
    st.markdown("### 📝 Preview Text Messages")
    for i, msg in enumerate(st.session_state["messages"]):
        st.markdown(f"**{i+1}.** {msg}")

# 🎤 Generate voice notes + GitHub upload
if st.button("🎤 Generate Voice Notes"):
    if not st.session_state["messages"]:
        st.warning("⚠️ Generate messages first.")
        st.stop()

    os.makedirs("voice_notes", exist_ok=True)
    mp3_files = []
    hosted_links = []

    for idx, row in df.iterrows():
        row = {k.lower().replace(" ", "_").replace("/", "_"): v for k, v in row.items()}
        vars = {key: resolve_var(row, key) for key in alias_map}
        vars["first_name"] = vars.get("first_name", "there").split()[0]

        message = st.session_state["messages"][idx]
        message = split_long_sentences(message)
        message = enhance_pacing(message)
        style_degree = round(random.uniform(0.5, 0.8), 2)

        payload = {
            "text": message,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.7,
                "style_degree": style_degree
            }
        }

        headers = {
            "xi-api-key": eleven_api_key,
            "Content-Type": "application/json"
        }

        res = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=payload
        )

        if res.status_code == 200 and res.content:
            file_id = f"{vars['first_name']}_{idx}"
            filename = f"voice_notes/{file_id}.mp3"

            if len(res.content) > 5000:
                with open(filename, "wb") as f:
                    f.write(res.content)

                github_path = f"public/voices/{file_id}.mp3"
                upload_to_github(filename, github_path)
                mp3_files.append(filename)
                hosted_links.append(f"https://voiceoutreach.ai/voice/{file_id}")
            else:
                st.warning(f"⚠️ Voice content too short for {file_id}, skipping.")
        else:
            st.warning(f"❌ ElevenLabs error on row {idx}: {res.text}")

    st.markdown("### 🔊 Voice Note Previews")
    for i, mp3 in enumerate(mp3_files):
        st.audio(mp3, format='audio/mp3')
        st.markdown(f"[Voice Link]({hosted_links[i]})")

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for mp3 in mp3_files:
            zipf.write(mp3, arcname=os.path.basename(mp3))
    zip_buffer.seek(0)

    st.download_button("📅 Download All Voice Notes", zip_buffer, "voice_notes.zip")
