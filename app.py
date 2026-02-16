import streamlit as st
import google.generativeai as genai
from PIL import Image
import uuid

# 1. 404 XƏTASINI KÖKÜNDƏN KƏSƏN MODEL YÜKLƏYİCİ
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    @st.cache_resource
    def get_model():
        # Əgər standart ad işləməsə, sistemdə mövcud olan ilk uyğun modeli tapır
        try:
            # Sənin mühitində hansı modellər var, onları yoxlayır
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if available_models:
                # Siyahıda 1.5-flash varsa onu seç, yoxdursa birincini götür
                flash_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
                return genai.GenerativeModel(flash_model)
        except:
            # Heç nə tapılmasa məcburi bu adı yoxla
            return genai.GenerativeModel('gemini-1.5-flash')
    
    model = get_model()
else:
    st.error("API Key tapılmadı! Secrets bölməsinə əlavə edin.")

# 2. UI AYARLARI
st.set_page_config(page_title="Omar's AI", layout="wide")
st.markdown("""
    <style>
    .stApp { background: transparent !important; }
    .main-container { max-width: 900px; margin: auto; }
    .stChatInputContainer { padding-bottom: 10px; }
    /* Şəkil yükləmə qutusunu kiçiltmək */
    .stFileUploader section { padding: 0px 10px !important; min-height: 80px !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. YADDAŞ (Session State)
if "archives" not in st.session_state: st.session_state.archives = {}
if "active_id" not in st.session_state:
    uid = str(uuid.uuid4())
    st.session_state.archives[uid] = {"title": "Yeni Söhbət", "msgs": []}
    st.session_state.active_id = uid

# 4. SIDEBAR - Arxiv
with st.sidebar:
    st.title("🚀 Omar's AI")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        uid = str(uuid.uuid4())
        st.session_state.archives[uid] = {"title": "Yeni Söhbət", "msgs": []}
        st.session_state.active_id = uid
        st.rerun()
    
    st.divider()
    st.subheader("📚 Arxiv")
    for c_id, data in list(st.session_state.archives.items()):
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"💬 {data['title'][:15]}", key=f"v_{c_id}", use_container_width=True):
                st.session_state.active_id = c_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"d_{c_id}"):
                del st.session_state.archives[c_id]
                if not st.session_state.archives or st.session_state.active_id == c_id:
                    uid = str(uuid.uuid4())
                    st.session_state.archives[uid] = {"title": "Yeni Söhbət", "msgs": []}
                    st.session_state.active_id = uid
                st.rerun()

# 5. ƏSAS EKRAN
active_chat = st.session_state.archives.get(st.session_state.active_id)
if active_chat:
    st.header(f"📍 {active_chat['title']}")
    
    # Mesaj tarixçəsi
    for msg in active_chat['msgs']:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # ---------------------------------------------------------
    # İNPUT SAHƏSİ (Şəkil + Yazı birlikdə)
    # ---------------------------------------------------------
    st.write("---")
    
    # Şəkil yükləmə (İnputun dərhal üstündə)
    img_file = st.file_uploader("🖼️ Şəkil analizi üçün bura klikləyin", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if img_file:
        st.image(img_file, width=150, caption="Analiz üçün hazır")

    # Yazı inputu
    prompt = st.chat_input("Sualınızı bura yazın...")

    if prompt:
        # Başlıq qoyma
        if not active_chat['msgs']: active_chat['title'] = prompt[:20]
        
        active_chat['msgs'].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                if img_file:
                    # Şəkil analizi
                    img = Image.open(img_file)
                    res = model.generate_content([prompt, img])
                else:
                    # Normal çat (Yaddaşla)
                    history = [{"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]} for m in active_chat['msgs'][:-1]]
                    chat = model.start_chat(history=history)
                    res = chat.send_message(prompt)
                
                st.markdown(res.text)
                active_chat['msgs'].append({"role": "assistant", "content": res.text})
                st.session_state.archives[st.session_state.active_id] = active_chat
            except Exception as e:
                if "429" in str(e):
                    st.warning("⏱️ Limit dolub, 1 dəqiqə gözləyin.")
                else:
                    st.error(f"Xəta: {e}")