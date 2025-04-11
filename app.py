import pyttsx3
import streamlit as st
import tempfile
import os

def get_voices():
    engine = pyttsx3.init()
    return engine.getProperty('voices')

def synthesize_speech(text, voice_index=0, save_file=False):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[voice_index].id)
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    if save_file:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        engine.save_to_file(text, temp_file.name)
        engine.runAndWait()
        return temp_file.name
    else:
        engine.say(text)
        engine.runAndWait()
        return None

# Streamlit UI
st.title("🗣️ Text to Speech Converter")

user_text = st.text_area("Enter text:", "Hello, this is a demo of text to speech.")
voices = get_voices()
voice_names = [f"{i}: {v.name}" for i, v in enumerate(voices)]
voice_index = st.selectbox("Select a voice:", range(len(voice_names)), format_func=lambda x: voice_names[x])
save_option = st.checkbox("Save to MP3 file")

if st.button("Convert"):
    output_file = synthesize_speech(user_text, voice_index, save_option)
    st.success("Speech conversion complete!")

    if output_file:
        with open(output_file, "rb") as f:
            st.download_button("Download MP3", f, file_name="speech.mp3", mime="audio/mpeg")
        os.remove(output_file)
