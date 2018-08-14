## Author: Yinsen Miao

import pandas as pd
import numpy as np
import sys, ctypes, os
import seaborn as sns
import datetime
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QMainWindow, QFileDialog, QApplication, QAction,
                             QDesktopWidget, QToolTip, QSplitter, QMessageBox)
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree import types as pTypes


class GUIWidget(QWidget):
    def __init__(self):
        super(GUIWidget, self).__init__()
        self.setup_gui()

    def setup_gui(self):
        QToolTip.setFont(QFont("Helvetica", 12))
        # set gui layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # set global background and foreground color and init widgets
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=True)
        self.wit_lwd_log = pg.GraphicsLayoutWidget()

        # init parameter tree
        self.tree = ParameterTree(showHeader=False)  # don't show param tree header
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.wit_lwd_log)
        self.splitter.setSizes([int(self.width() * 0.2), int(self.width() * 0.8)])

        # add plots
        self.plt_rop = self.wit_lwd_log.addPlot()
        self.wit_lwd_log.nextRow()
        self.plt_wob = self.wit_lwd_log.addPlot()
        self.wit_lwd_log.nextRow()
        self.plt_srpm = self.wit_lwd_log.addPlot()
        self.wit_lwd_log.nextRow()
        self.plt_drpm = self.wit_lwd_log.addPlot()
        self.wit_lwd_log.nextRow()
        self.plt_ashk = self.wit_lwd_log.addPlot()
        self.wit_lwd_log.nextRow()
        self.plt_lshk = self.wit_lwd_log.addPlot()

        # add grids
        self.plt_rop.showGrid(x=True, y=True, alpha=0.3)
        self.plt_wob.showGrid(x=True, y=True, alpha=0.3)
        self.plt_srpm.showGrid(x=True, y=True, alpha=0.3)
        self.plt_drpm.showGrid(x=True, y=True, alpha=0.3)
        self.plt_ashk.showGrid(x=True, y=True, alpha=0.3)
        self.plt_lshk.showGrid(x=True, y=True, alpha=0.3)

        # add x_linkage
        self.plt_wob.setXLink(self.plt_rop)
        self.plt_srpm.setXLink(self.plt_rop)
        self.plt_drpm.setXLink(self.plt_rop)
        self.plt_ashk.setXLink(self.plt_rop)
        self.plt_lshk.setXLink(self.plt_rop)

        # add y-label
        self.plt_rop.setLabel("left", '<font size="5", face="Helvetica">ROP (ft/h)</font>')
        self.plt_wob.setLabel("left", '<font size="5", face="Helvetica">WOB (kfbf)</font>')
        self.plt_srpm.setLabel("left", '<font size="5", face="Helvetica">SRPM (rpm)</font>')
        self.plt_drpm.setLabel("left", '<font size="5", face="Helvetica">DRPM (rpm)</font>')
        self.plt_ashk.setLabel("left", '<font size="5", face="Helvetica">ASHK (G)</font>')
        self.plt_lshk.setLabel("left", '<font size="5", face="Helvetica">LSHK (G)</font>')
        self.plt_lshk.setLabel("bottom", '<font size="6", face="Helvetica">Time (s)</font>')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.my_app_id = "Shell AI Vibration"
        # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.my_app_id)
        self.gui_widget = GUIWidget()
        self.setCentralWidget(self.gui_widget)
        self.init_ui()
        self.ptr = 0

    def init_ui(self):
        self.setWindowTitle("Vibration Analysis")
        self.setWindowIcon(QIcon("Shell_Logo.png"))
        self.setMinimumSize(1200, 800)
        self.create_short_cut_actions()
        self.create_menu()
        self.center()
        self.load_data()
        self.plot_data()
        self.create_param_tree()

    def create_short_cut_actions(self):
        self.full_screen_act = QAction("Enter &Full Screen", self, shortcut="F11", triggered=self.full_screen)
        self.about_act = QAction("&About", self, shortcut="Ctrl+A", triggered=self.about)
        self.about_qt_act = QAction("About &Qt", self, triggered=QApplication.instance().aboutQt)
        self.save_screen_shot_act = QAction("Save &Screen Shot", self, shortcut="F10", triggered=self.save_screen_shot)

    def create_menu(self):
        # save: save_screen_shot, save_interpretation
        self.save_menu = self.menuBar().addMenu("&Save")
        self.save_menu.addAction(self.save_screen_shot_act)

        # full screen
        self.view_menu = self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.full_screen_act)

        # help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.about_act)
        self.help_menu.addAction(self.about_qt_act)

    # Holesize 6.125 inch, Stabilizer No; MWD OD: 4.75 inch; DC No 1; DogLeg Reamer: No
    def create_param_tree(self):
        self.params = Parameter.create(name="Control Panel", type="group", children=[
            {"name": "Well Name: ", "type": "str", "value": "MONROE STATE 1-4 WRD 2H", "tip": "well name"},
            {"name": "Bit Run:", "type": "str", "value": "5"},
            {"name": "Start", "type": "action", "tip": "Start Analysis", "value": "Stream"},
            {"name": "BHA Configuration", "type": "group", "children":[
                {"name": "Hole Size: ", "type": "str", "value": "6.125 (in)", 'readonly': True},
                {"name": "Stabilizer: ", "type": "str", "value": "No", 'readonly': True},
                {"name": "MWD OD: ", "type": "str", "value": "4.75 (in)", 'readonly': True},
                {"name": "DC No.: ", "type": "str", "value": "1", 'readonly': True},
                {"name": "Dogleg Reamer: ", "type": "str", "value": "No", 'readonly': True},
            ]},
            {"name": "ASHK", "type": "group", "children":[
                {"name": "Actual", "type": "color", "value": "FF0", "tip": "ASHK Actual", "readonly": False},
                {"name": "Prediction", "type": "color", "value": "FF0", "tip": "ASHK Prediction", "readonly": False},
            ]},
            {"name": "LSHK", "type": "group", "children": [
                {"name": "Actual", "type": "color", "value": "FF0", "tip": "LSHK Actual", "readonly": False},
                {"name": "Prediction", "type": "color", "value": "FF0", "tip": "LSHK Prediction", "readonly": False},
            ]},

        ])
        self.gui_widget.tree.setParameters(self.params, showTop=True)
        self.params.param("Start").sigActivated.connect(self.start_act)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def about(self):
        QMessageBox.about(self, "About Vibration Analysis",
                          "This is <b>Vibration Analysis</b> PyQt5 Program Version 1.0"
                          "<br> Author E-mail: jie.yang2@shell.com")

    def save_screen_shot(self):
        self.showFullScreen()
        self.screen_shot = QApplication.primaryScreen().grabWindow(0)
        img, _ = QFileDialog.getSaveFileName(self, "Save screen shot",
                                             filter="PNG(*.png);; JPEG(*.jpg)")
        if img[-3:] == "png":
            self.screen_shot.save(img, "png")
        elif img[-3:] == "jpg":
            self.screen_shot.save(img, "jpg")

    def full_screen(self):
        if self.isFullScreen():
            self.showNormal()
            self.full_screen_act.setText("Enter &Full Screen")
        else:
            self.showFullScreen()
            self.full_screen_act.setText("Exit &Full Screen")

    def load_data(self):
        self.well_name = "Example Well"
        # load time base data
        self.full_lwd_df = pd.read_csv("demo_data.csv")
        self.n, _ = self.full_lwd_df.shape
        self.full_lwd_df["Time"] = np.arange(0, self.n) * 10
        self.gui_widget.plt_rop.setXRange(0, 10 * self.n, padding=0)
        self.gui_widget.plt_rop.setYRange(0, self.full_lwd_df["ROP"].max() + 5, padding=0)
        self.gui_widget.plt_wob.setYRange(0, self.full_lwd_df["WOB"].max() + 5, padding=0)
        self.gui_widget.plt_srpm.setYRange(self.full_lwd_df["SRPM"].min() - 5, self.full_lwd_df["SRPM"].max() + 5, padding=0)
        self.gui_widget.plt_drpm.setYRange(self.full_lwd_df["DRPM"].min() - 5, self.full_lwd_df["DRPM"].max() + 5, padding=0)
        self.gui_widget.plt_ashk.setYRange(0, self.full_lwd_df["ASHK2"].max() + 5, padding=0)
        self.gui_widget.plt_lshk.setYRange(0, self.full_lwd_df["LSHK2"].max() + 5, padding=0)

    def plot_data(self):
        self.plt_rop_data  = self.gui_widget.plt_rop.plot(pxMode=True, pen=pg.mkPen(color=(0, 48, 143, 255), width=3))
        self.plt_wob_data  = self.gui_widget.plt_wob.plot(pxMode=True, pen=pg.mkPen(color=(59, 122, 87, 255), width=3))
        self.plt_srpm_data = self.gui_widget.plt_srpm.plot(pxMode=True, pen=pg.mkPen(color=(0, 0, 0, 255), width=3))
        self.plt_drpm_data = self.gui_widget.plt_drpm.plot(pxMode=True, pen=pg.mkPen(color=(138, 43, 226, 255), width=3))
        self.plt_ashk_data = self.gui_widget.plt_ashk.plot(pxMode=True, pen=pg.mkPen(color=(150, 113, 23, 255), width=3))
        self.plt_lshk_data = self.gui_widget.plt_lshk.plot(pxMode=True, pen=pg.mkPen(color=(30, 77, 43, 255), width=3))
        ashk_inf = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(255, 0, 0, 255), width=2, style=QtCore.Qt.DashDotLine),
                               label='ASHK2={value:0.3f}g', pos=11.1856,
                               labelOpts={'color': (200, 0, 0, 0), 'movable': True, 'fill': (0, 0, 200, 0), "position": 0.9})
        self.gui_widget.plt_ashk.addItem(ashk_inf)

        lshk_inf = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(255, 0, 0, 255), width=2, style=QtCore.Qt.DashDotLine),
                               label='LSHK2={value:0.3f}g', pos=5.19,
                               labelOpts={'color': (200, 0, 0, 0), 'movable': True, 'fill': (0, 0, 200, 0), "position": 0.9})
        self.gui_widget.plt_lshk.addItem(lshk_inf)
    def update_plt_data(self):
        # self.lwd_df = self.full_lwd_df[:self.n]
        # set_data
        self.plt_rop_data.setData(y=list(self.lwd_df["ROP"]), x=list(self.lwd_df["Time"]))
        self.plt_wob_data.setData(y=list(self.lwd_df["WOB"]), x=list(self.lwd_df["Time"]))
        self.plt_srpm_data.setData(y=list(self.lwd_df["SRPM"]), x=list(self.lwd_df["Time"]))
        self.plt_drpm_data.setData(y=list(self.lwd_df["DRPM"]), x=list(self.lwd_df["Time"]))
        self.plt_ashk_data.setData(y=list(self.lwd_df["ASHK2"]), x=list(self.lwd_df["Time"]))
        self.plt_lshk_data.setData(y=list(self.lwd_df["LSHK2"]), x=list(self.lwd_df["Time"]))


        if self.lwd_df["pred_ASHK2"].values[-1] == "Top":
            self.params.param("ASHK").param("Prediction").setValue("FF0000")
        else:
            self.params.param("ASHK").param("Prediction").setValue("008000")

        if self.lwd_df["ASHK2"].values[-1] > 11.1856:
            self.params.param("ASHK").param("Actual").setValue("FF0000")
        else:
            self.params.param("ASHK").param("Actual").setValue("008000")


        if self.lwd_df["pred_LSHK2"].values[-1] == "Top":
            self.params.param("LSHK").param("Prediction").setValue("FF0000")
        else:
            self.params.param("LSHK").param("Prediction").setValue("008000")

        if self.lwd_df["LSHK2"].values[-1] > 5.19:
            self.params.param("LSHK").param("Actual").setValue("FF0000")
        else:
            self.params.param("LSHK").param("Actual").setValue("008000")


    def update(self):
        self.ptr += 1
        self.lwd_df = self.full_lwd_df[:self.ptr]
        self.update_plt_data()
        if self.ptr > self.n:
            self.timer.stop()
            self.ptr = 0
            self.params.param("Start").show(True)

    def start_act(self):
        self.params.param("Start").show(False)
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(200)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.resize(1100, 800)
    sys.exit(app.exec_())