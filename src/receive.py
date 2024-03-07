
import multiprocessing
import os
import json
import cv2
from window import Window
from camera import Camera
from consumer import Consumer


def worker(camera, lifeline, frame_buffer):
    consumer = Consumer(camera, lifeline, frame_buffer)
    consumer.start()


if __name__ == "__main__":
    # Navigate to the root of the project
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.chdir(project_root)

    # Extract Camera configurations
    camera_config_path = "config/receive.json"

    with open(camera_config_path) as config_file:
        config_json = json.load(config_file)
        cameras = [Camera.from_json(c) for c in config_json["cameras"]]
        frame_size = config_json["FrameSize"]

    lifeline = multiprocessing.Event()
    window = Window(len(cameras), frame_size)

    processes = list()
    for i, camera in enumerate(cameras):
        frame_buffer = multiprocessing.Queue()
        window.synchronize(i, frame_buffer)
        process = multiprocessing.Process(
            target=worker, args=(camera, lifeline, frame_buffer))
        processes.append(process)

    for process in processes:
        process.start()

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
        for process in processes:
            process.join()
