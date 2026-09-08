"""
VERONICA Always-On Mic
Continuously listens and sends to agent
"""
import sounddevice as sd
import numpy as np
import threading
import requests
import time
import queue
import wave
import tempfile
import os

SAMPLE_RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 0.015
SILENCE_DURATION = 1.5  # seconds of silence before sending
MIN_SPEECH_DURATION = 0.5  # minimum speech before sending
AGENT_URL = "http://127.0.0.1:8765/listen_raw"

audio_queue = queue.Queue()
is_speaking = False  # don't listen while VERONICA speaks

def rms(data):
    return np.sqrt(np.mean(data**2))

def listen_forever():
    global is_speaking
    print("[AlwaysOn] Mic started — always listening...")
    
    buffer = []
    silence_frames = 0
    speech_frames = 0
    recording = False
    frames_per_chunk = int(SAMPLE_RATE * CHUNK / SAMPLE_RATE)
    silence_limit = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK)
    min_speech = int(MIN_SPEECH_DURATION * SAMPLE_RATE / CHUNK)

    def callback(indata, frames, time_info, status):
        if not is_speaking:
            audio_queue.put(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                       blocksize=CHUNK, dtype='float32',
                       callback=callback):
        while True:
            try:
                data = audio_queue.get(timeout=0.5)
                volume = rms(data)

                if volume > SILENCE_THRESHOLD:
                    if not recording:
                        recording = True
                        buffer = []
                        speech_frames = 0
                        print("[AlwaysOn] Speech detected...")
                    buffer.append(data)
                    speech_frames += 1
                    silence_frames = 0
                else:
                    if recording:
                        silence_frames += 1
                        buffer.append(data)
                        if silence_frames > silence_limit:
                            if speech_frames >= min_speech:
                                audio_data = np.concatenate(buffer)
                                threading.Thread(
                                    target=send_audio,
                                    args=(audio_data,),
                                    daemon=True
                                ).start()
                            recording = False
                            buffer = []
                            silence_frames = 0
                            speech_frames = 0
            except queue.Empty:
                pass

def send_audio(audio_data):
    """Send audio to agent for transcription."""
    try:
        # Save to temp WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp_path = f.name
        
        audio_int = (audio_data * 32767).astype(np.int16)
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int.tobytes())
        
        # Send to agent
        with open(tmp_path, 'rb') as f:
            r = requests.post(
                AGENT_URL,
                files={'audio': ('audio.wav', f, 'audio/wav')},
                timeout=30
            )
        
        if r.status_code == 200:
            data = r.json()
            if data.get('text'):
                print(f"[AlwaysOn] Sent: {data['text']}")
        
        os.unlink(tmp_path)
    except Exception as e:
        print(f"[AlwaysOn] Error: {e}")

def set_speaking(val: bool):
    """Pause mic while VERONICA speaks."""
    global is_speaking
    is_speaking = val

def start():
    t = threading.Thread(target=listen_forever, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    start()
    print("Always-on mic running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")