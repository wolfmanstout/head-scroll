# Simple script to test scrolling.

import sys

import gaze_ocr
import head_scroll

scroller = head_scroll.Scroller(
    gaze_ocr.eye_tracking.EyeTracker.get_connected_instance(sys.argv[1]),
    gaze_ocr._dragonfly_wrappers.Mouse())
input("Press Enter to start scrolling...")
scroller.start()
input("Press Enter to stop scrolling...")
scroller.stop()
