# 🧠 Voice pacing helpers
def enhance_pacing(text):
    # Add natural pauses
    text = text.replace('. ', '.... ')
    text = text.replace(', ', ',... ')
    for trigger in ["Hi ", "Hey ", "Thanks", "Let me know", "I noticed"]:
        text = text.replace(trigger, f"{trigger}... ")
    return text

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

        # 📝 Prepare voice message
        message = st.session_state["messages"][idx]
        message = split_long_sentences(message)
        message = enhance_pacing(message)

        # 🎙️ Friendly, human voice settings
        payload = {
            "text": message,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,          # Balanced expressiveness
                "similarity_boost": 0.8,   # Natural voice fidelity
                "style": 0.35              # Human pacing
            }
        }

        headers = {
            "xi-api-key": eleven_api_key,
            "Content-Type": "application/json"
        }

        # 🔁 Call ElevenLabs API
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
                hosted_links.append(f"https://voiceoutreach.ai/voicenote/{file_id}")
            else:
                st.warning(f"⚠️ Voice content too short for {file_id}, skipping.")
        else:
            st.warning(f"❌ ElevenLabs error on row {idx}: {res.text}")

    # 🎧 Playback + links
    st.markdown("### 🔊 Voice Note Previews")
    for i, mp3 in enumerate(mp3_files):
        st.audio(mp3, format='audio/mp3')
        st.markdown(f"[Voice Link]({hosted_links[i]})")

    # 📦 ZIP download
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zipf:
        for mp3 in mp3_files:
            zipf.write(mp3, arcname=os.path.basename(mp3))
    zip_buffer.seek(0)

    st.download_button("📅 Download All Voice Notes", zip_buffer, "voice_notes.zip")
