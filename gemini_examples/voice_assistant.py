import os
import time
import queue
import threading
import shutil
import speech_recognition as sr
from gtts import gTTS
import config
import pyaudio
import numpy as np

# Import pydub
from pydub import AudioSegment 

# Import OpenWakeWord
try:
    from openwakeword.model import Model
    HAS_OWW = True
except ImportError:
    HAS_OWW = False
    print("OpenWakeWord not found. Local wake word disabled.")

class VoiceAssistant:
    def __init__(self, music_player):
        self.music = music_player
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_adjustment_damping = 0.16
        self.recognizer.dynamic_energy_ratio = 1.6
        
        self.speech_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_speaking = False
        
        # OpenWakeWord Init
        self.oww_model = None
        if HAS_OWW:
            try:
                # This might download models on first run
                print("Loading OpenWakeWord models...")
                self.oww_model = Model(wakeword_models=config.WAKE_WORD_MODELS)
                print(f"Loaded models: {config.WAKE_WORD_MODELS}")
            except Exception as e:
                print(f"Failed to load OWW: {e}")
                self.oww_model = None

        # Audio playback thread
        self.thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.thread.start()

    def calibrate_noise(self):
        print("Adjusting for ambient noise... Please be quiet.")
        with sr.Microphone(chunk_size=8192) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=config.AMBIENT_NOISE_DURATION)
            print(f"Energy threshold set to {self.recognizer.energy_threshold}")

    def wait_for_wake_word(self):
        """
        Listens for the wake word locally. Returns True when detected.
        Blocking (but low latency).
        """
        if not self.oww_model:
            print("Wake word model not loaded. Falling back to simple listen.")
            return True # If no model, we skip wake word check? Or we force manual trigger?
            # Actually, if no model, main.py should behave effectively like "listen always" or use old method.
            # But the caller expects a return.
        
        # PyAudio Stream
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1280
        
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        print("Waiting for wake word...")
        try:
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                # Convert to numpy
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Predict
                prediction = self.oww_model.predict(audio_data)
                
                # Check results
                for mdl in config.WAKE_WORD_MODELS:
                    if prediction[mdl] >= config.WAKE_WORD_THRESHOLD:
                        print(f"Wake word detected: {mdl}")
                        return True
                        
        except Exception as e:
            print(f"Wake word error: {e}")
            return False
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def listen(self):
        """
        Listens for audio and returns text. Blocking call (with timeout).
        """
        with sr.Microphone(chunk_size=8192) as source:
            try:
                print("Listening for command...")
                audio = self.recognizer.listen(source, timeout=config.STT_TIMEOUT)
                return self._stt(audio)
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                print(f"Listen error: {e}")
                return None

    def _stt(self, audio, verbose=False):
        try:
            text = self.recognizer.recognize_google(audio, language=config.LANGUAGE)
            return text
        except sr.UnknownValueError:
            if verbose: print("STT: Could not understand audio")
            return None
        except Exception as e:
            if verbose: print(f"STT Error: {e}")
            return None

    def speak(self, text):
        """
        Generates TTS and queues it for playback.
        """
        if not text:
            return

        filename = f"{config.TTS_OUTPUT_DIR}/{time.time()}_speech.wav"
        success = self._generate_tts(text, filename)
        if success:
            self.speech_queue.put(filename)

    def _generate_tts(self, text, output_file):
        try:
            if not os.path.exists(os.path.dirname(output_file)):
                os.makedirs(os.path.dirname(output_file))
            
            # Generate MP3
            temp_mp3 = output_file + ".mp3"
            tts = gTTS(text=text, lang=config.TTS_VOICE, slow=False)
            tts.save(temp_mp3)
            
            # Convert to WAV
            sound = AudioSegment.from_mp3(temp_mp3)
            sound.export(output_file, format="wav")
            
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
                
            return True
        except Exception as e:
            print(f"TTS Generation Error: {e}")
            return False

    def _playback_loop(self):
        while not self.stop_event.is_set():
            try:
                file_path = self.speech_queue.get(timeout=0.1)
                self.is_speaking = True
                
                print(f"Playing: {file_path}")
                self.music.sound_play(file_path, 100)
                
                s = AudioSegment.from_file(file_path)
                duration = len(s) / 1000.0
                time.sleep(duration + 0.2)
                
                self.is_speaking = False
                self.speech_queue.task_done()

            except queue.Empty:
                pass
            except Exception as e:
                print(f"Playback error: {e}")
                self.is_speaking = False

    def cleanup(self):
        self.stop_event.set()
