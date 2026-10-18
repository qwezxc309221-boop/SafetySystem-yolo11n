from config import Config


class TrackedObject:
    def __init__(self, bbox, name):
        self.bbox = bbox
        self.name = name
        self.hit_count = 1
        self.frames_since_seen = 0
        self.alerted = False


class ObjectSmoother:
    def __init__(self):
        self.objects = []

    def get_iou(self, boxA, boxB):
        xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
        xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(areaA + areaB - interArea + 1e-5)

    def update(self, detections):
        """
        核心逻辑：
        1. 匹配当前帧检测到的目标。
        2. 仅返回当前帧活跃的目标用于绘图（解决重影）。
        3. 内存保留消失的目标用于追踪连续性。
        """
        current_frame_matched_objects = []

        # --- 1. 目标匹配与更新 ---
        for det_box, det_name in detections:
            best_iou, best_obj = 0, None
            for obj in self.objects:
                iou = self.get_iou(det_box, obj.bbox)
                if iou > Config.IOU_THRESHOLD and iou > best_iou:
                    best_iou, best_obj = iou, obj

            if best_obj:
                # 匹配成功：更新坐标，计数加1，消失帧数重置为0
                best_obj.bbox = det_box
                best_obj.hit_count += 1
                best_obj.frames_since_seen = 0
                current_frame_matched_objects.append(best_obj)
            else:
                # 新目标：创建并加入内存
                new_obj = TrackedObject(det_box, det_name)
                self.objects.append(new_obj)
                current_frame_matched_objects.append(new_obj)

        # --- 2. 状态维护与结果筛选 ---
        results = []
        for obj in self.objects:
            # 如果内存中的对象在当前帧没被匹配到
            if obj not in current_frame_matched_objects:
                obj.frames_since_seen += 1

            # 报警逻辑：达到确认帧数且包含违规关键词
            should_alert = False
            if obj.hit_count >= Config.CONFIRM_FRAMES and not obj.alerted:
                if any(k in obj.name for k in Config.VIOLATION_KEYWORDS):
                    should_alert = True
                    obj.alerted = True

            # --- 关键修改点：解决重影 ---
            # 只有 frames_since_seen == 0 (即当前帧能看见的目标) 才返回给 UI 绘制
            if obj.frames_since_seen == 0:
                results.append((obj.bbox, obj.name, should_alert))

        # --- 3. 清理内存中消失过久的目标 ---
        self.objects = [o for o in self.objects if o.frames_since_seen <= Config.MAX_DISAPPEAR_FRAMES]

        return results