import sys, time, json, ssl
import requests, threading
import os
from datetime import datetime
from websockets.sync.client import connect as websocket_connect

# Base directory for the project
BASE_DIR = "/home/..."

# Dynamically generate main_dir based on the current date
DATE_STR = datetime.now().strftime("%Y%m%d")
MAIN_DIR = f"{BASE_DIR}/{DATE_STR}_Animal"

PROCESS_INTERVAL = 1  # in seconds
STATE_LOG = os.path.join(MAIN_DIR, 'animal_states_log.csv') # Path to state log
ANIMAL_NAME = 'animal'  # animal name, can be changed via command line

def get_last_animal_state():
    try:
        with open(STATE_LOG, 'r') as f:
            lines = f.readlines()
            if not lines:
                return None
            
            # Get last line and extract state
            last_line = lines[-1].strip()
            if not last_line:
                return None
                
            parts = last_line.split(',')
            if len(parts) >= 3:
                return parts[2]  # Return the state from second column
    except Exception as e:
        print(f"Error reading animal state log: {e}")
    
    return None


def send_websocket_request(data):
    try:
        with websocket_connect("wss://...", ssl=ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)) as websocket:
            websocket.send(json.dumps(data))
    except Exception as e:
        print(f"An error occurred: {e}")

def main(process_interval=PROCESS_INTERVAL, animal_name=ANIMAL_NAME):
    while True:
        # Get the last animal state
        animal_state = get_last_animal_state()
        
        if animal_state is not None:
            # Prepare data to send
            data = {
                animal_name: animal_state
            }
            
            # Send via WebSocket in a separate thread
            thread = threading.Thread(target=send_websocket_request, args=(data,))
            thread.start()
            
            print(f"{animal_name} - {animal_state}")
        
        time.sleep(process_interval)

if __name__ == "__main__":
    process_interval = int(sys.argv[1]) if len(sys.argv) > 1 else PROCESS_INTERVAL
    animal_name = sys.argv[2] if len(sys.argv) > 2 else ANIMAL_NAME
    main(process_interval, animal_name)




