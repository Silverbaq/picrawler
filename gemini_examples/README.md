# PiCrawler Gemini Assistant

A modular, AI-powered voice assistant for the SunFounder PiCrawler robot, powered by Google's Gemini 2.0 Flash thinking model.

This project transforms the PiCrawler into an interactive robot that can see, hear, speak, and move, featuring **Local Wake Word detection**, **Continuous Conversation**, and **Smart Vision**.

## 🌟 Features

*   **🧠 Advanced AI**: Uses Google Gemini 2.0 Flash for natural understanding and complex reasoning.
*   **🗣️ Local Wake Word**: Listens for "Hey Jarvis" (or other configured models) locally using `openwakeword`. This is fast, private, and saves API costs.
*   **🔄 Continuous Conversation**: Holds a natural back-and-forth dialogue without needing the wake word for every sentence.
*   **👁️ Smart Vision**: The robot can "see" through its camera. It intelligently captures images only when you ask visual questions (e.g., "What is this?", "Look at the red ball").
*   **🤖 Hardware Awareness**:
    *   **Face Centering**: Turns to face you when woken up (requires Face detection enabled).
    *   **Emotive Sounds**: Plays sounds for waking up, thinking, and sleeping.
    *   **Movement**: Can perform actions like "Wave", "Sit", "Stand", "Dance", and walking movements.

## 🛠️ Requirements

*   **SunFounder PiCrawler**: [Official Documentation](https://docs.sunfounder.com/projects/pi-crawler/en/latest/)
*   **Raspberry Pi**: (Pi 4 or 5 recommended for best AI performance)
*   **Peripherals**: Robot HAT, Camera module, Speaker, Microphone (USB or HAT-integrated).

## 🚀 Installation

### 1. System Dependencies
Ensure you have the basic system libraries for audio and vision:
```bash
sudo apt update
sudo apt install python3-pyaudio sox libsox-fmt-mp3 libatlas-base-dev
```
*(Note: `libatlas-base-dev` is often needed for numpy/opencv)*

### 2. Python Environment (Recommended)
Create a virtual environment to avoid conflicts:
```bash
cd /home/pi/picrawler/gemini_examples
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Packages
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. API Keys
Rename the example environment file and add your Gemini API Key:
```bash
cp .env.example .env
nano .env
```
Inside `.env`:
```ini
GEMINI_API_KEY=your_actual_api_key_here
```
Get your key from [Google AI Studio](https://aistudio.google.com/).

### 2. Fine-tuning (`config.py`)
Edit `config.py` to customize behavior:
*   **`TRIGGER_WORDS`**: Fallback keywords if local wake word fails or for text mode.
*   **`WAKE_WORD_MODELS`**: Change the local wake word model (default: `hey_jarvis_v0.1`).
    *   *Note: `openwakeword` supports many models like `alexa`, `hey_mycroft`, etc.*
*   **`SOUNDS`**: Path to your sound effect files.
*   **`VISION_KEYWORDS`**: Words that trigger image capture.

## 🎮 Usage

Run the main orchestrator script:
```bash
# If using hardware (GPIO/Audio), sudo is often required
sudo ./venv/bin/python main.py
```

### Voice Mode (Default)
1.  **Wake**: Say **"Hey Jarvis"**.
    *   The robot will chirp, wake up, and try to center its camera on your face.
2.  **Command**: Ask a question or give a command.
    *   *"Wave your hand!"*
    *   *"What do you see?"* (Triggers Vision)
    *   *"Tell me a joke about robots."*
3.  **Chat**: The robot replies. You have **5 seconds** to reply back without saying the wake word again.
4.  **End**: Stop talking, or say *"Good bye"* / *"Stop"* to end the session.

### Keyboard Mode
Run with `--keyboard` to type commands instead of speaking:
```bash
sudo python main.py --keyboard
```

## 📂 Architecture

The project is modularized for easier development:

*   **`main.py`**: The central brain. Manages the loop between Hearing -> Thinking -> Speaking/Moving.
*   **`gemini_agent.py`**: Wraps the Google GenAI SDK. Handles prompt engineering and JSON parsing.
*   **`voice_assistant.py`**: Handles Audio I/O.
    *   Runs `openwakeword` on a background stream.
    *   Uses `SpeechRecognition` (Google) for command transcription.
    *   Uses `gTTS` -> `pydub` -> `Speaker` for output.
*   **`robot_controller.py`**: Manages the physical robot.
    *   Queues movements to run in a background thread (non-blocking).
    *   Controls LEDs and Sound Effects.
*   **`vision_module.py`**: Uses OpenCV to detect faces and calculate offsets for the robot to turn.
*   **`config.py`**: Central configuration file.

## ⚠️ Troubleshooting

*   **"Vision libraries not found"**: Ensure `opencv-python` is installed. If using a Pi Camera, ensure your `vilib` or hardware interfaces (Legacy Camera vs Libcamera) are enabled in `raspi-config`.
*   **Audio Issues**: Use `alsamixer` to check microphone and speaker levels. If "Hey Jarvis" isn't detected, try speaking closer or adjusting `WAKE_WORD_THRESHOLD` in `config.py`.
*   **Permission Denied**: GPIO and some Audio drivers require root. Use `sudo` to run the script.
