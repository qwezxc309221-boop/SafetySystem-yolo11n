import os


class Config:

    # ===== 获取项目根目录 =====
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # ===== 路径配置（全部相对）=====
    MODEL_PATH = os.path.join(BASE_DIR, "weights", "best.pt")
    IMAGE_DIR = os.path.join(BASE_DIR, "records")
    VIDEO_DIR = os.path.join(BASE_DIR, "video")
    FONT_PATH = os.path.join(BASE_DIR, "msyh.ttc")  # 可放项目内

    # ===== 算法参数 =====
    IOU_THRESHOLD = 0.6
    CONFIRM_FRAMES = 5
    MAX_DISAPPEAR_FRAMES = 5

    # ===== 过滤规则 =====
    FILTER = {
        "作业人员": [True, "人"],
        "安全帽": [True, ["安全帽", "未戴安全帽"]],
        "口罩": [True, ["口罩", "未戴口罩"]],
        "安全背心": [True, ["安全背心", "未穿戴安全背心"]],
        "车辆机械": [True, ["车辆", "机械", "雪糕筒"]]
    }

    VIOLATION_KEYWORDS = ["未", "no", "off"]

    @staticmethod
    def check_env():
        errors = []

        # ===== 模型检查 =====
        if not os.path.exists(Config.MODEL_PATH):
            errors.append(f"模型文件不存在: {Config.MODEL_PATH}")

        # ===== 自动创建目录 =====
        for d in [Config.IMAGE_DIR, Config.VIDEO_DIR]:
            try:
                if not os.path.exists(d):
                    os.makedirs(d, exist_ok=True)
            except Exception as e:
                errors.append(f"路径 {d} 无法访问: {str(e)}")

        # ===== 字体检查（可选）=====
        if not os.path.exists(Config.FONT_PATH):
            print("⚠ 未找到字体文件，将使用默认字体")

        return errors