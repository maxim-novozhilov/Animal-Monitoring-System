Animal Monitoring System

Overview
This project implements a real-time, AI-powered animal monitoring system designed to observe and log animal behavior in various environments such as homes, farms, zoos, or safari parks. Leveraging YOLO11 for object detection and a robust state-tracking mechanism, the system processes live camera feeds (RTSP streams), identifies animals, tracks their movement, and infers their states (e.g., "walking," "resting," "unknown"). All detections and state changes are logged and can be pushed to a WebSocket for real-time web visualization.
This system is built with modularity in mind, allowing for easy adaptation to different animal types and camera setups.

Features
Real-time Object Detection: Utilizes a pre-trained or custom-trained YOLO11 model to detect animals in live video streams.
Multi-Camera Support: Configurable to monitor multiple RTSP camera feeds simultaneously.
Event-Driven Processing: Monitors new image frames saved from camera feeds and processes them automatically.
Behavioral State Tracking: Analyzes sequential frames to determine animal states (e.g., walk, rest, passive).
Configurable Movement Thresholds: Easily adjust sensitivity for movement detection.
Idle Timeout Detection: Automatically sets the animal's state to "unknown" if no relevant activity is detected for a specified period.
Comprehensive Logging: All animal detections and inferred states are logged to CSV files for later analysis.
Real-time Web Integration: Pushes the latest animal state to a WebSocket endpoint, enabling dynamic web dashboards or applications.
Modular Design: Separate components for camera handling, detection logging, state analysis, and web communication.

Project Structure
animal.py: Handles camera stream capturing (using ffmpeg), real-time object detection with YOLO11, and logging raw detections. It sets up file system observers to process newly saved frames.
states.py: Monitors the detection logs from animal.py, analyzes sequential frames to determine animal states (e.g., walk, rest), and logs these state changes to a separate CSV file. It includes logic for global state confirmation and idle timeouts.
web.py: Reads the latest animal state from the animal_states_log.csv and sends it to a specified WebSocket server for real-time updates.

Dependencies
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


License
This project is open-sourced under the MIT License.
