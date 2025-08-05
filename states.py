import pandas as pd
import time
from datetime import datetime
import os
from collections import deque

# Base directory for the project
BASE_DIR = "/home/..."

# Dynamically generate main_dir based on the current date
DATE_STR = datetime.now().strftime("%Y%m%d")
MAIN_DIR = f"{BASE_DIR}/{DATE_STR}_Animal"

# Configuration
CSV_FILE = os.path.join(MAIN_DIR, 'animal_detections_log.csv') # Path to detection log
PASSIVE_CAMERAS = range(0, 0)  # 0-0 inclusive
ACTIVE_CAMERAS = range(0, 0)  # 0-0 inclusive
MOVEMENT_THRESHOLD = 0.00
CHECK_INTERVAL = 1  # seconds between checks or another interval
STATE_LOG_FILE = os.path.join(MAIN_DIR, 'animal_states_log.csv') # Path to state log
CONFIRMATION_SEQUENCE_LENGTH = 1 # Number of consecutive states needed to confirm global state
IDLE_TIMEOUT_SECONDS = 1 # Set state to unknown if no new state-relevant data for this duration

# Ensure the MAIN_DIR exists before trying to create files within it
os.makedirs(MAIN_DIR, exist_ok=True)

# Initialize state log - Ensure 'notes' column is present
if not os.path.exists(STATE_LOG_FILE):
    with open(STATE_LOG_FILE, 'w') as f:
        f.write('timestamp,state,last_confirmed_state,camera,x_center,y_center,frames_used,notes\n')

# Global variables
last_confirmed_state = "unknown"
global_state_sequence = deque(maxlen=CONFIRMATION_SEQUENCE_LENGTH) # Tracks the last N states from valid *unique pair+state* combinations
processed_pair_state_combinations = set() # Tracks (start_frame_index, end_frame_index, state) of combinations added to global_state_sequence

# New global variable to track the timestamp of the last state-relevant detection
last_state_relevant_timestamp = None

# last_processed_timestamp (for file reading progress) is tracked locally in monitor_cat_states

def get_animal_detections(last_processed_ts):
    """
    Read the CSV file and return only cat detections with required columns
    strictly after the last processed timestamp.
    """
    try:
        # Use low_memory=False to avoid DtypeWarning with mixed types if any
        df = pd.read_csv(CSV_FILE, low_memory=False)
        
        # Filter for animal detections first
        animals = df[df['object_class'] == 'animal'].copy()
        
        if animals.empty:
            return pd.DataFrame() # Return empty if no animals found

        animals['timestamp'] = pd.to_datetime(cats['timestamp'])
        
        # Filter by timestamp after getting animals and parsing timestamps
        if last_processed_ts:
            new_animals = animals[animals['timestamp'] > last_processed_ts]
        else:
            new_animals = animals # Process all if starting or resuming

        return new_animals[['timestamp', 'camera', 'filename', 'x_center', 'y_center']]

    except FileNotFoundError:
        # print(f"CSV file not found: {CSV_FILE}") # Avoid excessive printing if file not there yet
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        # print(f"CSV file is empty: {CSV_FILE}") # Handle empty file case
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading or processing CSV: {e}")
        return pd.DataFrame()


def calculate_movement(frame1, frame2):
    """Calculate movement between two sequential frames"""
    dx = abs(frame2['x_center'] - frame1['x_center'])
    dy = abs(frame2['y_center'] - frame1['y_center'])
    # Using average of dx and dy as movement metric
    return (dx + dy) / 2

def determine_animal_state(frame1, frame2):
    """Determine the animal's state from two sequential frames"""
    camera = frame1['camera']

    # Home cameras override movement logic
    if camera in PASSIVE_CAMERAS:
        return "PASSIVE"

    # Active cameras: check movement
    if camera in ACTIVE_CAMERAS:
        movement = calculate_movement(frame1, frame2)
        return "walk" if movement > MOVEMENT_THRESHOLD else "rest"

    return "unknown" # Should not happen if all cameras are in either list, but good fallback

def get_frame_index_from_filename(filename):
    """Extracts the integer frame index from the filename."""
    if not isinstance(filename, str): # Handle potential non-string values
        return -1
    try:
        # Assuming filename format is like "123_cameraX_..."
        return int(filename.split('_')[0])
    except (ValueError, IndexError):
        # print(f"Warning: Could not extract frame index from filename: {filename}") # Avoid excessive logging
        return -1 # Indicate invalid index

