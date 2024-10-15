import streamlit as st
import requests
import moviepy.editor as mp
from google.cloud import speech
from google.cloud import texttospeech
from pydub import AudioSegment

# Initialize Google Cloud clients
speech_client = speech.SpeechClient()
text_to_speech_client = texttospeech.TextToSpeechClient()

def transcribe_audio(video_file):
    try:
        # Extract audio from video
        audio_file = "audio.wav"
        video_clip = mp.VideoFileClip(video_file)
        video_clip.audio.write_audiofile(audio_file)

        # Convert audio to mono
        audio_segment = AudioSegment.from_wav(audio_file)
        audio_segment = audio_segment.set_channels(1)  # Set to mono
        audio_segment.export(audio_file, format="wav")

        # Get sample rate
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
        return " ".join([result.alternatives[0].transcript for result in response.results])

    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return ""

def correct_transcription(transcription):
    # Add your transcription correction logic here if needed
    return transcription  # Returning unchanged for now

def generate_audio(corrected_text):
    try:
        synthesis_input = texttospeech.SynthesisInput(text=corrected_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-D",  # You can change the voice if needed
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )

        response = text_to_speech_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open("new_audio.mp3", "wb") as out:
            out.write(response.audio_content)

    except Exception as e:
        st.error(f"Error generating audio: {e}")

def replace_audio(video_file):
    try:
        video_clip = mp.VideoFileClip(video_file)
        new_audio = mp.AudioFileClip("new_audio.mp3")
        final_video = video_clip.set_audio(new_audio)
        final_video.write_videofile("final_video.mp4")
    except Exception as e:
        st.error(f"Error replacing audio: {e}")

def main():
    st.title("AI-Powered Audio Replacement")

    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "mov"])

    if uploaded_file is not None:
        with open("temp_video.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Video uploaded successfully!")

        if st.button("Process Video"):
            transcription = transcribe_audio("temp_video.mp4")
            if transcription:
                corrected_text = correct_transcription(transcription)
                generate_audio(corrected_text)
                replace_audio("temp_video.mp4")
                st.success("Audio replacement completed!")
                st.video("final_video.mp4")

if __name__ == "__main__":
    main()
