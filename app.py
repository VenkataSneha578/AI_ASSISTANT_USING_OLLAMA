import requests
import streamlit as st

#------------------------------
#Page config
#------------------------------
st.set_page_config(
    page_title="AI Assistant - Ollama Chatgpt clone",
    page_icon="🤖",
    layout="centered",
)

#------------------------------
#Custom CSS
#------------------------------
st.markdown("""
<style>
.block-container { max-width: 850px; padding-top: 2rem; }
.hero-card {
    background: linear-gradient(135deg, #111827, #020617);
    border: 1px solid rgba(34,197,94,0.40);
    border-radius: 24px;
    padding: 26px;
    margin-bottom: 20px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.20);
}
.brand-title { font-size: 34px; font-weight: 800; color: #f8fafc; margin-bottom: 6px; }
.brand-subtitle { font-size: 16px; color: #d1d5db; }
.green { color: #22c55e; }
.small-note { color: #9ca3af; font-size: 13px; margin-top: 8px; }
.stButton button {
    border-radius: 12px;
    background-color: #22c55e;
    color: #052e16;
    font-weight: 700;
    border: none;
}
.stButton button:hover { background-color: #16a34a; color: #052e16; }
</style>
""", unsafe_allow_html=True)

#------------------------------
#Header
#------------------------------
st.markdown("""
<div class="hero-card">
    <div class="brand-title">AI Assistant<span class="green">Local AI Chatbot</span></div>
    <div class="brand-subtitle">A ChatGPT clone powered by Ollama API</div>
    <div class="small-note">Generative AI project 1: Chat UI+Memory+Streaming+ Temperature Control using local models</div>
</div>
""", unsafe_allow_html=True)

#-----------------------------
#Ollama Settings
#-----------------------------
OLLAMA_URL = "http://localhost:11434/api/chat"  # Ollama API URL

with st.sidebar:
    st.title("Settings")
    model= st.selectbox("Choose Ollama Model", ["llama3.2", "llama3.1", "llama3", "mistral", "gemma2", "qwen2.5", "qwen2.5:3b"], index=0)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, help="0 = focused/robotic, 1=creative")
    system_prompt= st.text_area("System Prompt", value="You are a helpful assistant. Explain concepts clearly and simply. When useful, respond with examples. ", height=120, help="Set the system prompt for the AI model.")
    if(st.button("Clear Chat History")):
        st.session_state['messages'] = []
        st.success("Chat history cleared!")
        st.rerun()
    st.markdown("---")
    st.markdown("**Note:** This app uses the Ollama API to interact with local AI models. Make sure the Ollama server is running on your machine.")
    st.markdown("-Ollama runs model locally on your machine.")
    st.markdown("-Ollama API is free to use, but you need to install Ollama and download the models you want to use.")
    st.markdown("-Token = word chunk")
    st.markdown("-Temperature = randomness of the response. 0 = focused/robotic, 1=creative")
    st.markdown("LLMs are stateless unless we send history")

#-----------------------------
# Helper function to send messages to Ollama API
#-----------------------------
def check_ollama_running():
    try:
        response = requests.get("http://localhost:11434", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

#-----------------------------
# Session state/Memory
#-----------------------------
if 'messages' not in st.session_state:
    st.session_state.messages = []

#-----------------------------
#Ollama Health Check
#-----------------------------
if not check_ollama_running():
    st.error("Ollama server is not running. Please start the Ollama server on your machine.")
    st.info("Then pull a model using: ollama pull llama3.2")
    st.stop()

#-----------------------------
# Chat input and response handling
#-----------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#-----------------------------
#Chat input
#-----------------------------
user_prompt = st.chat_input("Type your message here...")
if user_prompt:
    #1. Display user message in chat message container
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    #2. Build full messages list for Ollama
    messages_for_ollama = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    #3. Stream response from Ollama API
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            payload={
                "model": model,
                "messages": messages_for_ollama,
                "temperature": temperature,
                "stream": True
            }
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=12) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                       data = line.decode('utf-8')
                       import json
                       chunk = json.loads(data)
                       if "message" in chunk and "content" in chunk["message"]:
                           content = chunk["message"]["content"]
                           full_response += content        
                           response_placeholder.markdown(full_response + "▌")
                       if chunk.get("done", False):
                            break
            response_placeholder.markdown(full_response)
        except requests.exceptions.HTTPError as e:
            full_response =(
                f"Http Error :{str(e)}\n\n"
                f"Most likely the model is not pulled yet. Please pull the model using: `ollama pull {model}`"
                f"Run this command in your terminal and wait for the model to download before trying again."
            )       
            response_placeholder.error(full_response)  
        except Exception as e:
            full_response = f"Error: {str(e)}"
            response_placeholder.error(full_response)
    #4. Store assistant response in memory
    st.session_state.messages.append({"role": "assistant", "content": full_response})
                