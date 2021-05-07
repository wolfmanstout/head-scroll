# Simple script to test scrolling.

import sys

import gaze_ocr
import head_scroll

from PySide2 import QtCore, QtGui, QtWidgets


class Visualization(QtWidgets.QWidget):
    def __init__(self, parent, scroller):
        super(Visualization, self).__init__(parent)
        self.scroller = scroller
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"),
                     self.update)
        self.timer.start(10)

    @staticmethod
    def _draw_horizontal_line(painter, y):
        painter.drawLine(-10000, y, 10000, y)

    @staticmethod
    def _with_alpha(color, alpha):
        new_color = QtGui.QColor(color)
        new_color.setAlphaF(alpha)
        return new_color

    def paintEvent(self, event):
        window = event.rect()
        painter = QtGui.QPainter(self)
        scroll = self.scroller
        # Round to nearest bucket to avoid excessive movement.
        center_x = round(scroll.gaze[0] / 250) * 250
        center_x = min(window.right() - 100, max(window.left() + 100, center_x))
        center_y = round(scroll.gaze[1] / 125) * 125
        center_y = min(window.bottom() - 100, max(window.top() + 100, center_y))
        painter.translate(center_x - window.left(), center_y - window.top())
        clip_rect = QtCore.QRect(-100, -200, 200, 400)
        painter.setClipRect(clip_rect)
        scale = 500
        line_width = 3
        diameter = 5
        # painter.setPen(QtCore.Qt.NoPen)
        # painter.setBrush(QtCore.Qt.white)
        # painter.drawRect(clip_rect)
        # painter.setPen(QtGui.QPen(QtCore.Qt.green if scroll.is_scrolling else QtCore.Qt.blue,
        #                           line_width))
        # painter.drawLine(0, 0, 0, -(scroll.smooth_pitch - scroll.expected_pitch) * scale)
        # painter.setPen(QtGui.QPen(QtCore.Qt.red, line_width))
        # min_diff = scroll.min_pitch - scroll.expected_pitch
        # max_diff = scroll.max_pitch - scroll.expected_pitch
        # painter.drawLine(-line_width, -min_diff * scale,
        #                  line_width, -min_diff * scale)
        # painter.drawLine(-line_width, -max_diff * scale,
        #                  line_width, -max_diff * scale)
        # painter.setPen(QtCore.Qt.NoPen)
        # painter.setBrush(QtCore.Qt.gray)
        # x = -scroll.rotation[1] * scale
        # y = -scroll.smooth_pitch * scale
        # painter.drawPie(QtCore.QRect(x - diameter / 2, y - diameter / 2, diameter, diameter), 0, 16 * 360)
        alpha = 0.25
        painter.setPen(QtGui.QPen(self._with_alpha(QtCore.Qt.blue, alpha), line_width))
        self._draw_horizontal_line(painter, -scroll.smooth_pitch * scale)
        painter.setPen(QtGui.QPen(self._with_alpha(QtCore.Qt.green, alpha), line_width))
        self._draw_horizontal_line(painter, -scroll.expected_pitch * scale)
        # painter.setPen(QtGui.QPen(QtCore.Qt.blue, line_width))
        # self._draw_horizontal_line(painter, -scroll.pinned_pitch * scale)
        painter.setPen(QtGui.QPen(self._with_alpha(QtCore.Qt.red, alpha), line_width))
        self._draw_horizontal_line(painter, -scroll.min_pitch * scale)
        self._draw_horizontal_line(painter, -scroll.max_pitch * scale)


class Overlay(QtWidgets.QWidget):
    def __init__(self, scroller, parent=None):
        super(Overlay, self).__init__(parent)
        self.scroller = scroller

        self.setWindowFlags(
            self.windowFlags() |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setGeometry(QtGui.QGuiApplication.primaryScreen().availableGeometry())

        self.visualization = Visualization(self, self.scroller)
        # self.start_button = QtWidgets.QPushButton("Start", self)
        # self.quit_button = QtWidgets.QPushButton("Quit", self)
        # self.connect(self.start_button, QtCore.SIGNAL("clicked()"),
        #              self.start)
        # self.connect(self.quit_button, QtCore.SIGNAL("clicked()"),
        #              self.quit)

        layout = QtWidgets.QVBoxLayout()
        # layout.addWidget(self.start_button)
        # layout.addWidget(self.quit_button)
        layout.addWidget(self.visualization)
        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_S:
            self.start()
        elif event.key() == QtCore.Qt.Key_Q:
            self.quit()

    @QtCore.Slot()
    def start(self):
        self.scroller.start()

    @QtCore.Slot()
    def quit(self):
        self.scroller.stop()
        QtWidgets.QApplication.instance().quit()


app = QtWidgets.QApplication(sys.argv)
scroller = head_scroll.Scroller(
    gaze_ocr.eye_tracking.EyeTracker.get_connected_instance(sys.argv[1]),
    gaze_ocr._dragonfly_wrappers.Mouse())
widget = Overlay(scroller)
widget.show()
sys.exit(app.exec_())
