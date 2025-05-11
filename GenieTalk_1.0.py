import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import os
import threading
from PyPDF2 import PdfReader
from googletrans import Translator
from datetime import datetime

# Load .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

translator = Translator()


# Setup TTS (Text-to-Speech)
tts = pyttsx3.init()
def speak(text):
    def _speak():
        tts.say(text)
        tts.runAndWait()
    threading.Thread(target=_speak).start()

# Voice recognition function
def recognize_voice():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        st.info("🎤 Listening...")
        audio = recognizer.listen(source, phrase_time_limit=8)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.warning("🤔 Couldn't understand your voice.")
        return None
    except sr.RequestError:
        st.error("⚠️ Voice recognition failed.")
        return None

# PDF extraction helper
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Streamlit config
st.set_page_config(page_title="Smart Gemini Chatbot", page_icon="🧠", layout="centered")
st.title("🤖 Chatbot -> for YOU")
st.info("👋 Welcome! Choose a task from the sidebar, upload a file if needed, then chat via text or voice.")

# Sidebar: task selection and file upload
with st.sidebar:
    st.header("📄 Your Task")
    task = st.selectbox("🧠 What do you want help with?", [
        "General Advice", "Coding Help", "Emotional Support", "Resume Review",
        "Math Problem Solver", "Text Summarizer", "AI/ML Tutor"
    ])
    uploaded_file = st.file_uploader("📄 Upload a file (txt/pdf)", type=["txt", "pdf"])

    st.divider()

    lang_map = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Tamil": "ta",
    "Bengali": "bn"
    }
    language = st.selectbox("🌐 Response Language", list(lang_map.keys()), index=0)
    target_lang = lang_map[language]


# Load uploaded file content
file_content = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        file_content = extract_text_from_pdf(uploaded_file)
    else:
        file_content = uploaded_file.read().decode("utf-8")

# Initialize session
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Clear chat button
if st.button("🗑️ Clear Chat"):
    st.session_state.chat_history = []
    st.session_state.chat_session = model.start_chat(history=[])

# Task instructions
prompt_map = {
    "Coding Help": "You're an expert software developer. Help with code, errors, or logic.",
    "Emotional Support": "You're a compassionate assistant. Provide kind and supportive advice.",
    "Resume Review": "You're a career coach. Review and improve resume content.",
    "Math Problem Solver": "You're a math tutor. Solve step-by-step with reasoning.",
    "Text Summarizer": "You're a smart summarizer. Condense the following content clearly.",
    "AI/ML Tutor": "You're a skilled ML/AI tutor. Explain concepts clearly and practically.",
    "General Advice": "You're a helpful assistant. Answer clearly and usefully."
}
system_prompt = prompt_map.get(task, "You're a helpful assistant.")

# Optional suggestion hints
suggestions = {
    "Resume Review": "💡 Try: *How can I improve my experience section?*",
    "Coding Help": "💡 Try: *Why does my Python loop not work?*",
    "AI/ML Tutor": "💡 Try: *Explain overfitting vs underfitting.*",
    "Math Problem Solver": "💡 Try: *Solve x^2 + 3x + 2 = 0 step-by-step.*"
}
if task in suggestions:
    st.markdown(suggestions[task])

# Chat history
st.divider()
st.subheader("🕒 Your Chat")
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# Optional summarization for uploaded file
if task == "Text Summarizer" and file_content:
    if st.button("📄 Summarize Uploaded Content"):
        full_prompt = f"{system_prompt}\n\n{file_content}"
        try:
            response = st.session_state.chat_session.send_message(full_prompt)

            reply = response.text
            # Translate if needed
            if target_lang != "en":
                try:
                    translated = translator.translate(reply, dest=target_lang).text
                    reply = f"{translated} \n\n🌐 (Original in English):\n{response.text}"
                except Exception as e:
                    st.warning("⚠️ Translation failed. Showing original.")

            st.chat_message("assistant").markdown(reply)
            speak(reply)
            st.session_state.chat_history.append(("user", "[Summarize File]"))
            st.session_state.chat_history.append(("assistant", reply))
        except Exception as e:
            st.error("⚠️ Could not summarize file.")
            with st.expander("Error details"):
                st.exception(e)

# Voice input
if st.button("🎤 Speak Now"):
    with st.spinner("Listening..."):
        voice_input = recognize_voice()
        if voice_input:
            st.chat_message("user").markdown(f"🗣️ {voice_input}")
            file_info = f"\n\nFile Content:\n{file_content}" if file_content and task in ["Resume Review", "Text Summarizer"] else ""
            full_prompt = f"{system_prompt}\n\nUser Input:\n{voice_input}{file_info}"
            try:
                response = st.session_state.chat_session.send_message(full_prompt)
                reply = response.text
                # Translate if needed
                if target_lang != "en":
                    try:
                        translated = translator.translate(reply, dest=target_lang).text
                        reply = f"{translated} \n\n🌐 (Original in English):\n{response.text}"
                    except Exception as e:
                        st.warning("⚠️ Translation failed. Showing original.")

                st.chat_message("assistant").markdown(reply)
                speak(reply)
                st.session_state.chat_history.append(("user", voice_input))
                st.session_state.chat_history.append(("assistant", reply))
            except Exception as e:
                st.error("⚠️ Something went wrong. Please try again.")
                with st.expander("Error details"):
                    st.exception(e)

# Text input
user_input = st.chat_input("Type here or use voice input...")
if user_input:
    st.chat_message("user").markdown(user_input)
    file_info = f"\n\nFile Content:\n{file_content}" if file_content and task in ["Resume Review", "Text Summarizer"] else ""
    full_prompt = f"{system_prompt}\n\nUser Input:\n{user_input}{file_info}"
    try:
        response = st.session_state.chat_session.send_message(full_prompt)
        reply = response.text
        st.chat_message("assistant").markdown(reply)
        speak(reply)
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("assistant", reply))
    except Exception as e:
        st.error("⚠️ Something went wrong. Please try again.")
        with st.expander("Error details"):
            st.exception(e)

if st.button("💾 Download Chat History"):
    chat_text = ""
    for role, msg in st.session_state.chat_history:
        chat_text += f"{role.upper()}:\n{msg}\n\n"
    filename = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    st.download_button("⬇️ Save Chat as Text File", data=chat_text, file_name=filename, mime="text/plain")

# streamlit run "C:\Users\Akash\Desktop\chatbot gemini\z.py"
