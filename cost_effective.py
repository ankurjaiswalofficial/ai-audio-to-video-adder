import streamlit as st
import moviepy.editor as mp
import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI
import os
from dotenv import load_dotenv
import pyttsx3

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Speech recognition could not understand the audio"
    except sr.RequestError:
        return "Could not request results from the speech recognition service"

def correct_text(text):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",  # Using GPT-3.5-turbo instead of GPT-4 to reduce costs
        messages=[
            {"role": "system", "content": "You are a helpful assistant that corrects grammatical mistakes and removes filler words."},
            {"role": "user", "content": f"Please correct the following text, removing grammatical mistakes and filler words: {text}"}
        ]
    )
    return response.choices[0].message['content']

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.save_to_file(text, 'output.mp3')
    engine.runAndWait()

def replace_audio(video_path, audio_path):
    video = mp.VideoFileClip(video_path)
    audio = mp.AudioFileClip(audio_path)

    final_clip = video.set_audio(audio)
    final_clip.write_videofile("output_video.mp4")

def main():
    st.title("Video Audio Replacement PoC")
    temp_vid = "temp_video.mp4"
    uploaded_file = st.file_uploader("Choose a video file", type=["mp4"])

    if uploaded_file is not None:
        st.video(uploaded_file)

        if st.button("Process Video"):
            with st.spinner("Processing..."):
                # Save uploaded video
                with open(temp_vid, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Extract audio from video
                video = mp.VideoFileClip(temp_vid)
                video.audio.write_audiofile("temp_audio.wav")

                # Transcribe audio
                transcription = transcribe_audio("temp_audio.wav")
                st.text("Original Transcription:")
                st.write(transcription)

                # Correct transcription
                corrected_text = correct_text(transcription)
                st.text("Corrected Transcription:")
                st.write(corrected_text)

                # Generate new audio
                text_to_speech(corrected_text)

                # Replace audio in video
                replace_audio(temp_vid, "output.mp3")

                st.success("Processing complete!")
                st.video("output_video.mp4")

if __name__ == "__main__":
    main()
