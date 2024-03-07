from consumer import Consumer
from camera import Camera
from window import Window
import cv2
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
    frame_size = config_json["FrameSize"]

lifeline = threading.Event()
window = Window(len(cameras), frame_size)

threads = list()
for i, camera in enumerate(cameras):
    cons = Consumer(camera, lifeline)
    window.synchronize(i, cons)
    thread = threading.Thread(target=cons.start)
    threads.append(thread)

for thread in threads:
    thread.start()

try:
    while not lifeline.is_set():
        window.refresh()
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            lifeline.set()
            break
except KeyboardInterrupt:
    pass
finally:
    cv2.destroyAllWindows()
    for thread in threads:
        thread.join()
