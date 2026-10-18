from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QGroupBox, QCheckBox, QMessageBox, QSizePolicy)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

from config import Config


class MainWindow(QMainWindow):

    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle("安全监控系统专业版 v5.1")
        self.resize(1300, 800)
        self.setStyleSheet("background-color: #1a1c23; color: white; font-family: 'Microsoft YaHei';")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        self.video_label = QLabel("正在初始化摄像头...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #333; border-radius: 5px;")
        self.video_label.setFixedSize(960, 720)
        self.video_label.setScaledContents(False)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.video_label, stretch=7)

        panel = QVBoxLayout()

        ctrl_group = QGroupBox("系统控制")
        ctrl_layout = QVBoxLayout()

        self.btn_run = QPushButton("停止监控")
        self.btn_run.setFixedHeight(45)
        self.btn_run.setStyleSheet("background-color: #d32f2f; font-weight: bold; border-radius: 5px;")

        self.btn_rec = QPushButton("开始录像")
        self.btn_rec.setFixedHeight(45)
        self.btn_rec.setStyleSheet("background-color: #37474f; border-radius: 5px;")

        ctrl_layout.addWidget(self.btn_run)
        ctrl_layout.addWidget(self.btn_rec)
        ctrl_group.setLayout(ctrl_layout)
        panel.addWidget(ctrl_group)

        filter_group = QGroupBox("目标筛选")
        filter_layout = QVBoxLayout()
        for key in Config.FILTER.keys():
            cb = QCheckBox(key)
            cb.setChecked(True)
            cb.toggled.connect(lambda state, k=key: self.update_filter(k, state))
            filter_layout.addWidget(cb)
        filter_group.setLayout(filter_layout)
        panel.addWidget(filter_group)

        self.stats_label = QLabel("实时统计: 等待数据...")
        self.stats_label.setStyleSheet("color: #4caf50; font-size: 15px; padding: 10px; background: #262a33;")
        panel.addWidget(self.stats_label)

        self.log_list = QListWidget()
        self.log_list.setStyleSheet("background-color: #262a33; border: none; color: #ff8a80; font-size: 12px;")
        panel.addWidget(QLabel("违规日志 (最新在顶):"))
        panel.addWidget(self.log_list)

        btn_exit = QPushButton("退出系统")
        btn_exit.setFixedHeight(40)
        btn_exit.setStyleSheet("background-color: #455a64; margin-top: 10px;")
        btn_exit.clicked.connect(self.close)
        panel.addWidget(btn_exit)

        layout.addLayout(panel, stretch=3)

    def connect_signals(self):
        self.btn_run.clicked.connect(self.toggle_monitoring)
        self.btn_rec.clicked.connect(self.toggle_recording)
        self.worker.image_update.connect(self.update_video_frame)
        self.worker.stats_update.connect(self.update_stats_ui)
        self.worker.log_update.connect(lambda m: self.log_list.insertItem(0, m))
        self.worker.error_signal.connect(self.handle_fatal_error)

    def update_filter(self, key, state):
        Config.FILTER[key][0] = state

    def toggle_monitoring(self):
        self.worker.running = not self.worker.running
        self.btn_run.setText("停止监控" if self.worker.running else "开始监控")
        self.btn_run.setStyleSheet(
            f"background-color: {'#d32f2f' if self.worker.running else '#388e3c'}; font-weight: bold;")

    def toggle_recording(self):
        self.worker.is_recording = not self.worker.is_recording
        self.btn_rec.setText("停止录像" if self.worker.is_recording else "开始录像")
        self.btn_rec.setStyleSheet(f"background-color: {'#e53935' if self.worker.is_recording else '#37474f'};")

    def update_stats_ui(self, inventory):
        lines = [f"● {k}: {v}" for k, v in inventory.items() if v > 0]
        self.stats_label.setText("实时统计:\n" + "\n".join(lines) if lines else "实时统计: 区域内无目标")

    def update_video_frame(self, frame):
        h, w, ch = frame.shape
        qt_img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(qt_img)

        scaled_pixmap = pixmap.scaled(
            960, 720,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.video_label.setPixmap(scaled_pixmap)

    def handle_fatal_error(self, err_msg):
        QMessageBox.critical(self, "系统错误", err_msg)
        self.btn_run.setEnabled(False)

    def closeEvent(self, event):
        self.worker.keep_alive = False
        self.worker.wait()
        event.accept()