def add_state_to_confirmation_sequence(state):
    """
    Add the determined state to the global sequence and check for global state confirmation.
    Assumes duplicate pair+state checks have already passed.
    Returns True if global state was just confirmed/changed.
    """
    global last_confirmed_state, global_state_sequence

    global_state_sequence.append(state)

    # Check for global state confirmation
    if len(global_state_sequence) == CONFIRMATION_SEQUENCE_LENGTH and all(s == global_state_sequence[0] for s in global_state_sequence):
        if last_confirmed_state != global_state_sequence[0]: # Compare against the consistent state in the deque
            last_confirmed_state = global_state_sequence[0]
            return True # State was just confirmed/changed
    return False # State was not just confirmed/changed


def log_state_change(timestamp, determined_state, camera, x, y, frame1, frame2, notes=""):
    """Log the state change (either from a pair or a timeout) to file and console"""
    global last_confirmed_state # Access the potentially updated global state here

    frames_str = 'TIMEOUT' if frame1 is None else f"{frame1['filename']};{frame2['filename']}"
    camera_val = 'N/A' if camera is None else camera
    x_val = 'N/A' if x is None else f"{x:.4f}"
    y_val = 'N/A' if y is None else f"{y:.4f}"

    # Use pandas to append for potentially better handling of CSV quoting etc.
    log_df = pd.DataFrame([{
        'timestamp': timestamp,
        'state': determined_state if determined_state else 'N/A', # State determined for pair or 'unknown' for timeout
        'last_confirmed_state': last_confirmed_state, # The global confirmed state *after* this event
        'camera': camera_val,
        'x_center': x_val,
        'y_center': y_val,
        'frames_used': frames_str,
        'notes': notes
    }])

    # Append to CSV without writing header if file already exists
    try:
        log_df.to_csv(STATE_LOG_FILE, mode='a', header=False, index=False)
    except Exception as e:
        print(f"Error writing to log file {STATE_LOG_FILE}: {e}")

    # Console output
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    if notes == 'IDLE_TIMEOUT':
        print(f"{timestamp_str}: --- IDLE TIMEOUT --- Last Confirmed State = {last_confirmed_state} (Set to 'unknown')")
    else:
        print(f"{timestamp_str}: Camera {camera_val}, Determined State = {determined_state}, Last Confirmed State = {last_confirmed_state} (Pos: {x_val}, {y_val})")
        if frames_str != 'TIMEOUT':
            prev_idx = get_frame_index_from_filename(frame1['filename'])
            curr_idx = get_frame_index_from_filename(frame2['filename'])
            if prev_idx != -1 and curr_idx != -1:
                print(f"  Compared frames: {frame1['filename']} ({prev_idx}) -> {frame2['filename']} ({curr_idx})")
            else:
                print(f"  Compared frames: {frame1['filename']} -> {frame2['filename']}")

    if notes and notes != 'IDLE_TIMEOUT': # Avoid printing IDLE_TIMEOUT note twice in console
        print(f"  Notes: {notes}")
    print("") # Add a blank line for readability


