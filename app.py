import streamlit as st
import google.generativeai as genai
import uuid
import json
import os
from PIL import Image

# --- 1. SƏNİN AI STUDIO TƏLİMATIN ---
# AI Studio-da yazdığın o özəl mətn bura əlavə olundu:
# SİSTEM TƏLİMATINI BELƏ DƏYİŞSƏN DAHA STABİL OLAR:
SİSTEM_TƏLİMATI = """
    Sən Ömərin köməkçisisən. Şəkilləri analiz edə bilirsən. 
    Sol tərəfdəki sidebar-da çat tarixçəsi var. 
    Hər zaman səmimi və Azərbaycan dilində cavab ver.
    """

# --- 2. YADDAŞ SİSTEMİ (JSON) ---
DB_FILE = "omar_chat_history.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

# --- 3. API VƏ MODEL AYARI ---
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = None

# Əvvəlcə secrets-dən baxır, yoxdursa istifadəçidən soruşacaq
main_key = st.secrets.get("GEMINI_API_KEY")
active_key = st.session_state.custom_api_key if st.session_state.custom_api_key else main_key

if active_key:
    genai.configure(api_key=active_key)

# Modeli sənin Playground-da seçdiyin yeni versiya ilə eyniləşdiririk
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", # <--- Dəqiq belə yazıldığına əmin ol
    system_instruction=SİSTEM_TƏLİMATI
)
# --- 4. SESSION STATE BAŞLATMA ---
if "archives" not in st.session_state:
    st.session_state.archives = load_data()

if not st.session_state.archives:
    uid = str(uuid.uuid4())
    st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
    st.session_state.active_id = uid
    save_data(st.session_state.archives)

if "active_id" not in st.session_state:
    st.session_state.active_id = list(st.session_state.archives.keys())[0]

# --- 5. SIDEBAR (TARİXCƏ VƏ SİLMƏK FUNKSİYASI) ---
with st.sidebar:
    st.title("🚀 Omar's AI")
    
    col_new, col_bomb = st.columns([3, 1])
    with col_new:
        if st.button("➕ Yeni Söhbət", use_container_width=True):
            uid = str(uuid.uuid4())
            st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
            st.session_state.active_id = uid
            save_data(st.session_state.archives)
            st.rerun()
    with col_bomb:
        if st.button("💣", help="Bütün tarixçəni sil"):
            st.session_state.archives = {}
            save_data({})
            st.rerun()
    
    st.divider()
    st.subheader("📚 Keçmiş Söhbətlər")
    
    # Söhbətlərin siyahısı və silmə düyməsi
    for c_id, data in list(st.session_state.archives.items()):
        col_chat, col_del = st.columns([4, 1])
        with col_chat:
            if st.button(f"💬 {data['title'][:15]}", key=f"v_{c_id}", use_container_width=True):
                st.session_state.active_id = c_id
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"d_{c_id}"):
                del st.session_state.archives[c_id]
                if not st.session_state.archives:
                    uid = str(uuid.uuid4())
                    st.session_state.archives[uid] = {"title": "Yeni Söhbət 💬", "msgs": []}
                    st.session_state.active_id = uid
                elif st.session_state.active_id == c_id:
                    st.session_state.active_id = list(st.session_state.archives.keys())[0]
                save_data(st.session_state.archives)
                st.rerun()

# --- 6. ƏSAS ÇAT EKRANI ---
active_chat = st.session_state.archives.get(st.session_state.active_id)

if active_chat:
    st.subheader(f"📍 {active_chat['title']}")
    
    # Köhnə mesajları göstər
    for m in active_chat['msgs']:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    st.divider()
    
    # Şəkil yükləmə hissəsi (Vision üçün)
    up_file = st.file_uploader("🖼️ Şəkil analizi", type=["jpg", "png", "jpeg"])
    
    # Mesaj girişi
    prompt = st.chat_input("Mesajınızı yazın...")

    if prompt:
        # İlk mesajdırsa başlığı yenilə
        if not active_chat['msgs']:
            active_chat['title'] = prompt[:20]
        
        # İstifadəçi mesajını göstər və yaddaşa yaz
        with st.chat_message("user"):
            st.markdown(prompt)
        active_chat['msgs'].append({"role": "user", "content": prompt})
        save_data(st.session_state.archives)

        # AI-dan cavab al
        with st.chat_message("assistant"):
            try:
                if up_file:
                    # Şəkilli analiz
                    img = Image.open(up_file)
                    res = model.generate_content([prompt, img])
                else:
                    # Normal çat (son 5 mesajı xatırlayır)
                    history = []
                    for m in active_chat['msgs'][:-1][-5:]:
                        role = "model" if m["role"] == "assistant" else "user"
                        history.append({"role": role, "parts": [m["content"]]})
                    
                    chat = model.start_chat(history=history)
                    res = chat.send_message(prompt)
                
                st.markdown(res.text)
                active_chat['msgs'].append({"role": "assistant", "content": res.text})
                save_data(st.session_state.archives)
                st.rerun()
                
            except Exception as e:
                # Limit və ya 404 xətası çıxarsa dərhal API Key xanası göstər
                if "429" in str(e) or "404" in str(e) or "400" in str(e):
                    st.warning("⏱️ API limitində və ya bağlantıda problem var! Yeni API Key daxil et:")
                    new_key = st.text_input("Gemini API Key:", type="password")
                    if st.button("Açarı Yenilə"):
                        st.session_state.custom_api_key = new_key
                        st.rerun()
                else:
                    st.error(f"Gözlənilməz xəta: {e}")