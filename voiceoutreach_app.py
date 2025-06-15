# ✅ Clean VoiceOutReach App with GitHub upload

import streamlit as st
import pandas as pd
import openai
import requests
import os
import random
from zipfile import ZipFile
from io import BytesIO
import base64

def upload_to_github(filename, repo_path):
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

    put_res = requests.put(api_url, headers=headers, json=data)
    if put_res.status_code not in (200, 201):
        st.warning(f"GitHub upload failed: {put_res.status_code}")
