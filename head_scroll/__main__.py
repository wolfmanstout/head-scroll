# Simple script to test scrolling.

import sys

import gaze_ocr
import head_scroll

from PySide2 import QtCore, QtGui, QtWidgets


class Visualization(QtWidgets.QWidget):
    def __init__(self, parent, scroller):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFixedSize(200, 200)
        self.scroller = scroller

    @staticmethod
    def _draw_horizontal_line(painter, y):
        painter.drawLine(-100, y, 100, y)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.black)
        painter.translate(100, 100)
        scale = 200
        x = -self.scroller.rotation[1] * scale
        y = -self.scroller.smooth_pitch * scale
        painter.drawPie(QtCore.QRect(x, y, 2, 2), 0, 16 * 360)
        painter.setPen(QtCore.Qt.green)
        self._draw_horizontal_line(painter, -self.scroller.expected_pitch * scale)
        painter.setPen(QtCore.Qt.blue)
        self._draw_horizontal_line(painter, -self.scroller.pinned_pitch * scale)
        painter.setPen(QtCore.Qt.red)
        self._draw_horizontal_line(painter, -self.scroller.min_pitch * scale)
        self._draw_horizontal_line(painter, -self.scroller.max_pitch * scale)


class Overlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)
        self.setWindowFlags(
            self.windowFlags() |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setGeometry(
            QtWidgets.QStyle.alignedRect(
                QtCore.Qt.LeftToRight, QtCore.Qt.AlignCenter,
                QtCore.QSize(400, 400),
                QtGui.QGuiApplication.primaryScreen().availableGeometry()))

        self.scroller = head_scroll.Scroller(
            gaze_ocr.eye_tracking.EyeTracker.get_connected_instance(sys.argv[1]),
            gaze_ocr._dragonfly_wrappers.Mouse())

        self.start_button = QtWidgets.QPushButton("Start", self)
        self.quit_button = QtWidgets.QPushButton("Quit", self)
        self.visualization = Visualization(self, self.scroller)
        self.timer = QtCore.QTimer(self)
        self.connect(self.start_button, QtCore.SIGNAL("clicked()"),
                     self.start)
        self.connect(self.quit_button, QtCore.SIGNAL("clicked()"),
                     self.quit)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"),
                     self.visualization.update)
        self.timer.start(10)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.quit_button)
        layout.addWidget(self.visualization)
        self.setLayout(layout)

    # Capture clicks on directly-painted overlay.
    def mousePressEvent(self, event):
        self.quit()

    @QtCore.Slot()
    def start(self):
        self.scroller.start()

    @QtCore.Slot()
    def quit(self):
        self.scroller.stop()
        QtWidgets.QApplication.instance().quit()


app = QtWidgets.QApplication(sys.argv)
widget = Overlay()
widget.show()
sys.exit(app.exec_())
