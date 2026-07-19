# 依赖说明

仓库 **[screen_ocr_ros2](https://github.com/Staaaaaaaaar/screen_ocr_ros2)** 分为 **ROS2 侧（C++）** 与 **识别 HTTP 服务（conda Python）** 两套环境，请分别安装，避免混用导致 ABI 冲突。

## ROS2 工作区（`screen_ocr` / `screen_ocr_msgs`）

### 系统要求

| 项目 | 版本 |
|------|------|
| 操作系统 | Ubuntu 22.04（Jammy），含 **x86_64 / arm64** |
| ROS2 | Humble Hawksbill |
| 编译器 | GCC 11+（支持 C++17） |

### apt 依赖

一键安装（推荐）：

```bash
./scripts/install_ros_deps.sh
```

或手动安装：

```bash
sudo apt update
sudo apt install -y \
  ros-humble-ros-base \
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  libcurl4-openssl-dev \
  nlohmann-json3-dev \
  python3-colcon-common-extensions
```

| 包名 | 用途 |
|------|------|
| `ros-humble-ros-base` | ROS2 核心（`rclcpp`、消息、launch 等） |
| `ros-humble-cv-bridge` | `sensor_msgs` ↔ OpenCV 图像转换 |
| `ros-humble-image-transport` | 图像话题常用组件（部分相机栈依赖） |
| `libcurl4-openssl-dev` | HTTP 客户端（编译 + 链接 libcurl） |
| `nlohmann-json3-dev` | 识别 API JSON 解析 |
| `python3-colcon-common-extensions` | `colcon build` 工作区编译 |

运行时还会自动拉取：`libopencv-*`（经 `cv_bridge`）、`libcurl4` 等。

### 编译

```bash
conda deactivate          # 重要：勿在 conda 下 colcon build
source /opt/ros/humble/setup.bash
cd ~/screen_ocr_ros2
colcon build
source install/setup.bash
```

---

## 识别 HTTP 服务（`recognition_service/`）

### 环境要求

| 项目 | 版本 |
|------|------|
| Python | 3.10 |
| 包管理 | conda（推荐）或 venv + pip |

### conda 依赖

```bash
cd recognition_service
conda env create -f environment.yml   # 环境名: ocr
conda activate ocr
```

### pip 依赖（`requirements.txt`）

| 包 | 版本 | 用途 |
|----|------|------|
| numpy | 1.23.5 | 数组与图像 buffer |
| opencv-python | 4.6.0.66 | ROI 裁剪、模板匹配、罗盘/箭头检测 |
| fastapi | 0.115.6 | HTTP API 框架 |
| uvicorn[standard] | 0.32.1 | ASGI 服务器 |
| python-multipart | 0.0.20 | 文件上传 |

可选：`pip install -e .` 安装识别库为可编辑包。

### 启动

```bash
conda activate ocr
cd recognition_service
./start_api_server.sh
```

---

## 环境隔离原则

| 场景 | 正确做法 |
|------|----------|
| `colcon build` / 运行 ROS 节点 | 系统 ROS2，`conda deactivate` |
| 运行识别 HTTP 服务 | `conda activate ocr` |
| arm64 机器狗部署 | ROS 用 C++ 节点；识别服务独立进程，经 HTTP 通信 |

`recognition_service/` 目录含 `COLCON_IGNORE`，不会被 colcon 编译。
