from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

from main_script import Stats, TrayIcon

app = QApplication([])
app.setWindowIcon(QIcon('star.png'))
# 实例化主程序
stats = Stats()
stats.ui.show()
# 实例化托盘程序
ti = TrayIcon(stats.ui)
ti.show()
app.exec_()