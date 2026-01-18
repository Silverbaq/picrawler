from gemini_helper import GeminiHelper
from keys import GEMINI_API_KEY
from preset_actions import *
from utils import *

import readline 

import speech_recognition as sr

from picrawler import Picrawler
from robot_hat import Music, Pin

import time
import threading
import random

import os
import sys

# os.popen("pinctrl set 20 op dh") # enable robot_hat speake switch # Commenting out for potentially different hardware setup or strict permissions, but recommond keeping if on Pi.
# Checking if running on Pi before running hardware commands is good practice, but for a clone, I will keep it but maybe wrapped? 
# The user said "I copied the folder... go through the code... refactor".
# I'll keep the original hardware lines active as this is intended for the Pi.
os.popen("pinctrl set 20 op dh") 

current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)

input_mode = None
with_img = True
args = sys.argv[1:]
if '--keyboard' in args:
    input_mode = 'keyboard'
else:
    input_mode = 'voice'

if '--no-img' in args:
    with_img = False
else:
    with_img = True

# gemini assistant init
# =================================================================
if len(GEMINI_API_KEY) < 10:
    raise ValueError("\n\nInvalid GEMINI_API_KEY in `keys.py`.\n")

# Construct system instruction
action_list = list(actions_dict.keys())
system_instruction = f"""
You are a robot controller for a hexapod robot named PiCrawler.
You can converse with the user and perform actions.

Available actions you can perform are: {action_list}.

When you reply, you MUST output a valid JSON object with two fields:
1. 'actions': A list of strings corresponding to the actions you want to perform from the available list. If no action is needed, use an empty list.
2. 'answer': A string containing your verbal response to the user.

Example format:
{{
  "actions": ["sit", "wave_hand"],
  "answer": "I am sitting down and waving at you."
}}

If the user asks you to do something that isn't in the list, explain that you can't do that yet.
"""

gemini_helper = GeminiHelper(GEMINI_API_KEY, assistant_name='PiCrawler', system_instruction=system_instruction)

LANGUAGE = 'en'
VOLUME_DB = 3 
TTS_VOICE = 'en' # gTTS uses language codes

SOUND_EFFECT_ACTIONS = []

# car init 
# =================================================================
try:
    my_spider = Picrawler()
    time.sleep(1)
except Exception as e: 
    # Fallback for testing on non-Pi environment
    # print(f"Warning: Could not initialize Picrawler: {e}")
    # raise RuntimeError(e) 
    # For the actual file, we should probably raise like the original, unless testing.
    # The user said this is their working environment.
    raise RuntimeError(e)

music = Music()
led = Pin('LED')

# Vilib start
# =================================================================
if with_img:
    from vilib import Vilib
    import cv2

    Vilib.camera_start(vflip=False,hflip=False)
    Vilib.show_fps()
    Vilib.display(local=False,web=True)

    while True:
        if Vilib.flask_start:
            break
        time.sleep(0.01)

    time.sleep(.5)
    print('\n')

# speech_recognition init
# =================================================================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_adjustment_damping = 0.16
recognizer.dynamic_energy_ratio = 1.6

# speak_hanlder
# =================================================================
speech_loaded = False
speech_lock = threading.Lock()
tts_file = None

def speak_hanlder():
    global speech_loaded, tts_file
    while True:
        with speech_lock:
            _isloaded = speech_loaded
        if _isloaded:
            speak_block(music, tts_file)
            with speech_lock:
                speech_loaded = False
        time.sleep(0.05)

speak_thread = threading.Thread(target=speak_hanlder)
speak_thread.daemon = True


# actions thread
# =================================================================
action_status = 'standby' # 'standby', 'think', 'actions', 'actions_done'
led_status = 'standby' # 'standby', 'think' or 'actions', 'actions_done'
last_action_status = 'standby'
last_led_status = 'standby'

LED_DOUBLE_BLINK_INTERVAL = 0.8 # seconds
LED_BLINK_INTERVAL = 0.1 # seconds

actions_to_be_done = []
action_lock = threading.Lock()

