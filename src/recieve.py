from consumer import Consumer
from camera import Camera
import threading
import json
import os

# Navigate to the root of the project
project_root = os.path.dirname(os.path.dirname(__file__))
os.chdir(project_root)

# Extract Camera configurations
camera_config_path = "config/receive.json"

with open(camera_config_path) as config_file:
    config_json = json.load(config_file)
    cameras = [Camera.from_json(c) for c in config_json["cameras"]]

lifeline = threading.Event()

threads = list()
for camera in cameras:
    cons = Consumer(camera, lifeline)
    thread = threading.Thread(target=cons.start)
    threads.append(thread)

for thread in threads:
    thread.start()

input("Press enter to terminate...")
lifeline.set()

for thread in threads:
    thread.join()
