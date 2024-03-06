import numpy as np
import socket
import cv2
from rtp import RTP

base_rtp = RTP()


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


class Consume(object):
    def __init__(self, host, port):
        self._reconstruct = ImageReconstruct()

        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((host, port))

    def receive_udp_data(self, buffer_size=65535):
        chunks = list()

        while True:
            chunk, addr = self._socket.recvfrom(buffer_size)
            if not chunk:
                break
            packet = RTP().fromBytes(chunk)
            self._reconstruct.submit(packet)

            if self._reconstruct.ready():
                frame = self._reconstruct.reconstruct()
                cv2.imshow("HOWDY", frame)
                cv2.waitKey(3)
                self._reconstruct.reset()

        # return b''.join(chunks)

    def deserialize_array(data):
        # Extract metadata
        metadata, data_bytes = data.split(b'|', 1)
        dtype, shape = metadata.decode().split(':')
        shape = tuple(map(int, shape.split(',')))
        # Reconstruct the array
        return np.frombuffer(data_bytes, dtype=dtype).reshape(shape)


consumer = Consume("127.0.0.1", 999)
consumer.receive_udp_data()

# UDP_IP = "127.0.0.1"
# UDP_PORT = 999
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind((UDP_IP, UDP_PORT))

# while True:
#     # data, addr = sock.recvfrom(65535)
#     receive_udp_data(sock)
