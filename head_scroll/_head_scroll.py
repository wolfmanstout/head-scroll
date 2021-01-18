import threading
import time

from collections import deque


class ScrollState:
    NOT_SCROLLING = 1
    SCROLLING_DOWN = 2
    STOPPING_SCROLLING_DOWN = 3
    SCROLLING_UP = 4
    STOPPING_SCROLLING_UP = 5


class Scroller(object):
    def __init__(self,
                 eye_tracker,
                 mouse,
                 up_threshold=0.15,
                 up_fast_threshold=0.35,
                 down_threshold=0.15,
                 down_fast_threshold=0.35,
                 stop_threshold=0.1,
                 shake_threshold=0.2,
                 check_frequency=20,
                 scroll_frequency=5,
                 smooth_frequency=4):
        """Note: check_frequency must be a multiple of scroll_frequency and
        smooth_frequency.
        """
        self.eye_tracker = eye_tracker
        self.mouse = mouse
        self.up_threshold = up_threshold
        self.up_fast_threshold = up_fast_threshold
        self.down_threshold = down_threshold
        self.down_fast_threshold = down_fast_threshold
        self.stop_threshold = stop_threshold
        self.shake_threshold = shake_threshold
        self.check_frequency = check_frequency
        self.scroll_frequency = scroll_frequency
        self.smooth_frequency = smooth_frequency
        self._stop_event = None

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
        state = ScrollState.NOT_SCROLLING
        check_period = 1.0 / self.check_frequency
        period_count = 0
        scroll_multiple = self.check_frequency // self.scroll_frequency
        smooth_multiple = self.check_frequency // self.smooth_frequency
        smooth_period = 1.0 / self.smooth_frequency
        recent_rotations = deque(maxlen=smooth_multiple)
        recent_rotations.append(self.eye_tracker.get_head_rotation_or_default())
        while not stop_event.is_set():
            time.sleep(check_period)
            period_count += 1

            rotation = self.eye_tracker.get_head_rotation_or_default()
            if len(recent_rotations) == smooth_multiple:
                x_velocity = (rotation[0] - recent_rotations[0][0]) / smooth_period
                y_velocity = (rotation[1] - recent_rotations[0][1]) / smooth_period

                if state == ScrollState.NOT_SCROLLING:
                    if x_velocity > self.up_threshold:
                        state = ScrollState.SCROLLING_UP
                        speed = 1
                    elif x_velocity < -self.down_threshold:
                        state = ScrollState.SCROLLING_DOWN
                        speed = 1
                elif state == ScrollState.SCROLLING_UP:
                    if x_velocity < -self.stop_threshold:
                        state = ScrollState.STOPPING_SCROLLING_UP
                elif state == ScrollState.SCROLLING_DOWN:
                    if x_velocity > self.stop_threshold:
                        state = ScrollState.STOPPING_SCROLLING_DOWN
                elif state == ScrollState.STOPPING_SCROLLING_UP:
                    if x_velocity > -self.stop_threshold:
                        state = ScrollState.NOT_SCROLLING
                elif state == ScrollState.STOPPING_SCROLLING_DOWN:
                    if x_velocity < self.stop_threshold:
                        state = ScrollState.NOT_SCROLLING

                if abs(y_velocity) > self.shake_threshold:
                    state = ScrollState.NOT_SCROLLING

            if period_count == scroll_multiple:
                period_count = 0
                if state == ScrollState.SCROLLING_UP:
                    # Use the maximum velocity observed while scrolling.
                    if x_velocity > self.up_fast_threshold:
                        speed = 4
                    self.mouse.scroll_up(speed)
                elif state == ScrollState.SCROLLING_DOWN:
                    if x_velocity < -self.down_fast_threshold:
                        speed = 4
                    self.mouse.scroll_down(speed)
                
            recent_rotations.append(rotation)
