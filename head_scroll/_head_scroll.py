import threading
import time

class Scroller(object):
    def __init__(self, eye_tracker, mouse, tilt_threshold=0.075, scroll_period=0.2):
        self.eye_tracker = eye_tracker
        self.mouse = mouse
        self.tilt_threshold = tilt_threshold
        self.scroll_period = scroll_period

    def start(self):
        self._start_gaze = self.eye_tracker.get_gaze_point_or_default()
        self.mouse.move((int(self._start_gaze[0]), int(self._start_gaze[1])))
        self._start_rotation = self.eye_tracker.get_head_rotation_or_default()
        self._stop_event = threading.Event()
        thread = threading.Thread(target=self._run)
        thread.setDaemon(True)
        thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        # TODO stop if mouse moves or head shakes
        while not self._stop_event.is_set():
            rotation = self.eye_tracker.get_head_rotation_or_default()
            x_delta = rotation[0] - self._start_rotation[0]
            if x_delta >= self.tilt_threshold:
                self.mouse.scroll_up()
            elif x_delta <= -self.tilt_threshold:
                self.mouse.scroll_down()
            time.sleep(self.scroll_period)
