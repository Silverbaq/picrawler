
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
        # Try a specific version if the alias fails, or handle it dynamically
        self.model_name = 'gemini-2.5-flash'
        
        self.client = genai.Client(api_key=self.api_key)
        
        # We'll initialize the chat in dialogue() or now if we want history.
        # But wait, managing history means we need to store the chat object.
        # Initialize chat with the model.
        try:
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                ),
                history=[]
            )
        except Exception as e:
            print(f"Error initializing chat with {self.model_name}: {e}")
            print("Trying 'gemini-1.5-flash-002'...")
            self.model_name = 'gemini-1.5-flash-002'
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                ),
                history=[]
            )

    def stt(self, audio, language='en', verbose=True):
        # using speech_recognition's google recognizer (free)
        r = sr.Recognizer()
        try:
            # audio is already an AudioData object from sr.Microphone
            text = r.recognize_google(audio, language=language)
            return text
        except sr.UnknownValueError:
            if verbose:
                print("Google Speech Recognition could not understand audio")
            return False
        except sr.RequestError as e:
            if verbose:
                print(f"Could not request results from Google Speech Recognition service; {e}")
            return False
        except Exception as e:
            if verbose:
                print(f"stt err:{e}")
            return False

    def dialogue(self, msg):
        chat_print("user", msg)
        try:
            response = self.chat.send_message(message=msg)
            
            value = response.text
            chat_print(self.assistant_name, value)
            
            return self._parse_json(value)
                    
        except Exception as e:
            print(f"Gemini error: {e}")
            return str(e)

    def dialogue_with_img(self, msg, img_path):
        chat_print("user", msg)
        
        try:
            if not os.path.exists(img_path):
                print(f"Image not found: {img_path}")
                return self.dialogue(msg)

            import PIL.Image
            img = PIL.Image.open(img_path)
            
            response = self.chat.send_message(message=[msg, img])
            
            value = response.text
            chat_print(self.assistant_name, value)
            
            return self._parse_json(value)

        except Exception as e:
            print(f"Gemini Vision error: {e}")
            # If 404/Not Found for model, maybe fallback to text only or try different model?
            # But the error implies the model itself wasn't found for vision.
            return str(e)
            
    def _parse_json(self, value):
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

    def text_to_speech(self, text, output_file, voice='en', response_format="mp3", speed=1):
        try:
            dir = os.path.dirname(output_file)
            if not os.path.exists(dir):
                os.makedirs(dir)
            
            tts = gTTS(text=text, lang='en', slow=False)
            
            # gTTS saves as mp3
            temp_mp3 = output_file
            if not temp_mp3.endswith('.mp3'):
               temp_mp3 = os.path.splitext(output_file)[0] + ".mp3"
            
            tts.save(temp_mp3)
            
            # If output format requested is different (e.g. wav), convert it
            if output_file.endswith('.wav'):
                 from pydub import AudioSegment
                 sound = AudioSegment.from_mp3(temp_mp3)
                 sound.export(output_file, format="wav")
                 # Optional: clean up temp mp3 if it wasn't the requested output
                 if temp_mp3 != output_file:
                     try:
                        os.remove(temp_mp3)
                     except:
                        pass
            elif output_file != temp_mp3:
                 shutil.move(temp_mp3, output_file)
            
            return True
        except Exception as e:
            print(f'tts err: {e}')
            return False