def monitor_animal_states():
    """Monitor cat detections and compare sequential pairs of frames"""
    global last_confirmed_state, global_state_sequence, processed_pair_state_combinations, last_state_relevant_timestamp # Declare globals used in this function

    print("Starting animal state monitor (pairwise sequential mode with global confirmation and idle timeout)...")
    print("Comparing strictly sequential frame pairs per camera.")
    print("Only the first processed detection for a given frame pair (e.g., frame N to N+1) *with a specific state* contributes to global state confirmation.")
    print(f"Global state confirmation requires {CONFIRMATION_SEQUENCE_LENGTH} consecutive states from unique processed sequential pair+state combinations.")
    print(f"Idle timeout threshold (sets global state to 'unknown'): {IDLE_TIMEOUT_SECONDS} seconds without new state-relevant data.")
    print(f"Logging to {STATE_LOG_FILE}")
    print("Press Ctrl+C to stop\n")

    last_processed_timestamp = None # Tracks the timestamp of the most recent row *read* from the CSV
    last_frame_per_camera = {}  # Stores the last seen frame per camera


    try:
        while True:
            current_check_time = datetime.now() # Get time at the start of the check

            # --- Idle Timeout Check (before processing new data) ---
            # Check based on time since the last state-relevant detection
            if last_state_relevant_timestamp: # Only check if we've ever processed state-relevant data
                time_since_last_relevant_data = current_check_time - last_state_relevant_timestamp

                if time_since_last_relevant_data.total_seconds() >= IDLE_TIMEOUT_SECONDS:
                    if last_confirmed_state != "unknown" or len(global_state_sequence) > 0:
                         # State has been active/resting/sleeping, but now no state-relevant data for timeout period
                         last_confirmed_state = "unknown"
                         # Clear global_state_sequence on IDLE_TIMEOUT ---
                         global_state_sequence.clear() # Clear the deque to ensure fresh confirmation sequence
                         processed_pair_state_combinations.clear() # Clear processed pairs as well for a truly fresh start
                         log_state_change(current_check_time, 'unknown', None, None, None, None, None, notes='IDLE_TIMEOUT')
                         # Corrected comment: log_state_change *logs* the event, but the history clearing (deque, set) is done above.
                         # log_state_change clears history


            # --- Read and Process New Detections ---
            # Pass last_processed_timestamp to get_cat_detections to only read newer rows
            animal_detections = get_animal_detections(last_processed_timestamp)


            if not animal_detections.empty:
                # Sort by timestamp to ensure chronological processing
                cat_detections.sort_values('timestamp', inplace=True)

                # Update last_processed_timestamp to the timestamp of the latest row found *in this check*
                # This ensures we don't re-read these rows in the next iteration
                last_processed_timestamp = animal_detections['timestamp'].iloc[-1]


                # Process new detections in their chronological order
                for _, detection in cat_detections.iterrows():
                    camera = detection['camera']
                    current_frame = {
                        'timestamp': detection['timestamp'],
                        'camera': camera,
                        'x_center': detection['x_center'],
                        'y_center': detection['y_center'],
                        'filename': detection['filename']
                    }

                    current_end_frame_index = get_frame_index_from_filename(current_frame['filename'])
                    if current_end_frame_index == -1:
                        # Skip if frame index extraction failed
                        # print(f"Skipping detection due to invalid filename: {current_frame['filename']}") # Already handled in get_frame_index_from_filename warning
                        continue # Just skip this row, last_processed_timestamp already updated


                    # Check if we have a previous frame from this camera
                    if camera in last_frame_per_camera:
                        prev_frame = last_frame_per_camera[camera]
                        prev_frame_index = get_frame_index_from_filename(prev_frame['filename'])

                        if prev_frame_index != -1:
                            # Ensure frames are strictly sequential for THIS camera
                            if current_end_frame_index == prev_frame_index + 1:
                                # --- Valid Sequential Pair Found for THIS Camera ---
                                current_start_frame_index = prev_frame_index

                                # Determine the state for this specific sequential pair
                                determined_state = determine_animal_state(prev_frame, current_frame)

                                # Define the unique combination of pair and state
                                current_pair_state_id = (current_start_frame_index, current_end_frame_index, determined_state)

                                notes = ""
                                pair_state_processed_for_state = False # Flag to indicate if this combination affects global state/sequence

                                # --- Check for Duplicate Pair+State Combination ---
                                if current_pair_state_id not in processed_pair_state_combinations:
                                    # --- Unique Pair+State Combination - Process for Global Confirmation ---

                                    # Add state to sequence and check for confirmation
                                    state_just_confirmed = add_state_to_confirmation_sequence(determined_state)
                                    if state_just_confirmed:
                                        notes = (notes + ";" if notes else "") + f"STATE_CONFIRMED={last_confirmed_state}"

                                    # Mark this combination as processed for state determination
                                    processed_pair_state_combinations.add(current_pair_state_id)
                                    pair_state_processed_for_state = True # This combination contributed to global state/sequence

                                    # Update the timestamp of the last state-relevant detection
                                    last_state_relevant_timestamp = current_frame['timestamp']


                                else:
                                    # --- Duplicate Pair+State Combination - Ignore for Global Confirmation ---
                                    notes = (notes + ";" if notes else "") + "IGNORED=DUPLICATE_PAIR_AND_STATE"
                                    # This does NOT update last_state_relevant_timestamp


                                # --- Log the Result ---
                                # Log the determined state for this pair and the *current* global confirmed state
                                log_state_change(
                                    current_frame['timestamp'],
                                    determined_state, # The state derived from this pair
                                    camera,
                                    current_frame['x_center'],
                                    current_frame['y_center'],
                                    prev_frame,
                                    current_frame,
                                    notes # Pass notes from processing
                                )

                            # else: Non-sequential pair found for this camera, skip for state logic


                        # else: No previous frame for this camera, cannot form a sequential pair yet


                    # Always update last frame for this camera with the current detection
                    # This allows the *next* detection for this camera to be checked against this one for sequential pair logic.
                    last_frame_per_camera[camera] = current_frame


                # End of loop over new_detections


            # --- End of Loop Iteration ---
            # If no new detections were found in this check, last_processed_timestamp remains as is from the previous check.
            # The timeout check at the start of the *next* iteration will use this older timestamp.

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error in monitoring: {e}")
        import traceback
        traceback.print_exc() # Print traceback for debugging

if __name__ == "__main__":
    monitor_animal_states()
