import threading
import time


class Scroller(object):
    def __init__(self,
                 eye_tracker,
                 mouse,
                 start_threshold=0.06,
                 fast_threshold=0.2,
                 stop_threshold=0.01,
                 scroll_period=0.2):
        self.eye_tracker = eye_tracker
        self.mouse = mouse
        self.start_threshold = start_threshold
        self.fast_threshold = fast_threshold
        self.stop_threshold = stop_threshold
        self.scroll_period = scroll_period

    def start(self):
        start_gaze = self.eye_tracker.get_gaze_point_or_default()
        self.mouse.move((int(start_gaze[0]), int(start_gaze[1])))
        self._start_rotation = self.eye_tracker.get_head_rotation_or_default()
        self._last_rotation = self._start_rotation
        self._stop_event = threading.Event()
        thread = threading.Thread(target=self._run)
        thread.setDaemon(True)
        thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            time.sleep(self.scroll_period)

            rotation = self.eye_tracker.get_head_rotation_or_default()
            start_delta = rotation[0] - self._start_rotation[0]
            last_delta = rotation[0] - self._last_rotation[0]

            if start_delta >= self.fast_threshold and last_delta > -self.stop_threshold:
                self.mouse.scroll_up(4)
            elif start_delta <= -self.fast_threshold and last_delta < self.stop_threshold:
                self.mouse.scroll_down(4)
            if start_delta >= self.start_threshold and last_delta > -self.stop_threshold:
                self.mouse.scroll_up()
            elif start_delta <= -self.start_threshold and last_delta < self.stop_threshold:
                self.mouse.scroll_down()

            self._last_rotation = rotation
