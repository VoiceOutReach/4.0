
import streamlit as st
import os
from io import BytesIO

# ✨ GitHub upload function
import base64

def upload_to_github(filename, repo_path):
    import requests

    with open(filename, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    api_url = f"https://api.github.com/repos/{st.secrets['GITHUB_USERNAME']}/{st.secrets['GITHUB_REPO']}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json"
    }

    # Check if file already exists (get SHA)
    get_res = requests.get(api_url, headers=headers)
    if get_res.status_code == 200:
        sha = get_res.json()["sha"]
    else:
        sha = None

    data = {
        "message": f"Add {os.path.basename(filename)}",
        "branch": st.secrets["GITHUB_BRANCH"],
        "content": b64_content
    }
    if sha:
        data["sha"] = sha

    put_res = requests.put(api_url, headers=headers, json=data)
    if put_res.status_code in [200, 201]:
        print(f"✅ Uploaded to GitHub: {repo_path}")
    else:
        st.warning(f"❌ GitHub upload failed: {put_res.status_code} {put_res.text}")


if st.button("🎤 Generate Voice Notes"):
    file_id = "Test_0"
    filename = f"voice_notes/{file_id}.mp3"
    with open(filename, "wb") as f:
            f.write(res.content)
            # 🚀 Upload to GitHub
            github_path = f"public/voices/{file_id}.mp3"
            upload_to_github(filename, github_path)
        f.write(b"dummy content")  # simulate audio file
