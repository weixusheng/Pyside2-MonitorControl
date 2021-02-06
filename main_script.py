from PySide2.QtWidgets import QApplication, QSlider, QLCDNumber
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Signal, QObject
from threading import Thread
from monitorcontrol import get_monitors
import time

# 全局变量
last_time = 0
global_monitor = get_monitors()

class MySignals(QObject):
    main_signal = Signal(int,int)

class Stats:

    def __init__(self):
        self.ui = QUiLoader().load('main_ui.ui')
        with global_monitor[0]:
            s_contrast = global_monitor[0].get_contrast()
            s_luminance = global_monitor[0].get_luminance()

        # 初始化划轴位置
        self.ui.horizontalSlider.setValue(s_luminance)
        self.ui.horizontalSlider_2.setValue(s_contrast)

        # 初始化显示
        self.ui.lcdNumber.display(s_luminance)
        self.ui.lcdNumber_2.display(s_contrast)

        # 建立信号量
        self.global_ms = MySignals()

        # 绑定事件
        self.ui.horizontalSlider.valueChanged.connect(lambda: self.update_shit(1))
        self.ui.horizontalSlider_2.valueChanged.connect(lambda: self.update_shit(2))
        self.global_ms.main_signal.connect(self.main_thread)

    def main_thread(self, index, value):
        global last_time
        now_time = time.time()
        global global_monitor
        if now_time-last_time>0.1:
            if index == 0:
                self.ui.lcdNumber.display(value)
                with global_monitor[0]:
                    global_monitor[0].set_luminance(value)
                last_time = now_time
            else:
                self.ui.lcdNumber_2.display(value)
                with global_monitor[0]:
                    global_monitor[0].set_contrast(value)
                last_time = now_time
        else:
            pass

    def update_shit(self,shit):
        def threadFunc():
            if shit == 1:
                new_data = self.ui.horizontalSlider.value()
                self.global_ms.main_signal.emit(0,new_data)
            else:
                new_data = self.ui.horizontalSlider_2.value()
                self.global_ms.main_signal.emit(1, new_data)
        thread = Thread(target=threadFunc)
        thread.start()

app = QApplication([])
stats = Stats()
stats.ui.show()
app.exec_()