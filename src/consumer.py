import numpy as np
import socket
import cv2
from rtp import RTP
from camera import Camera
import threading

### ----- Constants ----- #####

BUFFER_SIZE = 65535

##### ------------------- #####


class ImageReconstruct(object):
    def __init__(self):
        self._n_chunks = -1
        self._recieved = None
        self._data = None

    def submit(self, packet: RTP):
        if self._n_chunks == -1:
            self._n_chunks = packet.ssrc
            self._recieved = [False] * self._n_chunks
            self._data = [None] * self._n_chunks

        seq_num = packet.sequenceNumber
        self._recieved[seq_num] = True
        self._data[seq_num] = packet.payload

    def ready(self):
        return sum(self._recieved) == self._n_chunks

    def reconstruct(self):
        data = b''.join(self._data)

        # Extract metadata
        metadata, data_bytes = data.split(b'|', 1)
        dtype, shape = metadata.decode().split(':')
        shape = tuple(map(int, shape.split(',')))
        # Reconstruct the array
        return np.frombuffer(data_bytes, dtype=dtype).reshape(shape)

    def reset(self):
        self._recieved = [False] * self._n_chunks


class Consumer(object):
    def __init__(self, camera: Camera, lifeline: threading.Event):
        self._reconstruct = ImageReconstruct()

        self._host = camera.host
        self._port = camera.port
        self._name = camera.name
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._socket.bind((camera.host, camera.port))
        self._lifeline = lifeline

    def start(self):
        chunks = list()

        try:
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
                    cv2.imshow(self._name, frame)
                    cv2.waitKey(1)
                    self._reconstruct.reset()

        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyWindow(self._name)
