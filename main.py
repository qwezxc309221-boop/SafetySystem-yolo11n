import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui import MainWindow
from model import WorkerThread
from config import Config

def main():
    # 1. 环境预检
    errors = Config.check_env()
    if errors:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "启动失败", "\n".join(errors))
        return

    # 2. 启动逻辑
    app = QApplication(sys.argv)
    worker = WorkerThread()
    window = MainWindow(worker)
    
    worker.start()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()