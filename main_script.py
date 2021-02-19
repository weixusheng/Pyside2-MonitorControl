from PySide2.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Signal, QObject, Qt
from PySide2.QtGui import QIcon
from threading import Thread
from monitorcontrol import get_monitors
import screen_brightness_control as sbc
import time


# 全局变量
last_time = 0
global_monitor = get_monitors()
monitor_all = sbc.get_brightness()
# 当前模式
mode = 0
'''
0: 只有笔记本显示器
1: 只有外接显示器
2: 有外接显示器
'''


class MySignals(QObject):
    main_signal = Signal(int, int)


class Stats:

    def __init__(self):
        # 引入ui文件
        self.ui = QUiLoader().load('main_ui.ui')
        print(monitor_all)
        is_int = isinstance(monitor_all, int)
        global mode
        global global_monitor
        if is_int != True:
            mode = 2
            self.ui.label_4.setText("当前状态:[双显示屏]")
            self.ui.groupBox.setEnabled(True)
            # 更新外接亮度
            s_luminance = 50
            if monitor_all[1] == None:
                mode = 1
                self.set_mprimary()
            else:
                s_luminance = monitor_all[1]
                self.ui.horizontalSlider.setValue(s_luminance)
                self.ui.lcdNumber.display(s_luminance)
                # 更新笔记本亮度
                self.ui.horizontalSlider_3.setValue(monitor_all[0])
                self.ui.lcdNumber_3.display(monitor_all[0])
                # 探测更新显示器对比度(暂时先不更新)
                self.ui.horizontalSlider_2.setValue(50)
                '''
                with global_monitor[1]:
                    s_contrast = global_monitor[1].get_contrast()
                self.ui.horizontalSlider_2.setValue(s_contrast)
                self.ui.lcdNumber_2.display(s_contrast)
                '''
        else:  # 只有笔记本
            mode = 0
            self.ui.horizontalSlider_3.setValue(monitor_all)
            self.ui.lcdNumber_3.display(monitor_all)

        # 建立信号量实例(子线程改变主界面,防止画面阻塞)
        self.global_ms = MySignals()
        # 绑定事件
        self.ui.pushButton.clicked.connect(self.minimize_totray)
        self.ui.pushButton_2.clicked.connect(self.set_mprimary)
        # 外接亮度
        self.ui.horizontalSlider.valueChanged.connect(lambda: self.update_shit(1))
        # 外接对比度
        self.ui.horizontalSlider_2.valueChanged.connect(lambda: self.update_shit(2))
        # 笔记本亮度
        self.ui.horizontalSlider_3.valueChanged.connect(lambda: self.update_shit(3))
        self.global_ms.main_signal.connect(self.main_thread)

    def main_thread(self, index, value):
        global last_time
        now_time = time.time()
        global global_monitor
        if now_time-last_time > 0.1:
            if index == 0:  # luminance
                if mode == 1:  # 只有外显
                    with global_monitor[0]:
                        global_monitor[0].set_luminance(value)
                else:
                    with global_monitor[1]:
                        global_monitor[1].set_luminance(value)
                self.ui.lcdNumber.display(value)
                last_time = now_time
            elif index == 1:   # contrast
                if mode == 1:
                    with global_monitor[0]:
                        global_monitor[0].set_contrast(value)
                else:
                    with global_monitor[1]:
                        global_monitor[1].set_contrast(value)
                self.ui.lcdNumber_2.display(value)
                last_time = now_time
            else:  # index = 2 (控制笔记本)
                self.ui.lcdNumber_3.display(value)
                sbc.set_brightness(value, display=0)
                last_time = now_time
        else:
            pass

    def update_shit(self, shit):
        def threadFunc():
            if shit == 1:
                new_data = self.ui.horizontalSlider.value()
                self.global_ms.main_signal.emit(0, new_data)
            elif shit == 2:
                new_data = self.ui.horizontalSlider_2.value()
                self.global_ms.main_signal.emit(1, new_data)
            else:
                new_data = self.ui.horizontalSlider_3.value()
                self.global_ms.main_signal.emit(2, new_data)
        thread = Thread(target=threadFunc)
        thread.start()

    def set_mprimary(self):
        global mode
        mode = 1
        self.ui.label_4.setText("当前状态:[Monitor Only]")
        self.ui.groupBox.setEnabled(True)
        # 数值归位
        self.ui.horizontalSlider_3.setValue(0)
        self.ui.lcdNumber_3.display(0)
        self.ui.groupBox_2.setEnabled(False)  # 笔显状态
        with global_monitor[0]:
            s_luminance = global_monitor[0].get_luminance()
            s_contrast = global_monitor[0].get_contrast()
        self.ui.horizontalSlider.setValue(s_luminance)
        self.ui.lcdNumber.display(s_luminance)
        self.ui.horizontalSlider_2.setValue(s_contrast)
        self.ui.lcdNumber_2.display(s_contrast)

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
        #self.menu2 = QMenu()
        self.showAction2 = QAction("夜晚模式-显示器", self, triggered=lambda:self.adjust_tray(0,1))
        self.showAction3 = QAction("白天模式-显示器", self, triggered=lambda:self.adjust_tray(1,1))
        self.showAction4 = QAction("夜晚模式-双显示器", self, triggered=lambda: self.adjust_tray(0,2))
        self.showAction5 = QAction("白天模式-双显示器", self, triggered=lambda:self.adjust_tray(1,2))
        self.showAction6 = QAction("夜晚模式-笔记本", self, triggered=lambda: self.adjust_tray(0, 3))
        self.showAction7 = QAction("白天模式-笔记本", self, triggered=lambda: self.adjust_tray(1, 3))
        self.quitAction = QAction("退出", self, triggered=self.quitapp)
        # 托盘增加选项
        self.menu1 = self.menu.addMenu("笔记本")
        self.menu1.addAction(self.showAction6)
        self.menu1.addAction(self.showAction7)
        self.menu2 = self.menu.addMenu("显示器")
        self.menu2.addAction(self.showAction2)
        self.menu2.addAction(self.showAction3)
        self.menu3 = self.menu.addMenu("双显示器")
        self.menu3.addAction(self.showAction4)
        self.menu3.addAction(self.showAction5)
        self.menu.addAction(self.quitAction)
        self.setContextMenu(self.menu)
        # 设置图标
        self.setIcon(QIcon("star.png"))
        self.icon = self.MessageIcon()
        # 把鼠标点击图标的信号和槽连接
        self.activated.connect(self.onIconClicked)
    def adjust_tray(self, index, mode):
        global global_monitor
        if index == 0:
            str = "已开启夜晚模式"
            sc = 50
            sl = 35
            pl = 40
        else:
            str = "已开启白天模式"
            sc = 80
            sl = 75
            pl = 60
        if mode == 2 or mode == 3:  # 双显示器/笔记本
            sbc.set_brightness(pl, display=0)
            self.ui.horizontalSlider_3.setValue(pl)
        if mode == 1 or mode == 2:
            shit = mode-1
            with global_monitor[shit]:
                global_monitor[shit].set_luminance(sl)
                global_monitor[shit].set_contrast(sc)
            self.ui.horizontalSlider.setValue(sl)
            self.ui.horizontalSlider_2.setValue(sc)
            self.ui.lcdNumber.display(sl)
            self.ui.lcdNumber_2.display(sc)
        self.showMessage("Message", str, self.icon)

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

