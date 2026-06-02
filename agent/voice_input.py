"""
Voice input using faster-whisper - records from mic and transcribes
"""
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import tempfile
import os
from faster_whisper import WhisperModel

model = None

def load_model():
    global model
    if model is None:
        print("[Voice] Loading Whisper tiny model...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("[Voice] Whisper ready")
    return model

def record_audio(duration=5, sample_rate=16000):
    print(f"[Voice] Recording {duration}s...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='int16'
    )
    sd.wait()
    return audio, sample_rate

def transcribe(audio, sample_rate):
    m = load_model()
    tmp_path = os.path.join(tempfile.gettempdir(), "jarvis_voice.wav")
    wav.write(tmp_path, sample_rate, audio)
    segments, _ = m.transcribe(tmp_path, language="en")
    text = " ".join(s.text for s in segments).strip()
    return text

def listen_once(duration=5):
    audio, sr = record_audio(duration)
    return transcribe(audio, sr)

if __name__ == "__main__":
    load_model()
    print("Say something...")
    text = listen_once(5)
    print(f"You said: {text}")
