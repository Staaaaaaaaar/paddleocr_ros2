# 识别 HTTP 服务

本目录包含**管线仪屏幕识别**的全部重依赖逻辑，需在 conda 环境 `ocr` 中运行。  
该目录带有 `COLCON_IGNORE`，**不会**被 colcon 当作 ROS 包编译。

## 目录说明

```
recognition_service/
├── paddle_ocr/
│   ├── core.py              # 识别主流程（镜像校正、罗盘、箭头、数字调度）
│   ├── digit_reader.py      # 七段 LCD 模板匹配
│   ├── paths.py             # 配置/资源路径
│   ├── api_server.py        # FastAPI HTTP 服务
│   └── recognize_cli.py     # 命令行识别工具
├── config/
│   ├── rois.json            # 屏幕 ROI 标定
│   ├── compass.json         # 罗盘标定
│   ├── digit_slots.json     # 数码管切片比例
│   └── DEVICE.md            # 设备型号说明
├── assets/digit_templates/  # 数字模板（可自动生成）
├── examples/images/         # 测试截图
├── start_api_server.sh      # 启动脚本
└── setup.py                 # 可选 pip 安装
```

## 环境准备

```bash
# 在仓库根目录
conda env create -f environment.yml
conda activate ocr
```

可选安装命令行工具：

```bash
cd recognition_service
pip install -e .
```

## 启动服务

```bash
conda activate ocr
cd recognition_service
./start_api_server.sh
```

默认地址：`http://127.0.0.1:8000`

自定义监听地址：

```bash
PADDLE_OCR_API_HOST=0.0.0.0 PADDLE_OCR_API_PORT=8000 ./start_api_server.sh
```

## HTTP API

### `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

### `POST /v1/recognize`

```bash
curl -X POST http://127.0.0.1:8000/v1/recognize \
  -F "image=@examples/images/image0000000.bmp"
```

可选参数：`debug=true`、`frame_id=ros_frame_1`

成功响应示例：

```json
{
  "success": true,
  "data": {
    "signal_strength": "0.0%",
    "pipeline_current": "350 mA",
    "burial_depth": "140 m",
    "arrow_direction": "none",
    "compass_angle": "61°",
    "compass_angle_deg": 61.0
  },
  "meta": {
    "process_time_ms": 12.0,
    "fps": 83.33,
    "frame_id": ""
  }
}
```

### `GET /v1/config` / `PUT /v1/config`

读取或更新标定配置（ROI、罗盘）。

## 命令行识别

不启动 HTTP 服务、不使用 ROS，直接测试识别效果：

```bash
conda activate ocr
cd recognition_service

python -m paddle_ocr.recognize_cli examples/images/image0000000.bmp
python -m paddle_ocr.recognize_cli examples/images/image0000000.bmp --debug
```

`--debug` 会在 `recognition_service/output/` 下保存调试图像。

## 与 ROS 节点的关系

ROS 节点（`src/paddle_ocr/`）**不包含**本目录的识别代码，仅通过 HTTP 调用本服务：

```
ROS 节点  --POST /v1/recognize-->  本服务  --recognize()-->  JSON 结果
```

请确保 ROS 节点配置中的 `api_base_url` 与本服务地址一致。

## 换型标定

1. 修改 `config/DEVICE.md` 填写新型号信息
2. 更新 `config/rois.json`、`config/compass.json`、`config/digit_slots.json`
3. 删除 `assets/digit_templates/` 后运行一次识别，自动重建模板
4. 重启 HTTP 服务
