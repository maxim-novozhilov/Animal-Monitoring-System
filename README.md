Animal Monitoring System
Overview
This project implements a real-time, AI-powered animal monitoring system designed to observe and log animal behavior in various environments such as homes, farms, zoos, or safari parks. Leveraging YOLOv8 for object detection and a robust state-tracking mechanism, the system processes live camera feeds (RTSP streams), identifies animals, tracks their movement, and infers their states (e.g., "walking," "resting," "unknown"). All detections and state changes are logged and can be pushed to a WebSocket for real-time web visualization.

This system is built with modularity in mind, allowing for easy adaptation to different animal types and camera setups.

Features
Real-time Object Detection: Utilizes a pre-trained or custom-trained YOLOv8 model to detect animals in live video streams.

Multi-Camera Support: Configurable to monitor multiple RTSP camera feeds simultaneously.

Event-Driven Processing: Monitors new image frames saved from camera feeds and processes them automatically.

Behavioral State Tracking: Analyzes sequential frames to determine animal states (e.g., walk, rest, passive).

Configurable Movement Thresholds: Easily adjust sensitivity for movement detection.

Idle Timeout Detection: Automatically sets the animal's state to "unknown" if no relevant activity is detected for a specified period.

Comprehensive Logging: All animal detections and inferred states are logged to CSV files for later analysis.

Real-time Web Integration: Pushes the latest animal state to a WebSocket endpoint, enabling dynamic web dashboards or applications.

Modular Design: Separate components for camera handling, detection logging, state analysis, and web communication.

Project Structure
animal.py: Handles camera stream capturing (using ffmpeg), real-time object detection with YOLOv8, and logging raw detections. It sets up file system observers to process newly saved frames.

states.py: Monitors the detection logs from animal.py, analyzes sequential frames to determine animal states (e.g., walk, rest), and logs these state changes to a separate CSV file. It includes logic for global state confirmation and idle timeouts.

web.py: Reads the latest animal state from the animal_states_log.csv and sends it to a specified WebSocket server for real-time updates.

Getting Started
Prerequisites
Python 3.x

pip (Python package installer)

ffmpeg (for capturing RTSP streams)

A pre-trained YOLOv8 model (e.g., best.pt as referenced in animal.py). You will need to provide your own model or train one.

Install Python dependencies:

pip install -r requirements.txt

(You'll need to create a requirements.txt file. See the next section.)

Install ffmpeg: Follow instructions for your operating system. For example, on Ubuntu:

sudo apt update
sudo apt install ffmpeg

On macOS (with Homebrew):

brew install ffmpeg

On Windows: Download from ffmpeg.org and add to PATH.

Configuration
Before running, you'll need to configure the paths and camera details in animal.py and states.py.

animal.py:

Update model = YOLO("/home/.../best.pt") with the actual path to your YOLO model.

Update base_dir = "/home/..." to your desired base directory for logs and camera output.

Modify animal_config dictionary with your camera RTSP URLs and suffixes.

states.py:

Update BASE_DIR = "/home/..." to match the base directory in animal.py.

Adjust PASSIVE_CAMERAS, ACTIVE_CAMERAS, MOVEMENT_THRESHOLD, CHECK_INTERVAL, CONFIRMATION_SEQUENCE_LENGTH, and IDLE_TIMEOUT_SECONDS as needed for your specific monitoring requirements.

web.py:

Update BASE_DIR = "/home/..." to match the base directory in animal.py.

Change "wss://..." in send_websocket_request to your actual WebSocket server URL.

Running the System
The system is designed to run as three separate, concurrently operating components.

Start the Camera Monitoring and Detection (animal.py):
This script captures frames, runs detections, and logs them.

python animal.py

Start the Animal State Monitoring (states.py):
This script reads detection logs and infers animal states.

python states.py

Start the Web Socket Sender (web.py):
This script sends the latest state to your WebSocket server.

python web.py [PROCESS_INTERVAL_SECONDS] [ANIMAL_NAME]

PROCESS_INTERVAL_SECONDS (optional): How often to send updates (default: 1 second).

ANIMAL_NAME (optional): The name of the animal being monitored (default: 'animal').

Example: python web.py 5 dog

Note: Ensure all three scripts are running simultaneously for the full system to function.

Dependencies (for requirements.txt)
Create a file named requirements.txt in your project's root directory with the following content:

watchdog
ultralytics
pandas
torch
websockets
requests

Future Enhancements
Web Interface: Develop a full-fledged web dashboard to visualize real-time states, historical data, and camera feeds.

Database Integration: Store detection and state data in a more robust database (e.g., PostgreSQL, MongoDB) instead of CSV files for better querying and scalability.

Alerting System: Implement notifications (email, SMS, push) for specific state changes or events.

Machine Learning Model Retraining: Add scripts or workflows for easily retraining the YOLO model with new data.

Dockerization: Containerize the application for easier deployment across different environments.

Error Handling & Resilience: Enhance error handling and add mechanisms for automatic recovery from failures (e.g., camera disconnections).

Contributing
Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please open an issue or submit a pull request.

License
This project is open-sourced under the MIT License.
