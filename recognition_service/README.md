# 识别 HTTP 服务

本目录包含**管线仪屏幕识别**的全部逻辑，需在 conda 环境 `ocr` 中运行。  
目录带有 `COLCON_IGNORE`，**不会**被上级 colcon 工作区（[screen_ocr_ros2](../README.md)）编译。

基于 OpenCV 的固定 ROI + 七段 LCD 模板匹配，从实拍截图中解析仪表读数。

## 适用设备（占位）

标定配置仅适用于以下型号，部署到其他设备前请重新标定 `config/`（详见 `config/DEVICE.md`）：

| 项目 | 说明 |
|------|------|
| 设备名称 | `<DEVICE_NAME>` |
| 设备型号 | `<MODEL_NAME>` |
| 生产厂商 | `<MANUFACTURER>` |
| 屏幕规格 | `<SCREEN_WIDTH>` × `<SCREEN_HEIGHT>` |
| 固件版本 | `<FIRMWARE_VERSION>` |
| 备注 | `<NOTES>` |

## 识别字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `signal_strength` | 信号强度 | `0.0%` |
| `pipeline_current` | 管线电流 | `350 mA` |
| `burial_depth` | 埋设深度 | `140 m` |
| `compass_angle` | 罗盘角度 | `61°` |
| `arrow_direction` | 箭头方向 | `none` / `left` / `right` / `both` |

识别流程：

- **数字字段**：七段 LCD 模板匹配（针对该型号屏幕标定）
- **罗盘指针**：OpenCV 边缘检测 + 霍夫直线
- **箭头图标**：OpenCV 轮廓检测

## 目录结构

```
recognition_service/
├── src/
│   └── screen_ocr/         # 识别核心库
├── scripts/
│   ├── recognize.py        # CLI：读图输出 JSON
│   └── api_server.py       # HTTP API 服务
├── config/
│   ├── rois.json           # 各字段 ROI
│   ├── compass.json        # 罗盘圆心与半径
│   ├── digit_slots.json    # 七段数码管切片比例
│   └── DEVICE.md           # 设备型号说明
├── assets/
│   └── digit_templates/    # 数字匹配模板
├── examples/
│   └── images/             # 示例截图（image0000001.png ~ image0000047.png）
├── output/                 # 调试输出（--debug 时生成，gitignore）
├── environment.yml         # conda 环境定义
├── requirements.txt        # Python 依赖
├── start_api_server.sh     # 启动脚本
└── setup.py                # 可选 pip 安装
```

## 环境安装

### conda（推荐）

在本目录下执行：

```bash
conda env create -f environment.yml   # 环境名: ocr
conda activate ocr
```

### pip

```bash
conda create -n ocr python=3.10 -y
conda activate ocr
pip install -r requirements.txt
```

可选安装识别库：

```bash
pip install -e .
```

## 使用

### 命令行识别

```bash
conda activate ocr
cd recognition_service

python scripts/recognize.py
python scripts/recognize.py examples/images/image0000001.png
python scripts/recognize.py examples/images/image0000001.png --debug
```

`--debug` 会将中间步骤图片写入 `output/`。

### 启动 HTTP 服务

```bash
conda activate ocr
cd recognition_service
./start_api_server.sh
# 或: python scripts/api_server.py
```

环境变量（可选）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `SCREEN_OCR_API_HOST` | `127.0.0.1` | 监听地址 |
| `SCREEN_OCR_API_PORT` | `8000` | 监听端口 |

### HTTP API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/v1/config` | 读取标定配置 |
| PUT | `/v1/config` | 更新标定配置 |
| POST | `/v1/recognize` | 上传图片识别（`image` 文件 + 可选 `debug`、`frame_id`） |

示例：

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/v1/recognize \
  -F "image=@examples/images/image0000001.png"
```

## 配置与换型

| 文件 | 说明 |
|------|------|
| `config/rois.json` | 屏幕各字段区域 `[x1, y1, x2, y2]` |
| `config/compass.json` | 罗盘圆心与半径 |
| `config/digit_slots.json` | 七段数码管切片比例 |
| `assets/digit_templates/` | 数字匹配模板 |

`assets/digit_templates/` 中，信号强度模板命名为 `0_i.png`、`1_i.png` 这类形式；电流与深度模板命名为 `0.png`、`1.png` 这类形式；小数点模板命名为 `dot.png`。

更换管线仪型号时：

1. 更新 `config/DEVICE.md` 与上方「适用设备」信息
2. 重新标定 `config/` 下 JSON 配置文件
3. 重新制作并替换 `assets/digit_templates/` 下的数字模板
4. 重启 HTTP 服务

## 输出示例

```json
{
  "signal_strength": "0.0%",
  "pipeline_current": "350 mA",
  "burial_depth": "140 m",
  "arrow_direction": "none",
  "compass_angle": "61°",
  "compass_angle_deg": 61.0
}
```

## 核心依赖

| 包 | 版本 |
|----|------|
| Python | 3.10 |
| opencv-python | 4.6.0.66 |
| numpy | 1.23.5 |
| fastapi | 0.115.6 |
| uvicorn | 0.32.1 |

完整列表见 `requirements.txt`。

## License

MIT
