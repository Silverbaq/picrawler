# Picrawler Gemini examples usage

----------------------------------------------------------------

## Install dependencies

- Make sure you have installed PiCrawler and related dependencies first
    <https://docs.sunfounder.com/projects/pi-crawler/en/latest/python/python_start/download_and_run_code.html#install-all-the-modules>

- Install Google Gemini and speech processing libraries

> [!Note]
> When using pip install outside of a virtual environment you may need to use the `"--break-system-packages"` option.

    ```bash
    # Install Python dependencies for Gemini, TTS, and Audio
    sudo pip3 install -U google-generativeai gTTS SpeechRecognition --break-system-packages

    # Install system audio dependencies
    sudo apt install python3-pyaudio
    sudo apt install sox libsox-fmt-mp3
    sudo pip3 install -U sox --break-system-packages
    ```

----------------------------------------------------------------

## Setup Google Gemini

### GET API KEY

<https://aistudio.google.com/app/apikey>

Fill your `GEMINI_API_KEY` into the `keys.py` file.

```python
GEMINI_API_KEY = "AIzaS..." 
```

### System Instruction

The system instruction (behavior of the robot) is now defined directly in `gemini_spider.py` instead of being configured on a remote assistant platform. You can modify the `system_instruction` string in the code if you want to change its personality.

----------------------------------------------------------------

## Run

- Run with voice

```bash
sudo python3 gemini_spider.py
```

- Run with keyboard

```bash
sudo python3 gemini_spider.py --keyboard
```

- Run without image analysis

```bash
sudo python3 gemini_spider.py --keyboard --no-img
```

> [!Warning]
> You need to run with `sudo`, otherwise there may be no sound from the speaker or access to GPIO.

## Modify parameters [optional]

- Set language of STT

    Config `LANGUAGE` variable in the file `gemini_spider.py`. Default is `'en'`.

- Set TTS volume gain

    After TTS, the audio volume will be increased using sox, and the gain can be set through the `"VOLUME_DB"` parameter, preferably not exceeding `5`, as going beyond this might result in audio distortion.

- Select TTS voice role

    Config `TTS_VOICE` variable in the file `gemini_spider.py`. This uses `gTTS` (Google Translate TTS), so the voice parameter corresponds to language codes (e.g., `'en'`, `'es'`, `'fr'`).

```python
gemini_helper = GeminiHelper(GEMINI_API_KEY, assistant_name='PiCrawler', system_instruction=system_instruction)

LANGUAGE = 'en'
VOLUME_DB = 3 
TTS_VOICE = 'en' 
```
