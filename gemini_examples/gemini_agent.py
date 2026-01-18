import config
import os
import json
import ast
import time
from google import genai
from google.genai import types

class GeminiAgent:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        if not self.api_key:
             raise ValueError("GEMINI_API_KEY not found in environment variables or config.py.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = config.GEMINI_MODEL
        self.chat = None
        self._init_chat()

    def _init_chat(self):
        system_instruction = self._load_system_instruction()
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
            print(f"Trying fallback: {config.GEMINI_MODEL_FALLBACK}...")
            self.model_name = config.GEMINI_MODEL_FALLBACK
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                ),
                history=[]
            )

    def _load_system_instruction(self):
        try:
            with open(config.ASSISTANT_DESCRIPTION_FILE, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: {config.ASSISTANT_DESCRIPTION_FILE} not found. Using default.")
            return "You are a robot assistant. Reply in JSON with 'actions' and 'answer'."

    def chat_interact(self, message, image_path=None):
        """
        Sends a message (and optional image) to Gemini and returns the parsed response.
        """
        # print(f"User: {message}") # Debug logging replaced by caller handling UI
        
        try:
            if image_path and os.path.exists(image_path):
                import PIL.Image
                img = PIL.Image.open(image_path)
                response = self.chat.send_message(message=[message, img])
            else:
                response = self.chat.send_message(message=message)

            return self._parse_json(response.text)
        except Exception as e:
            print(f"Gemini Agent Error: {e}")
            return {"actions": [], "answer": f"I encountered an error: {e}"}

    def _parse_json(self, value):
        try:
            clean_value = value.strip()
            if clean_value.startswith('```json'):
                clean_value = clean_value[7:]
            if clean_value.startswith('```'):
                clean_value = clean_value.strip('`')
            if clean_value.endswith('```'):
                clean_value = clean_value[:-3]
            
            return json.loads(clean_value)
        except json.JSONDecodeError:
            try:
                # Fallback to literal eval if purely standard python dict string
                return ast.literal_eval(clean_value)
            except:
                print(f"Failed to parse JSON: {value}")
                return {"actions": [], "answer": value}
