# SafetySystem-yolo11n

> 基于 **PyQt6 + YOLO（Ultralytics）** 的工地安全实时监控系统：摄像头实时检测人员安全帽 / 口罩 / 安全背心穿戴情况，自动识别违规、抓拍存档、一键录像。

## ✨ 功能特性

- **实时目标检测**：人、安全帽、口罩、安全背心、车辆、机械、雪糕筒
- **违规自动判定**：未戴安全帽 / 未戴口罩 / 未穿安全背心 → 红框标注 + 自动抓拍 + 日志记录
- **目标跟踪平滑**：基于 IoU 的跟踪 + 连续多帧确认，抑制闪烁误报、消除重影
- **实时统计面板**：画面右侧显示各类目标数量与违规日志（最新在顶）
- **一键录像**：MP4 格式保存至 `video/` 目录
- **中文标注渲染**：PIL + 微软雅黑，字体缺失时自动回退默认字体
- **GPU 自动加速**：检测到 CUDA 自动使用 GPU，否则回退 CPU
- **多线程流水线**：采集 / 推理 / 保存 / 录像分离，UI 不卡顿


## 🚀 快速开始

### 环境要求

- Python **3.10+**
- 摄像头（USB 或内置）
- 可选：NVIDIA GPU + CUDA（强烈建议，CPU 下 FPS 较低）

### 1. 安装依赖

```bash
git clone https://github.com/qwezxc309221-boop/SafetySystem-yolo11n.git
cd SafetySystem-yolo11n
pip install -r requirements.txt
```

> GPU 用户建议按 [PyTorch 官网](https://pytorch.org/get-started/locally/) 指引安装对应 CUDA 版本的 torch，再执行上面的命令。

### 2. 准备模型

仓库已内置训练好的权重 `weights/best.pt`，开箱即用。

如需替换为自己的模型：将 `.pt` 文件放入 `weights/`，并修改 `config.py` 中的 `MODEL_PATH`。**注意**：模型类别名需与下文「配置说明」中的 `FILTER` 规则对应，否则无法匹配。

### 3. 运行

```bash
python main.py
```

启动后自动打开默认摄像头（索引 `0`）。若提示"无法打开摄像头"，修改 `model.py` 中 `cv2.VideoCapture(0)` 的索引为 `1`、`2` 逐个尝试。

## ⚙️ 配置说明（`config.py`）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `MODEL_PATH` | `weights/best.pt` | YOLO 模型权重路径 |
| `IOU_THRESHOLD` | `0.6` | 目标匹配 IoU 阈值，越大越难判定为同一目标 |
| `CONFIRM_FRAMES` | `5` | 连续命中多少帧才确认并报警（防误报） |
| `MAX_DISAPPEAR_FRAMES` | `5` | 目标消失多少帧后从内存清除 |
| `FILTER` | 见源码 | 各检测类别的启用开关与类别名映射 |
| `VIOLATION_KEYWORDS` | `["未", "no", "off"]` | 类别名包含这些关键词判定为违规 |
| `IMAGE_DIR` / `VIDEO_DIR` | `records/` / `video/` | 抓拍截图 / 录像输出目录（自动创建） |
| `FONT_PATH` | `msyh.ttc` | 中文字体，缺失时回退默认字体 |

## 📁 项目结构

```
SafetySystem-yolo11n/
├── main.py            # 程序入口（环境预检 + 启动）
├── config.py          # 全部路径与算法参数配置
├── model.py           # WorkerThread：采集/推理/显示/保存/录像 五线程流水线
├── tracker.py         # ObjectSmoother：IoU 目标跟踪与报警确认
├── ui.py              # PyQt6 主窗口界面
├── utils.py           # OpenCV ↔ PIL 转换与中文文字绘制
├── weights/
│   └── best.pt        # YOLO 模型权重
├── records/           # 违规抓拍截图（运行时自动生成）
└── video/             # 录像输出（运行时自动生成）
```

## ❓ 常见问题

**Q：启动时提示"未找到字体文件，将使用默认字体"？**
正常现象，不影响运行，中文标注会使用系统默认字体。想要更好的显示效果，可将自有的 `msyh.ttc`（微软雅黑）放到项目根目录——注意该字体为商业字体，请确保你有合法使用权，不要随仓库分发。

**Q：启动报错"模型文件不存在"？**
检查 `weights/best.pt` 是否完好，或修改 `config.py` 的 `MODEL_PATH`。

**Q：FPS 很低 / 画面卡顿？**
- 确认是否在用 GPU 运行（有 NVIDIA 显卡需安装 CUDA 版 torch）
- 当前模型 `yolo11n` 已是最轻量档，如需更高精度可换 `yolo11s/m`，速度会下降
- 可适当降低 `model.py` 中推理的 `conf` 阈值或缩小摄像头分辨率

**Q：检测出来的类别和界面上对不上？**
界面显示的类别来自模型权重本身的类别表，需保证模型训练时的类别名与 `config.py` 的 `FILTER` 规则一致（如 `安全帽`、`未戴安全帽`、`口罩`、`未戴口罩` 等）。

**Q：违规截图和录像存在哪？**
分别存在项目下的 `records/` 和 `video/` 目录，按"类别名_时间戳.jpg"和"REC_时间戳.mp4"命名，首次运行自动创建。


