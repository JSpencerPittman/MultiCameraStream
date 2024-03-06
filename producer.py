import cv2
from queue import Queue
import socket
import threading
import time
from rtp import RTP, Extension, PayloadType
from copy import deepcopy

### ----- Constants ----- #####

MAX_FRAME_POOL_SIZE = 10

##### ------------------- #####


class Producer(object):
    def __init__(self, src, host, port):
        self._src = src
        self._host = host
        self._port = port
        self._frames = Queue(MAX_FRAME_POOL_SIZE)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._base_packet = RTP()

        self._active = threading.Event()

    def start(self):
        cap = cv2.VideoCapture(self._src)
        fps = cap.get(cv2.CAP_PROP_FPS)

        time_per_frame = 1 / fps  # seconds

        if not cap.isOpened():
            print(f"Error: invalid source: {self._src}")
            return

        sender_thread = threading.Thread(target=self.send_loop)
        sender_thread.start()

        self._active.set()

        while cap.isOpened():
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

        print("Terminating...")

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
    def chunk_data(data, chunk_size=64000):
        return [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
