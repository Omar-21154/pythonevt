import streamlit as st
import google.generativeai as genai
from PIL import Image
import uuid
import time
import json
import os

# 1. FAYL YADDAŞI AYARI
DB_FILE = "omar_chat_history.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 2. API VƏ MODEL AYARI
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    @st.cache_resource
    def get_model():
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            m_name = next((n for n in available if "1.5-flash" in n), available[0])
            return genai.GenerativeModel(m_name)
        except: return genai.GenerativeModel('gemini-1.5-flash')
    model = get_model()
else:
    st.error("API Key tapılmadı!")
    model = None

# 3. YADDAŞI YÜKLƏ (Açılışda bir dəfə)
if "archives" not in st.session_state:
    st.session_state.archives = load_data()

if not st.session_state.archives:
    uid = str(uuid.uuid4())
    st.session_state.archives[uid] = {"title": "Yeni Söhbət", "msgs": []}
    st.session_state.active_id = uid
    save_data(st.session_state.archives)

if "active_id" not in st.session_state:
    st.session_state.active_id = list(st.session_state.archives.keys())[0]

# 4. SIDEBAR - Arxiv İdarəetməsi
with st.sidebar:
    st.title("🚀 Omar's AI")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        uid = str(uuid.uuid4())
        st.session_state.archives[uid] = {"title": "Yeni Söhbət", "msgs": []}
        st.session_state.active_id = uid
        save_data(st.session_state.archives)
        st.rerun()
    
    st.divider()
    st.subheader("📚 Keçmiş Söhbətlər")
    for c_id, data in list(st.session_state.archives.items()):
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"💬 {data['title'][:15]}", key=f"v_{c_id}", use_container_width=True):
                st.session_state.active_id = c_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"d_{c_id}"):
                del st.session_state.archives[c_id]
                if not st.session_state.archives:
                    uid = str(uuid.uuid4())
                    st.session_state.archives[uid] = {"title": "Yeni Söhbət", "msgs": []}
                    st.session_state.active_id = uid
                elif st.session_state.active_id == c_id:
                    st.session_state.active_id = list(st.session_state.archives.keys())[0]
                save_data(st.session_state.archives)
                st.rerun()

# 5. ƏSAS EKRAN
active_chat = st.session_state.archives.get(st.session_state.active_id)

if active_chat:
    st.header(f"📍 {active_chat['title']}")
    for m in active_chat['msgs']:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    st.divider()
    up_file = st.file_uploader("Şəkil analizi", type=["jpg", "png", "jpeg"])
    prompt = st.chat_input("Mesajınızı yazın...")

    if prompt and model:
        if not active_chat['msgs']: active_chat['title'] = prompt[:20]
        
        active_chat['msgs'].append({"role": "user", "content": prompt})
        save_data(st.session_state.archives) # Hər mesajda yadda saxla
        
        with st.chat_message("user"):
            st.markdown(prompt)
            if up_file: st.image(up_file, width=200)

        with st.chat_message("assistant"):
            try:
                if up_file:
                    res = model.generate_content([prompt, Image.open(up_file)])
                else:
                    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in active_chat['msgs'][:-1]]
                    chat = model.start_chat(history=history)
                    res = chat.send_message(prompt)
                
                st.markdown(res.text)
                active_chat['msgs'].append({"role": "assistant", "content": res.text})
                save_data(st.session_state.archives) # Cavabı da yadda saxla
                
            except Exception as e:
                if "429" in str(e):
                    p = st.empty()
                    for s in range(60, 0, -1):
                        p.warning(f"⏱️ Limit dolub. **{s} saniyə** gözləyin...")
                        time.sleep(1)
                    p.success("✅ İndi yenidən yoxlayın!")
                else: st.error(f"Xəta: {e}")