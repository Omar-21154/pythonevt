import streamlit as st
from huggingface_hub import InferenceClient
import uuid
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="Universal AI", page_icon="🌐", layout="wide")

# --- ✨ MODERN VISUALS ---
st.markdown("""
    <style>
        @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .stChatMessage { animation: slideUp 0.4s ease-out; border-radius: 12px; }
        .stButton button { border-radius: 8px; transition: all 0.2s ease; }
    </style>
""", unsafe_allow_html=True)

# 2. DATA MANAGEMENT
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
    st.session_state.chats[new_id] = {"name": "New Chat", "messages": []}
    st.session_state.current_chat_id = new_id
    save_data(st.session_state.chats)

# 3. INITIALIZATION
if "chats" not in st.session_state:
    st.session_state.chats = load_data()
    if not st.session_state.chats:
        create_new_chat()
    else:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[-1]

# 4. SIDEBAR
with st.sidebar:
    st.title("🌐 Universal AI")
    if st.button("➕ Start New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()
    st.write("📜 **History**")
    
    for chat_id in list(st.session_state.chats.keys()):
        chat_data = st.session_state.chats[chat_id]
        is_active = (st.session_state.current_chat_id == chat_id)
        
        col1, col2 = st.columns([0.82, 0.18])
        with col1:
            display_name = "New Chat" if chat_data['name'] == "Yeni Söhbət" else chat_data['name']
            btn_label = f"💬 {display_name}" if is_active else display_name
            if st.button(btn_label, key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chats[chat_id]
                if not st.session_state.chats: create_new_chat()
                elif st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[-1]
                save_data(st.session_state.chats)
                st.rerun()

# 5. MAIN INTERFACE
token = st.secrets.get("HF_TOKEN")
client = InferenceClient(model="meta-llama/Llama-3.1-8B-Instruct", token=token)

if st.session_state.current_chat_id:
    curr_chat = st.session_state.chats[st.session_state.current_chat_id]
    title_name = "New Chat" if curr_chat['name'] == "Yeni Söhbət" else curr_chat['name']
    st.title(f"🚀 {title_name}")

    for msg in curr_chat["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me anything..."):
        curr_chat["messages"].append({"role": "user", "content": prompt})
        if len(curr_chat["messages"]) == 1:
            curr_chat["name"] = prompt[:20] + "..."
        save_data(st.session_state.chats)
        st.rerun()

# --- 🧠 AI LOGIC WITH CREATOR INFO ---
if st.session_state.current_chat_id and st.session_state.chats[st.session_state.current_chat_id]["messages"]:
    if st.session_state.chats[st.session_state.current_chat_id]["messages"][-1]["role"] == "user":
        with st.chat_message("assistant"):
            # BURA ƏLAVƏ EDİLDİ: Bot artıq Öməri (səni) tanıyır!
            SYSTEM_PROMPT = """You are a helpful AI assistant. 
            Knowledge: You were developed by Omar (Ömər) using Python and Streamlit. 
            If anyone asks about your creator or Omar, say: 'Omar is my developer/creator who built me using Python.'
            Rule: Always respond in the language the user uses."""
            
            few_shot = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Who created you?"},
                {"role": "assistant", "content": "I was created by Omar using Python and Streamlit."},
                {"role": "user", "content": "Ömər kimdir?"},
                {"role": "assistant", "content": "Ömər mənim yaradıcımdır. O məni Python proqramlaşdırma dili və Streamlit kitabxanası vasitəsilə hazırlayıb."}
            ]
            
            full_msgs = few_shot + st.session_state.chats[st.session_state.current_chat_id]["messages"]
            
            try:
                def response_generator():
                    stream = client.chat_completion(messages=full_msgs, max_tokens=1500, temperature=0.3, stream=True)
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
                st.error(f"Error: {e}")