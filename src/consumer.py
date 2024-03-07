import numpy as np
import socket
import cv2
from rtp import RTP
from camera import Camera
import threading
from queue import Queue

### ----- Constants ----- #####

MAX_FRAME_POOL_SIZE = 10
BUFFER_SIZE = 65535

##### ------------------- #####


class ImageReconstruct(object):
    def __init__(self):
        self._n_chunks = -1
        self._received = None
        self._data = None

    def submit(self, packet: RTP):
        if self._n_chunks == -1:
            self._n_chunks = packet.ssrc
            self._received = [False] * self._n_chunks
            self._data = [None] * self._n_chunks

        seq_num = packet.sequenceNumber
        self._received[seq_num] = True
        self._data[seq_num] = packet.payload

    def ready(self):
        return sum(self._received) == self._n_chunks

    def reconstruct(self):
        data = b''.join(self._data)

        # Extract metadata
        metadata, data_bytes = data.split(b'|', 1)
        dtype, shape = metadata.decode().split(':')
        shape = tuple(map(int, shape.split(',')))
        # Reconstruct the array
        return np.frombuffer(data_bytes, dtype=dtype).reshape(shape)

    def reset(self):
        self._received = [False] * self._n_chunks


class Consumer(object):
    def __init__(self, camera: Camera, lifeline: threading.Event):
        self._reconstruct = ImageReconstruct()
        self._host = camera.host
        self._port = camera.port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._socket.bind((camera.host, camera.port))
        self._received_frames = Queue(MAX_FRAME_POOL_SIZE)
        self._lifeline = lifeline

    def start(self):
        while not self._lifeline.is_set():
            try:
                chunk, _ = self._socket.recvfrom(BUFFER_SIZE)
            except BlockingIOError:
                continue
            if not chunk:
                break
            packet = RTP().fromBytes(chunk)
            self._reconstruct.submit(packet)

            if self._reconstruct.ready():
                frame = self._reconstruct.reconstruct()
                if self._received_frames.full():
                    self._received_frames.get()
                self._received_frames.put(frame)
                self._reconstruct.reset()

    def retrieve(self):
        return self._received_frames.get()
