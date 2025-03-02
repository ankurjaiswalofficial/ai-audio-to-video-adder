import streamlit as st
import moviepy.editor as mp
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import openai
import os
from pydub import AudioSegment

# Set up Google Cloud credentials
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/google_credentials.json"

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAPI_KEY")


def transcribe_audio(audio_file):
    client = speech.SpeechClient()

    with open(audio_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    return " ".join([result.alternatives[0].transcript for result in response.results])


def correct_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that corrects grammatical mistakes and removes filler words."},
            {"role": "user",
             "content": f"Please correct the following text, removing grammatical mistakes and filler words: {text}"}
        ]
    )
    return response.choices[0].message['content']


def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F",
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open("./output.mp3", "wb") as out:
        out.write(response.audio_content)


def replace_audio(video_path, audio_path):
    video = mp.VideoFileClip(video_path)
    audio = mp.AudioFileClip(audio_path)

    final_clip = video.set_audio(audio)
    final_clip.write_videofile("output_video.mp4")


def main():
    st.title("Video Audio Replacement PoC")

    uploaded_file = st.file_uploader("Choose a video file", type=["mp4"])

    if uploaded_file is not None:
        st.video(uploaded_file)

        if st.button("Process Video"):
            with st.spinner("Processing..."):
                # Save uploaded video
                with open("./temp_video.mp4", "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Extract audio from video
                video = mp.VideoFileClip("./temp_video.mp4")
                video.audio.write_audiofile("./temp_audio.wav")

                # Transcribe audio
                transcription = transcribe_audio("./temp_audio.wav")
                st.text("Original Transcription:")
                st.write(transcription)

                # Correct transcription
                corrected_text = correct_text(transcription)
                st.text("Corrected Transcription:")
                st.write(corrected_text)

                # Generate new audio
                text_to_speech(corrected_text)

                # Replace audio in video
                replace_audio("./temp_video.mp4", "./output.mp3")

                st.success("Processing complete!")
                st.video("./output_video.mp4")


if __name__ == "__main__":
    main()
