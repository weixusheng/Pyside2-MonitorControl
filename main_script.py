from PySide2.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Signal, QObject, Qt
from PySide2.QtGui import QIcon
from threading import Thread
from monitorcontrol import get_monitors
import time


# 全局变量
last_time = 0
global_monitor = get_monitors()


class MySignals(QObject):
    main_signal = Signal(int, int)


class Stats():

    def __init__(self):
        # 引入ui文件
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
        # 建立信号量实例(子线程改变主界面,防止画面阻塞)
        self.global_ms = MySignals()
        # 绑定事件
        self.ui.pushButton.clicked.connect(self.minimize_totray)
        self.ui.horizontalSlider.valueChanged.connect(lambda: self.update_shit(1))
        self.ui.horizontalSlider_2.valueChanged.connect(lambda: self.update_shit(2))
        self.global_ms.main_signal.connect(self.main_thread)

    def main_thread(self, index, value):
        global last_time
        now_time = time.time()
        global global_monitor
        if now_time-last_time > 0.1:
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

    def update_shit(self, shit):
        def threadFunc():
            if shit == 1:
                new_data = self.ui.horizontalSlider.value()
                self.global_ms.main_signal.emit(0, new_data)
            else:
                new_data = self.ui.horizontalSlider_2.value()
                self.global_ms.main_signal.emit(1, new_data)
        thread = Thread(target=threadFunc)
        thread.start()

    def minimize_totray(self):
        self.ui.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.ui.showMinimized()


# 托盘类
class TrayIcon(QSystemTrayIcon):
    def __init__(self, MainWindow, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.ui = MainWindow
        self.createMenu()

    def createMenu(self):
        self.menu = QMenu()
        self.showAction1 = QAction("打开", self, triggered=self.show_window)
        self.showAction2 = QAction("夜晚模式", self, triggered=self.open_night)
        self.showAction3 = QAction("白天模式", self, triggered=self.open_light)
        self.quitAction = QAction("退出", self, triggered=self.quitapp)
        # 托盘增加选项
        self.menu.addAction(self.showAction1)
        self.menu.addAction(self.showAction2)
        self.menu.addAction(self.showAction3)
        self.menu.addAction(self.quitAction)
        self.setContextMenu(self.menu)
        # 设置图标
        self.setIcon(QIcon("star.png"))
        self.icon = self.MessageIcon()
        # 把鼠标点击图标的信号和槽连接
        self.activated.connect(self.onIconClicked)

    def open_night(self):
        # 系统提示弹窗
        self.showMessage("Message", "已开启夜晚模式", self.icon)
        # 实现过程
        global global_monitor
        with global_monitor[0]:
            global_monitor[0].set_contrast(50)
            global_monitor[0].set_luminance(35)
        self.ui.horizontalSlider.setValue(35)
        self.ui.horizontalSlider_2.setValue(50)
        self.ui.lcdNumber.display(35)
        self.ui.lcdNumber_2.display(50)

    def open_light(self):
        self.showMessage("Message", "已开启白天模式", self.icon)
        global global_monitor
        with global_monitor[0]:
            global_monitor[0].set_contrast(80)
            global_monitor[0].set_luminance(75)
        self.ui.horizontalSlider.setValue(75)
        self.ui.horizontalSlider_2.setValue(80)
        self.ui.lcdNumber.display(75)
        self.ui.lcdNumber_2.display(80)

    def show_window(self):
        # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
        self.ui.showNormal()
        self.ui.activateWindow()
        self.ui.setWindowFlags(Qt.Window)
        self.ui.show()

    def quitapp(self):
        QApplication.quit()

    # 点击托盘图标事件
    '''
    鼠标点击icon传递的信号会带有一个整形的值
    1是表示单击右键
    2是双击
    3是单击左键
    4是用鼠标中键点击
    '''
    def onIconClicked(self, reason):
        if reason == 2 or reason == 3:
            # self.showMessage("Message", "skr at here", self.icon)
            if self.ui.isMinimized() or not self.ui.isVisible():
                # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
                self.ui.showNormal()
                self.ui.activateWindow()
                self.ui.setWindowFlags(Qt.Window)
                self.ui.show()
            else:
                # 若不是最小化，则最小化
                self.ui.showMinimized()
                self.ui.setWindowFlags(Qt.SplashScreen)
                self.ui.show()


'''
if __name__ == "__main__":  # 用于当前窗体测试
    app = QApplication([])
    app.setWindowIcon(QIcon('star.png'))
    #实例化主程序
    stats = Stats()
    stats.ui.show()
    # 实例化托盘程序
    ti = TrayIcon(stats.ui)
    ti.show()
    app.exec_()
'''
