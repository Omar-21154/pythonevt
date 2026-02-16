import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. MODUL VƏ MODEL AYARI
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    @st.cache_resource
    def load_model():
        # 404 xətasını aradan qaldırmaq üçün sistemdəki aktiv modeli tapır
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if "1.5-flash" in m.name: return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-1.5-flash')
    model = load_model()
else:
    st.error("API Key tapılmadı!")

# 2. SESSİYA YADDAŞI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. MESAJLARI GÖSTƏR
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. İNPUT VƏ ŞƏKİL (İnputun tam üstündə, sanki daxilindəymiş kimi)
st.write("---") # Sərhəd qoyuruq
cols = st.columns([1, 6]) # Şəkil düyməsi üçün kiçik, yazı üçün böyük sütun

with cols[0]:
    # Şəkil yükləmə düyməsi (ikon kimi görünür)
    uploaded_file = st.file_uploader("🖼️", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

with cols[1]:
    # Yazı inputu
    user_input = st.chat_input("Nəsə yazın...")

# 5. MƏNTİQ
if user_input:
    # İstifadəçi mesajını göstər
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        if uploaded_file: st.image(uploaded_file, width=200)

    # AI Cavabı
    with st.chat_message("assistant"):
        try:
            if uploaded_file:
                img = Image.open(uploaded_file)
                response = model.generate_content([user_input, img])
            else:
                response = model.generate_content(user_input)
            
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Xəta: {e}")