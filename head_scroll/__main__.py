# Simple script to test scrolling.

import sys

import gaze_ocr
import head_scroll

from PySide2 import QtCore, QtGui, QtWidgets


class Visualization(QtWidgets.QWidget):
    def __init__(self, parent, scroller):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFixedSize(200, 200)
        self.setPalette(QtGui.QPalette(QtGui.QColor(255, 255, 255)))
        self.setAutoFillBackground(True)
        self.scroller = scroller

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.black)
        painter.translate(100, 100)
        scale = 200
        x = -self.scroller.rotation[1] * scale
        y = -self.scroller.smooth_x * scale
        painter.drawPie(QtCore.QRect(x, y, 2, 2), 0, 16 * 360)
        painter.setPen(QtCore.Qt.green)
        painter.drawLine(-100, -self.scroller.reference_x * scale,
                         100, -self.scroller.reference_x * scale)
        painter.setPen(QtCore.Qt.red)
        painter.drawLine(-100, -(self.scroller.reference_x + self.scroller.up_threshold) * scale,
                         100, -(self.scroller.reference_x + self.scroller.up_threshold) * scale)
        painter.drawLine(-100, -(self.scroller.reference_x - self.scroller.down_threshold) * scale,
                         100, -(self.scroller.reference_x - self.scroller.down_threshold) * scale)


class Overlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

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

    @QtCore.Slot()
    def start(self):
        self.scroller.start()

    @QtCore.Slot()
    def quit(self):
        self.scroller.stop()
        qApp.quit()


app = QtWidgets.QApplication(sys.argv)
widget = Overlay()
widget.show()
sys.exit(app.exec_())
