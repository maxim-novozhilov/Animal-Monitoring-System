import os
import gc
import time
import subprocess
import csv
import torch
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ultralytics import YOLO
from datetime import datetime

class DetectionLogger:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "animal_detections_log.csv")
        self._initialize_log()
        
    def _initialize_log(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'camera', 'filename', 'object_class', 'x_center', 'y_center'])
    
    def log_detection(self, timestamp, cam_num, filename, detection):
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for box in detection.boxes:
                cls = int(box.cls.item())
                xywhn = box.xywhn[0].tolist()
                writer.writerow([
                    timestamp,
                    cam_num,
                    filename,
                    detection.names[cls],
                    xywhn[0],
                    xywhn[1],
                ])

class FrameHandler(FileSystemEventHandler):
    def __init__(self, model, cam_num, logger):
        self.model = model
        self.cam_num = cam_num
        self.logger = logger
        self.processed = set()
        # self.desired_classes = [1, 2, ...] # Define the classes you want to detect
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.jpg'):
            if event.src_path not in self.processed:
                self.processed.add(event.src_path)
                self.process_frame(event.src_path)
                
    def process_frame(self, frame_path):
        try:
            results = self.model(frame_path)
            # if use self.desired_classes change results for
            # results = self.model(frame_path, classes=self.desired_classes)
            base_name = os.path.basename(frame_path)
            
            # Create labels subdirectory if it doesn't exist
            labels_dir = os.path.join(os.path.dirname(frame_path), "labels")
            os.makedirs(labels_dir, exist_ok=True)
            
            # Save YOLO format label file in labels subdirectory
            label_name = os.path.splitext(base_name)[0] + '.txt'
            label_path = os.path.join(labels_dir, label_name)
            
            # Save labels in YOLO format (class_id, x_center, y_center, width, height)
            with open(label_path, 'w') as f:
                for box in results[0].boxes:
                    cls = int(box.cls.item())
                    xywhn = box.xywhn[0].tolist()  # Normalized coordinates
                    f.write(f"{cls} {xywhn[0]} {xywhn[1]} {xywhn[2]} {xywhn[3]}\n")
            
            # Log detections
            self.logger.log_detection(
                timestamp=datetime.now().isoformat(),
                cam_num=self.cam_num,
                filename=base_name,
                detection=results[0]
            )
            
            # Print detection summary
            boxes = results[0].boxes
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Camera {self.cam_num} - {base_name}:")
            print(f"Detected objects: {', '.join(results[0].names[int(box.cls.item())] for box in boxes)}")
            print(f"Labels saved to: {label_path}")
            
        except Exception as e:
            print(f"Error processing {frame_path}: {str(e)}")
        finally:
            # Attempt to clear GPU memory cache and Python garbage
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect() # This collects Python objects, releasing their memory if no longer referenced      

def setup_camera_system():
    
    print(torch.cuda.get_device_name())
    print(torch.cuda.is_available())
    
    model = YOLO("/home/.../best.pt")
    base_dir = "/home/..."
    date_str = datetime.now().strftime("%Y%m%d")
    
    main_dir = f"{base_dir}/{date_str}_Animal"
    log_dir = main_dir
    os.makedirs(main_dir, exist_ok=True)
    
    logger = DetectionLogger(log_dir)
    
    animal_config = {
            1: {"rtsp_url": "rtsp://...", "suffix": "#"},
            2: {.....}
    }
    
    observers = []
    processes = []
    
    for cam_num, config in animal_config.items():
        cam_dir = f"{main_dir}/cam{cam_num}"
        os.makedirs(cam_dir, exist_ok=True)
        
        handler = FrameHandler(model, cam_num, logger)
        observer = Observer()
        observer.schedule(handler, cam_dir, recursive=False)
        observer.start()
        observers.append(observer)
        
        output_pattern = f"{cam_dir}/{datetime.now().strftime('%y%m%d')}%04d_{cam_num}_{config['suffix']}.jpg"
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-rtsp_transport", "tcp",
            "-i", config["rtsp_url"],
            "-r", "1", # or any another interval
            output_pattern
        ]
        processes.append(subprocess.Popen(cmd))
        print(f"Camera {cam_num} started - Saving to {cam_dir}")
    
    return observers, processes, logger

if __name__ == "__main__":
    try:
        print("Starting Animal Monitoring System")
        print(f"Initializing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        observers, processes, logger = setup_camera_system()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        for obs in observers:
            obs.stop()
        for proc in processes:
            proc.terminate()
        
    finally:
        for obs in observers:
            obs.join()
        print("System shutdown complete")
        print(f"Detection log saved to: {logger.log_file}")

