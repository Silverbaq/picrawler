import time
import sys
import os
import signal
import config
from gemini_agent import GeminiAgent
from robot_controller import RobotController
from voice_assistant import VoiceAssistant

# Optional Vision
try:
    from vilib import Vilib
    import cv2
    HAS_VISION = True
except ImportError:
    HAS_VISION = False
    print("Vision libraries not found. Running in blind mode.")

def main():
    # 1. Initialize Modules
    print("Initializing Robot Controller...")
    robot = RobotController()
    
    print("Initializing Voice Assistant...")
    # Pass robot's music player to voice assistant for shared audio resource
    voice = VoiceAssistant(robot.music)
    
    print("Initializing Gemini Agent...")
    agent = GeminiAgent()
    
    # 2. Vision Setup
    if HAS_VISION:
        Vilib.camera_start(vflip=config.CAMERA_VFLIP, hflip=config.CAMERA_HFLIP)
        Vilib.show_fps()
        Vilib.display(local=False, web=True)
        # Wait for camera to be ready
        while not Vilib.flask_start:
            time.sleep(0.1)
        print("Vision System Ready.")

    # 3. Audio Calibration
    robot.set_state('think') # Show user we are busy
    voice.calibrate_noise()
    robot.set_state('standby')

    print("System Ready. Say something!")
    
    input_mode = 'voice'
    if '--keyboard' in sys.argv:
        input_mode = 'keyboard'

    try:
        while True:
            # 1. TRIGGER PHASE
            text = None
            
            if input_mode == 'voice':
                if voice.oww_model:
                     # Local Wake Word
                     voice.wait_for_wake_word()
                     robot.set_state('think') # Brief blink to acknowledge
                     time.sleep(0.5)
                     robot.set_state('standby')
                     
                     # Listen for actual command
                     text = voice.listen()
                else:
                    # Cloud STT Trigger
                    text = voice.listen()
                    if not text: continue
                    triggered = any(trigger in text.lower() for trigger in config.TRIGGER_WORDS)
                    if not triggered:
                        print(".", end="", flush=True)
                        continue
            else:
                text = input("You: ")

            if not text: continue

            # 2. CONVERSATION LOOP
            # We enter this loop once triggered, and stay until silence breaks it
            while True:
                print(f"User: {text}")
                
                # B. Processing
                robot.set_state('think')
                
                img_path = None
                if HAS_VISION:
                    img_path = config.IMG_INPUT_PATH
                    cv2.imwrite(img_path, Vilib.img)
                
                response = agent.chat_interact(text, image_path=img_path)
                
                # C. Output
                answer = response.get('answer', '')
                actions = response.get('actions', [])
                
                print(f"Robot: {answer}")
                
                if answer:
                    voice.speak(answer)
                
                if actions:
                    robot.add_actions(actions)
                
                robot.set_state('standby')
                
                # Wait for speaking to start and finish
                time.sleep(0.5) 
                while voice.is_speaking:
                    time.sleep(0.1)
                
                # Wait for actions?
                # while not robot.action_queue.empty() or robot.state == 'actions':
                #    time.sleep(0.1)

                if input_mode == 'keyboard':
                    text = input("You (Enter to exit conv): ")
                    if not text: break
                else:
                    # Continuous Listen
                    print("Listening for follow-up...")
                    text = voice.listen() # Uses STT_TIMEOUT
                    if not text:
                        print("Conversation ended.")
                        break # Exit to Trigger Phase
                    
                    # Optional: Check for "Stop" or "Exit" commands to break manually
                    if "stop" in text.lower() or "bye" in text.lower():
                        break

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        voice.cleanup()
        robot.cleanup()
        if HAS_VISION:
            Vilib.camera_close()

if __name__ == "__main__":
    main()
