import cv2
import torch
import time
import queue
import threading
import os
import numpy as np
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from ultralytics import YOLO
from config import Config
from tracker import ObjectSmoother
from utils import draw_chinese_text


class WorkerThread(QThread):
    image_update = pyqtSignal(object)
    stats_update = pyqtSignal(dict)
    log_update = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.running = True
        self.keep_alive = True
        self.is_recording = False

        self.smoother = ObjectSmoother()

        # ===== 三线程队列 =====
        self.capture_queue = queue.Queue(maxsize=2)
        self.process_queue = queue.Queue(maxsize=2)

        # ===== IO队列 =====
        self.save_queue = queue.Queue(maxsize=30)
        self.video_queue = queue.Queue(maxsize=2)

        # ===== GPU设置（关闭FP16）=====
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        self.use_fp16 = False   # ✅ 关键：彻底关闭

        # ===== 启动线程 =====
        threading.Thread(target=self._capture_worker, daemon=True).start()
        threading.Thread(target=self._process_worker, daemon=True).start()
        threading.Thread(target=self._save_worker, daemon=True).start()
        threading.Thread(target=self._video_worker, daemon=True).start()

    # ===================== 采集线程 =====================
    def _capture_worker(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.error_signal.emit("无法打开摄像头")
            return

        while self.keep_alive:
            ret, frame = cap.read()
            if not ret:
                continue

            try:
                if self.capture_queue.full():
                    self.capture_queue.get_nowait()
                self.capture_queue.put_nowait(frame)
            except:
                pass

        cap.release()

    # ===================== 推理线程 =====================
    def _process_worker(self):
        try:
            model = YOLO(Config.MODEL_PATH)
            model.to(self.device)

            # ✅ 强制 float32（避免 half 冲突）
            model.model.float()

        except Exception as e:
            self.error_signal.emit(f"模型加载失败: {e}")
            return

        while self.keep_alive:
            try:
                frame = self.capture_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.005)
                continue

            display_frame = frame.copy()
            inventory = {k: 0 for k in ["人", "安全帽", "口罩", "安全背心", "车辆", "机械", "雪糕筒"]}

            if self.running:
                t0 = time.time()

                # ✅ 关键：关闭 half
                results = model.predict(
                    frame,
                    conf=0.5,
                    verbose=False,
                    half=False
                )[0]

                raw_dets = []

                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    name = model.names[cls_id]

                    for on, rule in Config.FILTER.values():
                        if on and (name == rule or (isinstance(rule, list) and name in rule)):
                            raw_dets.append((box.xyxy[0].cpu().numpy(), name))

                for bbox, name, alert in self.smoother.update(raw_dets):
                    x1, y1, x2, y2 = map(int, bbox)
                    is_vio = any(k in name for k in Config.VIOLATION_KEYWORDS)

                    for k in inventory:
                        if k in name:
                            inventory[k] += 1

                    color = (0, 0, 255) if is_vio else (0, 255, 0)
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)

                    display_frame = draw_chinese_text(
                        display_frame, name, (x1, y1 - 30), color[::-1], 22
                    )

                    if alert:
                        if not self.save_queue.full():
                            self.save_queue.put((frame.copy(), name))
                        self.log_update.emit(f"{datetime.now().strftime('%H:%M:%S')} 检出: {name}")

                # ===== FPS =====
                fps = 1.0 / (time.time() - t0 + 1e-5)
                display_frame = draw_chinese_text(
                    display_frame, f"FPS:{fps:.1f}", (10, 10), (0, 255, 0), 20
                )

            # ===== 时间 =====
            h, w = display_frame.shape[:2]
            time_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            overlay = display_frame.copy()
            cv2.rectangle(overlay, (w - 320, 10), (w - 10, 55), (0, 0, 0), -1)
            display_frame = cv2.addWeighted(overlay, 0.4, display_frame, 0.6, 0)

            display_frame = draw_chinese_text(
                display_frame, time_text, (w - 310, 18), (255, 255, 255), 22
            )

            try:
                if self.process_queue.full():
                    self.process_queue.get_nowait()
                self.process_queue.put_nowait((display_frame, inventory))
            except:
                pass

    # ===================== 显示线程 =====================
    def run(self):
        while self.keep_alive:
            try:
                frame, inventory = self.process_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.005)
                continue

            if self.is_recording:
                try:
                    if self.video_queue.full():
                        self.video_queue.get_nowait()
                    self.video_queue.put_nowait(frame.copy())
                except:
                    pass

            self.stats_update.emit(inventory)
            self.image_update.emit(frame)

            time.sleep(0.01)

    # ===================== 保存线程 =====================
    def _save_worker(self):
        while self.keep_alive:
            try:
                frame, name = self.save_queue.get(timeout=1)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = os.path.join(Config.IMAGE_DIR, f"{name}_{ts}.jpg")

                ok, buf = cv2.imencode(".jpg", frame)
                if ok:
                    with open(path, "wb") as f:
                        f.write(buf)

                self.save_queue.task_done()
            except:
                continue

    # ===================== 视频线程 =====================
    def _video_worker(self):
        writer = None

        while self.keep_alive:
            try:
                if self.is_recording:
                    frame = self.video_queue.get_nowait()

                    if writer is None:
                        h, w = frame.shape[:2]
                        path = os.path.join(Config.VIDEO_DIR, f"REC_{int(time.time())}.mp4")
                        writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), 20, (w, h))

                    writer.write(frame)
                else:
                    if writer:
                        writer.release()
                        writer = None
                    time.sleep(0.1)

            except queue.Empty:
                time.sleep(0.005)
            except Exception as e:
                print("录像错误:", e)