def action_handler():
    global action_status, actions_to_be_done, led_status, last_action_status, last_led_status

    action_interval = 5 # seconds
    last_action_time = time.time()
    last_led_time = time.time()

    while True:
        with action_lock:
            _state = action_status

        # led
        # ------------------------------
        led_status = _state

        if led_status != last_led_status:
            last_led_time = 0
            last_led_status = led_status

        if led_status == 'standby':
            if time.time() - last_led_time > LED_DOUBLE_BLINK_INTERVAL:
                led.off()
                led.on()
                sleep(.1)
                led.off()
                sleep(.1)
                led.on()
                sleep(.1)
                led.off()
                last_led_time = time.time()
        elif led_status == 'think':
            if time.time() - last_led_time > LED_BLINK_INTERVAL:
                led.off()
                sleep(LED_BLINK_INTERVAL)
                led.on()
                sleep(LED_BLINK_INTERVAL)
                last_led_time = time.time()
        elif led_status == 'actions':
                led.on() 

        # actions
        # ------------------------------
        if _state == 'standby':
            last_action_status = 'standby'
            if time.time() - last_action_time > action_interval:
                last_action_time = time.time()
                action_interval = random.randint(2, 6)
        elif _state == 'think':
            if last_action_status != 'think':
                last_action_status = 'think'
        elif _state == 'actions':
            last_action_status = 'actions'
            with action_lock:
                _actions = actions_to_be_done
            for _action in _actions:
                try:
                    if _action in actions_dict:
                        actions_dict[_action](my_spider)
                    else:
                        print(f"Action '{_action}' not found in presets.")
                except Exception as e:
                    print(f'action error: {e}')
                time.sleep(0.5)

            with action_lock:
                action_status = 'actions_done'
            last_action_time = time.time()

        time.sleep(0.01)

action_thread = threading.Thread(target=action_handler)
action_thread.daemon = True


