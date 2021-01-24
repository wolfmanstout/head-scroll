import threading
import time

from collections import deque


class Scroller(object):
    def __init__(self,
                 eye_tracker,
                 mouse,
                 up_threshold=0.1,
                 down_threshold=0.1,
                 stop_threshold=0.1,
                 shake_threshold=0.3,
                 check_frequency=20,
                 scroll_frequency=5,
                 smooth_frequency=10):
        """Note: check_frequency must be a multiple of scroll_frequency and
        smooth_frequency.
        """
        self.eye_tracker = eye_tracker
        self.mouse = mouse
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.stop_threshold = stop_threshold
        self.shake_threshold = shake_threshold
        self.check_frequency = check_frequency
        self.scroll_frequency = scroll_frequency
        self.smooth_frequency = smooth_frequency
        self._stop_event = None

        # For visualization.
        self.rotation = (0, 0, 0)
        self.reference_x = 0
        self.smooth_x = 0
        self.x_velocity = 0
        self.y_velocity = 0

    def start(self):
        if self._stop_event:
            return
        # Move cursor so we scroll in the right window.
        start_gaze = self.eye_tracker.get_gaze_point_or_default()
        self.mouse.move((int(start_gaze[0]), int(start_gaze[1])))
        stop_event = threading.Event()
        thread = threading.Thread(target=lambda: self._run(stop_event))
        thread.setDaemon(True)
        thread.start()
        self._stop_event = stop_event

    def stop(self):
        if not self._stop_event:
            return
        self._stop_event.set()
        self._stop_event = None

    def _run(self, stop_event):
        check_period = 1.0 / self.check_frequency
        scroll_period_count = 0
        scroll_multiple = self.check_frequency // self.scroll_frequency
        smooth_multiple = self.check_frequency // self.smooth_frequency
        smooth_period = 1.0 / self.smooth_frequency
        recent_rotations = deque(maxlen=smooth_multiple)
        rotation = self.eye_tracker.get_head_rotation_or_default()
        recent_rotations.append(rotation)
        smooth_x = rotation[0] / smooth_multiple
        reference_x = rotation[0]
        while not stop_event.is_set():
            time.sleep(check_period)

            rotation = self.eye_tracker.get_head_rotation_or_default()
            smooth_x += rotation[0] / smooth_multiple
            if len(recent_rotations) == smooth_multiple:
                smooth_x -= recent_rotations[0][0] / smooth_multiple
                x_velocity = (rotation[0] - recent_rotations[0][0]) / smooth_period
                y_velocity = (rotation[1] - recent_rotations[0][1]) / smooth_period
                if abs(y_velocity) > self.shake_threshold:
                    reference_x = rotation[0]
                relative_x = smooth_x - reference_x

                # Snapshot variables for visualization.
                self.rotation = rotation
                self.reference_x = reference_x
                self.smooth_x = smooth_x
                self.x_velocity = x_velocity
                self.y_velocity = y_velocity

                if relative_x > self.up_threshold and x_velocity > -self.stop_threshold:
                    if scroll_period_count == 0:
                        speed = round(relative_x / self.up_threshold)
                        self.mouse.scroll_up(speed)
                    scroll_period_count = (scroll_period_count + 1) % scroll_multiple
                elif relative_x < -self.down_threshold and x_velocity < self.stop_threshold:
                    if scroll_period_count == 0:
                        speed = round(relative_x / -self.down_threshold)
                        self.mouse.scroll_down(speed)
                    scroll_period_count = (scroll_period_count + 1) % scroll_multiple
                else:
                    scroll_period_count = 0

            recent_rotations.append(rotation)
