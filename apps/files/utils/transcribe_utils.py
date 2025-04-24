import os
import speech_recognition as sr
from moviepy import VideoFileClip
import tempfile


def speech_to_text(file):
    r = sr.Recognizer()

    if hasattr(file, "read"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(file.read())
            temp_audio_path = temp_audio.name
    else:
        temp_audio_path = file

    with sr.AudioFile(temp_audio_path) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)

    return text


def extract_audio_from_video(video_file, audio_path="temp_audio.wav"):
    with tempfile.NamedTemporaryFile(delete = False, suffix = ".mp4") as temp_video:
        for chunk in video_file.chunks():
            temp_video.write(chunk)
        temp_video_path = temp_video.name

    video = VideoFileClip(temp_video_path)
    video.audio.write_audiofile(audio_path)

    return audio_path


def video_to_text(video_file):
    audio_path = extract_audio_from_video(video_file)
    text = speech_to_text(audio_path)
    os.remove(audio_path)
    return text
