from producer import Producer
from camera import Camera
import threading
import json
import os

# Navigate to the root of the project
project_root = os.path.dirname(os.path.dirname(__file__))
os.chdir(project_root)

# Extract Camera configurations
camera_config_path = "config/serve.json"

with open(camera_config_path) as config_file:
    config_json = json.load(config_file)
    cameras = [Camera.from_json(c) for c in config_json["cameras"]]
    for c in cameras:
        c.resize = config_json["FrameSize"]

lifeline = threading.Event()

threads = list()
for camera in cameras:
    prod = Producer(camera, lifeline)
    thread = threading.Thread(target=prod.start)
    threads.append(thread)

for thread in threads:
    thread.start()

input("Press enter to terminate... ")
lifeline.set()

for thread in threads:
    thread.join()
