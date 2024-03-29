import numpy as np
import cv2
import math
from consumer import Consumer


class Window(object):
    def __init__(self, n_windows, frame_size):
        self._n_windows = n_windows
        self._consumers = [None] * self._n_windows
        self._frame_size = frame_size

        self._rows = min(n_windows, 2)
        self._cols = math.ceil(n_windows/2)
        self._width = self._cols * frame_size[1]
        self._height = self._rows * frame_size[0]

        self._display = np.zeros(
            (self._height, self._width, 3), dtype=np.uint8)

    def synchronize(self, win_idx, consumer: Consumer):
        self._consumers[win_idx] = consumer

    def update_subwindow(self, win_idx):
        if self._consumers[win_idx] is None:
            return

        new_frame = self._consumers[win_idx].retrieve()

        row = win_idx % 2
        col = win_idx // 2

        r_idx_start = row * self._frame_size[0]
        r_idx_end = r_idx_start + self._frame_size[0]

        c_idx_start = col * self._frame_size[1]
        c_idx_end = c_idx_start + self._frame_size[1]

        self._display[r_idx_start:r_idx_end,
                      c_idx_start:c_idx_end, :] = new_frame

    def refresh(self):
        for win_idx in range(self._n_windows):
            self.update_subwindow(win_idx)
        cv2.imshow("Live", self._display)
