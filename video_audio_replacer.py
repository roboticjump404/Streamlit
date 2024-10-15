import streamlit as st
import openai
import requests
import json
import moviepy.editor as mp
from google.cloud import speech
from google.cloud import texttospeech
from pydub import AudioSegment  

# Initialize Google clients
speech_client = speech.SpeechClient()
text_to_speech_client = texttospeech.TextToSpeechClient()

def transcribe_audio(video_file):
    # Extract audio from video
    audio_file = "audio.wav"
    video_clip = mp.VideoFileClip(video_file)
    video_clip.audio.write_audiofile(audio_file)

    # Convert audio to mono and saving it
    audio_segment = AudioSegment.from_wav(audio_file)
    audio_segment = audio_segment.set_channels(1)  # Set to mono
    audio_segment.export(audio_file, format="wav")  # Export as mono WAV

    # pydub to get the sample rate of the audio
    sample_rate = audio_segment.frame_rate

    # Transcribe audio using Google Speech-to-Text
    with open(audio_file, "rb") as audio:
        audio_content = audio.read()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="en-US",
    )

    response = speech_client.recognize(config=config, audio=audio)
    # Join transcriptions
    return " ".join([result.alternatives[0].transcript for result in response.results])

def correct_transcription(transcription):
    azure_openai_key = "22ec84421ec24230a3638d1b51e3a7dc"
    azure_openai_endpoint = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_key,
    }

    data = {
        "messages": [{"role": "user", "content": transcription}],
        "max_tokens": 1000,
    }

    response = requests.post(azure_openai_endpoint, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.error("Error correcting transcription.")
        return transcription

def generate_audio(corrected_text):
    synthesis_input = texttospeech.SynthesisInput(text=corrected_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D",
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    response = text_to_speech_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open("new_audio.mp3", "wb") as out:
        out.write(response.audio_content)

def replace_audio(video_file):
    video_clip = mp.VideoFileClip(video_file)
    new_audio = mp.AudioFileClip("new_audio.mp3")
    final_video = video_clip.set_audio(new_audio)
    final_video.write_videofile("final_video.mp4")

def main():
    st.title("Video Audio Replacement with AI Voice")

    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "mov", "mpeg4"])

    if uploaded_file is not None:
        with open("temp_video.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Video uploaded successfully!")

        if st.button("Process Video"):
            transcription = transcribe_audio("temp_video.mp4")
            corrected_text = correct_transcription(transcription)
            generate_audio(corrected_text)
            replace_audio("temp_video.mp4")

            st.success("Audio replacement completed!")
            st.video("final_video.mp4")

if __name__ == "__main__":
    main()
