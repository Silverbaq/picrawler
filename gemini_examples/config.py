import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Helper Config
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MODEL_FALLBACK = "gemini-1.5-flash-002"
ASSISTANT_NAME = "PiCrawler"
ASSISTANT_DESCRIPTION_FILE = "assistant_description"

# Audio Config
LANGUAGE = 'en' # STT Language
TTS_VOICE = 'en' # gTTS uses language codes
TTS_VOLUME_DB = 3 
STT_TIMEOUT = 5
AMBIENT_NOISE_DURATION = 2
TTS_OUTPUT_DIR = "./tts"

# Hardware Config
LED_PIN = "LED"
CAMERA_VFLIP = False
CAMERA_HFLIP = False

# Application Config
IMG_INPUT_PATH = "./img_input.jpg"
TRIGGER_WORDS = ["hey robot", "hi robot", "picrawler", "pi crawler", "spider", "hey google", "gemini"]
WAKE_WORD_MODELS = ["hey_jarvis_v0.1"] # openwakeword models
WAKE_WORD_THRESHOLD = 0.5
VISION_KEYWORDS = ["look", "see", "watch", "view", "what is this", "scan", "read"]

# Sound Effects (File paths)
SOUNDS = {
    "wake": "./sounds/wake.wav",
    "sleep": "./sounds/sleep.wav",
    "think": "./sounds/think.wav",
}
SOUND_EFFECT_ACTIONS = []

# Action Config
ACTION_INTERVAL_MIN = 2
ACTION_INTERVAL_MAX = 6
LED_DOUBLE_BLINK_INTERVAL = 0.8
LED_BLINK_INTERVAL = 0.1