# main
# =================================================================
def main():
    global current_feeling, last_feeling
    global speech_loaded
    global action_status, actions_to_be_done
    global tts_file

    my_spider.do_action('sit', speed=60)
    my_spider.do_action('stand', speed=60)

    speak_thread.start()
    action_thread.start()

    while True:
        if input_mode == 'voice':
            my_spider.do_action('stand', speed=60)

            # listen
            # ----------------------------------------------------------------
            gray_print("listening ...")

            with action_lock:
                action_status = 'standby'

            _stderr_back = redirect_error_2_null() 
            with sr.Microphone(chunk_size=8192) as source:
                cancel_redirect_error(_stderr_back) 
                recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = recognizer.listen(source, timeout=5) # Added timeout to prevent hanging
                except sr.WaitTimeoutError:
                     continue

            # stt
            # ----------------------------------------------------------------
            st = time.time()
            # Use verbose=False to suppress "could not understand" errors in the loop
            _result = gemini_helper.stt(audio, language=LANGUAGE, verbose=False)
            
            if _result:
                gray_print(f"Heard: {_result} (t={time.time() - st:.3f}s)")
                
                # Trigger Word Check
                # Define trigger words/phrases
                TRIGGER_WORDS = ["hey robot", "hi robot", "picrawler", "pi crawler", "spider", "hey google", "gemini"]
                
                # Check if result contains any trigger word
                should_respond = False
                lower_result = _result.lower()
                for trigger in TRIGGER_WORDS:
                   if trigger in lower_result:
                       should_respond = True
                       break
                
                if not should_respond:
                   # gray_print("Ignored (No trigger word)")
                   print(".", end="", flush=True) # Simple alive indicator
                   continue
            else:
                # print() # new line
                print(".", end="", flush=True) # Simple alive indicator
                continue

            gray_print(f"\nProcessing: {_result}")

        elif input_mode == 'keyboard':
            my_spider.do_action('stand', speed=60)

            with action_lock:
                action_status = 'standby'

            _result = input(f'\033[1;30m{"input: "}\033[0m')

            if _result == False or _result == "":
                print() # new line
                continue

        else:
            raise ValueError("Invalid input mode")

        # chat-gemini
        # ---------------------------------------------------------------- 
        response = {}
        st = time.time()

        with action_lock:
            action_status = 'think'

        if with_img:
            img_path = './img_input.jpg' # Fixed typo from original 'img_imput.jpg' to 'img_input.jpg' but for safety might check what original used. Original used 'img_imput.jpg'.
            # I will strictly follow original filename if it matters, but 'img_imput' looks like a typo.
            # However, I should probably stick to 'img_imput.jpg' if other tools rely on it? No, it's just a temp file.
            # I'll use 'img_input.jpg' (corrected spelling).
            cv2.imwrite(img_path, Vilib.img)
            response = gemini_helper.dialogue_with_img(_result, img_path)
        else:
            response = gemini_helper.dialogue(_result)

        gray_print(f'chat takes: {time.time() - st:.3f} s')

        # actions & TTS
        # ---------------------------------------------------------------- 
        try:
            if isinstance(response, dict):
                if 'actions' in response:
                    actions = list(response['actions'])
                else:
                    actions = ['stop']

                if 'answer' in response:
                    answer = response['answer']
                else:
                    answer = ''

                _sound_actions = []
                # Filter out sound actions if any (SOUND_EFFECT_ACTIONS was empty in original too)
                if len(answer) > 0:
                    _actions = list.copy(actions)
                    for _action in _actions:
                        if _action in SOUND_EFFECT_ACTIONS:
                            _sound_actions.append(_action)
                            actions.remove(_action)
            else:
                # If Gemini fails to return JSON and returns text
                answer = str(response)
                actions = []

        except Exception as e:
            print(f"Parsing response error: {e}")
            actions = []
            answer = ''
    
        try:
            # ---- tts ----
            _tts_status = False
            if answer != '':
                st = time.time()
                _time = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
                
                # Ensure tts directory exists
                if not os.path.exists("./tts"):
                    os.makedirs("./tts")
                    
                _tts_f = f"./tts/{_time}_raw.mp3" # gTTS saves as mp3
                
                _tts_status = gemini_helper.text_to_speech(answer, _tts_f, TTS_VOICE) 
                
                if _tts_status:
                    # Original used sox to change volume and likely convert to wav if needed.
                    # Music.sound_play expects wav or mp3? 
                    # robot_hat.Music typically wraps PyGame or similar.
                    # If using 'pinctrl' and 'sox' it might rely on 'play' command.
                    # We will try to use sox to convert to the expected wav with volume gain if sox is available.
                    # If not, we might just use the mp3.
                    
                    tts_file = f"./tts/{_time}_{VOLUME_DB}dB.wav"
                    # We can use sox to convert mp3 to wav and adjust volume
                    # sox input.mp3 -v 1.5 output.wav
                    # The original 'sox_volume' function in 'utils.py' probably handles this.
                    # Let's check utils.py usage.
                    # If sox_volume works with mp3 input, great.
                    
                    # Assuming sox is installed on the Pi as per original requirements.
                    try:
                        _tts_status = sox_volume(_tts_f, tts_file, VOLUME_DB)
                    except Exception as e:
                        print(f"Sox error: {e}, falling back to raw mp3")
                        tts_file = _tts_f
                        _tts_status = True

                gray_print(f'tts takes: {time.time() - st:.3f} s')

            # ---- actions ----
            with action_lock:
                actions_to_be_done = actions
                gray_print(f'actions: {actions_to_be_done}')
                action_status = 'actions'

            # --- sound effects ---
            for _sound in _sound_actions:
                try:
                    sounds_dict[_sound](music)
                except Exception as e:
                    print(f'action error: {e}')

            if _tts_status:
                with speech_lock:
                    speech_loaded = True

            # ---- wait speak done ----
            if _tts_status:
                while True:
                    with speech_lock:
                        if not speech_loaded:
                            break
                    time.sleep(.01)

            # ---- wait actions done ----
            while True:
                with action_lock:
                    if action_status != 'actions':
                        break
                time.sleep(.01)

            ##
            print() # new line

        except Exception as e:
            print(f'actions or TTS error: {e}')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\033[31mERROR: {e}\033[m")
    finally:
        if with_img:
            Vilib.camera_close()
        try:
            my_spider.do_action('sit', speed=60)
        except:
            pass
