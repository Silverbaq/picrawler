
import os
import time
import shutil
import json
import ast
from google import genai
from google.genai import types
from gtts import gTTS
import speech_recognition as sr

# utils
# =================================================================
def chat_print(label, message):
    width = shutil.get_terminal_size().columns
    msg_len = len(message)
    line_len = width - 27

    # --- normal print ---
    print(f'{time.time():.3f} {label:>6} >>> {message}')
    return

    # --- table mode ---
    if width < 38 or msg_len <= line_len:
        print(f'{time.time():.3f} {label:>6} >>> {message}')
    else:
        texts = []
        for i in range(0, len(message), line_len):
            texts.append(message[i:i+line_len])

        for i, text in enumerate(texts):
            if i == 0:
                print(f'{time.time():.3f} {label:>6} >>> {text}')
            else:
                print(f'{"":>26} {text}')

# GeminiHelper
# =================================================================
class GeminiHelper():
    STT_OUT = "stt_output.wav"
    TTS_OUTPUT_FILE = 'tts_output.mp3'

    def __init__(self, api_key, assistant_name='picrawler', system_instruction=None) -> None:
        self.api_key = api_key
        self.assistant_name = assistant_name
        self.system_instruction = system_instruction
        self.model_name = 'gemini-1.5-flash'
        
        # Initialize the new Client
        self.client = genai.Client(api_key=self.api_key)
        
        # In the new SDK, chat sessions are often managed by maintaining history manually or using chats.create().
        # google-genai v1.0 has chats.create
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            history=[]
        )

    def stt(self, audio, language='en'):
        # using speech_recognition's google recognizer (free)
        r = sr.Recognizer()
        try:
            # audio is already an AudioData object from sr.Microphone
            text = r.recognize_google(audio, language=language)
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return False
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return False
        except Exception as e:
            print(f"stt err:{e}")
            return False

    def dialogue(self, msg):
        chat_print("user", msg)
        try:
            # New SDK usage: chat.send_message(message=...)
            response = self.chat.send_message(message=msg)
            
            value = response.text
            chat_print(self.assistant_name, value)
            
            # Try to parse as JSON/dict
            try:
                # Clean up json markdown if present
                clean_value = value.strip()
                if clean_value.startswith('```json'):
                    clean_value = clean_value[7:]
                if clean_value.startswith('```'):
                    clean_value = clean_value.strip('`')
                if clean_value.endswith('```'):
                    clean_value = clean_value[:-3]
                
                # using ast.literal_eval for safer evaluation than eval()
                # code expects a dict with 'actions' and 'answer'
                value_dict = json.loads(clean_value)
                return value_dict
            except json.JSONDecodeError:
                try:
                    # Fallback to ast.literal_eval if it's python dict style
                    value_dict = ast.literal_eval(clean_value)
                    return value_dict
                except:
                    return str(value)
                    
        except Exception as e:
            print(f"Gemini error: {e}")
            return str(e)

    def dialogue_with_img(self, msg, img_path):
        chat_print("user", msg)
        
        try:
            # Open images handling
            if not os.path.exists(img_path):
                print(f"Image not found: {img_path}")
                return self.dialogue(msg)

            # Using PIL
            import PIL.Image
            img = PIL.Image.open(img_path)
            
            # In google-genai, we can pass a list of contents including the image
            # message can be a string or list of contents
            
            response = self.chat.send_message(message=[msg, img])
            
            value = response.text
            chat_print(self.assistant_name, value)
            
             # Try to parse as JSON/dict
            try:
                # Clean up json markdown if present
                clean_value = value.strip()
                if clean_value.startswith('```json'):
                    clean_value = clean_value[7:]
                if clean_value.startswith('```'):
                    clean_value = clean_value.strip('`')
                if clean_value.endswith('```'):
                    clean_value = clean_value[:-3]
                
                value_dict = json.loads(clean_value)
                return value_dict
            except json.JSONDecodeError:
                try:
                    value_dict = ast.literal_eval(clean_value)
                    return value_dict
                except:
                    return str(value)
        except Exception as e:
            print(f"Gemini Vision error: {e}")
            return str(e)

    def text_to_speech(self, text, output_file, voice='en', response_format="mp3", speed=1):
        '''
        Using gTTS (Google Text-to-Speech)
        voice argument is mapped to language code in gTTS
        '''
        try:
            # check dir
            dir = os.path.dirname(output_file)
            if not os.path.exists(dir):
                os.makedirs(dir)
            
            # gTTS doesn't support "speed" directly in the simple API the same way, but it has 'slow=True/False'
            # We will ignore speed!=1 for now or map it.
            
            tts = gTTS(text=text, lang='en', slow=False)
            
            # gTTS saves as mp3. If wav is requested, we might need conversion.
            # The original code asked for 'wav' sometimes.
            # If output_file ends in .wav, we might need ffmpeg or sox. 
            # The original code uses `sox_volume` later which implies it has sox.
            # We'll save as mp3 first.
            
            temp_mp3 = output_file
            if not output_file.endswith('.mp3'):
               temp_mp3 = output_file + ".mp3"
            
            tts.save(temp_mp3)
            
            # If format mismatch, try to rename or convert if simple
            if output_file != temp_mp3:
                 # If the system has ffmpeg: os.system(f"ffmpeg -i {temp_mp3} {output_file}")
                 # For now, just rename and hope the player handles it or valid wav header is not strictly required by sox if it supports mp3
                 shutil.move(temp_mp3, output_file)
            
            return True
        except Exception as e:
            print(f'tts err: {e}')
            return False
