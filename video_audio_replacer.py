import streamlit as st
import moviepy.editor as mp
from google.cloud import speech
from google.cloud import texttospeech
from pydub import AudioSegment
import os

# Initialize Google clients
speech_client = speech.SpeechClient()
text_to_speech_client = texttospeech.TextToSpeechClient()


def transcribe_audio(video_file):
    try:
        # Extract audio from video
        audio_file = "audio.wav"
        video_clip = mp.VideoFileClip(video_file)
        video_clip.audio.write_audiofile(audio_file, bitrate="64k")  # Lower bitrate for faster extraction
        st.info("Audio extracted from video.")

        # Convert audio to mono
        audio_segment = AudioSegment.from_wav(audio_file)
        audio_segment = audio_segment.set_channels(1)  # Set to mono
        audio_segment.export(audio_file, format="wav")
        st.info("Audio converted to mono.")

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
        st.info("Transcription completed.")
        return " ".join([result.alternatives[0].transcript for result in response.results])

    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return ""


def correct_transcription(transcription):
    # Placeholder for transcription correction
    return transcription


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
        st.info("Audio generated successfully.")

    except Exception as e:
        st.error(f"Error generating audio: {e}")


def replace_audio(video_file):
    try:
        # Load the video file
        video_clip = mp.VideoFileClip(video_file)

        # Load the new audio file
        new_audio = mp.AudioFileClip("new_audio.mp3")

        # Replace the audio in the video
        final_video = video_clip.set_audio(new_audio)

        # Save the new video with replaced audio
        final_video.write_videofile("final_video.mp4", threads=4)  # Use multiple threads to speed up video export

        # Close the video and audio clips to free up resources
        video_clip.close()
        new_audio.close()
        final_video.close()

        st.info("Audio replaced in video and video saved as final_video.mp4.")

    except Exception as e:
        st.error(f"Error replacing audio: {e}")


def clean_up():
    # Remove temporary files after processing
    if os.path.exists("audio.wav"):
        os.remove("audio.wav")
    if os.path.exists("new_audio.mp3"):
        os.remove("new_audio.mp3")
    if os.path.exists("temp_video.mp4"):
        try:
            os.remove("temp_video.mp4")
        except Exception as e:
            st.error(f"Error cleaning up video file: {e}")
    st.info("Temporary files cleaned up.")


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
                st.write(f"Transcription:\n{transcription}")
                corrected_text = correct_transcription(transcription)
                generate_audio(corrected_text)
                replace_audio("temp_video.mp4")
                st.success("Audio replacement completed!")
                st.video("final_video.mp4")

                # Provide download link for the video
                with open("final_video.mp4", "rb") as f:
                    st.download_button("Download the final video", f, file_name="final_video.mp4")

            clean_up()  # Clean up temp files after processing


if __name__ == "__main__":
    main()
