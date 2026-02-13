import streamlit as st
from huggingface_hub import InferenceClient
import uuid
import json
import os

# 1. Səhifə Ayarları
st.set_page_config(page_title="Universal AI", page_icon="🌐", layout="wide")

# --- ✨ MODERN VİSUAL VƏ HAMARLIQ ---
st.markdown("""
    <style>
        /* Mesaj animasiyası */
        @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .stChatMessage { animation: slideUp 0.4s ease-out; border-radius: 12px; }
        
        /* Sidebar düymələri - daha zərif */
        .stButton button {
            border-radius: 8px;
            transition: all 0.2s ease;
            border: 1px solid rgba(151, 151, 151, 0.1) !important;
            background-color: transparent;
        }
        
        /* Silmə düyməsi üçün xüsusi stil (balaca və qırmızımtıl hover) */
        div[data-testid="column"] button:contains("🗑️") {
            border: none !important;
            color: #ff4b4b !important;
            font-size: 14px;
        }
        
        div[data-testid="column"] button:contains("🗑️"):hover {
            background-color: rgba(255, 75, 75, 0.1) !important;
        }

        [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        .main { scroll-behavior: smooth; }
    </style>
""", unsafe_allow_html=True)

# 2. DAİMİ YADDAŞ
DB_FILE = "chat_history.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"name": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = new_id
    save_data(st.session_state.chats)

# 3. İLKİN YÜKLƏMƏ
if "chats" not in st.session_state:
    st.session_state.chats = load_data()
    if not st.session_state.chats:
        create_new_chat()
    else:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[-1]

# 4. SIDEBAR
with st.sidebar:
    st.title("🌐 Universal AI")
    if st.button("➕ Yeni Çat Başlat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()
    st.write("📜 **Tarixçə**")
    
    # Söhbətləri siyahıla
    for chat_id in list(st.session_state.chats.keys()):
        chat_data = st.session_state.chats[chat_id]
        
        # Aktiv çatı vurğulamaq üçün vizual fərq
        is_active = (st.session_state.current_chat_id == chat_id)
        
        col1, col2 = st.columns([0.82, 0.18])
        with col1:
            btn_label = f"💬 {chat_data['name']}" if is_active else chat_data['name']
            if st.button(btn_label, key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chats[chat_id]
                
                # Əgər heç bir çat qalmayıbsa, dərhal yenisini yarat
                if not st.session_state.chats:
                    create_new_chat()
                else:
                    # Əgər sildiyimiz aktiv çat idisə, ən sonuncunu seç
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[-1]
                
                save_data(st.session_state.chats)
                st.rerun()

# 5. ƏSAS ÇAT SAHƏSİ
token = st.secrets.get("HF_TOKEN")
client = InferenceClient(model="meta-llama/Llama-3.1-8B-Instruct", token=token)

if st.session_state.current_chat_id:
    curr_chat = st.session_state.chats[st.session_state.current_chat_id]
    
    st.title(f"🚀 {curr_chat['name']}")

    for msg in curr_chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Nə soraqlayırsan?"):
        curr_chat["messages"].append({"role": "user", "content": prompt})
        
        # Adı ilk mesajla yenilə
        if len(curr_chat["messages"]) == 1:
            curr_chat["name"] = prompt[:20] + "..."
            
        save_data(st.session_state.chats)
        st.rerun()

# AI CAVAB MƏNTİQİ
if st.session_state.current_chat_id and st.session_state.chats[st.session_state.current_chat_id]["messages"]:
    if st.session_state.chats[st.session_state.current_chat_id]["messages"][-1]["role"] == "user":
        with st.chat_message("assistant"):
            SYSTEM_PROMPT = "Sən ağıllı bir asistansan. İstifadəçi hansı dildə müraciət edərsə, həmin dildə cavab ver."
            
            try:
                def response_generator():
                    stream = client.chat_completion(
                        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.chats[st.session_state.current_chat_id]["messages"],
                        max_tokens=1500,
                        temperature=0.4,
                        stream=True
                    )
                    full_resp = ""
                    for chunk in stream:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_resp += content
                            yield content
                    st.session_state.chats[st.session_state.current_chat_id]["messages"].append({"role": "assistant", "content": full_resp})
                    save_data(st.session_state.chats)

                st.write_stream(response_generator())
            except Exception as e:
                st.error(f"Xəta: {e}")