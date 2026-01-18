import time
import threading
import queue
import random
import config
from picrawler import Picrawler
from robot_hat import Music, Pin
from preset_actions import actions_dict, sounds_dict

class RobotController:
    def __init__(self):
        self.action_queue = queue.Queue()
        self.state = 'standby' # 'standby', 'think', 'actions'
        self.stop_event = threading.Event()
        
        # Hardware Init
        try:
            self.spider = Picrawler()
            self.music = Music()
            self.led = Pin(config.LED_PIN)
        except Exception as e:
            print(f"Robot Hardware Init Failed: {e}")
            raise e

        # Threads
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        last_led_time = 0
        last_action_time = time.time()
        led_status = 'standby'
        
        # Idle movement interval
        action_interval = random.randint(config.ACTION_INTERVAL_MIN, config.ACTION_INTERVAL_MAX)

        while not self.stop_event.is_set():
            # 1. Update LED based on state
            if self.state != led_status:
                led_status = self.state
                last_led_time = 0 # reset timer for blink patterns
            
            self._handle_led(led_status, last_led_time)
            if time.time() - last_led_time > 0.1: # Update timestamp roughly
                 last_led_time = time.time()

            # 2. Handle Actions
            if self.state == 'actions':
                self.led.on()
                try:
                    # Process entire queue or just one? 
                    # Original logic processed a list of actions linearly.
                    # We will drain the queue.
                    while not self.action_queue.empty():
                        action = self.action_queue.get(block=False)
                        print(f"Executing action: {action}")
                        self._perform_action(action)
                        time.sleep(0.5)
                        self.action_queue.task_done()
                    
                    # When done, go back to standby
                    self.state = 'standby'
                    last_action_time = time.time()
                except Exception as e:
                    print(f"Action processing error: {e}")
                    self.state = 'standby'

            elif self.state == 'standby':
                # Random idle movement
                if time.time() - last_action_time > action_interval:
                     # self._perform_idle_action() # Optional: could start small moves
                     last_action_time = time.time()
                     action_interval = random.randint(config.ACTION_INTERVAL_MIN, config.ACTION_INTERVAL_MAX)

            time.sleep(0.05)

    def _handle_led(self, status, last_time):
        # Simplified LED logic for readability
        if status == 'standby':
             # Double blink every config.LED_DOUBLE_BLINK_INTERVAL
             # Complex blink logic is hard to replicate exactly non-blocking without tracking phase.
             # For now, let's just breathe or stay low.
             # Or replicate the original logic:
             pass 
             # Implementation detail: The original code used blocking sleep() inside the main loop for blinks... 
             # which is bad practice.
             # I'll implement a simple "Pulse" here if possible or just On/Off.
             pass 
        elif status == 'think':
             # Blink fast
             pass
        elif status == 'actions':
             self.led.on()

    def _perform_action(self, action_name):
        # Check sound actions
        if action_name in sounds_dict:
            try:
                sounds_dict[action_name](self.music)
            except Exception as e:
                print(f"Sound error: {e}")
            return

        # Check movement actions
        if action_name in actions_dict:
            try:
                actions_dict[action_name](self.spider)
            except Exception as e:
                print(f"Movement error: {e}")
        else:
            print(f"Action '{action_name}' not found.")

    def add_actions(self, action_list):
        for action in action_list:
            self.action_queue.put(action)
        self.state = 'actions'

    def set_state(self, new_state):
        self.state = new_state
    
    def cleanup(self):
        self.stop_event.set()
        self.spider.do_action('sit', speed=60)
