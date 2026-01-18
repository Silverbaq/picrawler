# Picrawler Gemini examples usage

----------------------------------------------------------------

## Install dependencies

- Make sure you have installed PiCrawler and related dependencies first
    <https://docs.sunfounder.com/projects/pi-crawler/en/latest/python/python_start/download_and_run_code.html#install-all-the-modules>

- Install Google Gemini and speech processing libraries

> [!Note]
> When using pip install on Raspberry Pi OS (Debian based), you may encounter errors about system-managed packages (e.g. `typing_extensions`). 
> **Option 1 (Recommended): Use a Virtual Environment**
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip3 install -r requirements.txt
> ```
> 
> **Option 2: Force Global Install**
> If you must install globally and face `uninstall-no-record-file` errors, add `--ignore-installed`:
> ```bash
> sudo pip3 install -U google-generativeai gTTS SpeechRecognition --break-system-packages --ignore-installed
> ```

    ```bash
    # Install Python dependencies for Gemini, TTS, and Audio
    # Use --ignore-installed to avoid conflicts with apt-installed packages
    sudo pip3 install -U google-generativeai gTTS SpeechRecognition --break-system-packages --ignore-installed

    # Install system audio dependencies
    sudo apt install python3-pyaudio
    sudo apt install sox libsox-fmt-mp3
    sudo pip3 install -U sox --break-system-packages --ignore-installed
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

> [!Important]
> If you used a virtual environment, make sure it is activated (`source venv/bin/activate`) before running!
> If running with `sudo` while using a user-created virtual environment, you might need to use the full path to the python executable (e.g., `sudo /home/pi/picrawler/gemini_examples/venv/bin/python3 gemini_spider.py`).

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
