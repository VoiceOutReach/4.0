{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier;\f1\fnil\fcharset0 AppleColorEmoji;}
{\colortbl;\red255\green255\blue255;\red188\green135\blue186;\red23\green23\blue23;\red202\green202\blue202;
\red113\green171\blue89;\red212\green212\blue212;\red194\green126\blue101;\red67\green192\blue160;\red70\green137\blue204;
\red113\green184\blue255;\red167\green197\blue152;\red212\green214\blue154;\red88\green147\blue206;}
{\*\expandedcolortbl;;\cssrgb\c78824\c61176\c77647;\cssrgb\c11765\c11765\c11765;\cssrgb\c83137\c83137\c83137;
\cssrgb\c50980\c71765\c42353;\cssrgb\c86275\c86275\c86275;\cssrgb\c80784\c56863\c47059;\cssrgb\c30588\c78824\c69020;\cssrgb\c33725\c61176\c83922;
\cssrgb\c50980\c77647\c100000;\cssrgb\c70980\c80784\c65882;\cssrgb\c86275\c86275\c66667;\cssrgb\c41176\c64706\c84314;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs28 \cf2 \cb3 \expnd0\expndtw0\kerning0
import\cf4  streamlit \cf2 as\cf4  st\cb1 \
\cf2 \cb3 import\cf4  pandas \cf2 as\cf4  pd\cb1 \
\cf2 \cb3 import\cf4  openai\cb1 \
\cf2 \cb3 import\cf4  requests\cb1 \
\cf2 \cb3 import\cf4  os\cb1 \
\cf2 \cb3 from\cf4  zipfile \cf2 import\cf4  ZipFile\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 # Config\cf4 \cb1 \
\pard\pardeftab720\partightenfactor0
\cf4 \cb3 st.set_page_config\cf6 (\cf4 page_title=\cf7 "VoiceOutReach"\cf6 ,\cf4  layout=\cf7 "wide"\cf6 )\cf4 \cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 # Upload CSV\cf4 \cb1 \
\pard\pardeftab720\partightenfactor0
\cf4 \cb3 st.title\cf6 (\cf7 "
\f1 \uc0\u55356 \u57241 \u65039 
\f0  VoiceOutReach.ai"\cf6 )\cf4 \cb1 \
\cb3 uploaded_file = st.file_uploader\cf6 (\cf7 "
\f1 \uc0\u55357 \u56548 
\f0  Upload your CSV file"\cf6 ,\cf4  \cf8 type\cf4 =\cf7 "csv"\cf6 )\cf4 \cb1 \
\
\cf2 \cb3 if\cf4  uploaded_file\cf6 :\cf4 \cb1 \
\cb3     df = pd.read_csv\cf6 (\cf4 uploaded_file\cf6 )\cf4 \cb1 \
\cb3     st.write\cf6 (\cf7 "
\f1 \uc0\u55357 \u56522 
\f0  Preview:"\cf6 ,\cf4  df.head\cf6 ())\cf4 \cb1 \
\
\cb3     \cf5 # Toggle: GPT or Template\cf4 \cb1 \
\cb3     use_gpt = st.checkbox\cf6 (\cf7 "
\f1 \uc0\u55357 \u56622 
\f0  Use GPT to generate full message"\cf6 ,\cf4  value=\cf9 True\cf6 )\cf4 \cb1 \
\
\cb3     \cf5 # Prompt or template\cf4 \cb1 \
\cb3     \cf2 if\cf4  use_gpt\cf6 :\cf4 \cb1 \
\cb3         gpt_prompt = st.text_area\cf6 (\cf7 "
\f1 \uc0\u9997 \u65039 
\f0  Your GPT Prompt"\cf6 ,\cf4  \cb1 \
\cb3             \cf7 "Write a LinkedIn message to \{first_name\}, who is a \{position\} at \{company_name\}. "\cf4 \cb1 \
\cb3             \cf7 "I have a candidate for the \{hiring_for_job_title\} role. Be confident and under 60 words."\cf4 \cb1 \
\cb3         \cf6 )\cf4 \cb1 \
\cb3     \cf2 else\cf6 :\cf4 \cb1 \
\cb3         template = st.text_area\cf6 (\cf7 "
\f1 \uc0\u55357 \u56516 
\f0  Your Message Template"\cf6 ,\cf4  \cb1 \
\cb3             \cf7 "Hi \{first_name\}, I saw you're hiring for a \{hiring_for_job_title\} at \{company_name\}. \{quick_jd\} Let's connect!"\cf4 \cb1 \
\cb3         \cf6 )\cf4 \cb1 \
\
\cb3     \cf5 # API keys\cf4 \cb1 \
\cb3     openai_key = st.text_input\cf6 (\cf7 "
\f1 \uc0\u55357 \u56592 
\f0  API KEY\'94\cf6 )\cf4 \cb1 \
\cb3     eleven_key = st.text_input\cf6 (\cf7 \'93API KEY"\cf6 )\cf4 \cb1 \
\cb3     voice_id = st.text_input\cf6 (\cf7 \'93VOICE ID\'94\cf6 )\cf4 \cb1 \
\
\cb3     \cf2 if\cf4  st.button\cf6 (\cf7 "
\f1 \uc0\u55357 \u56960 
\f0  Generate Voice Notes"\cf6 ):\cf4 \cb1 \
\cb3         \cf5 # Prepare output folder\cf4 \cb1 \
\cb3         os.makedirs\cf6 (\cf7 "voice_notes"\cf6 ,\cf4  exist_ok=\cf9 True\cf6 )\cf4 \cb1 \
\cb3         mp3_paths = \cf6 []\cf4 \cb1 \
\
\cb3         openai.api_key = openai_key\cb1 \
\
\cb3         \cf2 for\cf4  idx\cf6 ,\cf4  row \cf10 in\cf4  df.iterrows\cf6 ():\cf4 \cb1 \
\cb3             vars = row.to_dict\cf6 ()\cf4 \cb1 \
\cb3             vars\cf6 [\cf7 "first_name"\cf6 ]\cf4  = vars.get\cf6 (\cf7 "first_name"\cf6 )\cf4  \cf10 or\cf4  vars.get\cf6 (\cf7 "Name"\cf6 ,\cf4  \cf7 ""\cf6 )\cf4 .split\cf6 ()[\cf11 0\cf6 ]\cf4 \cb1 \
\
\cb3             \cf5 # Generate message\cf4 \cb1 \
\cb3             \cf2 if\cf4  use_gpt\cf6 :\cf4 \cb1 \
\cb3                 prompt = gpt_prompt.\cf12 format\cf6 (\cf4 **vars\cf6 )\cf4 \cb1 \
\cb3                 response = openai.ChatCompletion.create\cf6 (\cf4 \cb1 \
\cb3                     model=\cf7 "gpt-3.5-turbo"\cf6 ,\cf4 \cb1 \
\cb3                     messages=\cf6 [\{\cf7 "role"\cf6 :\cf4  \cf7 "user"\cf6 ,\cf4  \cf7 "content"\cf6 :\cf4  prompt\cf6 \}],\cf4 \cb1 \
\cb3                     temperature=\cf11 0.6\cf6 ,\cf4 \cb1 \
\cb3                     max_tokens=\cf11 100\cf4 \cb1 \
\cb3                 \cf6 )\cf4 \cb1 \
\cb3                 message = response.choices\cf6 [\cf11 0\cf6 ]\cf4 .message\cf6 [\cf7 "content"\cf6 ]\cf4 .strip\cf6 ()\cf4 \cb1 \
\cb3             \cf2 else\cf6 :\cf4 \cb1 \
\cb3                 \cf5 # Dummy summary\cf4 \cb1 \
\cb3                 vars\cf6 [\cf7 "quick_jd"\cf6 ]\cf4  = \cf7 "Looking for a skilled expert in the field."\cf4 \cb1 \
\cb3                 message = template.\cf12 format\cf6 (\cf4 **vars\cf6 )\cf4 \cb1 \
\
\cb3             \cf5 # Save MP3 from ElevenLabs\cf4 \cb1 \
\cb3             headers = \cf6 \{\cf4 \cb1 \
\cb3                 \cf7 "xi-api-key"\cf6 :\cf4  eleven_key\cf6 ,\cf4 \cb1 \
\cb3                 \cf7 "Content-Type"\cf6 :\cf4  \cf7 "application/json"\cf4 \cb1 \
\cb3             \cf6 \}\cf4 \cb1 \
\
\cb3             payload = \cf6 \{\cf4 \cb1 \
\cb3                 \cf7 "text"\cf6 :\cf4  message\cf6 ,\cf4 \cb1 \
\cb3                 \cf7 "model_id"\cf6 :\cf4  \cf7 "eleven_multilingual_v2"\cf6 ,\cf4 \cb1 \
\cb3                 \cf7 "voice_settings"\cf6 :\cf4  \cf6 \{\cf4 \cb1 \
\cb3                     \cf7 "stability"\cf6 :\cf4  \cf11 0.5\cf6 ,\cf4 \cb1 \
\cb3                     \cf7 "similarity_boost"\cf6 :\cf4  \cf11 0.7\cf6 ,\cf4 \cb1 \
\cb3                     \cf7 "style_degree"\cf6 :\cf4  \cf11 0.6\cf4 \cb1 \
\cb3                 \cf6 \}\cf4 \cb1 \
\cb3             \cf6 \}\cf4 \cb1 \
\
\cb3             url = \cf13 f\cf7 "https://api.elevenlabs.io/v1/text-to-speech/\cf6 \{\cf4 voice_id\cf6 \}\cf7 "\cf4 \cb1 \
\cb3             response = requests.post\cf6 (\cf4 url\cf6 ,\cf4  headers=headers\cf6 ,\cf4  json=payload\cf6 )\cf4 \cb1 \
\
\cb3             \cf2 if\cf4  response.status_code == \cf11 200\cf6 :\cf4 \cb1 \
\cb3                 filename = \cf13 f\cf7 "voice_notes/\cf6 \{\cf4 vars\cf6 [\cf7 'first_name'\cf6 ]\}\cf7 _\cf6 \{\cf4 idx\cf6 \}\cf7 .mp3"\cf4 \cb1 \
\cb3                 \cf2 with\cf4  \cf12 open\cf6 (\cf4 filename\cf6 ,\cf4  \cf7 "wb"\cf6 )\cf4  \cf2 as\cf4  f\cf6 :\cf4 \cb1 \
\cb3                     f.write\cf6 (\cf4 response.content\cf6 )\cf4 \cb1 \
\cb3                 mp3_paths.append\cf6 (\cf4 filename\cf6 )\cf4 \cb1 \
\cb3             \cf2 else\cf6 :\cf4 \cb1 \
\cb3                 st.warning\cf6 (\cf13 f\cf7 "Error for row \cf6 \{\cf4 idx\cf6 \}\cf7 : \cf6 \{\cf4 response.text\cf6 \}\cf7 "\cf6 )\cf4 \cb1 \
\
\cb3         \cf5 # Zip output\cf4 \cb1 \
\cb3         zip_path = \cf7 "voice_notes_output.zip"\cf4 \cb1 \
\cb3         \cf2 with\cf4  ZipFile\cf6 (\cf4 zip_path\cf6 ,\cf4  \cf7 "w"\cf6 )\cf4  \cf2 as\cf4  zipf\cf6 :\cf4 \cb1 \
\cb3             \cf2 for\cf4  file_path \cf10 in\cf4  mp3_paths\cf6 :\cf4 \cb1 \
\cb3                 zipf.write\cf6 (\cf4 file_path\cf6 )\cf4 \cb1 \
\
\cb3         \cf2 with\cf4  \cf12 open\cf6 (\cf4 zip_path\cf6 ,\cf4  \cf7 "rb"\cf6 )\cf4  \cf2 as\cf4  f\cf6 :\cf4 \cb1 \
\cb3             st.download_button\cf6 (\cf7 "
\f1 \uc0\u55357 \u56549 
\f0  Download All Voice Notes"\cf6 ,\cf4  f\cf6 ,\cf4  file_name=\cf7 "voice_notes.zip"\cf6 )\cf4 \cb1 \
\
\
}