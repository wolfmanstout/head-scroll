import threading
import time

from collections import deque


class ScrollState:
    NOT_SCROLLING = 1
    SCROLLING_DOWN = 2
    SCROLLING_UP = 3


class Scroller(object):
    def __init__(self,
                 eye_tracker,
                 mouse,
                 coefs=[-0.21, -0.11,  0.00043,  0.00055],
                 gaze_alignment_threshold=0.1,
                 misaligned_pitch_velocity_threshold=0.05,
                 stop_threshold=0.1,
                 shake_threshold=0.4,
                 check_frequency=20,
                 scroll_frequency=5,
                 smooth_frequency=10):
        """Note: check_frequency must be a multiple of scroll_frequency and
        smooth_frequency.
        """
        self.eye_tracker = eye_tracker
        self.mouse = mouse
        self.coefs = coefs
        self.gaze_alignment_threshold = gaze_alignment_threshold
        self.misaligned_pitch_velocity_threshold = misaligned_pitch_velocity_threshold
        self.stop_threshold = stop_threshold
        self.shake_threshold = shake_threshold
        self.check_frequency = check_frequency
        self.scroll_frequency = scroll_frequency
        self.smooth_frequency = smooth_frequency
        self._stop_event = None

        # For visualization.
        self.gaze = (0, 0)
        self.rotation = (0, 0, 0)
        self.smooth_pitch = 0
        self.pitch_velocity = 0
        self.yaw_velocity = 0
        self.expected_pitch = 0
        self.pinned_pitch = 0
        self.min_pitch = 0
        self.max_pitch = 0
        self.is_scrolling = False

    def start(self):
        if self._stop_event:
            return
        # Move cursor so we scroll in the right window.
        start_gaze = self.eye_tracker.get_gaze_point_or_default()
        self.mouse.move((round(start_gaze[0]), round(start_gaze[1])))
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
        smooth_pitch = rotation[0] / smooth_multiple
        pinned_pitch = rotation[0]
        recent_gaze = deque(maxlen=smooth_multiple)
        gaze = self.eye_tracker.get_gaze_point_or_default()
        recent_gaze.append(gaze)
        smooth_gaze = (gaze[0] / smooth_multiple, gaze[1] / smooth_multiple)
        state = ScrollState.NOT_SCROLLING
        while not stop_event.is_set():
            time.sleep(check_period)

            rotation = self.eye_tracker.get_head_rotation_or_default()
            head_position = self.eye_tracker.get_head_position_or_default()
            gaze = self.eye_tracker.get_gaze_point_or_default()
            smooth_pitch += rotation[0] / smooth_multiple
            smooth_gaze = (smooth_gaze[0] + gaze[0] / smooth_multiple,
                           smooth_gaze[1] + gaze[1] / smooth_multiple)
            if len(recent_rotations) == smooth_multiple:
                smooth_pitch -= recent_rotations[0][0] / smooth_multiple
                smooth_gaze = (smooth_gaze[0] - recent_gaze[0][0] / smooth_multiple,
                               smooth_gaze[1] - recent_gaze[0][1] / smooth_multiple)
                pitch_velocity = (rotation[0] - recent_rotations[0][0]) / smooth_period
                yaw_velocity = (rotation[1] - recent_rotations[0][1]) / smooth_period

                # Update thresholds based on gaze if not scrolling.
                if state == ScrollState.NOT_SCROLLING:
                    monitor_size = self.eye_tracker.get_monitor_size()
                    expected_pitch = (self.coefs[0] +
                                      self.coefs[1] * (smooth_gaze[1] / monitor_size[1]) +
                                      self.coefs[2] * head_position[1] +
                                      self.coefs[3] * head_position[2])
                    if not(pinned_pitch < expected_pitch and smooth_pitch < pinned_pitch or
                           pinned_pitch > expected_pitch and smooth_pitch > pinned_pitch):
                        # Eye and gaze movements are aligned, so we keep pitch in bounds.
                        # This allows pitch to lag gaze.
                        pinned_pitch = smooth_pitch

                    min_pitch = min(expected_pitch - self.gaze_alignment_threshold,
                                    pinned_pitch - self.misaligned_pitch_velocity_threshold)
                    max_pitch = max(expected_pitch + self.gaze_alignment_threshold,
                                    pinned_pitch + self.misaligned_pitch_velocity_threshold)

                # Update state.
                if smooth_pitch > max_pitch:
                    state = ScrollState.SCROLLING_UP
                elif smooth_pitch < min_pitch:
                    state = ScrollState.SCROLLING_DOWN
                else:
                    if state != ScrollState.NOT_SCROLLING:
                        # Reset pinned pitch so we don't start scrolling again.
                        pinned_pitch = smooth_pitch
                    state = ScrollState.NOT_SCROLLING

                # if abs(yaw_velocity) > self.shake_threshold:
                #     pinned_pitch = smooth_pitch
                #     state = ScrollState.NOT_SCROLLING

                # Perform scrolling. Pause if pitch is moving in the wrong direction.
                is_scrolling = False
                if state == ScrollState.SCROLLING_UP and pitch_velocity > -self.stop_threshold:
                    if scroll_period_count == 0:
                        speed = 2 ** round((smooth_pitch - max_pitch) / self.gaze_alignment_threshold)
                        self.mouse.scroll_up(speed)
                    scroll_period_count = (scroll_period_count + 1) % scroll_multiple
                    is_scrolling = True
                elif state == ScrollState.SCROLLING_DOWN and pitch_velocity < self.stop_threshold:
                    if scroll_period_count == 0:
                        speed = 2 ** round((min_pitch - smooth_pitch) / self.gaze_alignment_threshold)
                        self.mouse.scroll_down(speed)
                    scroll_period_count = (scroll_period_count + 1) % scroll_multiple
                    is_scrolling = True
                else:
                    scroll_period_count = 0

                # Snapshot variables for visualization.
                self.gaze = smooth_gaze
                self.rotation = rotation
                self.smooth_pitch = smooth_pitch
                self.pitch_velocity = pitch_velocity
                self.yaw_velocity = yaw_velocity
                self.expected_pitch = expected_pitch
                self.pinned_pitch = pinned_pitch
                self.min_pitch = min_pitch
                self.max_pitch = max_pitch
                self.is_scrolling = is_scrolling

            recent_rotations.append(rotation)
            recent_gaze.append(gaze)
