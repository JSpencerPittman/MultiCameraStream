import cv2
from queue import Queue
import socket
import threading
import time
from rtp import RTP
from camera import Camera
from copy import deepcopy

### ----- Constants ----- #####

MAX_FRAME_POOL_SIZE = 10
CHUNK_SIZE = 64000

##### ------------------- #####


class Producer(object):
    def __init__(self, camera: Camera, lifeline: threading.Event):
        self._src = camera.uri
        self._host = camera.host
        self._port = camera.port
        self._frames = Queue(MAX_FRAME_POOL_SIZE)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._base_packet = RTP()
        self._resize = camera.resize

        self._lifeline = lifeline
        self._active = threading.Event()

    def start(self):
        cap = cv2.VideoCapture(self._src)
        fps = cap.get(cv2.CAP_PROP_FPS)

        time_per_frame = 1 / fps  # seconds

        if not cap.isOpened():
            print(f"Error: invalid source: {self._src}")
            return

        self._active.set()

        sender_thread = threading.Thread(target=self.send_loop)
        sender_thread.start()

        try:
            while cap.isOpened() and not self._lifeline.is_set():
                start_time = time.time()

                ret, frame = cap.read()

                if not ret:
                    break

                if self._frames.full():
                    self._frames.get()
                self._frames.put(frame)

                remaining_time = time_per_frame - (time.time() - start_time)

                if remaining_time > 0:
                    time.sleep(remaining_time)
        except KeyboardInterrupt:
            pass
        finally:
            self._active.clear()
            cap.release()
            sender_thread.join()

    def send_loop(self):
        while self._active.is_set():
            self.send_frame()

    def send_frame(self):
        if self._frames.empty():
            return

        frame = self._frames.get_nowait()

        if self._resize is not None:
            frame = cv2.resize(frame, self._resize)

        d = frame.flatten()
        s = d.tobytes()

        dtype = str(frame.dtype)
        shape = ','.join(map(str, frame.shape))
        metadata = f"{dtype}:{shape}|".encode()

        s = metadata + s

        chunks = self.chunk_data(s)

        for i, chunk in enumerate(chunks):
            packet = deepcopy(self._base_packet)
            packet.sequenceNumber = i
            packet.timestamp = int(time.time())
            packet.ssrc = len(chunks)
            packet.payload = bytearray(chunk)
            self._socket.sendto(packet.toBytes(), (self._host, self._port))

    @staticmethod
    def chunk_data(data):
        return [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
