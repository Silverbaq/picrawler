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
    from vision_module import VisionModule
    HAS_VISION = True
except ImportError:
    HAS_VISION = False
    print("Vision libraries not found. Running in blind mode.")

def center_on_face(vision, robot, timeout=3):
    """
    Attempts to center the robot body on a detected face for a few seconds.
    """
    if not HAS_VISION: return
    
    print("Centering on face...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Get Frame
        # Vilib runs in background, updating Vilib.img
        if Vilib.img is None:
            time.sleep(0.1)
            continue
            
        offset_x, offset_y = vision.detect_face(Vilib.img) or (None, None)
        
        if offset_x is None:
            # No face, just wait
            time.sleep(0.1)
            continue
            
        # Determine movement
        # offset_x is -1 (left) to 1 (right)
        THRESHOLD = 0.2
        if offset_x < -THRESHOLD:
            robot.add_actions(['turn_left']) # Queues a turn
            # Wait for it to happen?? The queue is async. 
            # This might overshoot if we queue many.
            # Ideally we want a single step immediate.
            # But for Phase 3 PoC, let's just queue one and break/wait?
            time.sleep(0.5) 
        elif offset_x > THRESHOLD:
            robot.add_actions(['turn_right'])
            time.sleep(0.5)
        else:
            # Centered enough
            break
            
        time.sleep(0.1)

def main():
    # 1. Initialize Modules
    print("Initializing Robot Controller...")
    robot = RobotController()
    
    print("Initializing Voice Assistant...")
    voice = VoiceAssistant(robot.music)
    
    print("Initializing Gemini Agent...")
    agent = GeminiAgent()
    
    vision = None
    if HAS_VISION:
        vision = VisionModule()
        Vilib.camera_start(vflip=config.CAMERA_VFLIP, hflip=config.CAMERA_HFLIP)
        Vilib.show_fps()
        Vilib.display(local=False, web=True)
        while not Vilib.flask_start:
            time.sleep(0.1)
        print("Vision System Ready.")

    # 3. Audio Calibration
    robot.set_state('think') 
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
                     voice.wait_for_wake_word()
                     
                     robot.set_state('wake') # Sound + Status
                     # Try to look at user
                     if HAS_VISION:
                         center_on_face(vision, robot)
                         
                     # Listen for actual command
                     text = voice.listen()
                else:
                    text = voice.listen()
                    if not text: continue
                    triggered = any(trigger in text.lower() for trigger in config.TRIGGER_WORDS)
                    if not triggered:
                        print(".", end="", flush=True)
                        continue
                    robot.set_state('wake')
            else:
                text = input("You: ")

            if not text: continue

            # 2. CONVERSATION LOOP
            while True:
                print(f"User: {text}")
                
                # B. Processing
                robot.set_state('think')
                
                img_path = None
                # Smart Vision Logic
                if HAS_VISION:
                    # Only capture if keyword present
                    is_visual_query = any(kw in text.lower() for kw in config.VISION_KEYWORDS)
                    if is_visual_query:
                        print("Visual query detected. Capturing image...")
                        img_path = config.IMG_INPUT_PATH
                        cv2.imwrite(img_path, Vilib.img)
                    else:
                        print("Text-only query.")
                
                response = agent.chat_interact(text, image_path=img_path)
                
                # C. Output
                answer = response.get('answer', '')
                actions = response.get('actions', [])
                
                print(f"Robot: {answer}")
                
                if answer:
                    voice.speak(answer)
                
                if actions:
                    robot.add_actions(actions)
                
                # Wait for speaking to start
                time.sleep(0.5) 
                
                # Reset to standby (which allows random idle moves in RobotController)
                robot.set_state('standby')
                
                while voice.is_speaking:
                    time.sleep(0.1)

                if input_mode == 'keyboard':
                    text = input("You (Enter to exit conv): ")
                    if not text: break
                else:
                    print("Listening for follow-up...")
                    text = voice.listen()
                    if not text:
                        # Play sleep sound?
                        robot.set_state('sleep') 
                        print("Conversation ended.")
                        break 
                    
                    if "stop" in text.lower() or "bye" in text.lower():
                        robot.set_state('sleep')
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
